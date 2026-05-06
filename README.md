# PgVault

**Auditor de seguridad y cumplimiento para PostgreSQL**

PgVault es una herramienta diseñada para conectarse a bases de datos PostgreSQL en modo read-only y analizar aspectos de seguridad, configuraciones, privilegios, funciones riesgosas y posibles datos sensibles, sin modificar la base auditada.

## Índice

- [Descripción general](#descripción-general)
- [Integrantes del equipo](#integrantes-del-equipo)
- [Problema que resuelve](#problema-que-resuelve)
- [Objetivo del proyecto](#objetivo-del-proyecto)
- [Principios del sistema](#principios-del-sistema)
- [Arquitectura](#arquitectura)
- [Módulos principales](#módulos-principales)
- [Alcance inicial del MVP](#alcance-inicial-del-mvp)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Uso básico](#uso-básico)
- [Reportes](#reportes)
- [Pitch](#pitch)

## Descripción general

PgVault busca proporcionar una vista clara del estado de seguridad de una base de datos PostgreSQL. Para ello, ejecuta consultas de lectura sobre catálogos del sistema, configuraciones, permisos y estructuras de datos, con el objetivo de identificar hallazgos relevantes y presentarlos de forma organizada.

El sistema no realiza cambios sobre la base auditada. Su propósito es observar, analizar y reportar.

## Integrantes del equipo

- Borquez Hernandez, Daniela
- Mc Donald Smith, Dowshel Jekeal
- Méndez Yépez, César Alejandro
- Rito Michelena, Mariajosé
- Vega Cabrera, Diego

## Problema que resuelve

Muchas bases de datos PostgreSQL pueden contener datos sensibles, privilegios excesivos o configuraciones inseguras sin que el equipo tenga visibilidad completa. Esto dificulta detectar riesgos, priorizar correcciones y mantener evidencia técnica de los problemas encontrados.

PgVault ayuda a centralizar el análisis de seguridad para que los hallazgos puedan revisarse, clasificarse y documentarse de manera más clara.

## Objetivo del proyecto

- Conectarse a PostgreSQL en modo read-only.
- Ejecutar análisis de seguridad.
- Detectar hallazgos relevantes.
- Clasificar hallazgos por severidad.
- Mostrar resultados en un dashboard.
- Generar reportes exportables.
- Mantener evidencia técnica por hallazgo.

## Principios del sistema

### Read-only

PgVault no modifica la base de datos auditada. Su funcionamiento se basa en consultas de lectura.

### Seguridad

El sistema debe proteger credenciales y evitar exponer datos sensibles durante el análisis y la visualización de resultados.

### Evidencia

Cada hallazgo debe contar con soporte técnico que permita entender por qué representa un riesgo.

### Extensibilidad

Las reglas de análisis deben poder crecer sin depender de nombres específicos hardcodeados.

## Arquitectura

Por definir.

La arquitectura inicial deberá contemplar, como mínimo, los siguientes componentes:

- Conector read-only hacia PostgreSQL.
- Motor de análisis de reglas.
- Almacenamiento temporal o persistente de resultados.
- API para consultar hallazgos.
- Dashboard web.
- Generador de reportes exportables.

## Módulos principales

### Módulo 1: Auditoría de configuración y seguridad

Analiza roles, privilegios, autenticación, logging, extensiones y funciones `SECURITY DEFINER`.

### Módulo 2: Descubrimiento de datos sensibles

Detecta datos sensibles por nombre de columna y por contenido. Algunos patrones iniciales son: `curp`, `rfc`, `email`, `telefono`, `tarjeta`, `cvv` y `password`.

### Módulo 3: Reportes y visualización

Presenta hallazgos en un dashboard, clasifica resultados por severidad, muestra evidencia, incluye recomendaciones y permite exportar reportes.

## Alcance inicial del MVP

- Conexión a PostgreSQL.
- Lectura de catálogos del sistema.
- Detección de configuraciones inseguras.
- Detección de privilegios excesivos.
- Detección de datos sensibles.
- Dashboard web.
- Exportación de reportes.

## Tecnologías

- Backend: FastAPI o Node/Express.
- Base de datos objetivo: PostgreSQL.
- Frontend: React/Vite u otra alternativa simple.
- Reportes: PDF.
- Despliegue: Docker Compose.

## Estructura del proyecto

Por definir.

La estructura final del repositorio se documentará cuando se definan los módulos técnicos principales.

## Instalación

```bash
git clone <URL_DEL_REPOSITORIO>
cd pgvault
cp .env.example .env
docker compose up --build
```

## Uso básico

1. Configurar conexión a PostgreSQL.
2. Levantar el proyecto.
3. Ejecutar análisis.
4. Revisar hallazgos en dashboard.
5. Exportar reportes.

## Reportes

Por definir.

Los reportes deberán incluir hallazgos clasificados por severidad, evidencia técnica y recomendaciones generales para su revisión.

## Pitch

Link del pitch: <AGREGAR_LINK_AQUI>
