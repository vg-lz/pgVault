# FintechDB v1.0 — Lista Maestra de Hallazgos

⚠️ **DOCUMENTO CONFIDENCIAL — SOLO PROFESOR** ⚠️

No compartir con alumnos. Este documento es la verdad de fondo para
evaluar el Criterio 2.1 (Cobertura) del proyecto PgVault.

---

## Resumen ejecutivo

- **Total de problemas plantados: 22**
- Distribución: 10 configuración/postura, 9 datos sensibles, 3 cumplimiento
- Para 12/12 pts en cobertura: detectar 20-22 (≥90%)
- Para 10/12 pts: detectar 17-19 (75-89%)
- Para 8/12 pts: detectar 14-16 (60-74%)

---

## MÓDULO 1: Configuración y postura de seguridad (10 problemas)

### H01 — Usuario `admin` con contraseña débil
- **Tipo:** Credenciales débiles
- **Detección esperada:** consultar lista de roles y comparar contra diccionario común de passwords débiles, o detectar passwords de longitud < N caracteres si pueden leerse de `pg_authid`
- **Evidencia:** rol `admin` con password `admin123` (en `pg_authid.rolpassword` aparece como SCRAM/MD5)
- **Recomendación esperada:** forzar reset de contraseña + política de complejidad
- **Nota:** detectar passwords débiles directamente desde `pg_authid` requiere acceso especial. Aceptar también detección por nombre de rol "admin" + recomendar política, o por defecto sospechar de admin/superadmin con métodos de auth débiles.
- **Severidad:** ALTA

### H02 — Usuario `app_legacy` sin contraseña
- **Tipo:** Cuenta sin password (autenticación trust requerida)
- **Detección esperada:** `SELECT rolname FROM pg_authid WHERE rolpassword IS NULL AND rolcanlogin = true;`
- **Evidencia:** rol `app_legacy` con `rolpassword = NULL`
- **Recomendación esperada:** asignar password fuerte o eliminar el rol si no se usa
- **Severidad:** ALTA

### H03 — pg_hba.conf permite `trust` desde `0.0.0.0/0` para app_legacy
- **Tipo:** Misconfig de autenticación de red
- **Detección esperada:** `SELECT * FROM pg_hba_file_rules WHERE auth_method = 'trust';`
- **Evidencia:** vista `pg_hba_file_rules` muestra una línea con `auth_method=trust` y `address={0.0.0.0/0}`
- **Recomendación esperada:** eliminar la línea, usar `md5` o `scram-sha-256` con TLS
- **Severidad:** CRÍTICA

### H04 — Rol `analyst_user` con SUPERUSER
- **Tipo:** Privilegios excesivos
- **Detección esperada:** `SELECT rolname FROM pg_roles WHERE rolsuper = true;` y reportar todos los superusers no esenciales (todos excepto `postgres` típicamente)
- **Evidencia:** `analyst_user` tiene `rolsuper = true`
- **Recomendación esperada:** revocar SUPERUSER y otorgar solo los privilegios mínimos necesarios
- **Severidad:** ALTA

### H05 — Rol `reports_user` con SELECT en `cards` (PCI violation)
- **Tipo:** Acceso indebido a datos de tarjetas (viola PCI-DSS)
- **Detección esperada:** identificar tablas con datos PCI (cards, por nombre o por contenido PAN/CVV) y verificar quién tiene SELECT
- **Evidencia:** `information_schema.role_table_grants` muestra `reports_user|cards|SELECT`
- **Recomendación esperada:** revocar SELECT, crear vista enmascarada (last 4 digits)
- **Mapeo regulatorio:** PCI-DSS Req. 3 (Protect stored cardholder data), Req. 7 (Restrict access)
- **Severidad:** CRÍTICA

### H06 — `PUBLIC` con SELECT en `customers`
- **Tipo:** Privilegio peligroso heredado por todos los roles nuevos
- **Detección esperada:** consultar grants donde `grantee = 'PUBLIC'` sobre tablas con PII detectada
- **Evidencia:** `customers` tiene grant de SELECT a PUBLIC
- **Recomendación esperada:** `REVOKE SELECT ON customers FROM PUBLIC;`
- **Mapeo regulatorio:** LFPDPPP (principio de información mínima)
- **Severidad:** ALTA

### H07 — `get_customer_full_data()` es SECURITY DEFINER con search_path mutable
- **Tipo:** Vector clásico de ataque por search_path injection
- **Detección esperada:** `SELECT proname FROM pg_proc WHERE prosecdef = true AND proconfig IS NULL;` o `proconfig` no contiene `search_path`
- **Evidencia:** función con `prosecdef=t` y `proconfig=NULL`
- **Recomendación esperada:** `ALTER FUNCTION ... SET search_path = pg_catalog, public;`
- **Severidad:** CRÍTICA

### H08 — Logging desactivado (sin auditoría de accesos)
- **Tipo:** Misconfig de auditoría
- **Detección esperada:** `SHOW log_statement; SHOW log_connections; SHOW log_min_duration_statement;`
- **Evidencia:** `log_statement='none'`, `log_connections=off`, `log_min_duration_statement=-1`
- **Recomendación esperada:** activar al menos `log_connections=on`, `log_disconnections=on`, `log_statement='ddl'` o `'mod'`, `log_min_duration_statement=1000`
- **Mapeo regulatorio:** PCI-DSS Req. 10 (Track and monitor access)
- **Severidad:** ALTA

### H09 — Extensión `dblink` instalada sin uso aparente
- **Tipo:** Superficie de ataque innecesaria
- **Detección esperada:** `SELECT extname FROM pg_extension;` y reportar extensiones peligrosas (dblink, pg_read_server_files, lo_import, etc.)
- **Evidencia:** `dblink` aparece en `pg_extension`
- **Recomendación esperada:** verificar uso real; si no se usa, `DROP EXTENSION dblink;`
- **Severidad:** MEDIA

### H10 — `archive_mode = off` (sin política de backups continua)
- **Tipo:** Sin point-in-time recovery
- **Detección esperada:** `SHOW archive_mode;`
- **Evidencia:** `archive_mode = off`
- **Recomendación esperada:** activar `archive_mode=on` con `archive_command` apropiado, o documentar estrategia de backup alternativa
- **Mapeo regulatorio:** ISO 27001 (continuidad de negocio), CNBV (resguardo de información)
- **Severidad:** ALTA

---

## MÓDULO 2: Descubrimiento de datos sensibles (9 problemas)

### H11 — `customers.rfc` no marcada como sensible
- **Tipo:** PII detectable por nombre de columna
- **Detección esperada:** regex sobre nombres de columna: `\\brfc\\b`
- **Evidencia:** existe la columna `customers.rfc VARCHAR(13)`
- **Mapeo regulatorio:** LFPDPPP (datos personales)
- **Severidad:** ALTA

### H12 — `customers.curp` no marcada como sensible
- **Tipo:** PII detectable por nombre
- **Detección esperada:** regex `\\bcurp\\b`
- **Evidencia:** columna `customers.curp VARCHAR(18)`
- **Severidad:** ALTA

### H13 — `customers.email` no marcada como sensible
- **Tipo:** PII detectable por nombre
- **Detección esperada:** regex `\\bemail\\b|\\bmail\\b`
- **Evidencia:** columna `customers.email`
- **Nota:** `internal_users.email` también existe pero es información laboral menos crítica. Algunos detectores la marcarán igual; aceptable.
- **Severidad:** MEDIA

### H14 — `cards.pan` (número de tarjeta completo) — VIOLACIÓN PCI GROSERA
- **Tipo:** PAN sin tokenización
- **Detección esperada:** regex `\\bpan\\b` en nombres de columna + (opcional) sampling de contenido para detectar 13-19 dígitos Luhn-válidos
- **Evidencia:** columna `cards.pan VARCHAR(20)` con valores tipo `5000000076543387`
- **Recomendación esperada:** tokenizar el PAN, almacenar solo last 4 + token, usar gateway PCI compliant
- **Mapeo regulatorio:** PCI-DSS Req. 3.2 (Do not store sensitive authentication data after authorization)
- **Severidad:** CRÍTICA

### H15 — `cards.cvv` almacenado — ULTRA PROHIBIDO POR PCI
- **Tipo:** CVV/CVV2 nunca debe almacenarse después de la autorización
- **Detección esperada:** regex `\\bcvv\\b|\\bcvv2\\b|\\bcid\\b` en nombres de columna
- **Evidencia:** columna `cards.cvv VARCHAR(4)` con valores de 3 dígitos
- **Recomendación esperada:** ELIMINAR INMEDIATAMENTE. CVV nunca debe persistirse, ni encriptado.
- **Mapeo regulatorio:** PCI-DSS Req. 3.2.2 (PROHIBIDO almacenar CVV)
- **Severidad:** CRÍTICA

### H16 — `internal_users.password_plain` con contraseñas en TEXT plano
- **Tipo:** Credenciales en plain text
- **Detección esperada:** regex `password|passwd|pwd` en nombres de columna + sampling para verificar que no parecen hashes (longitud > 50, formato bcrypt/argon2)
- **Evidencia:** columna con valores como `admin123`, `pass1!23`
- **Recomendación esperada:** migrar a bcrypt/argon2, eliminar la columna plain
- **Mapeo regulatorio:** OWASP, ISO 27001
- **Severidad:** CRÍTICA

### H17 — `customer_notes.body` contiene CURPs y RFCs en texto libre
- **Tipo:** PII oculta en columna con nombre genérico
- **Detección esperada:** sampling de contenido de columnas TEXT/VARCHAR grandes, aplicando regex de RFC y CURP a los valores
- **Evidencia:** ~2000 filas contienen `CURP: XXXX######HXXXXXXX##` literalmente, ~1000 contienen `RFC: XXXX######XXX`
- **Recomendación esperada:** sanitizar el campo, identificar y enmascarar la PII, capacitar a soporte para no escribirla
- **Severidad:** ALTA

### H18 — `audit_log.details` (JSONB) contiene PII
- **Tipo:** PII en logs (común y peligroso)
- **Detección esperada:** muestrear documentos JSONB y aplicar regex/heurísticas sobre valores escalares; identificar claves como `email`, `pan`, `pan_last4`, etc.
- **Evidencia:** ~5000 entradas tienen `{"exported_email": "...", "exported_pan_last4": "..."}` en `details`
- **Recomendación esperada:** sanitizar logs de PII, usar IDs en lugar de valores, política de retención agresiva
- **Severidad:** ALTA

### H19 — `merchants.bank_account` contiene CLABE (18 dígitos)
- **Tipo:** PII de pago en columna con nombre genérico
- **Detección esperada:** sampling de columnas y aplicar regex `^[0-9]{18}$` (CLABE mexicana)
- **Evidencia:** 200 filas con CLABEs de 18 dígitos
- **Recomendación esperada:** marcar como sensible, considerar enmascaramiento, restringir acceso por rol
- **Mapeo regulatorio:** LFPDPPP, CNBV
- **Severidad:** MEDIA

---

## MÓDULO 3: Cumplimiento y auditoría (3 problemas)

### H20 — Tabla `cards` sin auditoría
- **Tipo:** Falta de cobertura de auditoría sobre datos sensibles
- **Detección esperada:** para cada tabla con datos sensibles detectados, verificar si existen triggers que escriban en alguna tabla de auditoría O si existe una tabla `<table>_history` o `<table>_audit`
- **Evidencia:**
  - `SELECT count(*) FROM information_schema.triggers WHERE event_object_table='cards';` = 0
  - `SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'cards_%';` = 0
- **Recomendación esperada:** crear trigger AFTER INSERT/UPDATE/DELETE que escriba en `audit_log`, o tabla de history dedicada
- **Mapeo regulatorio:** PCI-DSS Req. 10.2 (Track all access to cardholder data)
- **Severidad:** ALTA

### H21 — `audit_log` no es append-only
- **Tipo:** Logs alterables (no cumple requisitos de inmutabilidad)
- **Detección esperada:** verificar que existan privilegios UPDATE/DELETE sobre `audit_log` para roles que no deberían tenerlos
- **Evidencia:** `audit_log` tiene grants de UPDATE y DELETE para PUBLIC
- **Recomendación esperada:** `REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC;`, crear trigger BEFORE UPDATE/DELETE que raise exception, o hacer la tabla un foreign data wrapper a almacenamiento append-only
- **Mapeo regulatorio:** PCI-DSS Req. 10.5 (Secure audit trails)
- **Severidad:** ALTA

### H22 — `audit_log` sin política de retención (datos de 3+ años)
- **Tipo:** Acumulación indefinida de logs con PII
- **Detección esperada:** detectar tablas con `MIN(created_at)` muy antiguo y sin partitioning visible
- **Evidencia:** ~1000 registros con `created_at` de hace 3+ años
- **Recomendación esperada:** definir política de retención (ej. 7 años para fintech), implementar partitioning por fecha, archivar registros antiguos
- **Mapeo regulatorio:** LFPDPPP (principio de calidad — datos no deben conservarse más de lo necesario)
- **Severidad:** MEDIA

---

## Cómo verificar manualmente

Antes del Demo Day, ejecuta estas queries para confirmar que los problemas están plantados:

```sql
-- H01: admin existe
SELECT rolname FROM pg_roles WHERE rolname IN ('admin', 'superadmin');

-- H02: app_legacy sin password
SELECT rolname FROM pg_authid WHERE rolname = 'app_legacy' AND rolpassword IS NULL;

-- H03: pg_hba con trust desde 0.0.0.0/0
SELECT user_name, address, auth_method FROM pg_hba_file_rules WHERE auth_method = 'trust' AND address::text = '0.0.0.0';

-- H04: superusers no esenciales
SELECT rolname FROM pg_roles WHERE rolsuper = true AND rolname != 'postgres';

-- H05: roles con acceso a cards
SELECT grantee, privilege_type FROM information_schema.role_table_grants WHERE table_name = 'cards';

-- H06: PUBLIC con SELECT en customers
SELECT grantee, privilege_type FROM information_schema.role_table_grants
WHERE table_name = 'customers' AND grantee = 'PUBLIC';

-- H07: SECURITY DEFINER con search_path mutable
SELECT proname FROM pg_proc WHERE prosecdef = true AND proconfig IS NULL AND pronamespace = 'public'::regnamespace;

-- H08: logging desactivado
SHOW log_statement; SHOW log_connections; SHOW log_min_duration_statement;

-- H09: extensiones peligrosas
SELECT extname FROM pg_extension WHERE extname IN ('dblink', 'pg_read_server_files');

-- H10: archive_mode
SHOW archive_mode;

-- H11-H16: columnas con nombres sensibles
SELECT table_name, column_name FROM information_schema.columns
WHERE column_name ~ '(rfc|curp|email|pan|cvv|password|phone|clabe)$'
  AND table_schema = 'public' ORDER BY table_name;

-- H17: CURPs en customer_notes
SELECT count(*) FROM customer_notes WHERE body ~ '[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9]{2}';

-- H18: PII en audit_log JSONB
SELECT count(*) FROM audit_log WHERE details ? 'exported_email';

-- H19: CLABEs en merchants
SELECT count(*) FROM merchants WHERE bank_account ~ '^[0-9]{18}$';

-- H20: triggers en cards (debería ser 0)
SELECT count(*) FROM information_schema.triggers WHERE event_object_table = 'cards';

-- H21: privilegios DELETE/UPDATE en audit_log para PUBLIC
SELECT privilege_type FROM information_schema.role_table_grants
WHERE table_name = 'audit_log' AND grantee = 'PUBLIC' AND privilege_type IN ('UPDATE', 'DELETE');

-- H22: registros antiguos en audit_log
SELECT MIN(created_at)::date, count(*) FROM audit_log
WHERE created_at < NOW() - INTERVAL '2 years';
```

---

## Niveles de dificultad esperada

- **Fáciles (debería detectar todos):** H02, H04, H07, H09, H10, H11, H12, H13, H14, H15, H16
- **Medios:** H01, H03, H05, H06, H08, H19, H20, H21, H22
- **Difíciles (separan al excelente):** H17 (sampling de texto libre), H18 (recursión en JSONB)

Si la mayoría detecta menos del 50%, considerar bajar el umbral del Criterio 2.1
o aclarar mejor la documentación pública.
Si la mayoría detecta más del 90% sin esfuerzo, plantar problemas más sutiles.

---

## Observaciones para el Demo Day

Algunos detectores van a reportar adicionales que NO están en la lista pero son
razonables:

- `merchants.rfc` (existe en el schema, regex `\brfc\b` la detecta) — es PII real,
  no penalizar como falso positivo. **Aceptar como hallazgo bonus.**
- `customers.phone` (regex podría detectarla) — PII también, no penalizar.
- `internal_users.email` — info laboral, no penalizar.
- Funciones del schema `public` que no son SECURITY DEFINER pero podrían
  beneficiarse de search_path explícito — no plantadas como problema, no
  contar como hallazgo.

Si un equipo reporta 25 hallazgos pero solo 19 están en la lista oficial,
los 6 adicionales razonables se cuentan como cobertura legítima si son PII real.
Los falsos positivos reales (reportar `customers.full_name` como PII crítica
cuando no lo es para regla de negocio típica, etc.) sí restan.
