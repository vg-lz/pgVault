"""Read-only PostgreSQL access helpers for PgVault.

The SQL guard is intentionally conservative. It protects PgVault modules from
accidentally issuing write statements, but production deployments must still
use a real PostgreSQL user with read-only permissions.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import asyncpg

from pgvault.config import PgVaultConfig


class UnsafeQueryError(ValueError):
    """Raised when a query is not allowed by PgVault's read-only guard."""


ALLOWED_QUERY_PREFIXES = {"SELECT", "WITH", "SHOW", "EXPLAIN"}
BLOCKED_QUERY_PREFIXES = {
    "ALTER",
    "CALL",
    "COPY",
    "CREATE",
    "DELETE",
    "DO",
    "DROP",
    "GRANT",
    "INSERT",
    "REVOKE",
    "TRUNCATE",
    "UPDATE",
    "MERGE",
}


def _strip_leading_comments(sql: str) -> str:
    remaining = sql.strip()
    while True:
        if remaining.startswith("--"):
            _, _, remaining = remaining.partition("\n")
            remaining = remaining.strip()
            continue
        if remaining.startswith("/*"):
            end = remaining.find("*/")
            if end == -1:
                return ""
            remaining = remaining[end + 2 :].strip()
            continue
        return remaining


def _has_multiple_statements(sql: str) -> bool:
    in_single_quote = False
    in_double_quote = False
    i = 0
    while i < len(sql):
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < len(sql) else ""
        if in_single_quote:
            if char == "'" and next_char == "'":
                i += 2
                continue
            if char == "'":
                in_single_quote = False
        elif in_double_quote:
            if char == '"' and next_char == '"':
                i += 2
                continue
            if char == '"':
                in_double_quote = False
        elif char == "'":
            in_single_quote = True
        elif char == '"':
            in_double_quote = True
        elif char == ";":
            return bool(sql[i + 1 :].strip())
        i += 1
    return False


def assert_readonly_query(sql: str) -> None:
    """Validate that a SQL statement is acceptable for PgVault reads."""

    candidate = _strip_leading_comments(sql)
    if not candidate:
        raise UnsafeQueryError("Empty SQL is not allowed.")
    if _has_multiple_statements(candidate):
        raise UnsafeQueryError("Multiple SQL statements are not allowed.")

    match = re.match(r"([A-Za-z]+)", candidate)
    prefix = match.group(1).upper() if match else ""
    if prefix in BLOCKED_QUERY_PREFIXES:
        raise UnsafeQueryError(f"Blocked unsafe SQL statement: {prefix}.")
    if prefix not in ALLOWED_QUERY_PREFIXES:
        raise UnsafeQueryError(
            f"Only read-only statements are allowed: {', '.join(sorted(ALLOWED_QUERY_PREFIXES))}."
        )
    if prefix == "EXPLAIN" and re.search(r"\bANALYZE\b", candidate, re.IGNORECASE):
        raise UnsafeQueryError("EXPLAIN ANALYZE is not allowed because it executes the query.")
    if prefix == "EXPLAIN" and re.search(
        r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE)\b",
        candidate,
        re.IGNORECASE,
    ):
        raise UnsafeQueryError("EXPLAIN is only allowed for read-only queries.")
    if prefix == "WITH" and re.search(
        r"\b(INSERT|UPDATE|DELETE|MERGE)\b",
        candidate,
        re.IGNORECASE,
    ):
        raise UnsafeQueryError("Data-changing common table expressions are not allowed.")


def quote_identifier(name: str) -> str:
    """Safely quote one PostgreSQL identifier component."""

    if not isinstance(name, str) or not name:
        raise ValueError("PostgreSQL identifier must be a non-empty string.")
    if "\x00" in name:
        raise ValueError("PostgreSQL identifier cannot contain NUL bytes.")
    return '"' + name.replace('"', '""') + '"'


def qualified_name(schema: str, table: str) -> str:
    """Safely quote a schema-qualified PostgreSQL relation name."""

    return f"{quote_identifier(schema)}.{quote_identifier(table)}"


class DatabaseClient:
    """Small asyncpg wrapper that applies PgVault's read-only guard."""

    def __init__(self, config: PgVaultConfig):
        self.config = config
        self._connection: asyncpg.Connection | None = None

    async def connect(self) -> None:
        """Open the PostgreSQL connection."""

        self._connection = await asyncpg.connect(
            **self.config.asyncpg_connect_kwargs(),
            timeout=self.config.query_timeout_seconds,
        )

    async def close(self) -> None:
        """Close the PostgreSQL connection if it is open."""

        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> "DatabaseClient":
        await self.connect()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    @property
    def connection(self) -> asyncpg.Connection:
        if self._connection is None:
            raise RuntimeError("Database client is not connected.")
        return self._connection

    async def fetch(self, sql: str, *args: Any) -> list[asyncpg.Record]:
        """Run a guarded read query and return all rows."""

        assert_readonly_query(sql)
        return await self.connection.fetch(
            sql,
            *args,
            timeout=self.config.query_timeout_seconds,
        )

    async def fetchrow(self, sql: str, *args: Any) -> asyncpg.Record | None:
        """Run a guarded read query and return one row."""

        assert_readonly_query(sql)
        return await self.connection.fetchrow(
            sql,
            *args,
            timeout=self.config.query_timeout_seconds,
        )

    async def fetchval(self, sql: str, *args: Any) -> Any:
        """Run a guarded read query and return one scalar value."""

        assert_readonly_query(sql)
        return await self.connection.fetchval(
            sql,
            *args,
            timeout=self.config.query_timeout_seconds,
        )


def records_to_dicts(rows: Sequence[asyncpg.Record]) -> list[dict[str, Any]]:
    """Convert asyncpg records into plain dictionaries."""

    return [dict(row) for row in rows]
