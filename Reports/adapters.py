"""Adapters from PgVault canonical models to legacy report dictionaries."""

from __future__ import annotations

from pgvault.models import Finding, ScanResult


def finding_to_report_dict(finding: Finding) -> dict[str, object]:
    """Return the minimum dictionary shape expected by legacy report code."""

    return {
        "id": finding.id,
        "module": finding.module,
        "category": finding.category,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity.value.lower(),
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
        "remediation_sql": finding.remediation_sql,
        "regulation_refs": [ref.model_dump() for ref in finding.regulation_refs],
        "regulations": [
            ref.framework if ref.article is None else f"{ref.framework} {ref.article}"
            for ref in finding.regulation_refs
        ],
        "table_schema": finding.table_schema,
        "table_name": finding.table_name,
        "column_name": finding.column_name,
        "confidence_score": finding.confidence_score,
        "metadata": finding.metadata,
    }


def scan_result_to_report_findings(result: ScanResult) -> list[dict[str, object]]:
    """Convert ``ScanResult.findings`` for Integrante 4's current report code."""

    return [finding_to_report_dict(finding) for finding in result.findings]
