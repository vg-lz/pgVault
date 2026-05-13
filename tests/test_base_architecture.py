from __future__ import annotations

import pytest

from modules.pii_scanner.scanner import PiiScanner
from pgvault.config import PgVaultConfig
from pgvault.db import UnsafeQueryError, assert_readonly_query, qualified_name, quote_identifier
from pgvault.models import CatalogSnapshot, ColumnMeta, Finding, ScanResult, Severity
from pgvault.modules import ScanContext, get_default_modules
from pgvault.orchestrator import run_scan


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "SHOW server_version",
        "EXPLAIN SELECT 1",
        "SELECT ';' AS semicolon",
    ],
)
def test_readonly_guard_allows_safe_reads(sql: str):
    assert_readonly_query(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO x VALUES (1)",
        "UPDATE x SET a = 1",
        "DELETE FROM x",
        "DROP TABLE x",
        "ALTER TABLE x ADD COLUMN y int",
        "CREATE TABLE x (id int)",
        "SELECT 1; SELECT 2",
        "EXPLAIN ANALYZE SELECT 1",
        "EXPLAIN INSERT INTO x VALUES (1)",
        "WITH deleted AS (DELETE FROM x RETURNING *) SELECT * FROM deleted",
    ],
)
def test_readonly_guard_blocks_unsafe_sql(sql: str):
    with pytest.raises(UnsafeQueryError):
        assert_readonly_query(sql)


def test_quote_identifier_and_qualified_name_escape_names():
    assert quote_identifier('customer"data') == '"customer""data"'
    assert qualified_name("public", 'weird"table') == '"public"."weird""table"'
    with pytest.raises(ValueError):
        quote_identifier("")


def test_default_modules_include_pii_scanner():
    modules = get_default_modules()
    assert any(isinstance(module, PiiScanner) for module in modules)


class FakeDb:
    async def fetch(self, sql: str, *args):
        assert_readonly_query(sql)
        return [{"value": "ana@example.com"}, {"value": "not-email"}]


def _config() -> PgVaultConfig:
    return PgVaultConfig(pg_password=None, sample_limit=10, _env_file=None)


def _snapshot(columns: list[ColumnMeta]) -> CatalogSnapshot:
    return CatalogSnapshot(
        database_name="testdb",
        current_user="readonly",
        columns=columns,
    )


@pytest.mark.asyncio
async def test_pii_scanner_name_detection_returns_canonical_findings():
    scanner = PiiScanner()
    context = ScanContext(
        config=_config(),
        db=FakeDb(),
        snapshot=_snapshot(
            [
                ColumnMeta(
                    table_schema="public",
                    table_name="customers",
                    column_name="email",
                    data_type="text",
                    is_nullable=True,
                    ordinal_position=1,
                    table_type="BASE TABLE",
                )
            ]
        ),
        scan_id="scan-1",
    )

    findings = await scanner.run(context)

    assert len(findings) == 1
    assert isinstance(findings[0], Finding)
    assert findings[0].module == "pii"
    assert findings[0].severity in set(Severity)
    assert findings[0].table_schema == "public"
    assert findings[0].column_name == "email"


@pytest.mark.asyncio
async def test_pii_scanner_whitelisted_columns_do_not_generate_findings():
    scanner = PiiScanner()
    context = ScanContext(
        config=_config(),
        db=FakeDb(),
        snapshot=_snapshot(
            [
                ColumnMeta(
                    table_schema="public",
                    table_name="customers",
                    column_name="id",
                    data_type="uuid",
                    is_nullable=False,
                    ordinal_position=1,
                    table_type="BASE TABLE",
                )
            ]
        ),
        scan_id="scan-1",
    )

    assert await scanner.run(context) == []


@pytest.mark.asyncio
async def test_pii_evidence_omits_sensitive_values():
    scanner = PiiScanner()
    context = ScanContext(
        config=_config(),
        db=FakeDb(),
        snapshot=_snapshot(
            [
                ColumnMeta(
                    table_schema="public",
                    table_name="customers",
                    column_name="email",
                    data_type="text",
                    is_nullable=True,
                    ordinal_position=1,
                    table_type="BASE TABLE",
                )
            ]
        ),
        scan_id="scan-1",
    )

    finding = (await scanner.run(context))[0]

    assert "ana@example.com" not in finding.evidence
    assert "Content match ratio" in finding.evidence


class FailingModule:
    name = "failing"

    async def run(self, context):
        raise RuntimeError("boom")


class FindingModule:
    name = "ok"

    async def run(self, context):
        return [
            Finding(
                id="ok-1",
                module=self.name,
                category="TEST",
                title="Test finding",
                description="Synthetic finding.",
                severity=Severity.LOW,
                evidence="No sensitive evidence.",
                recommendation="No action.",
            )
        ]


class OrchestratorFakeDb:
    async def fetch(self, sql: str, *args):
        assert_readonly_query(sql)
        return []

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_orchestrator_continues_when_module_fails():
    snapshot = CatalogSnapshot(database_name="testdb", current_user="readonly")

    result = await run_scan(
        config=_config(),
        modules=[FailingModule(), FindingModule()],
        db=OrchestratorFakeDb(),
        snapshot=snapshot,
    )

    assert isinstance(result, ScanResult)
    assert len(result.findings) == 1
    assert len(result.errors) == 1
    assert result.errors[0].module == "failing"
    assert result.metadata["error_count"] == 1
    assert result.metadata["finding_count"] == 1
