"""Tests para ConfigurationScanner - Auditor de configuración de seguridad."""

import pytest
from unittest.mock import AsyncMock, Mock
from pgvault.scanners.configuration_scanner import ConfigurationScanner
from pgvault.models import (
    CatalogSnapshot,
    PrivilegeMeta,
    RoleMeta,
    FunctionMeta,
    SettingMeta,
    HbaRuleMeta,
    ExtensionMeta,
)
from pgvault.modules import ScanContext


@pytest.fixture
def mock_context_clean():
    """Contexto de escaneo sin problemas de seguridad."""
    snapshot = CatalogSnapshot(
        database_name="testdb",
        current_user="testuser",
        roles=[
            RoleMeta(
                role_name="postgres",
                can_login=True,
                is_superuser=True,
                is_inherit=True,
                is_create_role=True,
                is_create_db=True,
            )
        ],
        functions=[
            FunctionMeta(
                schema_name="public",
                function_name="safe_func",
                security_definer=False,
            )
        ],
        settings=[
            SettingMeta(name="log_connections", setting="on"),
            SettingMeta(name="log_disconnections", setting="on"),
            SettingMeta(name="archive_mode", setting="on"),
        ],
        extensions=[],
        hba_rules=[
            HbaRuleMeta(
                line_number=1,
                rule_type="local",
                database=["all"],
                user=["all"],
                address=None,
                auth_method="md5",
                error=None,
            )
        ],
    )
    context = Mock(spec=ScanContext)
    context.snapshot = snapshot
    context.db = Mock()
    context.db.fetch = AsyncMock(return_value=[])
    return context


@pytest.fixture
def mock_context_with_issues():
    """Contexto de escaneo con problemas de seguridad detectables."""
    snapshot = CatalogSnapshot(
        database_name="testdb",
        current_user="testuser",
        roles=[
            RoleMeta(
                role_name="postgres",
                can_login=True,
                is_superuser=True,
                is_inherit=True,
                is_create_role=True,
                is_create_db=True,
            ),
            RoleMeta(
                role_name="admin",
                can_login=True,
                is_superuser=True,  # CFG-001: SUPERUSER innecesario
                is_inherit=True,
                is_create_role=False,
                is_create_db=False,
            ),
        ],
        functions=[
            FunctionMeta(
                schema_name="public",
                function_name="unsafe_definer",
                security_definer=True,  # CFG-002: SECURITY DEFINER sin search_path
            )
        ],
        settings=[
            SettingMeta(name="log_connections", setting="off"),  # CFG-003
            SettingMeta(name="log_disconnections", setting="off"),  # CFG-004
            SettingMeta(name="archive_mode", setting="off"),  # CFG-009: sin PITR
        ],
        extensions=[
            ExtensionMeta(name="dblink", version="1.2", schema_name="public"),  # CFG-007
        ],
        hba_rules=[
            HbaRuleMeta(
                line_number=9,
                rule_type="host",
                database=["all"],
                user=["all"],
                address="0.0.0.0/0",
                auth_method="trust",  # CFG-005: trust desde internet (CRITICAL)
                error=None,
            ),
            HbaRuleMeta(
                line_number=17,
                rule_type="local",
                database=["all"],
                user=["all"],
                address=None,
                auth_method="trust",  # CFG-005: trust local (HIGH)
                error=None,
            ),
        ],
        privileges=[
            PrivilegeMeta(
                object_type="table",
                object_schema="public",
                object_name="cards",
                grantee="reports_user",
                privilege_type="SELECT",
                grantable=False,
            ),  # CFG-010: acceso PCI sin necesidad (H05)
            PrivilegeMeta(
                object_type="table",
                object_schema="public",
                object_name="customers",
                grantee="PUBLIC",
                privilege_type="SELECT",
                grantable=False,
            ),  # CFG-011: PUBLIC con acceso a PII (H06)
        ],
    )
    context = Mock(spec=ScanContext)
    context.snapshot = snapshot
    context.db = Mock()
    context.db.fetch = AsyncMock(return_value=[{"rolname": "app_legacy"}])  # CFG-008: sin password
    return context


@pytest.mark.asyncio
async def test_scanner_name():
    """Verifica que el scanner tiene el nombre correcto."""
    scanner = ConfigurationScanner()
    assert scanner.name == "configuration"


@pytest.mark.asyncio
async def test_no_findings_on_clean_config(mock_context_clean):
    """No debe generar hallazgos en configuración limpia."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_clean)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_detects_superuser_roles(mock_context_with_issues):
    """Debe detectar roles SUPERUSER innecesarios (CFG-001)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg001_findings = [f for f in findings if f.id.startswith("CFG-001")]
    assert len(cfg001_findings) == 1
    assert cfg001_findings[0].severity == "HIGH"
    assert "admin" in cfg001_findings[0].evidence


@pytest.mark.asyncio
async def test_detects_security_definer_without_search_path(mock_context_with_issues):
    """Debe detectar funciones SECURITY DEFINER inseguras (CFG-002)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg002_findings = [f for f in findings if f.id.startswith("CFG-002")]
    assert len(cfg002_findings) == 1
    assert cfg002_findings[0].severity == "MEDIUM"
    assert "unsafe_definer" in cfg002_findings[0].evidence


@pytest.mark.asyncio
async def test_detects_logging_disabled(mock_context_with_issues):
    """Debe detectar logging desactivado (CFG-003 y CFG-004)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg003_findings = [f for f in findings if f.id == "CFG-003-log-connections"]
    cfg004_findings = [f for f in findings if f.id == "CFG-004-log-disconnections"]
    
    assert len(cfg003_findings) == 1
    assert cfg003_findings[0].severity == "HIGH"
    
    assert len(cfg004_findings) == 1
    assert cfg004_findings[0].severity == "MEDIUM"


@pytest.mark.asyncio
async def test_detects_trust_authentication(mock_context_with_issues):
    """Debe detectar autenticación trust insegura (CFG-005)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg005_findings = [f for f in findings if f.id.startswith("CFG-005")]
    assert len(cfg005_findings) == 2
    
    # Verificar severidad correcta
    critical_findings = [f for f in cfg005_findings if f.severity == "CRITICAL"]
    high_findings = [f for f in cfg005_findings if f.severity == "HIGH"]
    
    assert len(critical_findings) == 1  # 0.0.0.0/0
    assert len(high_findings) == 1  # local


@pytest.mark.asyncio
async def test_total_findings_count(mock_context_with_issues):
    """Debe detectar todos los problemas plantados (9 hallazgos)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    # 1 CFG-001 + 1 CFG-002 + 1 CFG-003 + 1 CFG-004 + 2 CFG-005 + 1 CFG-006 + 1 CFG-007
    # + 1 CFG-008 + 1 CFG-009 + 1 CFG-010 + 1 CFG-011 = 12 hallazgos
    assert len(findings) == 12


@pytest.mark.asyncio
async def test_all_findings_have_required_fields(mock_context_with_issues):
    """Todos los hallazgos deben tener campos requeridos."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    for finding in findings:
        assert finding.id
        assert finding.module == "configuration"
        assert finding.category
        assert finding.title
        assert finding.description
        assert finding.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        assert finding.evidence
        assert finding.recommendation
        # remediation_sql puede ser None para algunos hallazgos
        # regulation_refs puede ser lista vacía


@pytest.mark.asyncio
async def test_detects_weak_credential_role_names(mock_context_with_issues):
    """Debe detectar roles con nombres sospechosos (CFG-006)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg006_findings = [f for f in findings if f.id.startswith("CFG-006")]
    assert len(cfg006_findings) == 1
    assert cfg006_findings[0].severity == "HIGH"
    assert "admin" in cfg006_findings[0].title.lower()


@pytest.mark.asyncio
async def test_detects_dangerous_extensions(mock_context_with_issues):
    """Debe detectar extensiones peligrosas instaladas (CFG-007)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)
    
    cfg007_findings = [f for f in findings if f.id.startswith("CFG-007")]
    assert len(cfg007_findings) == 1
    assert cfg007_findings[0].severity == "MEDIUM"
    assert "dblink" in cfg007_findings[0].evidence


@pytest.mark.asyncio
async def test_detects_role_without_password(mock_context_with_issues):
    """Debe detectar roles sin contraseña configurada (CFG-008)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)

    cfg008_findings = [f for f in findings if f.id.startswith("CFG-008")]
    assert len(cfg008_findings) == 1
    assert cfg008_findings[0].severity == "HIGH"
    assert "app_legacy" in cfg008_findings[0].id


@pytest.mark.asyncio
async def test_no_cfg008_when_db_inaccessible(mock_context_clean):
    """Si pg_authid no es accesible, CFG-008 debe omitirse silenciosamente."""
    mock_context_clean.db.fetch = AsyncMock(side_effect=Exception("permission denied"))
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_clean)
    cfg008_findings = [f for f in findings if f.id.startswith("CFG-008")]
    assert len(cfg008_findings) == 0


@pytest.mark.asyncio
async def test_detects_archive_mode_off(mock_context_with_issues):
    """Debe detectar archive_mode desactivado (CFG-009)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)

    cfg009_findings = [f for f in findings if f.id == "CFG-009-archive-mode"]
    assert len(cfg009_findings) == 1
    assert cfg009_findings[0].severity == "HIGH"
    assert "archive_mode" in cfg009_findings[0].evidence


@pytest.mark.asyncio
async def test_detects_pci_table_grants(mock_context_with_issues):
    """Debe detectar roles con SELECT sobre tablas PCI (CFG-010)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)

    cfg010_findings = [f for f in findings if f.id.startswith("CFG-010")]
    assert len(cfg010_findings) == 1
    assert cfg010_findings[0].severity == "CRITICAL"
    assert "reports_user" in cfg010_findings[0].title
    assert "cards" in cfg010_findings[0].title


@pytest.mark.asyncio
async def test_detects_public_table_grants(mock_context_with_issues):
    """Debe detectar grants SELECT a PUBLIC sobre tablas (CFG-011)."""
    scanner = ConfigurationScanner()
    findings = await scanner.run(mock_context_with_issues)

    cfg011_findings = [f for f in findings if f.id.startswith("CFG-011")]
    assert len(cfg011_findings) == 1
    assert cfg011_findings[0].severity == "HIGH"
    assert "customers" in cfg011_findings[0].title
