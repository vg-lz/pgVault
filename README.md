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

## Validacion con Docker

1. Verificar la configuracion de Compose:

```bash
docker compose config
```

2. Construir la imagen de PgVault:

```bash
docker compose build pgvault
```

3. Ejecutar pruebas dentro del contenedor:

```bash
docker compose run --rm --no-deps pgvault python -m pytest -q
```

4. Levantar PostgreSQL y ejecutar PgVault:

```bash
docker compose up --build
```

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
