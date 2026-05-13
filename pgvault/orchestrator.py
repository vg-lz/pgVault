"""Main PgVault scan orchestration flow."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from pgvault.config import PgVaultConfig, load_config
from pgvault.db import DatabaseClient
from pgvault.models import CatalogSnapshot, Finding, ScanError, ScanResult, ScanWarning
from pgvault.modules import ScanContext, ScannerModule, get_default_modules
from pgvault.snapshot import extract_catalog_snapshot, preflight_catalog_access


async def run_scan(
    config: PgVaultConfig | None = None,
    modules: Sequence[ScannerModule] | None = None,
    db: DatabaseClient | None = None,
    snapshot: CatalogSnapshot | None = None,
) -> ScanResult:
    """Run a complete PgVault scan and return a normalized result."""

    config = config or load_config()
    scan_id = str(uuid4())
    started_at = datetime.now(UTC)
    warnings: list[ScanWarning] = []
    errors: list[ScanError] = []
    findings: list[Finding] = []
    active_modules = list(modules) if modules is not None else get_default_modules()

    owns_db = db is None
    db = db or DatabaseClient(config)

    try:
        if owns_db:
            await db.connect()
        warnings.extend(await preflight_catalog_access(db))
        snapshot = snapshot or await extract_catalog_snapshot(db)
        context = ScanContext(
            config=config,
            db=db,
            snapshot=snapshot,
            scan_id=scan_id,
            warnings=warnings,
        )
        for module in active_modules:
            try:
                findings.extend(await module.run(context))
            except Exception as exc:
                errors.append(
                    ScanError(
                        module=getattr(module, "name", module.__class__.__name__),
                        message="Scanner module failed.",
                        detail=str(exc),
                    )
                )
    finally:
        if owns_db:
            await db.close()

    completed_at = datetime.now(UTC)
    return ScanResult(
        scan_id=scan_id,
        database=snapshot.database_name if snapshot else config.pg_database,
        started_at=started_at,
        completed_at=completed_at,
        snapshot=snapshot,
        findings=findings,
        warnings=warnings,
        errors=errors,
        metadata={
            "module_count": len(active_modules),
            "finding_count": len(findings),
            "warning_count": len(warnings),
            "error_count": len(errors),
        },
    )
