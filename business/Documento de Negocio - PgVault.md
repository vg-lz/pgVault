# Documento de Negocio — PgVault

> Auditoría de seguridad y cumplimiento para PostgreSQL

---

## 1. El problema

Las empresas medianas en México que manejan datos sensibles (fintechs, healthtechs, SaaS B2B) operan bases de datos PostgreSQL sin saber con certeza qué datos sensibles tienen, quién puede acceder a ellos ni si su configuración cumple con la regulación vigente.

Preparar una auditoría de cumplimiento hoy es un proceso manual, lento y propenso a errores. Un equipo de TI de 3 personas puede tardar días o semanas en recopilar evidencia para una revisión de CNBV o LFPDPPP. Y aun así, los hallazgos suelen ser incompletos.

**El problema en tres líneas:**
- No saben qué datos sensibles tienen ni dónde están
- No saben si los privilegios de su base de datos están bien configurados
- No pueden generar evidencia de cumplimiento regulatorio de forma rápida

---

## 2. La solución — PgVault

PgVault es una herramienta de auditoría de seguridad y cumplimiento para PostgreSQL. Se conecta en modo **solo lectura**, analiza la base de datos y genera reportes accionables en minutos.

### Qué hace PgVault

| Módulo | Qué analiza |
|---|---|
| **Conector** | Conexión read-only, extracción de catálogo, orquestación |
| **Auditor de configuración** | Roles, privilegios, SUPERUSER innecesarios, funciones SECURITY DEFINER |
| **Descubridor de datos sensibles** | CURP, RFC, email, tarjetas, teléfonos, passwords — por nombre de columna y por contenido |
| **Reportes** | Score de seguridad, reporte ejecutivo, reporte técnico, exportación PDF |
| **Mapeo regulatorio** | LFPDPPP, PCI-DSS, CNBV — con artículos específicos por hallazgo |

### Lo que PgVault NO hace
- No escribe nada en la base de datos auditada
- No almacena datos sensibles encontrados
- No requiere agente instalado en el servidor

---

## 3. Mercado objetivo

### Segmento primario
Fintechs, healthtechs y SaaS B2B mexicanas de **20 a 200 empleados** que:
- Usan PostgreSQL en producción
- Manejan datos personales o financieros de usuarios
- Están sujetas a LFPDPPP, CNBV o PCI-DSS
- Tienen equipos de TI pequeños (1-5 personas) sin herramientas especializadas de auditoría

### Tamaño de mercado (estimado)
- México tiene más de 500 fintechs registradas ante CNBV (2024)
- El segmento de 20-200 empleados representa ~60% del ecosistema
- Herramientas comparables (Satori, Cyral) no tienen oferta accesible para este segmento en LATAM

---

## 4. User Persona

### Carlos Mendoza — CISO / Responsable de TI

| Atributo | Detalle |
|---|---|
| **Edad** | 35-45 años |
| **Rol** | CISO, Head of Engineering o Responsable de TI |
| **Empresa** | Fintech mexicana, 50-150 empleados |
| **Stack** | PostgreSQL en AWS RDS o servidor propio |
| **Equipo** | 2-4 personas en TI |
| **Regulación** | Sujeto a LFPDPPP y CNBV, posiblemente PCI-DSS |

**Sus problemas:**
- Recibe auditorías de CNBV y tarda semanas en preparar evidencia manualmente
- No tiene visibilidad de qué columnas contienen datos sensibles en producción
- Sospecha que hay usuarios con más privilegios de los necesarios pero no tiene tiempo de revisarlo
- Las herramientas enterprise (Satori, Imperva) están fuera de su presupuesto

**Sus metas:**
- Demostrar cumplimiento regulatorio sin contratar una consultoría cara
- Tener visibilidad del estado de seguridad de su BD en cualquier momento
- Reducir el tiempo de preparación de auditorías de semanas a horas

**Cómo PgVault le resuelve la vida:**
Ejecuta PgVault en modo lectura, obtiene un reporte con score de seguridad, hallazgos priorizados y mapeo a artículos de LFPDPPP en menos de 10 minutos. Tiene evidencia lista para su próxima auditoría.

---

## 5. Entrevistas con usuarios

> _Esta sección se completará con los resultados de las entrevistas realizadas al equipo._

### Metodología
Se realizaron entrevistas semiestructuradas de ~20 minutos con perfiles de seguridad, TI y compliance. El objetivo fue validar el problema antes de presentar la solución.

### Entrevista 1 — Maybel Noguera

**Perfil del entrevistado:** DBA Senior en MySQL, empresa de telecomunicaciones

**¿Usa PostgreSQL en producción?** Sí — maneja alrededor de 300 bases de datos de diferentes tipos

**Problema principal mencionado:**
> "No sé qué datos específicos hay — sé que son datos de clientes pero no cuáles exactamente."

**Proceso de auditoría:** Cuando hay auditorías, piden evidencias de cumplimiento y el equipo recopila la información manualmente para enviarla.

**Herramientas que usa hoy:** Plugin de audit nativo de MySQL

**Reacción a PgVault:**
> "Se tendría que revisar más a detalle qué tanta información sensible puede proporcionar la herramienta. De primera instancia no la usaría hasta validar."

**Disposición a pagar:** Acepta ambos modelos — pago único con costo menor que la suscripción mensual acumulada.

---

### Entrevista 2 — Eduardo Pacheco Ledezma

**Perfil del entrevistado:** Consultor DBA de Oracle, empresa de consultoría

**¿Usa PostgreSQL en producción?** Sí — maneja MySQL, PostgreSQL y Oracle

**Problema principal mencionado:**
> "Desconozco qué datos sensibles hay ya que el usuario es dueño de la información. Solo se sabe cuando hay un requerimiento del área de seguridad."

**Proceso de auditoría:** Reciben solicitudes con puntos específicos a revisar: usuarios, permisos, si son de aplicativos o consulta, y un hardening para detectar vulnerabilidades.

**Herramientas que usa hoy:** Tabla de auditoría interna que registra movimientos DDL y DML, consultada por personal de seguridad.

**Reacción a PgVault:**
> "La herramienta ayudaría al personal de seguridad de la información para identificar de manera rápida dónde se encuentran datos sensibles en el negocio."

**Disposición a pagar:** La decisión de precio se toma en conjunto entre DBAs, seguridad de la información y área comercial.

---

### Entrevista 3

**Perfil del entrevistado:** _(rol, industria, tamaño de empresa)_

**¿Usa PostgreSQL en producción?** _Sí / No — detalle_

**Problema principal mencionado:**
> _Cita textual aquí_

**Herramientas que usa hoy:** _pgAudit / scripts manuales / ninguna / otra_

**Reacción a PgVault:**
> _Resumen de su reacción y objeciones_

**Disposición a pagar:** _Monto o rango mencionado_

---

### Síntesis de hallazgos

> _Completar después de las 3 entrevistas_

**Problema más común identificado:** _Por completar_

**Principal objeción a PgVault:** _Por completar_

**Rango de disposición a pagar:** _Por completar_

---

## 6. Análisis competitivo

> Fuentes: Vendr, SelectHub, AIM Multiple, PeerSpot, GlobeNewswire — verificado mayo 2026.

| Herramienta | Segmento | Precio real (anual) | Enfoque principal | Disponible en LATAM | Español | On-premise | PostgreSQL específico |
|---|---|---|---|---|---|---|---|
| **Satori** | Enterprise | ~$95,000 USD (promedio); hasta $230,000 USD | Data access control y auditoría | No | No | No | No |
| **Cyral** *(adquirida por Varonis, marzo 2025)* | Enterprise | Cotización — absorbida en plataforma Varonis | Database activity monitoring agentless | No | No | No | No |
| **Immuta** | Enterprise | Desde $5,000 USD/usuario/mes — cotización | Data governance y access control | No | No | Parcial | No |
| **BigID** | Enterprise | $15,000–$175,000 USD anuales — cotización | Data discovery y clasificación | No | No | No | No |
| **PgVault** | SMB LATAM | Por definir (objetivo: $50–150 USD/mes) | Seguridad + cumplimiento regulación MX | **Sí** | **Sí** | **Sí** | **Sí** |

---

## 7. Modelo de negocio (propuesta)

---

## 8. Mapeo regulatorio

### LFPDPPP (Ley Federal de Protección de Datos Personales en Posesión de Particulares)

| Artículo | Obligación | Cómo PgVault ayuda |
|---|---|---|
| Art. 19 | Implementar medidas de seguridad técnicas | Identifica configuraciones inseguras y privilegios excesivos |
| Art. 20 | Establecer y mantener medidas de seguridad | Genera evidencia auditable del estado de seguridad |
| Art. 25 | Proteger datos contra tratamiento no autorizado | Detecta columnas con datos sensibles sin protección adecuada |

### PCI-DSS v4.0

| Requerimiento | Descripción | Cómo PgVault ayuda |
|---|---|---|
| Req. 3 | Proteger datos de tarjetahabientes almacenados | Detecta patrones de tarjetas en columnas y contenido |
| Req. 7 | Restringir acceso a componentes del sistema | Audita roles y privilegios excesivos |
| Req. 8 | Identificar y autenticar acceso | Revisa usuarios con SUPERUSER y permisos innecesarios |

### CNBV (Circular Única de Bancos / Disposiciones para Instituciones de Tecnología Financiera)

| Disposición | Obligación | Cómo PgVault ayuda |
|---|---|---|
| Art. 71 LRITF | Medidas de seguridad de la información | Reporte ejecutivo con hallazgos priorizados |
| Anexo G | Controles de acceso lógico | Auditoría de privilegios y roles en PostgreSQL |

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| El cliente no usa PostgreSQL | Media | Roadmap a MySQL/MariaDB en v2 |
| Desconfianza por acceso a la BD | Alta | Modo read-only verificable + código abierto |
| Competidor grande entra al segmento SMB | Baja | Ventaja de especialización en regulación MX |
| Falsos positivos en detección de datos sensibles | Media | Score de confianza + revisión humana recomendada |

---
