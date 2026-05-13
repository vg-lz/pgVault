"""FastAPI web interface for PgVault."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr

from pgvault.config import PgVaultConfig
from pgvault.db import DatabaseClient
from pgvault.orchestrator import run_scan
from pgvault.storage import WebStorage


DEFAULT_STORAGE_PATH = Path(os.getenv("PGVAULT_WEB_DB", "data/pgvault_web.sqlite"))
STATIC_DIR = Path(__file__).parent / "static"


class ConnectionPayload(BaseModel):
    alias: str = Field(min_length=1, max_length=80)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(min_length=1, max_length=255)
    user: str = Field(min_length=1, max_length=255)
    password: SecretStr | None = None
    sslmode: str = "prefer"
    sample_limit: int = Field(default=100, ge=0, le=10000)
    query_timeout: float = Field(default=10.0, gt=0, le=120)

    def to_config(self) -> PgVaultConfig:
        return PgVaultConfig(
            pg_host=self.host,
            pg_port=self.port,
            pg_database=self.database,
            pg_user=self.user,
            pg_password=self.password,
            pg_sslmode=self.sslmode,
            sample_limit=self.sample_limit,
            query_timeout_seconds=self.query_timeout,
            _env_file=None,
        )

    def profile_dict(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "sslmode": self.sslmode,
            "sample_limit": self.sample_limit,
            "query_timeout": self.query_timeout,
        }


class ValidationResponse(BaseModel):
    ok: bool
    message: str
    profile: dict[str, object] | None = None


ScanRunner = Callable[[PgVaultConfig], Awaitable[object]]


async def validate_connection(config: PgVaultConfig) -> None:
    """Open a guarded read-only connection and run a tiny read query."""

    db = DatabaseClient(config)
    try:
        await db.connect()
        await db.fetchval("SELECT 1")
    finally:
        await db.close()


def friendly_connection_error(exc: Exception, payload: ConnectionPayload) -> str:
    """Return a clearer message for common web/Docker connection mistakes."""

    raw = str(exc)
    if payload.host in {"localhost", "127.0.0.1", "::1"} and "Connection refused" in raw:
        return (
            "Connection refused. La web corre dentro de Docker; para la base de "
            "docker-compose usa host 'postgres'. Usa 'host.docker.internal' solo "
            "si quieres conectar contra un PostgreSQL instalado en tu maquina."
        )
    return raw


def default_storage() -> WebStorage:
    return WebStorage(DEFAULT_STORAGE_PATH)


def create_app(
    *,
    storage: WebStorage | None = None,
    scanner: ScanRunner | None = None,
    connection_validator: Callable[[PgVaultConfig], Awaitable[None]] | None = None,
) -> FastAPI:
    app = FastAPI(title="pgvault web", version="0.1.0")
    app.state.storage = storage or default_storage()
    app.state.scanner = scanner or run_scan
    app.state.connection_validator = connection_validator or validate_connection

    def get_storage() -> WebStorage:
        return app.state.storage

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/app")
    async def web_app() -> FileResponse:
        return FileResponse(STATIC_DIR / "app.html")

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "project": "pgvault"}

    @app.get("/api/profiles")
    async def list_profiles() -> list[dict[str, object]]:
        return []

    @app.get("/api/profiles/{alias}")
    async def get_profile(alias: str) -> dict[str, object]:
        raise HTTPException(
            status_code=404,
            detail="Profiles are stored only in the user's browser.",
        )

    @app.post("/api/profiles")
    async def save_profile(
        payload: ConnectionPayload,
    ) -> dict[str, object]:
        profile = payload.profile_dict()
        profile["password_saved"] = False
        profile["local_only"] = True
        return profile

    @app.delete("/api/profiles/{alias}")
    async def delete_profile(
        alias: str,
    ) -> dict[str, object]:
        return {"deleted": False, "alias": alias, "local_only": True}

    @app.post("/api/validate", response_model=ValidationResponse)
    async def validate(
        payload: ConnectionPayload,
    ) -> ValidationResponse:
        try:
            await app.state.connection_validator(payload.to_config())
        except Exception as exc:
            return ValidationResponse(ok=False, message=friendly_connection_error(exc, payload))
        return ValidationResponse(
            ok=True,
            message="Connection validated. Profile data was not saved.",
            profile=None,
        )

    @app.post("/api/scans")
    async def scan(
        payload: ConnectionPayload,
    ) -> dict[str, object]:
        try:
            config = payload.to_config()
            result = await app.state.scanner(config)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "profile": payload.profile_dict(),
            "history": None,
            "result": result.model_dump(mode="json"),
        }

    @app.get("/api/scans")
    async def list_scans(
        alias: str | None = None,
    ) -> list[dict[str, object]]:
        return []

    @app.get("/api/scans/{history_id}")
    async def get_scan(
        history_id: int,
    ) -> dict[str, object]:
        raise HTTPException(
            status_code=404,
            detail="Scan history is stored only in the user's browser.",
        )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
