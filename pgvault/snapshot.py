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
    PrivilegeMeta,
    RlsMeta,
    RoleMeta,
    RoleMembershipMeta,
    ScanWarning,
    SchemaMeta,
    SettingMeta,
    TableMeta,
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
    "information_schema.table_privileges": "SELECT 1 FROM information_schema.table_privileges LIMIT 1",
    "pg_namespace_acl": "SELECT nspacl FROM pg_catalog.pg_namespace LIMIT 1",
    "pg_policy": "SELECT 1 FROM pg_catalog.pg_policy LIMIT 1",
}

SOURCE_LIMITATIONS: dict[str, str] = {
    "information_schema.columns": "PII and column-level checks may be incomplete.",
    "information_schema.tables": "Table inventory and row-estimate context may be incomplete.",
    "pg_roles": "Role and privilege-risk checks may be incomplete.",
    "pg_auth_members": "Role inheritance and membership checks may be incomplete.",
    "pg_class": "Table owner, RLS, and row estimate checks may be incomplete.",
    "pg_namespace": "Schema ownership and schema privilege checks may be incomplete.",
    "pg_proc": "Function and SECURITY DEFINER checks may be incomplete.",
    "pg_settings": "Configuration checks may be incomplete.",
    "pg_extension": "Extension risk checks may be incomplete.",
    "pg_hba_file_rules": "Client authentication checks may be unavailable for non-superusers.",
    "information_schema.table_privileges": "Table privilege checks may be incomplete.",
    "pg_namespace_acl": "Schema privilege checks may be incomplete.",
    "pg_policy": "RLS policy checks may be incomplete.",
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
                    detail=f"{exc}. Impact: {SOURCE_LIMITATIONS.get(source, 'Some checks may be limited.')}",
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

    schemas = await _fetch_schemas(db)
    tables = await _fetch_tables(db)
    columns = await _fetch_columns(db)
    roles, role_memberships = await _fetch_roles(db)
    functions = await _fetch_functions(db)
    settings = await _fetch_settings(db)
    extensions = await _fetch_extensions(db)
    hba_rules = await _fetch_hba_rules(db)
    privileges = await _fetch_privileges(db)
    rls = await _fetch_rls(db)

    return CatalogSnapshot(
        database_name=database_name,
        current_user=current_user,
        schemas=schemas,
        tables=tables,
        columns=columns,
        roles=roles,
        role_memberships=role_memberships,
        functions=functions,
        settings=settings,
        extensions=extensions,
        hba_rules=hba_rules,
        privileges=privileges,
        rls=rls,
        metadata={
            "schema_count": len(schemas),
            "table_count": len(tables),
            "column_count": len(columns),
        },
    )


async def _fetch_schemas(db: DatabaseClient) -> list[SchemaMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT n.nspname AS schema_name, pg_catalog.pg_get_userbyid(n.nspowner) AS owner
            FROM pg_catalog.pg_namespace n
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp_%'
            ORDER BY n.nspname
            """
        )
    except asyncpg.PostgresError:
        return []
    return [SchemaMeta(**dict(row)) for row in rows]


async def _fetch_tables(db: DatabaseClient) -> list[TableMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                n.nspname AS table_schema,
                c.relname AS table_name,
                CASE c.relkind
                    WHEN 'r' THEN 'BASE TABLE'
                    WHEN 'p' THEN 'PARTITIONED TABLE'
                    WHEN 'v' THEN 'VIEW'
                    WHEN 'm' THEN 'MATERIALIZED VIEW'
                    WHEN 'f' THEN 'FOREIGN TABLE'
                    ELSE c.relkind::text
                END AS table_type,
                pg_catalog.pg_get_userbyid(c.relowner) AS owner,
                GREATEST(c.reltuples::bigint, 0) AS row_estimate
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp_%'
            ORDER BY n.nspname, c.relname
            """
        )
    except asyncpg.PostgresError:
        return []
    return [TableMeta(**dict(row)) for row in rows]


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


async def _fetch_roles(db: DatabaseClient) -> tuple[list[RoleMeta], list[RoleMembershipMeta]]:
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
        return [], []
    memberships: dict[str, list[str]] = {}
    membership_edges: list[RoleMembershipMeta] = []
    try:
        membership_rows = await db.fetch(
            """
            SELECT
                member_role.rolname AS member,
                parent_role.rolname AS role,
                grantor_role.rolname AS grantor,
                m.admin_option
            FROM pg_catalog.pg_auth_members m
            JOIN pg_catalog.pg_roles member_role ON member_role.oid = m.member
            JOIN pg_catalog.pg_roles parent_role ON parent_role.oid = m.roleid
            LEFT JOIN pg_catalog.pg_roles grantor_role ON grantor_role.oid = m.grantor
            ORDER BY member_role.rolname, parent_role.rolname
            """
        )
    except asyncpg.PostgresError:
        membership_rows = []
    for row in membership_rows:
        memberships.setdefault(row["member"], []).append(row["role"])
        membership_edges.append(RoleMembershipMeta(**dict(row)))

    roles: list[RoleMeta] = []
    for row in role_rows:
        data = dict(row)
        data["member_of"] = memberships.get(row["role_name"], [])
        roles.append(RoleMeta(**data))
    return roles, membership_edges


async def _fetch_functions(db: DatabaseClient) -> list[FunctionMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                n.nspname AS schema_name,
                p.proname AS function_name,
                pg_catalog.pg_get_userbyid(p.proowner) AS owner,
                l.lanname AS language,
                p.prosecdef AS security_definer,
                COALESCE(p.proconfig, ARRAY[]::text[]) AS proconfig
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


async def _fetch_privileges(db: DatabaseClient) -> list[PrivilegeMeta]:
    privileges: list[PrivilegeMeta] = []
    try:
        table_rows = await db.fetch(
            """
            SELECT
                'table' AS object_type,
                table_schema AS object_schema,
                table_name AS object_name,
                grantee,
                privilege_type,
                is_grantable = 'YES' AS grantable
            FROM information_schema.table_privileges
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name, grantee, privilege_type
            """
        )
        privileges.extend(PrivilegeMeta(**dict(row)) for row in table_rows)
    except asyncpg.PostgresError:
        pass
    try:
        schema_rows = await db.fetch(
            """
            SELECT
                'schema' AS object_type,
                n.nspname AS object_schema,
                NULL::text AS object_name,
                COALESCE(grantee.rolname, 'PUBLIC') AS grantee,
                decoded.privilege_type,
                decoded.is_grantable AS grantable
            FROM pg_catalog.pg_namespace n
            CROSS JOIN LATERAL pg_catalog.aclexplode(COALESCE(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) acl
            LEFT JOIN pg_catalog.pg_roles grantee ON grantee.oid = acl.grantee
            CROSS JOIN LATERAL (
                SELECT CASE acl.privilege_type
                    WHEN 'USAGE' THEN 'USAGE'
                    WHEN 'CREATE' THEN 'CREATE'
                    ELSE acl.privilege_type
                END AS privilege_type,
                acl.is_grantable
            ) decoded
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp_%'
            ORDER BY n.nspname, COALESCE(grantee.rolname, 'PUBLIC'), privilege_type
            """
        )
        privileges.extend(PrivilegeMeta(**dict(row)) for row in schema_rows)
    except asyncpg.PostgresError:
        pass
    return privileges


async def _fetch_rls(db: DatabaseClient) -> list[RlsMeta]:
    try:
        rows = await db.fetch(
            """
            SELECT
                n.nspname AS table_schema,
                c.relname AS table_name,
                c.relrowsecurity AS rls_enabled,
                c.relforcerowsecurity AS rls_forced,
                COUNT(p.polname)::int AS policy_count
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_catalog.pg_policy p ON p.polrelid = c.oid
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp_%'
            GROUP BY n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity
            ORDER BY n.nspname, c.relname
            """
        )
    except asyncpg.PostgresError:
        return []
    return [RlsMeta(**dict(row)) for row in rows]
