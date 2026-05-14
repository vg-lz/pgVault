"""Scanner module contract and scan context for PgVault extensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pgvault.config import PgVaultConfig
from pgvault.db import DatabaseClient
from pgvault.models import CatalogSnapshot, Finding, ScanWarning


@dataclass
class ScanContext:
    """Shared runtime data passed to every scanner module.

    Modules should read catalog metadata from ``context.snapshot`` first and
    only run extra SQL through ``context.db`` when metadata is not enough. Any
    SQL must pass PgVault's read-only guard. Modules return ``list[Finding]``
    using ``pgvault.models.Finding`` and append non-fatal limitations to
    ``context.warnings`` when a check cannot run completely.
    """

    config: PgVaultConfig
    db: DatabaseClient
    snapshot: CatalogSnapshot
    scan_id: str
    warnings: list[ScanWarning] = field(default_factory=list)


class ScannerModule(Protocol):
    """Protocol implemented by every scanner that emits canonical findings."""

    name: str

    async def run(self, context: ScanContext) -> list[Finding]:
        ...


def get_default_modules() -> list[ScannerModule]:
    """Return scanner modules included in the base PgVault runtime."""

    from modules.pii_scanner.scanner import PiiScanner
    from pgvault.scanners.configuration_scanner import ConfigurationScanner

    return [
        PiiScanner(),
        ConfigurationScanner(),
    ]
