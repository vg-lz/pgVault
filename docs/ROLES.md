# Roles

Los roles sirven para repartir responsabilidad, no para aislar el trabajo. Todos deben entender lo básico de todo PgVault.

## Roles por asignar

Cuando el equipo lo decida, copiar cada rol a la persona correspondiente en el README.

| Rol | Integrante asignado |
|---|---|
| Conector y orquestador |  |
| Auditor de configuración |  |
| Descubridor de datos sensibles |  |
| Reportes y mapeo regulatorio |  |
| Producto, negocio y coordinación |  |

## Conector y orquestador

Responsable de:

- Conexión read-only a PostgreSQL.
- Extracción de catálogo.
- Orquestación de módulos.
- Integración de hallazgos con recomendaciones.
- Docker Compose junto con el equipo.

Debe explicar al equipo cómo PgVault se conecta y cómo fluye la auditoría.

## Auditor de configuración

Responsable de:

- Checks de roles y privilegios.
- SUPERUSER innecesarios.
- Funciones `SECURITY DEFINER`.
- Configuraciones inseguras.
- Reglas extensibles.
- Recomendaciones técnicas para corregir cada hallazgo.

Debe explicar al equipo cómo se genera un hallazgo de seguridad y qué recomendación corresponde.

## Descubridor de datos sensibles

Responsable de:

- Detección por nombre de columna.
- Detección por contenido con sampling.
- Patrones de CURP, RFC, email, tarjetas, teléfonos, passwords, tokens.
- Score de confianza.
- Recomendaciones según tipo de dato sensible encontrado.

Debe explicar al equipo cómo se detectan datos sensibles sin exponerlos innecesariamente y cómo se recomienda protegerlos.

## Reportes y mapeo regulatorio

Responsable de:

- Score de seguridad.
- Reporte ejecutivo.
- Reporte técnico.
- Sección de recomendaciones automáticas.
- Exportación PDF.
- Mapeo LFPDPPP, PCI-DSS y regulación relevante.

Debe explicar al equipo cómo los hallazgos se convierten en recomendaciones y reportes.

## Producto, negocio y coordinación

Responsable de:

- GitHub Project.
- Documento de negocio.
- Análisis competitivo.
- Pitch.
- Demo.
- Coordinación general.

Debe entender también la parte técnica para defender el producto en Q&A.
