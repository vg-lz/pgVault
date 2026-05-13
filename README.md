# PgVault

PgVault es un auditor de seguridad y cumplimiento para PostgreSQL. Se conecta
en modo read-only, analiza configuracion, privilegios y datos sensibles, y
produce hallazgos con evidencia agregada y recomendaciones accionables.

## Equipo

Integrantes del equipo:

- Borquez Hernandez, Daniela
- Mc Donald Smith, Dowshel Jekeal
- Mendez Yepez, Cesar Alejandro
- Rito Michelena, Mariajose
- Vega Cabrera, Diego

| Integrante | Rol principal | Nombre |
|---|---|---|
| Integrante 1 | Conector y orquestador | Diego Vega |
| Integrante 2 | Auditor de configuracion | Dowshell Smith |
| Integrante 3 | Descubridor de datos sensibles | Daniela Borquez |
| Integrante 4 | Reportes y mapeo regulatorio | Mariajose Rito |
| Integrante 5 | Producto, negocio y coordinacion | Cesar Mendez |

## Objetivo

El proyecto busca entregar un MVP capaz de ejecutar una revision reproducible
de bases PostgreSQL sin modificar datos. La salida debe ser entendible para
usuarios tecnicos y no tecnicos: severidad, evidencia, recomendacion,
referencias regulatorias y reportes.

## Alcance del MVP

- Conexion read-only a PostgreSQL.
- Extraccion de informacion del catalogo.
- Checks de seguridad y configuracion.
- Deteccion de datos sensibles por nombre y contenido.
- Recomendaciones automaticas por hallazgo detectado.
- Interfaz web para validar conexion y ejecutar revisiones.
- Reporte ejecutivo y tecnico.
- Exportacion a PDF.
- Ejecucion con Docker Compose.

## Ejecucion rapida

El proyecto esta preparado para ejecutarse con Docker Compose:

```bash
docker compose up --build
```

La interfaz web queda disponible en:

```text
http://localhost:8000
```

El CLI usa el mismo orquestador que la web:

```bash
docker compose run --rm pgvault python -m pgvault scan
```

## Documentos utiles

- [Guia base tecnica](docs/BASE.md)
- [Uso, demos y validacion](docs/USO_DEMOS.md)
- [GitHub Projects](docs/CONTROL_GITHUB_PROJECTS.md)
- [Reglas de Git](docs/REGLAS_GIT.md)
- [Roles](docs/ROLES.md)
- [Documento de negocio](docs/Documento%20de%20Negocio%20-%20PgVault.md)

## Arquitectura general

PgVault tiene un flujo unico para CLI, web, Docker y reportes:

```mermaid
flowchart LR
  A["CLI / Web / Docker"] --> B["run_scan"]
  B --> C["DatabaseClient read-only"]
  C --> D["CatalogSnapshot"]
  D --> E["ScannerModule[]"]
  E --> F["Finding[]"]
  F --> G["ScanResult"]
```

Los detalles del contrato tecnico, modelos, snapshot, guardia read-only y forma
de crear modulos estan documentados en [docs/BASE.md](docs/BASE.md).

## Entregas

- **9 de mayo:** base inicial, roles, tablero, primeras tareas y avance tecnico inicial.
- **12 de mayo:** demo parcial con integracion y al menos 8 hallazgos funcionando.
- **15 de mayo:** MVP final, Docker Compose, reportes, pitch, video demo y Q&A.

## Módulos de escaneo

PgVault utiliza un sistema modular de escáneres que analizan diferentes aspectos
de seguridad y cumplimiento en PostgreSQL. Cada módulo implementa el protocolo
`ScannerModule` y retorna hallazgos con evidencia, recomendaciones y SQL de
remediación.

### ConfigurationScanner

Audita la configuración de seguridad del servidor PostgreSQL. Detecta problemas
en roles, funciones, logging y autenticación.

**Reglas implementadas:**

| ID | Descripción | Severidad |
|---|---|---|
| **CFG-001** | Roles con privilegio SUPERUSER innecesario (excluyendo 'postgres') | HIGH |
| **CFG-002** | Funciones SECURITY DEFINER sin `search_path` seguro | CRITICAL |
| **CFG-003** | Logging de conexiones desactivado (`log_connections = off`) | HIGH |
| **CFG-004** | Logging de desconexiones desactivado (`log_disconnections = off`) | MEDIUM |
| **CFG-005** | Autenticación 'trust' en `pg_hba.conf` desde redes externas | CRITICAL/HIGH |
| **CFG-006** | Roles con nombres sospechosos asociados a credenciales débiles | HIGH |
| **CFG-007** | Extensiones peligrosas instaladas (dblink, pg_read_server_files, file_fdw) | MEDIUM |

**Detalles de CFG-005:**
- CRITICAL: reglas `trust` desde `0.0.0.0/0` o `::/0` (acceso desde cualquier red)
- HIGH: reglas `trust` locales (socket Unix, `127.0.0.1/32`, `::1/128`)

**Detalles de CFG-006:**
- Detecta roles con nombres comunes como 'admin', 'administrator', 'root', 'test', 'demo'
- Recomienda política de contraseñas robustas y renombrado de roles

**Cobertura actual:** 8/10 problemas de configuración detectados (80%)

**Uso:**

El `ConfigurationScanner` se carga automáticamente mediante `pgvault.modules.get_default_modules()`
con fallback opcional si el módulo no está disponible. No requiere configuración
adicional.

## Tecnologia

El equipo puede elegir las herramientas que considere mejores. Se permite usar
herramientas open source e IA, siempre que se entienda, se valide y se declare
su uso.

Condiciones importantes:

- El producto debe respetar read-only.
- Debe correr con `docker compose up`.
- No debe depender de hardcodear la base demo.
- Cada hallazgo importante debe incluir una recomendacion clara.
- Todos deben poder explicar lo que se entrega.

## Flujo de trabajo

1. Crear o tomar una Issue del GitHub Project.
2. Crear rama propia.
3. Hacer commits claros.
4. Abrir Pull Request.
5. Pedir revision cruzada.
6. Hacer merge solo cuando el PR este aprobado.

Estados del Project:

- Todo
- In Progress
- In Review
- Done

## Uso de IA

Se puede usar IA para apoyo, investigacion, documentacion, revision o ideas
tecnicas. Cualquier uso relevante debe declararse en el Pull Request.
