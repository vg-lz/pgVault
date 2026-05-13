# FintechDB — Base de datos demo para PgVault

Base de datos de demostración para el proyecto **PgVault** (SIS2404).
Contiene una fintech mexicana ficticia con datos sintéticos y problemas
de seguridad / cumplimiento plantados intencionalmente para que tu
producto los detecte.

> ⚠️ **Advertencia importante**
> Esta BD contiene **prácticas de seguridad intencionalmente inseguras**
> con fines pedagógicos: contraseñas débiles, PAN/CVV almacenados, roles
> con privilegios excesivos, etc. **Nunca uses esta configuración en
> producción.** Todos los datos personales (RFCs, CURPs, números de
> tarjeta, CLABEs) son **sintéticos**: cumplen formato/regex pero no
> corresponden a personas reales.

---

## Cómo levantarla

```bash
docker compose up -d
```

La primera vez tarda **1-2 minutos** mientras se crea el schema y se siembran
los datos. Para ver el progreso:

```bash
docker compose logs -f db
```

Cuando veas el mensaje `FintechDB v1.0 ready with 22 planted problems`, está lista.

---

## Cómo conectarte

| Parámetro | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5433` (no 5432, para coexistir con TiendaDB) |
| Base de datos | `fintechdb` |
| Usuario | `fintech_user` |
| Contraseña | `fintech_pass` |

Desde la línea de comandos:

```bash
docker exec -it fintechdb psql -U fintech_user -d fintechdb
```

O desde un cliente externo (DBeaver, pgAdmin, psql local):

```bash
psql -h localhost -p 5433 -U fintech_user -d fintechdb
```

---

## Esquema

10 tablas que simulan una procesadora de pagos / fintech:

| Tabla | Descripción | Filas (modo base) |
|---|---|---|
| `customers` | Clientes finales con datos personales | 5,000 |
| `merchants` | Comercios afiliados | 200 |
| `internal_users` | Operadores y administradores | 25 |
| `accounts` | Cuentas bancarias asociadas | 3,000 |
| `cards` | Tarjetas registradas | 8,000 |
| `transactions` | Autorizaciones de pago | 100,000 |
| `payments` | Pagos liquidados | 80,000 |
| `kyc_documents` | Documentos KYC | 5,000 |
| `customer_notes` | Notas libres de soporte | 30,000 |
| `audit_log` | Bitácora de auditoría | 50,000 |

---

## Modo grande (opcional)

Si quieres probar tu producto contra un volumen más realista, puedes escalar
la BD a aproximadamente 3 GB y millones de filas:

```bash
docker exec -i fintechdb psql -U fintech_user -d fintechdb < scripts/scale_to_large.sql
```

Tarda 10-15 minutos. Los problemas plantados siguen activos después de escalar.

⚠️ Para tu cobertura del Demo Day, usa el **modo base** que es lo que el
profesor evaluará. El modo grande es para validar que tu producto escala
con BDs reales.

---

## ¿Qué problemas plantamos?

No te lo voy a decir. **Esa es la chamba de tu producto: detectarlos.**

Lo que sí te puedo decir:

- Hay **22 problemas plantados** distribuidos en los 3 módulos del producto:
  - **Configuración y postura de seguridad** (~10 problemas): roles, privilegios,
    funciones peligrosas, configuración del servidor, autenticación.
  - **Descubrimiento de datos sensibles** (~9 problemas): columnas con PII por
    nombre y por contenido, en distintos formatos (texto plano, JSONB, free text).
  - **Cumplimiento y auditoría** (~3 problemas): integridad de logs, retención,
    cobertura de auditoría sobre datos sensibles.
- Tu producto debe detectar al menos **15 de los 22** para sacar puntaje
  básico en el Criterio 2.1 de la rúbrica.
- Para sacar puntaje completo (12/12) debes detectar 20-22 (≥90%).
- Cada falso positivo te resta 0.5 puntos (tope -3).
- El día del Demo Day el profesor entregará una **versión 2** con problemas
  disfrazados y algunos nuevos. Si tu producto los detecta sin haberlos
  visto, ganas hasta +3 pts de bonus.

---

## Cómo evitar hardcodear

Tu producto NO debe asumir cosas como:

- "El usuario problemático se llama `admin`."
- "La columna que viola PCI es `cards.pan`."
- "La tabla con datos sensibles se llama `customers`."
- "La función vulnerable se llama `get_customer_full_data`."

Tu producto SÍ debe pensar de forma genérica:

- "Para cada función con `prosecdef = true` en `pg_proc`, verifico si
  `proconfig` incluye `search_path`. Si no, es vulnerable."
- "Para cada columna en `information_schema.columns`, comparo el nombre
  contra una lista regex de patrones sensibles (`pan`, `cvv`, `password`,
  `rfc`, `curp`, `email`, etc.)."
- "Para cada rol en `pg_roles`, verifico si tiene `rolsuper = true` y
  reporto los que sí."
- "Para cada tabla con datos sensibles detectados, verifico si tiene
  triggers que escriban en algún tipo de tabla de auditoría."

Esto te protegerá cuando llegue la BD demo v2 el día del Demo Day.

---

## Detección de PII por contenido

Algunos problemas (H17, H18, H19) requieren detectar PII oculta en texto
libre o JSONB con nombres de columna genéricos. Estrategia recomendada:

1. **Toma una muestra estadísticamente válida** (1,000 filas suelen
   ser suficientes para tablas con millones).
2. **Aplica regex contra cada valor** para los patrones que conozcas:
   - RFC: `^[A-Z]{4}[0-9]{6}[A-Z0-9]{3}$`
   - CURP: `^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9]{2}$`
   - PAN: `^[0-9]{13,19}$` (más validación Luhn opcional)
   - Email: regex estándar
   - CLABE: `^[0-9]{18}$`
3. **Si X% de la muestra coincide**, reporta la columna como sensible.
4. **Justifica el sampling matemáticamente** en tu defensa
   (nivel de confianza, tamaño de muestra).

Para JSONB, debes recursar en las claves del documento y aplicar el
mismo análisis sobre los valores escalares.

---

## Acceso a información de configuración

Tu producto necesita leer:

- `pg_roles` y `pg_authid` (para roles y privilegios)
- `pg_proc` (para funciones)
- `pg_extension` (para extensiones instaladas)
- `pg_hba_file_rules` (para reglas de autenticación efectivas en memoria)
- `pg_settings` (para configuración del servidor)
- `information_schema.*` (para schema y privilegios)

El usuario `fintech_user` tiene los permisos necesarios. Si quieres usar
un usuario más restringido (recomendado para una postura de "producto
read-only"), puedes crear uno con permisos mínimos:

```sql
CREATE ROLE pgvault_audit WITH LOGIN PASSWORD 'audit_pass';
GRANT pg_read_all_settings TO pgvault_audit;
GRANT pg_read_all_stats TO pgvault_audit;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pgvault_audit;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO pgvault_audit;
```

---

## Reset

Si necesitas reiniciar la BD desde cero:

```bash
docker compose down -v
docker compose up -d
```

⚠️ El comando `down -v` borra todos los datos. Vuelve a tardar 1-2 min en
sembrar.

---

## Problemas comunes

**Puerto 5433 ocupado:** otro Postgres está usando 5433. Edita el `docker-compose.yml`
o detén el otro servicio.

**FintechDB y TiendaDB al mismo tiempo:** ambos están configurados en
puertos distintos (5432 y 5433) precisamente para que puedas tener
ambos corriendo si trabajas en otro proyecto.

**Permisos del archivo `pg_hba.conf`:** si ves errores de permisos en
los logs, asegúrate de que el archivo `config/pg_hba.conf` sea legible.

---

## Una última cosa

Esta BD está diseñada para **enseñarte** sobre seguridad de bases de datos
en producción real. Cada problema plantado es uno que existe en empresas
reales y le ha costado dinero, multas o caída de bolsa a alguien.

Cuando tu producto los detecte y los explique bien, no solo estarás sacando
buena nota: estarás construyendo algo genuinamente vendible a fintechs
mexicanas que lidian con CNBV, LFPDPPP y PCI-DSS todos los días.

Mucha suerte.
