# Reglas De Git

## Reglas principales

- No hacer push directo a `main`.
- Trabajar en ramas por tarea.
- Abrir Pull Request para integrar cambios.
- Cada PR debe tener al menos una revisión.
- Cada integrante debe tener commits propios.
- Declarar uso relevante de IA en el PR.

## Ramas

Formato:

```text
feature/nombre-corto
fix/nombre-corto
docs/nombre-corto
test/nombre-corto
```

Ejemplos:

```text
feature/conexion-readonly
feature/detector-superuser
feature/detector-curp
feature/reporte-ejecutivo
docs/readme
fix/docker-compose
```

## Commits

Ejemplos:

```text
feat: agrega conexión read-only
feat: implementa detector de superuser
feat: agrega detección de CURP
fix: corrige error de conexión
docs: actualiza README
test: valida detector de email
```

## Pull Requests

Cada PR debe explicar:

- Qué se hizo.
- Cómo se validó.
- Qué Issue resuelve.
- Si se usó IA.
