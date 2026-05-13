"""Environment-based configuration for the PgVault runtime."""

from __future__ import annotations

import ssl
from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PgVaultConfig(BaseSettings):
    """Runtime configuration loaded from environment variables.

    The config accepts PostgreSQL-compatible variable names (`PGHOST`,
    `PGPORT`, etc.) so PgVault can run locally, in Docker Compose, and in
    future deployment environments without code changes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    pg_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("PGHOST", "pg_host"),
    )
    pg_port: int = Field(default=5432, validation_alias=AliasChoices("PGPORT", "pg_port"))
    pg_database: str = Field(
        default="fintechdb",
        validation_alias=AliasChoices("PGDATABASE", "pg_database"),
    )
    pg_user: str = Field(
        default="pgvault_readonly",
        validation_alias=AliasChoices("PGUSER", "pg_user"),
    )
    pg_password: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("PGPASSWORD", "pg_password"),
    )
    pg_sslmode: str = Field(
        default="prefer",
        validation_alias=AliasChoices("PGSSLMODE", "pg_sslmode"),
    )
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    sample_limit: int = Field(
        default=100,
        validation_alias=AliasChoices("PGVAULT_SAMPLE_LIMIT", "sample_limit"),
        ge=0,
    )
    query_timeout_seconds: float = Field(
        default=10.0,
        validation_alias=AliasChoices(
            "PGVAULT_QUERY_TIMEOUT_SECONDS",
            "query_timeout_seconds",
        ),
        gt=0,
    )

    @field_validator("pg_sslmode")
    @classmethod
    def validate_sslmode(cls, value: str) -> str:
        allowed = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"PGSSLMODE must be one of: {', '.join(sorted(allowed))}")
        return normalized

    def asyncpg_connect_kwargs(self) -> dict[str, object]:
        """Return keyword arguments compatible with `asyncpg.connect`."""

        if self.database_url:
            return {"dsn": self.database_url}

        kwargs: dict[str, object] = {
            "host": self.pg_host,
            "port": self.pg_port,
            "database": self.pg_database,
            "user": self.pg_user,
        }
        if self.pg_password is not None:
            kwargs["password"] = self.pg_password.get_secret_value()
        if self.pg_sslmode == "disable":
            kwargs["ssl"] = False
        elif self.pg_sslmode == "require":
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            kwargs["ssl"] = ssl_context
        elif self.pg_sslmode in {"verify-ca", "verify-full"}:
            ssl_context = ssl.create_default_context()
            if self.pg_sslmode == "verify-ca":
                ssl_context.check_hostname = False
            kwargs["ssl"] = ssl_context
        return kwargs


@lru_cache
def load_config() -> PgVaultConfig:
    """Load and cache process-level PgVault configuration."""

    return PgVaultConfig()
