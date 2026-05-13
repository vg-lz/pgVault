"""SQLite persistence for PgVault web profiles and scan history."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROFILE_FIELDS = (
    "alias",
    "host",
    "port",
    "database",
    "user",
    "sslmode",
    "sample_limit",
    "query_timeout",
)


class WebStorage:
    """Small SQLite repository used by the FastAPI web interface."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS connection_profiles (
                    alias TEXT PRIMARY KEY,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    database_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    sslmode TEXT NOT NULL,
                    sample_limit INTEGER NOT NULL,
                    query_timeout REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT NOT NULL,
                    database_name TEXT NOT NULL,
                    scan_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    total_findings INTEGER NOT NULL,
                    total_warnings INTEGER NOT NULL,
                    total_errors INTEGER NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def upsert_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Create or update a connection profile without storing passwords."""

        now = datetime.now(UTC).isoformat()
        normalized = {
            "alias": profile["alias"].strip(),
            "host": profile["host"].strip(),
            "port": int(profile["port"]),
            "database": profile["database"].strip(),
            "user": profile["user"].strip(),
            "sslmode": profile["sslmode"],
            "sample_limit": int(profile["sample_limit"]),
            "query_timeout": float(profile["query_timeout"]),
        }
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM connection_profiles WHERE alias = ?",
                (normalized["alias"],),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO connection_profiles (
                    alias, host, port, database_name, username, sslmode,
                    sample_limit, query_timeout, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                    host = excluded.host,
                    port = excluded.port,
                    database_name = excluded.database_name,
                    username = excluded.username,
                    sslmode = excluded.sslmode,
                    sample_limit = excluded.sample_limit,
                    query_timeout = excluded.query_timeout,
                    updated_at = excluded.updated_at
                """,
                (
                    normalized["alias"],
                    normalized["host"],
                    normalized["port"],
                    normalized["database"],
                    normalized["user"],
                    normalized["sslmode"],
                    normalized["sample_limit"],
                    normalized["query_timeout"],
                    existing["created_at"] if existing else now,
                    now,
                ),
            )
        return self.get_profile(normalized["alias"]) or normalized

    def list_profiles(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT alias, host, port, database_name, username, sslmode,
                       sample_limit, query_timeout, created_at, updated_at
                FROM connection_profiles
                ORDER BY updated_at DESC, alias ASC
                """
            ).fetchall()
        return [self._profile_from_row(row) for row in rows]

    def get_profile(self, alias: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT alias, host, port, database_name, username, sslmode,
                       sample_limit, query_timeout, created_at, updated_at
                FROM connection_profiles
                WHERE alias = ?
                """,
                (alias,),
            ).fetchone()
        return self._profile_from_row(row) if row else None

    def delete_profile(self, alias: str) -> bool:
        """Delete a saved connection profile."""

        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM connection_profiles WHERE alias = ?",
                (alias,),
            )
        return cursor.rowcount > 0

    def save_scan_result(self, alias: str, result: Any) -> dict[str, Any]:
        """Persist a Pydantic ScanResult and return its history summary."""

        payload = result.model_dump(mode="json")
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scan_history (
                    alias, database_name, scan_id, started_at, completed_at,
                    total_findings, total_warnings, total_errors, result_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alias,
                    result.database,
                    result.scan_id,
                    result.started_at.isoformat(),
                    result.completed_at.isoformat(),
                    result.total_findings,
                    result.total_warnings,
                    result.total_errors,
                    json.dumps(payload),
                    created_at,
                ),
            )
            history_id = int(cursor.lastrowid)
        return {
            "id": history_id,
            "alias": alias,
            "database": result.database,
            "scan_id": result.scan_id,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "total_findings": result.total_findings,
            "total_warnings": result.total_warnings,
            "total_errors": result.total_errors,
            "created_at": created_at,
        }

    def list_scan_history(self, alias: str | None = None) -> list[dict[str, Any]]:
        params: tuple[Any, ...] = ()
        where = ""
        if alias:
            where = "WHERE alias = ?"
            params = (alias,)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, alias, database_name, scan_id, started_at, completed_at,
                       total_findings, total_warnings, total_errors, created_at
                FROM scan_history
                {where}
                ORDER BY created_at DESC
                """,
                params,
            ).fetchall()
        return [self._history_from_row(row) for row in rows]

    def get_scan_result(self, history_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM scan_history WHERE id = ?",
                (history_id,),
            ).fetchone()
        return json.loads(row["result_json"]) if row else None

    @staticmethod
    def _profile_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "alias": row["alias"],
            "host": row["host"],
            "port": row["port"],
            "database": row["database_name"],
            "user": row["username"],
            "sslmode": row["sslmode"],
            "sample_limit": row["sample_limit"],
            "query_timeout": row["query_timeout"],
            "password_saved": False,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _history_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "alias": row["alias"],
            "database": row["database_name"],
            "scan_id": row["scan_id"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "total_findings": row["total_findings"],
            "total_warnings": row["total_warnings"],
            "total_errors": row["total_errors"],
            "created_at": row["created_at"],
        }
