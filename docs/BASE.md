# Guia Tecnica

Esta guia documenta la arquitectura interna de PgVault. El README es la puerta
principal del proyecto; este documento queda como referencia para mantener,
extender o revisar el codigo.

## Estructura

```text
pgvault/
  config.py        Configuracion desde entorno o payload web.
  db.py            Conexion asyncpg y guardia read-only.
  models.py        Contratos Pydantic compartidos.
  snapshot.py      Preflight y extraccion del catalogo.
  modules.py       Interfaz para scanners.
  orchestrator.py  Flujo principal del scan.
  cli.py           Entrada por linea de comandos.
  web.py           API FastAPI y archivos estaticos.

pgvault/scanners/
  configuration_scanner.py

modules/
  name_scanner.py
  pii_scanner/
    scanner.py
    content_validators.py
    score_engine.py

Reports/
  adapters.py
  generator.py
  regulations_map.py
  scoring.py

tests/
  test_base_architecture.py
  test_configuration_scanner.py
  test_demo_databases.py
```

## Orquestador

El flujo principal vive en `pgvault.orchestrator.run_scan`:

1. Carga configuracion si no se recibe una explicita.
2. Crea un `scan_id`.
3. Abre `DatabaseClient` si no se inyecto uno.
4. Ejecuta `preflight_catalog_access`.
5. Extrae un `CatalogSnapshot`.
6. Construye un `ScanContext`.
7. Ejecuta cada modulo registrado.
8. Agrega `Finding`, `ScanWarning` y `ScanError`.
9. Cierra la conexion si el orquestador la abrio.
10. Devuelve un `ScanResult`.

Si un modulo falla, el scan no se cancela. El error queda registrado en
`ScanResult.errors` con el nombre del modulo.

## Modelos Canonicos

Todos los modulos deben importar modelos desde `pgvault.models`.

Modelo central de hallazgos:

- `Finding`: hallazgo emitido por cualquier scanner.
- `Severity`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- `RegulationRef`: referencia regulatoria.

Modelos de ejecucion:

- `ScanResult`: resultado final del scan.
- `ScanWarning`: limitacion o problema no fatal.
- `ScanError`: error de modulo capturado sin detener el scan.
- `CatalogSnapshot`: metadata extraida del catalogo.

El `CatalogSnapshot` incluye schemas, tablas, columnas, roles, membresias,
funciones, extensiones, settings, reglas HBA, privilegios y estado RLS cuando
estan disponibles.

## Guardia Read-Only

La guardia vive en `pgvault.db.assert_readonly_query`.

Permite:

- `SELECT`
- `WITH`
- `SHOW`
- `EXPLAIN`

Bloquea:

- sentencias de escritura o DDL;
- multiples sentencias;
- `EXPLAIN ANALYZE`;
- `EXPLAIN` sobre operaciones no read-only;
- CTEs que modifican datos.

La guardia protege contra errores de implementacion, pero la defensa principal
en produccion debe ser un usuario PostgreSQL con permisos read-only.

## Snapshot De Catalogo

`pgvault.snapshot.extract_catalog_snapshot` consulta fuentes estandar de
PostgreSQL:

- `information_schema.columns`
- `information_schema.tables`
- `pg_catalog.pg_roles`
- `pg_catalog.pg_auth_members`
- `pg_catalog.pg_class`
- `pg_catalog.pg_namespace`
- `pg_catalog.pg_proc`
- `pg_catalog.pg_settings`
- `pg_catalog.pg_extension`
- `pg_catalog.pg_hba_file_rules`
- `information_schema.table_privileges`
- `pg_catalog.pg_policy`

Antes del snapshot, `preflight_catalog_access` intenta leer cada fuente. Si una
vista no esta disponible para el usuario conectado, agrega un `ScanWarning`
con el impacto esperado.

## Modulos

Un scanner debe exponer `name` y `run(context)`:

```python
from pgvault.models import Finding
from pgvault.modules import ScanContext


class MyScanner:
    name = "my_scanner"

    async def run(self, context: ScanContext) -> list[Finding]:
        return []
```

Los modulos por defecto se registran en `pgvault.modules.get_default_modules`.
Actualmente se ejecutan:

- `modules.pii_scanner.scanner.PiiScanner`
- `pgvault.scanners.configuration_scanner.ConfigurationScanner`

## PII Scanner

El scanner PII usa:

- `modules/name_scanner.py` para detectar candidatos por nombre de columna.
- `modules/pii_scanner/content_validators.py` para validar muestras.
- `modules/pii_scanner/score_engine.py` para calcular score y severidad.
- `modules/pii_scanner/scanner.py` como integracion con `ScannerModule`.

El sampling se ejecuta solo si `sample_limit > 0` y la relacion es una tabla
base o particionada. La evidencia se mantiene agregada: no se exponen valores
crudos de la base.

## Configuration Scanner

`pgvault/scanners/configuration_scanner.py` lee principalmente el snapshot y
emite hallazgos `CFG-*` para roles, funciones, logging, autenticacion,
extensiones, passwords, PITR y privilegios.

La unica regla que consulta fuera del snapshot es `CFG-008`, porque necesita
`pg_catalog.pg_authid`. Si el usuario no tiene acceso, el check se omite de
forma silenciosa.

## Web

`pgvault.web` expone:

```text
GET  /
GET  /app
GET  /api/health
POST /api/validate
POST /api/scans
```

Los endpoints de perfiles e historial existen para compatibilidad de UI, pero
la persistencia visible se maneja en el navegador con `localStorage`. La
contrasena no se persiste.

## Reportes

`Reports.adapters.scan_result_to_report_findings` transforma
`ScanResult.findings` al formato usado por `Reports.generator`.

`Reports.generator.generate_all` genera:

- reporte ejecutivo;
- reporte tecnico.

## Validacion

Comandos recomendados:

```bash
docker compose config
docker compose build pgvault
docker compose run --rm --no-deps pgvault python -m pytest -q
```

La validacion no requiere Python local; se ejecuta dentro del contenedor.
