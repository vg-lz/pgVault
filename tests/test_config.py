from pgvault.config import PgVaultConfig


PGVAULT_ENV_VARS = [
    "PGHOST",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
    "PGSSLMODE",
    "DATABASE_URL",
    "PGVAULT_SAMPLE_LIMIT",
    "PGVAULT_QUERY_TIMEOUT_SECONDS",
]


def clear_pgvault_env(monkeypatch):
    for name in PGVAULT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_config_defaults(monkeypatch):
    clear_pgvault_env(monkeypatch)

    config = PgVaultConfig(_env_file=None)

    assert config.pg_host == "localhost"
    assert config.pg_port == 5432
    assert config.pg_database == "fintechdb"
    assert config.pg_user == "pgvault_readonly"
    assert config.sample_limit == 100
    assert config.query_timeout_seconds == 10.0


def test_config_database_url_takes_connect_precedence():
    config = PgVaultConfig(DATABASE_URL="postgresql://example/db", _env_file=None)

    assert config.asyncpg_connect_kwargs() == {"dsn": "postgresql://example/db"}


def test_config_accepts_python_field_names(monkeypatch):
    clear_pgvault_env(monkeypatch)

    config = PgVaultConfig(
        pg_host="db.internal",
        pg_port=15432,
        pg_database="auditdb",
        pg_user="readonly",
        sample_limit=25,
        query_timeout_seconds=3,
        _env_file=None,
    )

    assert config.pg_host == "db.internal"
    assert config.pg_port == 15432
    assert config.pg_database == "auditdb"
    assert config.pg_user == "readonly"
    assert config.sample_limit == 25
    assert config.query_timeout_seconds == 3
