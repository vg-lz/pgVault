"""
PII Scanner — Modelos de datos compartidos con el equipo PgVault.
Todos los módulos importan Finding y Severity desde aquí.
"""

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
    """Referencia a un artículo o requisito regulatorio."""
    framework: str           # "LFPDPPP" | "PCI-DSS" | "CNBV"
    article: str             # "Art. 3" | "Req. 3.2"
    description: str         # Texto breve del requisito


class Finding(BaseModel):
    """
    Hallazgo individual generado por cualquier módulo de PgVault.
    El módulo de reportes consume esta estructura directamente.
    """
    id: str                              # Ej: "PII-clientes-email-001"
    module: str = "pii"                  # "pii" | "config" | "privileges"
    table_schema: str = "public"
    table_name: str
    column_name: str
    detected_type: str                   # "EMAIL" | "CURP" | "CVV" | ...
    severity: Severity
    confidence_score: float = Field(ge=0.0, le=1.0)

    # Evidencia para el reporte técnico
    detection_method: str                # "name_match" | "content_match" | "ai_classifier"
    evidence: str                        # Descripción textual de la evidencia
    sample_size: Optional[int] = None    # Filas analizadas en el sampling
    match_ratio: Optional[float] = None  # % de filas que coincidieron con el patrón

    # Recomendación con SQL ejecutable
    recommendation: str
    remediation_sql: Optional[str] = None

    # Mapeo regulatorio
    regulation_refs: list[RegulationRef] = []

    class Config:
        use_enum_values = True


class ColumnMeta(BaseModel):
    """Metadata de una columna extraída del catálogo de Postgres."""
    table_schema: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int


class ScanResult(BaseModel):
    """Resultado completo de un scan del módulo PII."""
    scan_id: str
    database: str
    total_columns_scanned: int
    total_findings: int
    findings: list[Finding]
    scan_duration_seconds: float
    errors: list[str] = []
