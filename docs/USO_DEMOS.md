# Uso, demos y validacion

Esta guia concentra los detalles operativos para ejecutar PgVault, usar la web,
probar las bases demo y validar el proyecto con Docker.

## Docker Compose

Levantar todo el entorno:

```bash
docker compose up --build
```

La web queda disponible en:

```text
http://localhost:8000
```

El servicio `pgvault` levanta FastAPI y sirve el frontend estatico desde el
mismo contenedor.

Ejecutar la CLI dentro del contenedor:

```bash
docker compose run --rm pgvault python -m pgvault scan
```

## Bases demo

Docker Compose levanta tres bases demo con problemas plantados:

| Base | Host desde la web | Puerto desde la web | Puerto local | Usuario | Contrasena |
|---|---|---:|---:|---|---|
| FintechDB | `fintechdb` | `5432` | `5433` | `fintech_user` | `fintech_pass` |
| TiendaDB | `tiendadb` | `5432` | `5432` | `tienda_user` | `tienda_pass` |
| AppDB | `appdb` | `5432` | `5434` | `app_user` | `app_pass` |

Cuando PgVault corre dentro de Docker, el host debe ser el nombre del servicio
(`fintechdb`, `tiendadb` o `appdb`), no `localhost`.

## Datos para la web

Usa estos valores en el formulario de `http://localhost:8000`. El puerto es
siempre `5432` porque PgVault se conecta desde otro contenedor dentro de la red
de Docker Compose.

| Alias sugerido | Host | Puerto | Base de datos | Usuario | Contrasena | sslmode | Sample limit | Query timeout |
|---|---|---:|---|---|---|---|---:|---:|
| `fintechdb-demo` | `fintechdb` | `5432` | `fintechdb` | `fintech_user` | `fintech_pass` | `disable` | `100` | `10` |
| `tiendadb-demo` | `tiendadb` | `5432` | `tiendadb` | `tienda_user` | `tienda_pass` | `disable` | `100` | `10` |
| `appdb-demo` | `appdb` | `5432` | `appdb` | `app_user` | `app_pass` | `disable` | `100` | `10` |

## Alcance de las bases demo

Las bases demo estan integradas como servicios de Docker Compose y se conservan
sin modificar. Sirven para demostrar conexion, extraccion de catalogo,
deteccion de datos sensibles y controles de configuracion.

| Perfil en la web | Base | Objetivo de demostracion | Credenciales |
|---|---|---|---|
| `fintechdb-demo` | `fintechdb` | Seguridad, cumplimiento, roles, privilegios y datos sensibles | `fintech_user` / `fintech_pass` |
| `tiendadb-demo` | `tiendadb` | Inventario, datos sensibles y controles de configuracion disponibles por catalogo | `tienda_user` / `tienda_pass` |
| `appdb-demo` | `appdb` | Inventario, datos sensibles y controles de configuracion disponibles por catalogo | `app_user` / `app_pass` |

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

La pantalla inicial muestra el formulario de conexion para PostgreSQL: alias,
host, puerto, base de datos, usuario, contrasena, `sslmode`, `sample limit` y
`query timeout`.

Flujo recomendado:

1. Abrir `http://localhost:8000`.
2. Elegir un perfil demo guardado o completar los datos de conexion.
3. Opcionalmente presionar **Guardar datos** para persistir el perfil sin contrasena.
4. Presionar **Validar conexion**.
5. Si la validacion es correcta, presionar **Realizar revision**.
6. Revisar hallazgos, warnings, errores, recomendaciones, SQL sugerido y referencias regulatorias.

### Perfiles e historial locales

La web guarda perfiles de conexion por alias e historial de revisiones solo en
el navegador del usuario mediante `localStorage`. Por seguridad, esos datos no
se guardan en el backend, no se comparten con otros usuarios de la misma
instancia y no se versionan en Git.

- Guardar perfiles es opcional. **Validar conexion** no persiste datos.
- **Guardar / actualizar** persiste o edita alias, host, puerto, base, usuario,
  `sslmode`, `sample limit` y `query timeout`.
- La contrasena no se persiste ni se muestra de vuelta en la UI.
- Al reutilizar un perfil guardado, hay que escribir la contrasena de nuevo.
- Si se limpia el almacenamiento del navegador, se pierden perfiles e historial locales.

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

## Validacion con Docker

Verificar la configuracion de Compose:

```bash
docker compose config
```

Construir la imagen de PgVault:

```bash
docker compose build pgvault
```

Ejecutar pruebas dentro del contenedor:

```bash
docker compose run --rm --no-deps pgvault python -m pytest -q
```

Levantar las bases demo y la web PgVault:

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

## CLI para otra base demo

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
