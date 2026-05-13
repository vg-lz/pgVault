import asyncpg
import uuid
import time
import logging
from dataclasses import dataclass
from typing import Optional

from .models import Finding, ScanResult, RegulationRef
from .inventory import get_all_columns, get_table_row_count
from .name_scanner import scan_by_name
from .content_sampler import sample_column
from .score_engine import calculate_score, ScoreInput

logger = logging.getLogger(__name__)


@dataclass
class PiiScanConfig:
    min_confidence_score: float = 0.40
    max_tables: Optional[int] = None
    enable_ai_classifier: bool = False
    skip_schemas: list = None

    def __post_init__(self):
        if self.skip_schemas is None:
            self.skip_schemas = []


REGULATION_MAP: dict[str, list[RegulationRef]] = {
    "CVV": [RegulationRef(framework="PCI-DSS", article="Req. 3.2",
                          description="Prohibido almacenar CVV tras la autorización.")],
    "CARD_NUMBER": [RegulationRef(framework="PCI-DSS", article="Req. 3",
                                  description="Proteger datos de titulares de tarjetas.")],
    "PASSWORD": [RegulationRef(framework="LFPDPPP", article="Art. 19",
                               description="Obligación de seguridad sobre datos personales.")],
    "CURP": [
        RegulationRef(framework="LFPDPPP", article="Art. 3",
                      description="CURP es dato personal identificable."),
        RegulationRef(framework="LFPDPPP", article="Art. 19",
                      description="Obligación de seguridad sobre datos personales."),
    ],
    "RFC": [RegulationRef(framework="LFPDPPP", article="Art. 3",
                          description="RFC es dato personal identificable.")],
    "EMAIL": [RegulationRef(framework="LFPDPPP", article="Art. 3",
                            description="Email es dato personal de contacto.")],
    "PHONE": [RegulationRef(framework="LFPDPPP", article="Art. 3",
                            description="Teléfono es dato personal de contacto.")],
    "TOKEN": [RegulationRef(framework="CNBV", article="Disposición 6a",
                            description="Seguridad de credenciales en entidades financieras.")],
    "CLABE": [
        RegulationRef(framework="CNBV", article="Disposición 6a",
                      description="Datos bancarios regulados por CNBV."),
        RegulationRef(framework="PCI-DSS", article="Req. 3",
                      description="Protección de datos bancarios en reposo."),
    ],
    "SSN": [RegulationRef(framework="LFPDPPP", article="Art. 3",
                          description="NSS es dato personal sensible.")],
}

REMEDIATION_SQL_MAP: dict[str, str] = {
    "CVV": "ALTER TABLE {schema}.{table} DROP COLUMN {column};",
    "PASSWORD": (
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;\n"
        "UPDATE {schema}.{table} SET {column} = crypt({column}, gen_salt('bf', 10));"
    ),
    "TOKEN": (
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;\n"
        "UPDATE {schema}.{table} SET {column} = encode(hmac({column}::bytea, 'secret_key', 'sha256'), 'hex');"
    ),
    "DEFAULT": (
        "ALTER TABLE {schema}.{table} ENABLE ROW LEVEL SECURITY;\n"
        "CREATE POLICY {table}_pii_access ON {schema}.{table}\n"
        "  USING (current_user = 'authorized_role');"
    ),
}


def _build_remediation_sql(data_type: str, schema: str, table: str, column: str) -> str:
    template = REMEDIATION_SQL_MAP.get(data_type, REMEDIATION_SQL_MAP["DEFAULT"])
    return template.format(schema=schema, table=table, column=column)


def _build_finding_id(schema: str, table: str, column: str, data_type: str) -> str:
    return f"PII-{schema}-{table}-{column}-{data_type}".lower().replace("_", "-")


async def run_pii_scan(
    conn: asyncpg.Connection,
    config: PiiScanConfig = None,
    database_name: str = "unknown",
) -> ScanResult:
    if config is None:
        config = PiiScanConfig()

    scan_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    findings: list[Finding] = []
    errors: list[str] = []

    logger.info(f"[{scan_id}] Iniciando PII scan en {database_name}")

    try:
        all_columns = await get_all_columns(conn)
        logger.info(f"[{scan_id}] {len(all_columns)} columnas encontradas")
    except Exception as e:
        errors.append(f"Error en inventario de columnas: {str(e)}")
        return ScanResult(
            scan_id=scan_id, database=database_name,
            total_columns_scanned=0, total_findings=0,
            findings=[], scan_duration_seconds=0.0, errors=errors,
        )

    if config.skip_schemas:
        all_columns = [c for c in all_columns if c.table_schema not in config.skip_schemas]

    name_matches = scan_by_name(all_columns)
    logger.info(f"[{scan_id}] {len(name_matches)} candidatos por nombre")

    seen_findings: set[str] = set()

    for match in name_matches:
        col = match.column
        finding_key = f"{col.table_schema}.{col.table_name}.{col.column_name}"

        if finding_key in seen_findings:
            continue
        seen_findings.add(finding_key)

        try:
            total_rows = await get_table_row_count(conn, col.table_schema, col.table_name)

            sample_result = await sample_column(
                conn=conn,
                schema=col.table_schema,
                table=col.table_name,
                column=col.column_name,
                data_type=match.data_type,
                total_rows_estimate=total_rows,
            )

            score_input = ScoreInput(
                name_score=match.name_score,
                content_score=sample_result.content_score,
                sample_size=sample_result.sample_size,
                data_type=match.data_type,
                table_name=col.table_name,
                column_name=col.column_name,
                severity_hint=match.severity_hint,
            )
            score_output = calculate_score(score_input)

            if not score_output.should_report:
                continue

            if sample_result.sample_size > 0 and sample_result.ratio > 0:
                detection_method = "name_match + content_match"
                evidence = (
                    f"Columna '{col.column_name}' detectada por nombre (score: {match.name_score}). "
                    f"Sampling: {sample_result.valid_count}/{sample_result.sample_size} filas "
                    f"({sample_result.ratio*100:.1f}%) contienen {match.data_type} válidos."
                )
            else:
                detection_method = "name_match"
                evidence = (
                    f"Columna '{col.column_name}' detectada por nombre (score: {match.name_score}). "
                    f"Sin datos para content sampling."
                )

            finding = Finding(
                id=_build_finding_id(col.table_schema, col.table_name, col.column_name, match.data_type),
                module="pii",
                table_schema=col.table_schema,
                table_name=col.table_name,
                column_name=col.column_name,
                detected_type=match.data_type,
                severity=score_output.severity,
                confidence_score=score_output.final_score,
                detection_method=detection_method,
                evidence=evidence,
                sample_size=sample_result.sample_size,
                match_ratio=sample_result.ratio,
                recommendation=match.recommendation,
                remediation_sql=_build_remediation_sql(
                    match.data_type, col.table_schema, col.table_name, col.column_name
                ),
                regulation_refs=list(match.regulation_refs) + REGULATION_MAP.get(match.data_type, []),
            )
            findings.append(finding)

        except Exception as e:
            err_msg = f"Error escaneando {finding_key}: {str(e)}"
            logger.error(f"[{scan_id}] {err_msg}")
            errors.append(err_msg)

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 9), -f.confidence_score))

    duration = round(time.time() - start_time, 2)
    logger.info(f"[{scan_id}] Scan completo: {len(findings)} hallazgos en {duration}s")

    return ScanResult(
        scan_id=scan_id,
        database=database_name,
        total_columns_scanned=len(all_columns),
        total_findings=len(findings),
        findings=findings,
        scan_duration_seconds=duration,
        errors=errors,
    )