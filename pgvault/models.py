"""Shared Pydantic contracts used by PgVault scanners and reports."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class Severity(str, Enum):
    """Normalized severity levels for every PgVault finding."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RegulationRef(BaseModel):
    """Reference to a compliance framework, article, or requirement."""

    framework: str
    article: str | None = None
    description: str | None = None


class Finding(BaseModel):
    """Generic finding emitted by any PgVault scanner module."""

    id: str
    module: str
    category: str
    title: str
    description: str
    severity: Severity
    evidence: str
    recommendation: str
    remediation_sql: str | None = None
    regulation_refs: list[RegulationRef] = Field(default_factory=list)
    table_schema: str | None = None
    table_name: str | None = None
    column_name: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanWarning(BaseModel):
    """Non-fatal issue discovered during preflight or scanning."""

    source: str
    message: str
    detail: str | None = None


class ScanError(BaseModel):
    """Module-level error captured without stopping the full scan."""

    module: str
    message: str
    detail: str | None = None


class ColumnMeta(BaseModel):
    """Column metadata extracted from PostgreSQL catalog sources."""

    table_schema: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    table_type: str | None = None


class RoleMeta(BaseModel):
    """Role and membership metadata extracted from PostgreSQL."""

    role_name: str
    can_login: bool
    is_superuser: bool
    is_inherit: bool
    is_create_role: bool
    is_create_db: bool
    member_of: list[str] = Field(default_factory=list)


class FunctionMeta(BaseModel):
    """Function metadata used by security and privilege scanners."""

    schema_name: str
    function_name: str
    owner: str | None = None
    language: str | None = None
    security_definer: bool = False


class ExtensionMeta(BaseModel):
    """Installed PostgreSQL extension metadata."""

    name: str
    version: str | None = None
    schema_name: str | None = None


class SettingMeta(BaseModel):
    """Runtime setting metadata from `pg_settings`."""

    name: str
    setting: str
    unit: str | None = None
    source: str | None = None
    context: str | None = None
    vartype: str | None = None


class HbaRuleMeta(BaseModel):
    """Parsed row from `pg_hba_file_rules` when the view is available."""

    line_number: int | None = None
    rule_type: str | None = None
    database: list[str] = Field(default_factory=list)
    user: list[str] = Field(default_factory=list)
    address: str | None = None
    auth_method: str | None = None
    error: str | None = None


class CatalogSnapshot(BaseModel):
    """Read-only snapshot of database catalog metadata."""

    database_name: str
    current_user: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    columns: list[ColumnMeta] = Field(default_factory=list)
    roles: list[RoleMeta] = Field(default_factory=list)
    functions: list[FunctionMeta] = Field(default_factory=list)
    extensions: list[ExtensionMeta] = Field(default_factory=list)
    settings: list[SettingMeta] = Field(default_factory=list)
    hba_rules: list[HbaRuleMeta] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanResult(BaseModel):
    """Top-level result returned by PgVault scans and printed by the CLI."""

    scan_id: str
    database: str
    started_at: datetime
    completed_at: datetime
    snapshot: CatalogSnapshot | None = None
    findings: list[Finding] = Field(default_factory=list)
    warnings: list[ScanWarning] = Field(default_factory=list)
    errors: list[ScanError] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @computed_field
    @property
    def total_warnings(self) -> int:
        return len(self.warnings)

    @computed_field
    @property
    def total_errors(self) -> int:
        return len(self.errors)
