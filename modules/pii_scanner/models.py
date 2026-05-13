"""Compatibility exports for the PII scanner.

The shared model contract now lives in `pgvault.models`. This file remains so
older imports from `modules.pii_scanner.models` continue to resolve while the
scanner code uses the central PgVault models.
"""

from pgvault.models import (
    CatalogSnapshot,
    ColumnMeta,
    ExtensionMeta,
    Finding,
    FunctionMeta,
    HbaRuleMeta,
    PrivilegeMeta,
    RegulationRef,
    RlsMeta,
    RoleMembershipMeta,
    RoleMeta,
    ScanError,
    ScanResult,
    ScanWarning,
    SchemaMeta,
    SettingMeta,
    Severity,
    TableMeta,
)

__all__ = [
    "ColumnMeta",
    "CatalogSnapshot",
    "ExtensionMeta",
    "Finding",
    "FunctionMeta",
    "HbaRuleMeta",
    "PrivilegeMeta",
    "RegulationRef",
    "RlsMeta",
    "RoleMembershipMeta",
    "RoleMeta",
    "ScanError",
    "ScanResult",
    "ScanWarning",
    "SchemaMeta",
    "SettingMeta",
    "Severity",
    "TableMeta",
]
