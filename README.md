# PgVault

PgVault es un auditor de seguridad y cumplimiento para PostgreSQL. Se conecta en modo read-only, analiza configuración, privilegios y datos sensibles, y genera hallazgos con evidencia, recomendaciones automáticas, score y reportes.

## Equipo

Integrantes del equipo:

- Borquez Hernandez, Daniela
- Mc Donald Smith, Dowshel Jekeal
- Mendez Yepez, Cesar Alejandro
- Rito Michelena, Mariajose
- Vega Cabrera, Diego

Cuando el equipo defina roles, llenar esta tabla. En GitHub Projects, Issues y PRs se recomienda usar el número de integrante para mantener todo ordenado.

| Integrante | Nombre | Rol principal |
|---|---|---|
| Integrante 1 |  |  |
| Integrante 2 |  |  |
| Integrante 3 |  |  |
| Integrante 4 |  |  |
| Integrante 5 |  |  |

Aunque cada quien tenga un rol principal después, todos deben entender lo básico del proyecto completo.

## Entregas

- **9 de mayo:** base inicial, roles, tablero, primeras tareas y avance técnico inicial.
- **12 de mayo:** demo parcial con integración y al menos 8 hallazgos funcionando.
- **15 de mayo:** MVP final, Docker Compose, reportes, pitch, video demo y Q&A.

## Documentos útiles

- [GitHub Projects](docs/CONTROL_GITHUB_PROJECTS.md)
- [Reglas de Git](docs/REGLAS_GIT.md)
- [Roles](docs/ROLES.md)

## Alcance del MVP

- Conexión read-only a PostgreSQL.
- Extracción de información del catálogo.
- Checks de seguridad y configuración.
- Detección de datos sensibles por nombre y contenido.
- Recomendaciones automáticas por hallazgo detectado.
- Dashboard o salida visual.
- Reporte ejecutivo y técnico.
- Exportación a PDF.
- Docker Compose.

## Tecnología

El equipo puede elegir las herramientas que considere mejores. Se permite usar herramientas open source e IA, siempre que se entienda, se valide y se declare su uso.

Condiciones importantes:

- El producto debe respetar read-only.
- Debe correr con `docker compose up`.
- No debe depender de hardcodear la base demo.
- Cada hallazgo importante debe incluir una recomendación clara.
- Todos deben poder explicar lo que se entrega.

## Flujo de trabajo

1. Crear o tomar una Issue del GitHub Project.
2. Crear rama propia.
3. Hacer commits claros.
4. Abrir Pull Request.
5. Pedir revisión cruzada.
6. Hacer merge solo cuando el PR esté aprobado.

Estados del Project:

- Todo
- In Progress
- In Review
- Done

## Uso de IA

Se puede usar IA para apoyo, investigación, documentación, revisión o ideas técnicas. Cualquier uso relevante debe declararse en el Pull Request.
