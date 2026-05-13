"""PII scanner integrated with the PgVault module contract."""

from __future__ import annotations

import asyncpg

from modules.name_scanner import NameMatch, scan_by_name
from modules.pii_scanner.content_validators import match_ratio
from modules.pii_scanner.score_engine import ScoreInput, calculate_score
from pgvault.db import qualified_name, quote_identifier
from pgvault.models import Finding, ScanWarning, Severity
from pgvault.modules import ScanContext


class PiiScanner:
    """Detect likely PII columns using catalog names and optional safe sampling."""

    name = "pii"

    async def run(self, context: ScanContext) -> list[Finding]:
        findings: list[Finding] = []
        for match in scan_by_name(context.snapshot.columns):
            sample_size = 0
            content_ratio = 0.0
            if context.config.sample_limit > 0 and self._can_sample(match):
                sample_size, content_ratio = await self._sample_content_ratio(context, match)
            findings.append(self._finding_from_match(match, sample_size, content_ratio))
        return findings

    @staticmethod
    def _can_sample(match: NameMatch) -> bool:
        return (match.column.table_type or "BASE TABLE") in {"BASE TABLE", "PARTITIONED TABLE"}

    async def _sample_content_ratio(
        self,
        context: ScanContext,
        match: NameMatch,
    ) -> tuple[int, float]:
        column = match.column
        relation = qualified_name(column.table_schema, column.table_name)
        identifier = quote_identifier(column.column_name)
        sql = f"""
            SELECT {identifier}::text AS value
            FROM {relation}
            WHERE {identifier} IS NOT NULL
            LIMIT $1
        """
        try:
            rows = await context.db.fetch(sql, context.config.sample_limit)
        except (asyncpg.PostgresError, ValueError, RuntimeError) as exc:
            context.warnings.append(
                ScanWarning(
                    source=f"{self.name}:{column.table_schema}.{column.table_name}.{column.column_name}",
                    message="PII content sampling skipped for this column.",
                    detail=str(exc),
                )
            )
            return 0, 0.0
        sample = [str(row["value"]) for row in rows if row["value"] is not None]
        return len(sample), match_ratio(sample, match.data_type)

    def _finding_from_match(
        self,
        match: NameMatch,
        sample_size: int,
        content_ratio: float,
    ) -> Finding:
        column = match.column
        score = calculate_score(
            ScoreInput(
                name_score=match.name_score,
                content_score=content_ratio,
                sample_size=sample_size,
                data_type=match.data_type,
                table_name=column.table_name,
                column_name=column.column_name,
                severity_hint=match.severity_hint,
            )
        )
        severity = self._max_severity(Severity(match.severity_hint), score.severity)
        confidence = max(match.name_score, score.final_score)
        evidence = (
            f"Column name matches {match.data_type} pattern. "
            f"Sampled non-null rows: {sample_size}. "
            f"Content match ratio: {content_ratio:.2f}. "
            "Evidence is aggregated; raw values are intentionally omitted."
        )
        return Finding(
            id=self._finding_id(match),
            module=self.name,
            category="PII",
            title=f"Potential {match.data_type} data in column {column.table_schema}.{column.table_name}.{column.column_name}",
            description=(
                "The column name suggests it may store personal, financial, or secret data. "
                "Review access controls, retention, masking, and encryption requirements."
            ),
            severity=severity,
            evidence=evidence,
            recommendation=match.recommendation,
            regulation_refs=list(match.regulation_refs),
            table_schema=column.table_schema,
            table_name=column.table_name,
            column_name=column.column_name,
            confidence_score=round(confidence, 4),
            metadata={
                "pii_type": match.data_type,
                "matched_pattern": match.matched_pattern,
                "name_score": match.name_score,
                "content_match_ratio": content_ratio,
                "sample_size": sample_size,
                "score_breakdown": score.score_breakdown,
            },
        )

    @staticmethod
    def _finding_id(match: NameMatch) -> str:
        column = match.column
        raw = f"pii:{column.table_schema}:{column.table_name}:{column.column_name}:{match.data_type}"
        return "".join(char.lower() if char.isalnum() else "-" for char in raw).strip("-")

    @staticmethod
    def _max_severity(left: Severity, right: Severity) -> Severity:
        order: dict[Severity, int] = {
            Severity.LOW: 0,
            Severity.MEDIUM: 1,
            Severity.HIGH: 2,
            Severity.CRITICAL: 3,
        }
        return left if order[left] >= order[right] else right
