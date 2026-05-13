from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEMO_DATABASES = {
    "fintechdb": {
        "alias": "fintechdb-demo",
        "host": "fintechdb",
        "port": "5433:5432",
        "database": "fintechdb",
        "user": "fintech_user",
        "password": "fintech_pass",
        "required_files": [
            "README.md",
            "docker-compose.yml",
            "init/01_schema.sql",
            "init/02_seed_data.sql",
            "init/03_plant_problems.sql",
            "config/postgresql.conf",
            "config/pg_hba.conf",
        ],
        "readme_marker": "22 planted problems",
    },
    "tiendadb": {
        "alias": "tiendadb-demo",
        "host": "tiendadb",
        "port": "5432:5432",
        "database": "tiendadb",
        "user": "tienda_user",
        "password": "tienda_pass",
        "required_files": [
            "README.md",
            "docker-compose.yml",
            "init/01_schema.sql",
            "init/02_seed_data.sql",
            "init/03_plant_problems.sql",
            "postgresql.conf",
            "scripts/start_idle_tx.sh",
        ],
        "readme_marker": "18 planted problems",
    },
    "appdb": {
        "alias": "appdb-demo",
        "host": "appdb",
        "port": "5434:5432",
        "database": "appdb",
        "user": "app_user",
        "password": "app_pass",
        "required_files": [
            "README.md",
            "docker-compose.yml",
            "init/01_schema.sql",
            "init/02_seed_data.sql",
            "init/03_plant_problems.sql",
            "postgresql.conf",
        ],
        "readme_marker": "20 planted problematic queries",
    },
}


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def test_demo_database_assets_are_present():
    for name, spec in DEMO_DATABASES.items():
        base = ROOT / "demo-databases" / name
        assert base.is_dir(), f"Missing demo database directory: {name}"
        for relative_path in spec["required_files"]:
            assert (base / relative_path).is_file(), f"Missing {name}/{relative_path}"


def test_demo_database_readmes_describe_planted_test_cases():
    for name, spec in DEMO_DATABASES.items():
        readme = read_text(f"demo-databases/{name}/README.md")
        assert spec["database"] in readme
        assert spec["user"] in readme
        assert spec["password"] in readme
        assert spec["readme_marker"] in readme


def test_project_compose_mounts_demo_databases_without_copying_data():
    compose = read_text("docker-compose.yml")
    for name, spec in DEMO_DATABASES.items():
        assert f"{name}:" in compose
        assert "image: postgres:16" in compose
        assert f"POSTGRES_DB: {spec['database']}" in compose
        assert f"POSTGRES_USER: {spec['user']}" in compose
        assert f"POSTGRES_PASSWORD: {spec['password']}" in compose
        assert f'"{spec["port"]}"' in compose
        assert f"./demo-databases/{name}/init:/docker-entrypoint-initdb.d:ro" in compose


def test_web_demo_profiles_match_demo_database_credentials():
    app_js = read_text("pgvault/static/app.js")
    for spec in DEMO_DATABASES.values():
        assert f'alias: "{spec["alias"]}"' in app_js
        assert f'host: "{spec["host"]}"' in app_js
        assert f'database: "{spec["database"]}"' in app_js
        assert f'user: "{spec["user"]}"' in app_js
        assert f'password: "{spec["password"]}"' in app_js
        assert 'sslmode: "disable"' in app_js


def test_readme_has_web_connection_table_for_all_demo_databases():
    readme = read_text("README.md")
    for spec in DEMO_DATABASES.values():
        assert spec["alias"] in readme
        assert f"`{spec['host']}`" in readme
        assert f"`{spec['database']}`" in readme
        assert f"`{spec['user']}`" in readme
        assert f"`{spec['password']}`" in readme
