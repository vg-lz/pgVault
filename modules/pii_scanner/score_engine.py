from dataclasses import dataclass

from pgvault.models import Severity

W_NAME = 0.35
W_CONTENT = 0.55
W_CONTEXT = 0.10

THRESHOLD_CRITICAL = 0.80
THRESHOLD_HIGH = 0.60
THRESHOLD_MEDIUM = 0.40
THRESHOLD_SKIP = 0.40
MIN_RELIABLE_SAMPLE = 50
THRESHOLD_EPSILON = 0.005


@dataclass
class ScoreInput:
    name_score: float
    content_score: float
    sample_size: int
    data_type: str
    table_name: str
    column_name: str
    severity_hint: str


@dataclass
class ScoreOutput:
    final_score: float
    severity: Severity
    context_score: float
    should_report: bool
    score_breakdown: dict


def _calculate_context_score(data_type: str, table_name: str, column_name: str) -> float:
    HIGH_RISK_TABLES = {
        "clientes", "customers", "usuarios", "users",
        "tarjetas", "cards", "pagos", "payments",
        "transacciones", "transactions",
    }
    AUDIT_TABLES = {
        "logs", "audit", "auditoria", "eventos", "events",
        "history", "historial",
    }
    table_lower = table_name.lower()
    if any(t in table_lower for t in HIGH_RISK_TABLES):
        return 1.0
    if any(t in table_lower for t in AUDIT_TABLES):
        return 0.5
    return 0.7


def _adjust_for_sample_size(content_score: float, sample_size: int) -> float:
    if sample_size == 0:
        return 0.0
    if sample_size < MIN_RELIABLE_SAMPLE:
        factor = sample_size / MIN_RELIABLE_SAMPLE
        return content_score * factor
    return content_score


def calculate_score(inp: ScoreInput) -> ScoreOutput:
    adjusted_content = _adjust_for_sample_size(inp.content_score, inp.sample_size)
    context_score = _calculate_context_score(inp.data_type, inp.table_name, inp.column_name)

    final_score = (
        W_NAME * inp.name_score +
        W_CONTENT * adjusted_content +
        W_CONTEXT * context_score
    )
    final_score = round(min(1.0, max(0.0, final_score)), 4)

    if final_score >= THRESHOLD_CRITICAL - THRESHOLD_EPSILON:
        severity = Severity.CRITICAL
    elif final_score >= THRESHOLD_HIGH:
        severity = Severity.HIGH
    elif final_score >= THRESHOLD_MEDIUM:
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    should_report = final_score >= THRESHOLD_SKIP

    breakdown = {
        "name_score": inp.name_score,
        "name_contribution": round(W_NAME * inp.name_score, 4),
        "content_score_raw": inp.content_score,
        "content_score_adjusted": round(adjusted_content, 4),
        "content_contribution": round(W_CONTENT * adjusted_content, 4),
        "context_score": round(context_score, 4),
        "context_contribution": round(W_CONTEXT * context_score, 4),
        "final_score": final_score,
        "sample_size": inp.sample_size,
    }

    return ScoreOutput(
        final_score=final_score,
        severity=severity,
        context_score=context_score,
        should_report=should_report,
        score_breakdown=breakdown,
    )
