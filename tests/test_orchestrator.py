from datetime import UTC, datetime

import pytest

from pgvault.config import PgVaultConfig
from pgvault.models import CatalogSnapshot, Finding, Severity
from pgvault.orchestrator import run_scan


class FakeDb:
    async def connect(self):
        raise AssertionError("Injected db should already be usable.")

    async def close(self):
        raise AssertionError("Injected db should not be owned by orchestrator.")

    async def fetch(self, *_args, **_kwargs):
        return []


class FindingModule:
    name = "finding-module"

    async def run(self, context):
        return [
            Finding(
                id=f"{context.scan_id}-demo",
                module=self.name,
                category="test",
                title="Demo finding",
                description="Fake finding for orchestrator tests.",
                severity=Severity.LOW,
                evidence="Synthetic evidence.",
                recommendation="No action needed.",
            )
        ]


class FailingModule:
    name = "failing-module"

    async def run(self, _context):
        raise RuntimeError("planned failure")


@pytest.mark.asyncio
async def test_orchestrator_merges_fake_module_results():
    snapshot = CatalogSnapshot(
        database_name="demo",
        current_user="pgvault",
        captured_at=datetime.now(UTC),
    )

    result = await run_scan(
        config=PgVaultConfig(_env_file=None),
        modules=[FindingModule()],
        db=FakeDb(),
        snapshot=snapshot,
    )

    assert result.database == "demo"
    assert len(result.findings) == 1
    assert result.findings[0].module == "finding-module"
    assert result.errors == []


@pytest.mark.asyncio
async def test_orchestrator_continues_when_module_fails():
    snapshot = CatalogSnapshot(
        database_name="demo",
        current_user="pgvault",
        captured_at=datetime.now(UTC),
    )

    result = await run_scan(
        config=PgVaultConfig(_env_file=None),
        modules=[FailingModule(), FindingModule()],
        db=FakeDb(),
        snapshot=snapshot,
    )

    assert len(result.findings) == 1
    assert len(result.errors) == 1
    assert result.errors[0].module == "failing-module"
    assert "planned failure" in (result.errors[0].detail or "")
