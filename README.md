# PgVault

PgVault es un auditor de seguridad y cumplimiento para PostgreSQL. Se conecta
en modo read-only, analiza configuracion, privilegios y datos sensibles, y
produce hallazgos con evidencia y recomendaciones.

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

## Entregas

- **9 de mayo:** base inicial, roles, tablero, primeras tareas y avance tecnico inicial.
- **12 de mayo:** demo parcial con integracion y al menos 8 hallazgos funcionando.
- **15 de mayo:** MVP final, Docker Compose, reportes, pitch, video demo y Q&A.

## Documentos utiles

- [Guia base](docs/BASE.md)
- [GitHub Projects](docs/CONTROL_GITHUB_PROJECTS.md)
- [Reglas de Git](docs/REGLAS_GIT.md)
- [Roles](docs/ROLES.md)

## Ejecucion

El proyecto esta preparado para ejecutarse con Docker Compose:

```bash
docker compose up --build
```

La interfaz web queda disponible en:

```text
http://localhost:8000
```

El servicio `pgvault` levanta FastAPI y sirve el frontend estatico desde el
mismo contenedor.

Docker Compose levanta tres bases demo con problemas plantados:

| Base | Host desde la web | Puerto desde la web | Puerto local | Usuario | Contrasena |
|---|---|---:|---:|---|---|
| FintechDB | `fintechdb` | `5432` | `5433` | `fintech_user` | `fintech_pass` |
| TiendaDB | `tiendadb` | `5432` | `5432` | `tienda_user` | `tienda_pass` |
| AppDB | `appdb` | `5432` | `5434` | `app_user` | `app_pass` |

La web incluye perfiles demo para estas tres bases. Cuando PgVault corre dentro
de Docker, el host debe ser el nombre del servicio (`fintechdb`, `tiendadb` o
`appdb`), no `localhost`.

### Datos para conectar desde la pagina web

Usa estos valores en el formulario de `http://localhost:8000`. El puerto es
siempre `5432` porque PgVault se conecta desde otro contenedor dentro de la red
de Docker Compose.

| Alias sugerido | Host | Puerto | Base de datos | Usuario | Contrasena | sslmode | Sample limit | Query timeout |
|---|---|---:|---|---|---|---|---:|---:|
| `fintechdb-demo` | `fintechdb` | `5432` | `fintechdb` | `fintech_user` | `fintech_pass` | `disable` | `100` | `10` |
| `tiendadb-demo` | `tiendadb` | `5432` | `tiendadb` | `tienda_user` | `tienda_pass` | `disable` | `100` | `10` |
| `appdb-demo` | `appdb` | `5432` | `appdb` | `app_user` | `app_pass` | `disable` | `100` | `10` |

## Bases de prueba del profesor

Las bases de datos de prueba entregadas por el profesor estan integradas como
servicios de Docker Compose y se conservan sin modificar. PgVault debe
analizarlas tal como vienen, porque contienen los errores y problemas plantados
para evaluar la deteccion.

| Perfil en la web | Base | Objetivo de prueba | Credenciales |
|---|---|---|---|
| `fintechdb-demo` | `fintechdb` | Seguridad, cumplimiento, roles, privilegios y datos sensibles | `fintech_user` / `fintech_pass` |
| `tiendadb-demo` | `tiendadb` | Salud general, indices, bloat, configuracion y rendimiento | `tienda_user` / `tienda_pass` |
| `appdb-demo` | `appdb` | Queries problematicas, planes de ejecucion y anti-patterns | `app_user` / `app_pass` |

Para probarlas desde la web:

1. Levantar el entorno con `docker compose up --build`.
2. Abrir `http://localhost:8000`.
3. Elegir uno de los perfiles demo.
4. Presionar **Validar conexion**.
5. Presionar **Realizar revision**.

Puertos para clientes externos como DBeaver, pgAdmin o `psql` local:

```text
fintechdb -> localhost:5433
tiendadb  -> localhost:5432
appdb     -> localhost:5434
```

## Interfaz web

La pantalla inicial muestra solamente el formulario de conexion para PostgreSQL:
alias, host, puerto, base de datos, usuario, contrasena, `sslmode`,
`sample limit` y `query timeout`.

1. Abrir `http://localhost:8000`.
2. Elegir un perfil demo guardado o completar los datos de conexion. Para
   FintechDB dentro de Docker Compose:

```text
alias: fintechdb-demo
host: fintechdb
puerto: 5432
base de datos: fintechdb
usuario: fintech_user
contrasena: fintech_pass
sslmode: disable
sample limit: 100
query timeout: 10
```

3. Opcionalmente presionar **Guardar datos** para persistir el perfil sin
   contrasena.
4. Presionar **Validar conexion**. PgVault abre una conexion con
`pgvault.db.DatabaseClient` y ejecuta una consulta read-only minima.
5. Si la validacion es correcta, se habilita **Realizar revision**.
6. Al ejecutar la revision, la web llama a `pgvault.orchestrator.run_scan(...)`
con una instancia de `PgVaultConfig` construida desde el formulario.
7. El resultado se muestra en una vista de dos paneles: hallazgos, warnings y
errores a la izquierda; explicacion tecnica, recomendacion, SQL sugerido,
referencias regulatorias y documentacion publica a la derecha.

### Perfiles e historial locales

La web guarda perfiles de conexion por alias e historial de revisiones solo en
el navegador del usuario mediante `localStorage`. Por seguridad, esos datos no
se guardan en el backend, no se comparten con otros usuarios de la misma
instancia y no se versionan en Git.

- Guardar perfiles es opcional. **Validar conexion** no persiste datos.
- **Guardar / actualizar** persiste o edita alias, host, puerto, base, usuario,
  `sslmode`, `sample limit` y `query timeout`.
- Los perfiles se seleccionan desde el sidebar izquierdo.
- Cada perfil tiene un menu de tres puntos. En perfiles locales permite
  **Modificar** o **Eliminar**; en perfiles demo solo permite cargarlos para
  modificarlos como base de un nuevo perfil local.
- **Eliminar** borra un perfil guardado manualmente. Los perfiles demo siguen
  apareciendo como accesos rapidos y no se eliminan desde la UI.
- Al elegir **Nuevo perfil**, el formulario se limpia para capturar una nueva
  conexion.
- El historial de revisiones se guarda por alias/base de datos y aparece junto
  a la lista de hallazgos.
- Por seguridad, la contrasena no se persiste en SQLite ni se muestra de vuelta
  en la UI. Al reutilizar un perfil guardado, hay que escribir la contrasena de
  nuevo antes de validar o revisar.
- La contrasena nunca se guarda en `localStorage`; solo se usa en la sesion para
  validar o ejecutar una revision.
- Si se limpia el almacenamiento del navegador, se pierden perfiles e historial
  locales.

Endpoints utiles:

```text
GET  /api/profiles
POST /api/validate
POST /api/scans
GET  /api/scans?alias=fintechdb-demo
GET  /api/scans/{id}
```

Nota: los endpoints de perfiles e historial no guardan datos del lado servidor.
La persistencia visible en la UI es local al navegador.

## CLI

La CLI existente sigue disponible:

```bash
python -m pgvault scan
```

Dentro de Docker Compose:

```bash
docker compose run --rm pgvault python -m pgvault scan
```

Por defecto la CLI dentro de Compose apunta a FintechDB. Para escanear otra
base demo desde la CLI:

```powershell
docker compose run --rm `
  -e PGHOST=tiendadb `
  -e PGDATABASE=tiendadb `
  -e PGUSER=tienda_user `
  -e PGPASSWORD=tienda_pass `
  pgvault python -m pgvault scan
```

## Validacion con Docker

1. Verificar la configuracion de Compose:

```bash
docker compose config
```

2. Construir la imagen de PgVault:

```bash
docker compose build pgvault
```

3. Ejecutar pruebas dentro del contenedor. La suite valida la integracion de
   `demo-databases`, Docker Compose, perfiles demo de la web y documentacion:

```bash
docker compose run --rm --no-deps pgvault python -m pytest -q
```

4. Levantar las bases demo y la web PgVault:

```bash
docker compose up --build
```

La primera inicializacion puede tardar varios minutos, especialmente AppDB.
Si ya existia un volumen anterior de PostgreSQL y quieres cargar las bases demo
desde cero, ejecuta:

```bash
docker compose down -v --remove-orphans
docker compose up --build
```

Ese comando borra los datos de los contenedores de demo y vuelve a sembrarlos.

## Alcance del MVP

- Conexion read-only a PostgreSQL.
- Extraccion de informacion del catalogo.
- Checks de seguridad y configuracion.
- Deteccion de datos sensibles por nombre y contenido.
- Recomendaciones automaticas por hallazgo detectado.
- Dashboard o salida visual.
- Reporte ejecutivo y tecnico.
- Exportacion a PDF.
- Docker Compose.

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
