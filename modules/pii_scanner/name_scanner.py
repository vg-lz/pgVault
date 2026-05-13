"""Compatibility wrapper for PII name-based detection.

The implementation currently lives in ``modules.name_scanner`` so legacy
imports keep working. New PII code should import through this package path.
"""

from modules.name_scanner import (  # noqa: F401
    COLUMN_WHITELIST,
    NAME_PATTERNS,
    NameMatch,
    NamePattern,
    scan_by_name,
)

__all__ = [
    "COLUMN_WHITELIST",
    "NAME_PATTERNS",
    "NameMatch",
    "NamePattern",
    "scan_by_name",
]
