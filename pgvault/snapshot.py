"""Catalog preflight checks and metadata snapshot extraction."""

from __future__ import annotations

import asyncpg

from pgvault.db import DatabaseClient
from pgvault.models import (
    CatalogSnapshot,
    ColumnMeta,
    ExtensionMeta,
    FunctionMeta,
    HbaRuleMeta,
    RoleMeta,
    ScanWarning,
    SettingMeta,
)


CATALOG_SOURCES: dict[str, str] = {
    "information_schema.columns": "SELECT 1 FROM information_schema.columns LIMIT 1",
    "information_schema.tables": "SELECT 1 FROM information_schema.tables LIMIT 1",
    "pg_roles": "SELECT 1 FROM pg_catalog.pg_roles LIMIT 1",
    "pg_auth_members": "SELECT 1 FROM pg_catalog.pg_auth_members LIMIT 1",
    "pg_class": "SELECT 1 FROM pg_catalog.pg_class LIMIT 1",
    "pg_namespace": "SELECT 1 FROM pg_catalog.pg_namespace LIMIT 1",
    "pg_proc": "SELECT 1 FROM pg_catalog.pg_proc LIMIT 1",
    "pg_settings": "SELECT 1 FROM pg_catalog.pg_settings LIMIT 1",
    "pg_extension": "SELECT 1 FROM pg_catalog.pg_extension LIMIT 1",
    "pg_hba_file_rules": "SELECT 1 FROM pg_catalog.pg_hba_file_rules LIMIT 1",
}


async def preflight_catalog_access(db: DatabaseClient) -> list[ScanWarning]:
    """Check whether the connected user can read required catalog sources."""

    warnings: list[ScanWarning] = []
    for source, query in CATALOG_SOURCES.items():
        try:
            await db.fetch(query)
        except (asyncpg.PostgresError, PermissionError, RuntimeError) as exc:
            warnings.append(
                ScanWarning(
                    source=source,
                    message=f"Catalog source unavailable: {source}",
                    detail=str(exc),
                )
            )
    return warnings


async def extract_catalog_snapshot(db: DatabaseClient) -> CatalogSnapshot:
    """Collect PostgreSQL catalog metadata without reading table data."""

    identity = await db.fetchrow(
        "SELECT current_database() AS database_name, current_user AS current_user"
    )
    database_name = identity["database_name"] if identity else ""
    current_user = identity["current_user"] if identity else ""

    columns = await _fetch_columns(db)
    roles = await _fetch_roles(db)
    functions = await _fetch_functions(db)
    settings = await _fetch_settings(db)
    extensions = await _fetch_extensions(db)
    hba_rules = await _fetch_hba_rules(db)

    return CatalogSnapshot(
        database_name=database_name,
        current_user=current_user,
        columns=columns,
        roles=roles,
        functions=functions,
        settings=settings,
        extensions=extensions,
        hba_rules=hba_rules,
        metadata={
            "table_count": len({(col.table_schema, col.table_name) for col in columns}),
            "column_count": len(columns),
        },
    )


async def _fetch_columns(db: DatabaseClient) -> list[ColumnMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                c.table_schema,
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable = 'YES' AS is_nullable,
                c.ordinal_position,
                t.table_type
            FROM information_schema.columns c
            JOIN information_schema.tables t
              ON t.table_schema = c.table_schema
             AND t.table_name = c.table_name
            WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY c.table_schema, c.table_name, c.ordinal_position
            """
        )
    except asyncpg.PostgresError:
        return []
    return [ColumnMeta(**dict(row)) for row in rows]


async def _fetch_roles(db: DatabaseClient) -> list[RoleMeta]:
    try:
        role_rows = await db.fetch(
            """
            SELECT
                r.rolname AS role_name,
                r.rolcanlogin AS can_login,
                r.rolsuper AS is_superuser,
                r.rolinherit AS is_inherit,
                r.rolcreaterole AS is_create_role,
                r.rolcreatedb AS is_create_db
            FROM pg_catalog.pg_roles r
            ORDER BY r.rolname
            """
        )
    except asyncpg.PostgresError:
        return []
    memberships: dict[str, list[str]] = {}
    try:
        membership_rows = await db.fetch(
            """
            SELECT member_role.rolname AS member, parent_role.rolname AS parent
            FROM pg_catalog.pg_auth_members m
            JOIN pg_catalog.pg_roles member_role ON member_role.oid = m.member
            JOIN pg_catalog.pg_roles parent_role ON parent_role.oid = m.roleid
            ORDER BY member_role.rolname, parent_role.rolname
            """
        )
    except asyncpg.PostgresError:
        membership_rows = []
    for row in membership_rows:
        memberships.setdefault(row["member"], []).append(row["parent"])

    roles: list[RoleMeta] = []
    for row in role_rows:
        data = dict(row)
        data["member_of"] = memberships.get(row["role_name"], [])
        roles.append(RoleMeta(**data))
    return roles


async def _fetch_functions(db: DatabaseClient) -> list[FunctionMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                n.nspname AS schema_name,
                p.proname AS function_name,
                pg_catalog.pg_get_userbyid(p.proowner) AS owner,
                l.lanname AS language,
                p.prosecdef AS security_definer
            FROM pg_catalog.pg_proc p
            JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
            JOIN pg_catalog.pg_language l ON l.oid = p.prolang
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY n.nspname, p.proname
            """
        )
    except asyncpg.PostgresError:
        return []
    return [FunctionMeta(**dict(row)) for row in rows]


async def _fetch_settings(db: DatabaseClient) -> list[SettingMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT name, setting, unit, source, context, vartype
            FROM pg_catalog.pg_settings
            ORDER BY name
            """
        )
    except asyncpg.PostgresError:
        return []
    return [SettingMeta(**dict(row)) for row in rows]


async def _fetch_extensions(db: DatabaseClient) -> list[ExtensionMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT e.extname AS name, e.extversion AS version, n.nspname AS schema_name
            FROM pg_catalog.pg_extension e
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
            ORDER BY e.extname
            """
        )
    except asyncpg.PostgresError:
        return []
    return [ExtensionMeta(**dict(row)) for row in rows]


async def _fetch_hba_rules(db: DatabaseClient) -> list[HbaRuleMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                line_number,
                type AS rule_type,
                database,
                user_name AS "user",
                address,
                auth_method,
                error
            FROM pg_catalog.pg_hba_file_rules
            ORDER BY line_number
            """
        )
    except asyncpg.PostgresError:
        return []
    return [HbaRuleMeta(**dict(row)) for row in rows]
