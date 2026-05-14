# Roles Del Equipo

Los roles reparten responsabilidad, pero no aislan el trabajo. Todos los
integrantes deben poder explicar el flujo principal de PgVault: conexion
read-only, snapshot, modulos, hallazgos y salida por web/CLI.

| Rol | Integrante asignado |
|---|---|
| Conector y orquestador | Diego Vega |
| Auditor de configuracion | Dowshell Smith |
| Descubridor de datos sensibles | Daniela Borquez |
| Reportes y mapeo regulatorio | Mariajose Rito |
| Producto, negocio y coordinacion | Cesar Mendez |

## Conector Y Orquestador

Responsable de:

- Conexion read-only a PostgreSQL.
- Extraccion de catalogo.
- Orquestacion de modulos.
- Integracion de hallazgos con recomendaciones.
- Docker Compose junto con el equipo.

Debe explicar al equipo como PgVault se conecta y como fluye la auditoria.

## Auditor De Configuracion

Responsable de:

- Checks de roles y privilegios.
- SUPERUSER innecesarios.
- Funciones `SECURITY DEFINER`.
- Configuraciones inseguras.
- Reglas extensibles.
- Recomendaciones tecnicas para corregir cada hallazgo.

Debe explicar al equipo como se genera un hallazgo de seguridad y que
recomendacion corresponde.

## Descubridor De Datos Sensibles

Responsable de:

- Deteccion por nombre de columna.
- Deteccion por contenido con sampling.
- Patrones de CURP, RFC, email, tarjetas, telefonos, passwords, tokens.
- Score de confianza.
- Recomendaciones segun tipo de dato sensible encontrado.

Debe explicar al equipo como se detectan datos sensibles sin exponerlos
innecesariamente y como se recomienda protegerlos.

## Reportes Y Mapeo Regulatorio

Responsable de:

- Score de seguridad.
- Reporte ejecutivo.
- Reporte tecnico.
- Seccion de recomendaciones automaticas.
- Exportacion PDF.
- Mapeo LFPDPPP, PCI-DSS y regulacion relevante.

Debe explicar al equipo como los hallazgos se convierten en recomendaciones y
reportes.

## Producto, Negocio Y Coordinacion

Responsable de:

- GitHub Project.
- Documento de negocio.
- Analisis competitivo.
- Pitch.
- Demo.
- Coordinacion general.

Debe entender tambien la parte tecnica para defender el producto en Q&A.
