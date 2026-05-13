"""Scanner module contract and scan context for PgVault extensions."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Protocol

from pgvault.config import PgVaultConfig
from pgvault.db import DatabaseClient
from pgvault.models import CatalogSnapshot, Finding, ScanWarning


@dataclass
class ScanContext:
    """Shared runtime data passed to every scanner module."""

    config: PgVaultConfig
    db: DatabaseClient
    snapshot: CatalogSnapshot
    scan_id: str
    warnings: list[ScanWarning] = field(default_factory=list)


class ScannerModule(Protocol):
    """Protocol implemented by every scanner that emits findings."""

    name: str

    async def run(self, context: ScanContext) -> list[Finding]:
        ...


class CatalogBaselineScanner:
    """Baseline scanner registered by default until domain modules are added."""

    name = "catalog_baseline"

    async def run(self, context: ScanContext) -> list[Finding]:
        return []


def _load_optional_configuration_scanner() -> ScannerModule | None:
    """Carga el escáner de configuración solo si existe en este checkout."""

    try:
        module = importlib.import_module("pgvault.scanners.configuration_scanner")
        scanner_class = getattr(module, "ConfigurationScanner")
    except Exception:
        return None
    return scanner_class()


def get_default_modules() -> list[ScannerModule]:
    """Return scanner modules included in the base PgVault runtime."""

    modules: list[ScannerModule] = [CatalogBaselineScanner()]
    configuration_scanner = _load_optional_configuration_scanner()
    if configuration_scanner is not None:
        modules.append(configuration_scanner)
    return modules
