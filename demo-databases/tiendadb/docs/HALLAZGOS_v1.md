# TiendaDB v1.0 — Lista Maestra de Hallazgos

⚠️ **DOCUMENTO CONFIDENCIAL — SOLO PROFESOR** ⚠️

No compartir con alumnos. Este documento es la verdad de fondo para
evaluar el Criterio 2.1 (Cobertura) del proyecto PgGuardian.

---

## Resumen ejecutivo

- **Total de problemas plantados: 18**
- Distribución: 5 índices, 3 bloat/mantenimiento, 4 queries, 4 config, 2 salud general
- Para 12/12 pts en cobertura: detectar 17 o 18 (≥90%)
- Para 10/12 pts: detectar 14-16 (75-89%)
- Para 8/12 pts: detectar 11-13 (60-74%)

---

## Categoría 1: Índices (5 problemas)

### H01 — orders.customer_id sin índice
- **Tipo:** Foreign key sin índice de soporte
- **Detección esperada:** consultar `pg_constraint` para FKs y verificar si existe índice sobre la columna referenciada en la tabla origen
- **Evidencia:** `EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1;` muestra Seq Scan
- **Recomendación esperada:** `CREATE INDEX idx_orders_customer_id ON orders(customer_id);`
- **Severidad:** ALTA (afecta JOINs y queries de cliente)

### H02 — Índice duplicado en products.category_id
- **Tipo:** Dos índices con la misma definición efectiva
- **Detección esperada:** agrupar índices por `(table, columns, where_clause)` en `pg_index` y reportar grupos con más de 1 entrada
- **Evidencia:** existen `idx_products_category_id` e `idx_products_category_dup` ambos sobre `(category_id)`
- **Recomendación esperada:** eliminar uno de los dos
- **Severidad:** MEDIA (consume espacio y ralentiza writes)

### H03 — Índice no usado en customers.birth_date
- **Tipo:** Índice con `idx_scan = 0` o muy bajo
- **Detección esperada:** consultar `pg_stat_user_indexes` y reportar índices con `idx_scan = 0` cuya tabla sí ha tenido actividad
- **Evidencia:** `idx_customers_birth_date_unused` existe pero nunca se ha usado
- **Recomendación esperada:** eliminar el índice si confirmamos que no hay queries pendientes que lo necesiten
- **Severidad:** MEDIA

### H04 — Falta índice parcial en orders WHERE status = 'pending'
- **Tipo:** Oportunidad de índice parcial (partial index)
- **Detección esperada:** identificar columnas con distribución muy sesgada (ej. 95% mismo valor) y queries frecuentes que filtran por valor minoritario
- **Evidencia:** ~95% de orders están en `status='pending'`, queries de \"pedidos activos\" filtran por status
- **Recomendación esperada:** `CREATE INDEX idx_orders_pending ON orders(customer_id) WHERE status = 'pending';` o equivalente
- **Severidad:** MEDIA

### H05 — Falta índice cubriente para reporte frecuente
- **Tipo:** Oportunidad de índice covering / INCLUDE
- **Detección esperada:** analizar queries top en `pg_stat_statements` y detectar patrones donde un índice cubriente daría index-only scan
- **Evidencia:** la query `SELECT id, total, order_date FROM orders WHERE customer_id = ?` (H09) se beneficiaría de un índice con INCLUDE
- **Recomendación esperada:** `CREATE INDEX ON orders(customer_id) INCLUDE (total, order_date);`
- **Severidad:** BAJA-MEDIA (es optimización, no problema crítico)

---

## Categoría 2: Bloat y mantenimiento (3 problemas)

### H06 — event_log con bloat severo (~30-40%)
- **Tipo:** Tabla con alto porcentaje de espacio muerto
- **Detección esperada:** usar `pgstattuple` o estimación vía `pg_stat_user_tables` (`n_dead_tup` / `n_live_tup`)
- **Evidencia:** después del DELETE masivo del seed, hay miles de tuples muertos sin VACUUM
- **Recomendación esperada:** ejecutar `VACUUM (FULL, ANALYZE) event_log;` o `VACUUM ANALYZE` si bloat es moderado
- **Severidad:** ALTA

### H07 — autovacuum desactivado en inventory
- **Tipo:** Configuración a nivel tabla peligrosa
- **Detección esperada:** consultar `pg_class.reloptions` y reportar tablas con `autovacuum_enabled=false`
- **Evidencia:** `SELECT reloptions FROM pg_class WHERE relname = 'inventory';` devuelve `{autovacuum_enabled=false}`
- **Recomendación esperada:** `ALTER TABLE inventory RESET (autovacuum_enabled);` (deja el default que es true)
- **Severidad:** ALTA

### H08 — reviews con muchos tuples muertos (~30-40%)
- **Tipo:** Similar a H06 pero distinto mecanismo (UPDATE masivo, no DELETE)
- **Detección esperada:** misma técnica que H06 — ratio dead/live tuples
- **Evidencia:** después de los UPDATEs masivos en seed con autovacuum off
- **Recomendación esperada:** `VACUUM ANALYZE reviews;` y reactivar autovacuum
- **Severidad:** ALTA

---

## Categoría 3: Queries problemáticas (4 problemas)

### H09 — Query con seq scan en orders
- **Tipo:** Query top en `pg_stat_statements` haciendo Seq Scan donde debería usar índice
- **Detección esperada:** las queries de `pg_stat_statements` se ejecutan con `EXPLAIN`, se detecta `Seq Scan` sobre tabla grande, se compara con índices disponibles
- **Evidencia:** `SELECT count(*) FROM orders WHERE customer_id = $1;` aparece como query frecuente con Seq Scan (consecuencia de H01)
- **Recomendación esperada:** crear el índice de H01
- **Severidad:** ALTA
- **Nota:** detectar esta query NO equivale a detectar H01. Son hallazgos distintos: H01 es la falta del índice, H09 es la query problemática que se beneficia de él. Aceptar ambos.

### H10 — Mismatch estimated vs actual rows en products
- **Tipo:** Estadísticas obsoletas (planner con info desactualizada)
- **Detección esperada:** ejecutar `EXPLAIN ANALYZE` sobre queries en `pg_stat_statements` y comparar `rows estimated` vs `rows actual`. Diferencia >5x es anomalía
- **Evidencia:** se insertaron 5000 productos sin ANALYZE; la tabla `products` tiene stats que dicen ~1000 filas pero hay ~6000
- **Recomendación esperada:** `ANALYZE products;` y considerar más frecuencia de auto-analyze
- **Severidad:** ALTA

### H11 — Query con sort en disco
- **Tipo:** `work_mem` insuficiente causa que sorts escriban a disco
- **Detección esperada:** `EXPLAIN (ANALYZE, BUFFERS)` muestra `Sort Method: external merge Disk`, o `pg_stat_statements.temp_blks_written > 0`
- **Evidencia:** la query de H11 (top productos por venta) genera spill a disco
- **Recomendación esperada:** aumentar `work_mem` a nivel sesión/usuario para queries de reporte, o reescribir la query
- **Severidad:** MEDIA-ALTA
- **Nota:** está relacionado con H14 pero es hallazgo distinto. H14 es la config global, H11 es la query específica afectada.

### H12 — Query con LIKE '%text%' (anti-pattern)
- **Tipo:** Wildcard al inicio impide uso de índice
- **Detección esperada:** parsear queries de `pg_stat_statements` y detectar patrones `LIKE '%...'`
- **Evidencia:** `SELECT count(*) FROM products WHERE description LIKE '%premium%';`
- **Recomendación esperada:** usar full-text search (`tsvector` + GIN), o `pg_trgm` con índice GIN, o cambiar la lógica de búsqueda
- **Severidad:** MEDIA

---

## Categoría 4: Configuración (4 problemas)

### H13 — shared_buffers muy bajo (128MB)
- **Tipo:** Misconfig de memoria para el dataset
- **Detección esperada:** `SHOW shared_buffers` y comparar contra tamaño total de datos en disco
- **Evidencia:** `shared_buffers = 128MB` en `postgresql.conf`
- **Recomendación esperada:** elevar a 25% de RAM disponible (en producción real)
- **Severidad:** MEDIA

### H14 — work_mem muy bajo (4MB)
- **Tipo:** Misconfig que causa H11
- **Detección esperada:** `SHOW work_mem` y observar `temp_blks_written` en `pg_stat_statements` o spills en planes
- **Evidencia:** `work_mem = 4MB` cuando los queries de reporte requieren más
- **Recomendación esperada:** elevar a 32-64MB para queries OLTP, considerar valores distintos por rol/sesión
- **Severidad:** MEDIA

### H15 — pg_stat_statements.max muy bajo (100)
- **Tipo:** Tracking insuficiente
- **Detección esperada:** `SHOW pg_stat_statements.max` y comparar con cantidad real de queries únicas
- **Evidencia:** `pg_stat_statements.max = 100` cuando hay cientos de queries únicas
- **Recomendación esperada:** elevar a 5000 o 10000
- **Severidad:** BAJA-MEDIA

### H16 — log_min_duration_statement = -1
- **Tipo:** Slow query logging desactivado
- **Detección esperada:** `SHOW log_min_duration_statement`. Si es -1, no se loguean queries lentas
- **Evidencia:** `log_min_duration_statement = -1` en `postgresql.conf`
- **Recomendación esperada:** establecer en 1000ms (1 segundo) como inicio razonable
- **Severidad:** MEDIA

---

## Categoría 5: Salud general (2 problemas)

### H17 — Conexión idle in transaction de larga duración
- **Tipo:** TX abierta sin commit/rollback bloqueando recursos
- **Detección esperada:** `SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction' AND state_change < NOW() - INTERVAL '30 minutes';`
- **Evidencia:** el contenedor `tiendadb_idle_tx` mantiene una TX abierta vía `pg_sleep(86400)`
- **Recomendación esperada:** identificar al cliente, terminarlo con `pg_terminate_backend()` o `idle_in_transaction_session_timeout`
- **Severidad:** ALTA

### H18 — event_log sin política de retención
- **Tipo:** Tabla creciendo sin control y con datos antiguos
- **Detección esperada:** detectar tablas grandes con `MIN(created_at)` muy antiguo y sin partitioning
- **Evidencia:** hay registros de hace 2+ años en `event_log`
- **Recomendación esperada:** implementar retención (DELETE periódico, particionamiento por fecha, archivado)
- **Severidad:** MEDIA

---

## Cómo verificar manualmente

Antes del Demo Day, ejecuta estas queries para confirmar que los problemas están plantados:

```sql
-- H01 verificación
SELECT count(*) FROM pg_indexes
WHERE tablename = 'orders' AND indexdef LIKE '%customer_id%';
-- Debería retornar 0

-- H02 verificación
SELECT count(*) FROM pg_indexes
WHERE tablename = 'products' AND indexdef LIKE '%(category_id)%';
-- Debería retornar 2

-- H06, H08 verificación bloat
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE relname IN ('event_log', 'reviews')
ORDER BY dead_pct DESC;
-- Ambas deberían tener > 20% dead

-- H07 verificación
SELECT relname, reloptions FROM pg_class
WHERE relname = 'inventory';
-- Debería tener autovacuum_enabled=false

-- H09-H12 verificación
SELECT query, calls, total_exec_time
FROM pg_stat_statements
WHERE query NOT LIKE 'BEGIN%' AND query NOT LIKE 'COMMIT%'
ORDER BY total_exec_time DESC
LIMIT 20;
-- Deberían aparecer las queries plantadas

-- H13-H16 verificación
SHOW shared_buffers;       -- 128MB
SHOW work_mem;             -- 4MB
SHOW pg_stat_statements.max;  -- 100
SHOW log_min_duration_statement;  -- -1

-- H17 verificación
SELECT state, count(*), MAX(NOW() - state_change) AS oldest
FROM pg_stat_activity
WHERE state = 'idle in transaction'
GROUP BY state;
-- Debería haber al menos 1

-- H18 verificación
SELECT MIN(created_at) FROM event_log;
-- Debería ser de hace ~2 años
```

---

## Ajustes finos durante el semestre

Si en práctica los alumnos se quejan de que algún problema es muy difícil
de detectar o muy fácil, ajustar aquí:

- **Fáciles (debería detectar todos):** H01, H02, H03, H07, H13, H14, H16
- **Medios:** H04, H05, H06, H08, H09, H10, H11, H12, H15, H18
- **Difíciles (separan al excelente):** H17 (requiere pg_stat_activity en vivo)

Si la mayoría detecta menos del 50%, considerar bajar el umbral del Criterio 2.1.
Si la mayoría detecta más del 90% sin esfuerzo, considerar plantar problemas
más sutiles en futuros semestres.
