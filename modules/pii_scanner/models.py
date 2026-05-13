"""Compatibility exports for the PII scanner.

The shared model contract now lives in `pgvault.models`. This file remains so
older imports from `modules.pii_scanner.models` continue to resolve while the
scanner code uses the central PgVault models.
"""

from pgvault.models import ColumnMeta, Finding, RegulationRef, ScanResult, Severity

__all__ = [
    "ColumnMeta",
    "Finding",
    "RegulationRef",
    "ScanResult",
    "Severity",
]
