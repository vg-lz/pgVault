import pytest

from pgvault.db import UnsafeQueryError, assert_readonly_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM information_schema.tables",
        "WITH columns AS (SELECT 1) SELECT * FROM columns",
        "SHOW server_version",
        "EXPLAIN SELECT 1",
        "-- comment\nSELECT 1",
        "/* comment */ SELECT 1;",
        "SELECT 'DROP is only text' AS example",
    ],
)
def test_readonly_guard_allows_safe_queries(query):
    assert_readonly_query(query)


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO audit_log VALUES (1)",
        "UPDATE users SET admin = true",
        "DELETE FROM users",
        "DROP TABLE users",
        "ALTER TABLE users ADD COLUMN secret text",
        "CREATE TABLE demo(id int)",
        "TRUNCATE users",
        "GRANT SELECT ON users TO app",
        "REVOKE SELECT ON users FROM app",
        "CALL dangerous()",
        "DO $$ BEGIN END $$",
        "COPY users TO '/tmp/users.csv'",
        "SELECT 1; DROP TABLE users",
        "WITH deleted AS (DELETE FROM users RETURNING *) SELECT * FROM deleted",
        "EXPLAIN ANALYZE DELETE FROM users",
    ],
)
def test_readonly_guard_blocks_unsafe_queries(query):
    with pytest.raises(UnsafeQueryError):
        assert_readonly_query(query)
