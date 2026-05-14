# Control Del Proyecto

Este documento describe como mantener el trabajo organizado despues de la
entrega inicial. El README concentra la informacion de uso y arquitectura; este
archivo se limita a reglas operativas del equipo.

## Tablero

Nombre sugerido:

```text
PgVault - Control del Proyecto
```

Columnas recomendadas:

- Todo
- In Progress
- In Review
- Done

## Labels

- `backend`
- `postgres`
- `security-checks`
- `sensitive-data`
- `reports`
- `web`
- `documentation`
- `business`
- `demo`
- `testing`
- `urgent`

## Criterios Para Crear Issues

Crear una issue cuando el trabajo:

- cambie comportamiento del scanner;
- agregue o modifique una regla de deteccion;
- toque modelos compartidos;
- cambie contratos de API;
- afecte Docker Compose o las bases demo;
- agregue documentacion relevante para usuarios o mantenedores;
- corrija un bug reproducible.

## Flujo Recomendado

1. Crear o tomar una issue.
2. Crear una rama corta y descriptiva.
3. Implementar cambios pequenos y revisables.
4. Ejecutar validacion local o en Docker.
5. Abrir pull request con resumen y pruebas.
6. Solicitar revision cruzada.
7. Integrar solo cuando la revision este aprobada.

## Definicion De Done

Una tarea se considera terminada cuando:

- el cambio esta implementado;
- las pruebas relevantes pasan;
- no hay imports rotos ni archivos obsoletos referenciados;
- la documentacion queda alineada con el comportamiento real;
- el PR explica impacto, validacion y cualquier uso relevante de IA.
