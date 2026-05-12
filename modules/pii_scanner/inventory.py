import asyncpg
from .models import ColumnMeta

EXCLUDED_SCHEMAS = frozenset({
    "pg_catalog",
    "information_schema",
    "pg_toast",
    "pg_temp_1",
    "pg_toast_temp_1",
})

QUERY_COLUMNS = """
    SELECT
        c.table_schema,
        c.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable = 'YES' AS is_nullable,
        c.ordinal_position
    FROM information_schema.columns c
    JOIN information_schema.tables t
        ON t.table_schema = c.table_schema
        AND t.table_name  = c.table_name
    WHERE c.table_schema NOT IN ({placeholders})
      AND t.table_type = 'BASE TABLE'
    ORDER BY c.table_schema, c.table_name, c.ordinal_position
"""


async def get_all_columns(conn: asyncpg.Connection) -> list[ColumnMeta]:
    placeholders = ", ".join(f"${i+1}" for i in range(len(EXCLUDED_SCHEMAS)))
    query = QUERY_COLUMNS.format(placeholders=placeholders)
    rows = await conn.fetch(query, *EXCLUDED_SCHEMAS)
    return [
        ColumnMeta(
            table_schema=row["table_schema"],
            table_name=row["table_name"],
            column_name=row["column_name"],
            data_type=row["data_type"],
            is_nullable=row["is_nullable"],
            ordinal_position=row["ordinal_position"],
        )
        for row in rows
    ]


async def get_table_row_count(conn: asyncpg.Connection, schema: str, table: str) -> int:
    row = await conn.fetchrow(
        """
        SELECT reltuples::bigint AS estimate
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = $1 AND c.relname = $2
        """,
        schema, table
    )
    if row is None:
        return 0
    return max(0, row["estimate"])
