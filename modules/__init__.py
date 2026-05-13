"""Compatibility exports for legacy ``modules`` imports.

Canonical PgVault contracts live in ``pgvault.models``. Keep this package
lightweight so importing subpackages such as ``modules.pii_scanner`` does not
eagerly load older experimental pipeline code.
"""

from pgvault.models import ColumnMeta, Finding, RegulationRef, ScanResult, Severity

__all__ = [
    "Finding",
    "Severity",
    "ColumnMeta",
    "ScanResult",
    "RegulationRef",
]
