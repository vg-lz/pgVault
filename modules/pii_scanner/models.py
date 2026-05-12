from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RegulationRef(BaseModel):
    framework: str
    article: str
    description: str


class Finding(BaseModel):
    id: str
    module: str = "pii"
    table_schema: str = "public"
    table_name: str
    column_name: str
    detected_type: str
    severity: Severity
    confidence_score: float = Field(ge=0.0, le=1.0)
    detection_method: str
    evidence: str
    sample_size: Optional[int] = None
    match_ratio: Optional[float] = None
    recommendation: str
    remediation_sql: Optional[str] = None
    regulation_refs: list[RegulationRef] = []

    class Config:
        use_enum_values = True


class ColumnMeta(BaseModel):
    table_schema: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int


class ScanResult(BaseModel):
    scan_id: str
    database: str
    total_columns_scanned: int
    total_findings: int
    findings: list[Finding]
    scan_duration_seconds: float
    errors: list[str] = []