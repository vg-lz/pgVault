# Documento de Negocio — PgVault
> Auditoría de seguridad y cumplimiento para PostgreSQL
> Repositorio: https://github.com/vg-lz/pgVault

---

## 1. Resumen ejecutivo

Las fintechs mexicanas de 20 a 200 empleados operan bases de datos PostgreSQL con datos sensibles de sus clientes sin saber con certeza qué tienen, quién puede acceder a ellos ni si su configuración cumple con LFPDPPP, CNBV o PCI-DSS. Cuando llega una auditoría regulatoria, el equipo de TI pasa días recopilando evidencia de forma manual — un proceso costoso, incompleto y repetible.

PgVault es una herramienta de auditoría de seguridad y cumplimiento para PostgreSQL. Se conecta en modo solo lectura, detecta datos sensibles (CURP, RFC, tarjetas, emails), audita privilegios y configuración insegura, y genera un reporte con score de seguridad y mapeo a regulación mexicana — en minutos, no semanas.

El mercado objetivo son las más de 500 fintechs registradas ante la CNBV en México. Las herramientas comparables (Satori, Cyral, Immuta, BigID) cuestan entre $15,000 y $175,000 USD anuales y no tienen soporte para regulación mexicana. PgVault apunta a $50–150 USD/mes, especializándose en el segmento que nadie atiende.

El equipo está compuesto por 5 ingenieros con roles especializados en conexión, auditoría de configuración, detección de datos sensibles, reportes regulatorios y producto. El diferenciador central es el mapeo nativo a LFPDPPP y CNBV — algo que ningún competidor ofrece hoy.

---

## 2. Problema

### 2.1 Descripción del problema

Las fintechs mexicanas de 20 a 200 empleados manejan bases de datos PostgreSQL con datos personales y financieros de sus clientes. Están sujetas a LFPDPPP, disposiciones de CNBV y en muchos casos PCI-DSS. Sin embargo, sus equipos de TI — de 2 a 5 personas — no tienen visibilidad proactiva sobre tres preguntas críticas:

1. **¿Qué datos sensibles tenemos y dónde están?** La respuesta típica es "más o menos", dependiendo de que alguien haya documentado el esquema en algún momento.
2. **¿Quién puede acceder a qué?** Los privilegios de base de datos se configuran al inicio y rara vez se revisan. Con el tiempo, usuarios de aplicativos acumulan más acceso del necesario.
3. **¿Cumplimos con la regulación?** La evidencia de cumplimiento se recopila manualmente cuando llega una auditoría — un proceso que puede tomar días o semanas.

El resultado: equipos de TI reactivos, auditorías costosas en tiempo y dinero, y riesgo regulatorio permanente que solo se hace visible cuando ya es un problema.

### 2.2 User persona principal

| Atributo | Valor |
|---|---|
| **Nombre y rol** | Marcos Rodríguez, CISO / Responsable de TI |
| **Edad** | 35–42 años |
| **Experiencia** | 8–12 años en TI, 2–4 años en el rol actual |
| **Tamaño de empresa** | Fintech mexicana, 50–150 empleados |
| **Industria** | Tecnología financiera — pagos, crédito digital, ahorro |
| **Stack** | PostgreSQL en AWS RDS o servidor propio, backend Python o Node |
| **Equipo de TI** | 2–4 personas, sin DBA dedicado |
| **Día típico** | Apaga fuegos, revisa incidentes, coordina con área de cumplimiento antes de auditorías |
| **Problemas principales** | No sabe qué datos sensibles tiene en producción; recibe auditorías de CNBV y tarda días preparando evidencia; sospecha que hay usuarios con más privilegios de los necesarios |
| **Cómo resuelve hoy** | Scripts manuales, revisión periódica a ojo, plugin nativo de auditoría de la BD |
| **Costo del problema** | 3–5 días de trabajo manual por auditoría, riesgo de multa INAI si hay brecha |

> *"Desconozco qué datos sensibles hay. Solo se sabe cuando hay un requerimiento del área de seguridad."* — Eduardo Pacheco, Consultor DBA (entrevistado)

### 2.3 Frecuencia y severidad

**Frecuencia:** Las auditorías de CNBV ocurren 1–2 veces al año. Las revisiones internas de cumplimiento deberían ser mensuales pero en la práctica son reactivas. Los privilegios de BD nunca se revisan sistemáticamente.

**Severidad:** Una brecha de datos personales bajo LFPDPPP puede resultar en multas de hasta 320,000 días de salario mínimo (~$17M MXN). Una auditoría de CNBV fallida puede derivar en sanciones operativas. El costo de preparar evidencia manualmente se estima en 3–5 días-hombre por evento, a un costo de $500–2,000 USD por auditoría en tiempo del equipo.

**Costo estimado sin PgVault:** $1,500–6,000 USD/año en tiempo de auditoría manual, sin contar el riesgo de multas regulatorias.

---

## 3. Investigación de usuarios

### 3.1 Resumen de entrevistas

| Nombre / Rol | Empresa / Sector | Duración |
|---|---|---|
| Maybel Noguera — DBA Senior | Telecomunicaciones | ~15 min |
| Eduardo Pacheco — Consultor DBA | Consultoría de BD | ~15 min |
| _[ Entrevistado 3 — por completar ]_ | | |

### 3.2 Preguntas hechas

1. ¿Cuál es tu rol actual y en qué tipo de empresa trabajas?
2. ¿Tienen bases de datos PostgreSQL en producción? ¿Cuántas, más o menos?
3. ¿Saben qué datos sensibles tienen almacenados en su base de datos? ¿Cómo lo saben?
4. ¿Han tenido alguna auditoría de seguridad o cumplimiento? ¿Qué proceso siguieron para prepararla?
5. ¿Tienen control sobre quién puede acceder a qué tablas o columnas en la base de datos?
6. Si tuvieran que demostrar hoy que su base de datos cumple con LFPDPPP o PCI-DSS, ¿cuánto tiempo les tomaría?
7. ¿Qué herramientas usan hoy para monitorear o auditar su base de datos?
8. ¿Qué tan fácil es saber si alguien tiene más privilegios de los que debería en la base de datos?
9. Si existiera una herramienta que se conecta en modo solo lectura a su PostgreSQL, detecta datos sensibles, revisa privilegios y genera un reporte con mapeo a regulación mexicana en minutos — ¿la usarían? ¿Qué les generaría desconfianza?
10. ¿Qué precio les parecería razonable por algo así? ¿Lo preferirían como suscripción mensual o pago único?

### 3.3 Aprendizajes principales

**Aprendizaje 1 — La visibilidad es reactiva, no proactiva.**
Ambos entrevistados solo saben qué datos sensibles tienen cuando alguien externo lo solicita (auditoría, requerimiento de seguridad). No existe revisión sistemática y proactiva.

**Aprendizaje 2 — El proceso de auditoría es completamente manual.**
Maybel Noguera describió el proceso como "nos piden evidencias y nosotros recopilamos la información y se la enviamos" — sin herramienta de apoyo, dependiendo del conocimiento individual del equipo.

**Aprendizaje 3 — La desconfianza inicial es la principal barrera de adopción.**
Eduardo Pacheco señaló que la decisión de adoptar una herramienta nueva involucra múltiples áreas (DBA, seguridad, comercial). Maybel indicó que "de primera instancia no la usaría hasta validar". Esto refuerza la necesidad de un modelo open source y verificable.

**Aprendizaje 4 — El precio no es la objeción principal.**
Ningún entrevistado mencionó el precio como barrera. La confianza y la capacidad de validar lo que hace la herramienta son más importantes.

**Aprendizaje 5 — Hay preferencia por pago único o descuento en anual.**
Maybel señaló que preferiría pago único a menor costo que mensualidad acumulada — consistente con el comportamiento de compra de equipos de TI en empresas medianas mexicanas.

---

## 4. Solución

Carlos llega un lunes por la mañana con un correo de la CNBV: tienen 48 horas para demostrar cumplimiento. Sin PgVault, llama a su equipo, pasan el día revisando logs manualmente y preparando un Excel con usuarios y permisos. Con PgVault, ejecuta un análisis en 10 minutos y obtiene un reporte PDF con score de seguridad, hallazgos priorizados y mapeo exacto a los artículos de LFPDPPP y CNBV que debe cumplir. Envía el reporte esa misma tarde.

PgVault se instala con Docker Compose, se conecta con credenciales de solo lectura y no requiere ningún agente en el servidor de producción. El cliente nunca pierde control de sus datos.

### 4.1 Funcionalidades core

| Feature | Beneficio para el usuario |
|---|---|
| Detección de datos sensibles por nombre de columna | Sabe inmediatamente qué columnas contienen CURP, RFC, emails, tarjetas o teléfonos |
| Detección por contenido con muestreo estadístico | Encuentra datos sensibles aunque la columna tenga un nombre genérico |
| Score de confianza por hallazgo | Diferencia hallazgos certeros de posibles falsos positivos |
| Auditoría de privilegios y roles | Identifica usuarios con SUPERUSER innecesario y accesos excesivos |
| Detección de funciones SECURITY DEFINER | Encuentra configuraciones inseguras que elevan privilegios automáticamente |
| Reporte PDF con score de seguridad | Entrega evidencia lista para presentar en auditorías |
| Mapeo a LFPDPPP, PCI-DSS y CNBV | Vincula cada hallazgo al artículo regulatorio específico que incumple |
| Recomendaciones con SQL exacto | El equipo sabe exactamente cómo corregir cada hallazgo |

---

## 5. Análisis competitivo

> Fuentes: Vendr, SelectHub, AIM Multiple, PeerSpot, GlobeNewswire — verificado mayo 2026.

### 5.1 Tabla comparativa

| Característica | Satori | Cyral *(adq. Varonis 2025)* | Immuta | BigID | **PgVault** |
|---|---|---|---|---|---|
| Precio anual | ~$95,000 USD | N/A — absorbida | >$60,000 USD | $15,000–$175,000 USD | **~$600–1,800 USD** |
| Self-hosted / on-premise | No | No | Parcial | No | **Sí** |
| Sin agente | No | Sí | No | No | **Sí** |
| Soporte en español | No | No | No | No | **Sí** |
| Regulación mexicana (LFPDPPP/CNBV) | No | No | No | No | **Sí** |
| Especializado en PostgreSQL | No | No | No | No | **Sí** |
| Segmento objetivo | Enterprise | Enterprise | Enterprise | Enterprise | **SMB LATAM** |
| Disponible en LATAM | No | No | No | No | **Sí** |
| Modo solo lectura verificable | No | No | No | No | **Sí** |

### 5.2 Análisis honesto

**Satori:**
- Mejor que nosotros en: cobertura multi-base de datos, integraciones enterprise, soporte 24/7
- Nosotros mejores en: precio (50x menor), regulación mexicana, especialización en PostgreSQL, on-premise

**Cyral (ahora Varonis):**
- Mejor que nosotros en: integración con ecosistema Varonis, monitoreo de actividad en tiempo real
- Nosotros mejores en: precio, independencia de plataforma, regulación local, foco en PostgreSQL

**Immuta:**
- Mejor que nosotros en: governance de datos a escala enterprise, políticas de acceso dinámicas
- Nosotros mejores en: precio (33x menor), simplicidad de instalación, regulación mexicana

**BigID:**
- Mejor que nosotros en: discovery en múltiples fuentes de datos, clasificación avanzada con ML
- Nosotros mejores en: precio (hasta 100x menor), especialización, on-premise, regulación local

### 5.3 Espacio en blanco

**Nuestro nicho:** Fintechs y SaaS B2B mexicanas de 20–200 empleados con PostgreSQL en producción y obligaciones regulatorias LFPDPPP/CNBV.

**Los competidores no atienden bien este nicho porque:** Sus precios son inaccesibles para equipos de menos de 200 personas, no tienen mapeo a regulación mexicana, no tienen soporte en español y requieren implementaciones complejas que superan la capacidad de equipos de TI pequeños.

**Nosotros podemos servirlo bien porque:** Somos open source, sin agente, con instalación en un comando Docker, precio accesible, reporte en español y mapeo nativo a LFPDPPP y CNBV.

---

## 6. Modelo de negocio

### 6.1 Tipo de modelo de revenue

- [x] Suscripción mensual / anual

### 6.2 Tiers de pricing

| Tier | Precio | Comprador objetivo | Qué incluye |
|---|---|---|---|
| **Starter** | $49 USD/mes | Fintech de 20–50 empleados, 1 BD | 1 BD PostgreSQL, todos los checks, reporte PDF, mapeo LFPDPPP |
| **Pro** | $99 USD/mes | Fintech de 50–150 empleados, hasta 5 BDs | Hasta 5 BDs, histórico de reportes, comparación entre escaneos |
| **Team** | $149 USD/mes | Empresa de 150–200 empleados, hasta 15 BDs | Hasta 15 BDs, exportación para auditorías CNBV, soporte por correo |
| **Anual** | 20% de descuento | Cualquier tier | Pago único anual con descuento — preferido por equipos de TI mexicanos según entrevistas |

### 6.3 Justificación del precio

El tier Starter de $49/mes representa menos del 1% del costo de una auditoría manual anual ($1,500–6,000 USD). Frente a Satori (~$7,900 USD/mes), PgVault es 160 veces más barato en el tier de entrada.

Podemos ofrecer este precio porque somos open source, sin infraestructura propia de datos del cliente, sin equipo de ventas enterprise y sin soporte global 24/7. El cliente corre PgVault en su servidor — nuestro costo marginal por cliente nuevo es cercano a cero.

---

## 7. Tamaño de mercado

### 7.1 TAM — Total Addressable Market

**Definición:** Todas las empresas en LATAM que usan PostgreSQL y están sujetas a regulación de datos.

**Cálculo:** El mercado global de database security vale **$14.82B USD en 2025** y crece a una tasa de 19.4% anual (Research and Markets, 2025 — https://www.researchandmarkets.com/reports/6226436/database-security-market-report). El mercado de ciberseguridad en LATAM generó $14,368 millones USD en 2025 con un CAGR de 12.4% hasta 2033 (Grand View Research — https://www.grandviewresearch.com/horizon/outlook/cyber-security-market/latin-america). Database security representa aproximadamente el 8% del gasto total en ciberseguridad.

**TAM estimado:** ~$1,149M USD en LATAM (8% de $14,368M).

### 7.2 SAM — Serviceable Addressable Market

**Definición:** Fintechs y SaaS B2B en México con PostgreSQL en producción y obligaciones regulatorias LFPDPPP/CNBV.

**Cálculo:**
- México tiene más de 1,000 fintechs en operación, concentrando el 20% del ecosistema fintech de LATAM (Fintech Radar México 2025, Finnovista — https://dock.tech/es/fluid/blog/financiero/fintechs-en-mexico/)
- De las 515 fintechs mapeadas por la CNBV, ~200 deben cumplir obligatoriamente con la Ley Fintech (Banco Santander / CNBV — https://www.santander.com/es/sala-de-comunicacion/insights/el-horizonte-de-las-fintech-en-mexico)
- Estimamos que ~60% de estas usa PostgreSQL como BD principal = ~120 empresas en el segmento core
- Ticket promedio objetivo: $1,200 USD/año

**SAM estimado:** ~$144,000 USD anuales en México (segmento core). Expandible a Colombia, Chile y Argentina con regulaciones similares (~4x): **~$576,000 USD**.

### 7.3 SOM — Serviceable Obtainable Market

**Definición:** Lo que PgVault puede capturar realistamente en 3–5 años.

**Supuestos de penetración:** 10% del SAM en México en año 3 (mercado temprano, herramienta especializada), expandiendo a LATAM en año 4–5.

**Cálculo:** 120 empresas × 10% = 12 clientes × $1,200 USD = **$14,400 USD ARR en año 3**. Con expansión LATAM al 5% del SAM expandido: **~$28,800 USD ARR en año 5**.

### 7.4 Tendencias relevantes

**Tendencia 1 — Crecimiento de PostgreSQL en LATAM:** PostgreSQL es el motor de BD de mayor crecimiento en startups latinoamericanas. Su adopción en fintechs creció 40% entre 2022 y 2024 (DB-Engines ranking).

**Tendencia 2 — Endurecimiento regulatorio en México:** La CNBV aumentó el número de disposiciones de seguridad de la información para ITFs en 2023. El INAI incrementó sus multas a empresas que no acreditan medidas técnicas de protección.

**Tendencia 3 — Consolidación del mercado enterprise:** La adquisición de Cyral por Varonis en marzo 2025 confirma que el mercado enterprise se consolida hacia plataformas grandes, dejando el segmento SMB sin opciones especializadas accesibles.

---

## 8. Go-to-market

### 8.1 Primeros 10 clientes

**Objetivo:** 10 clientes pagados en los primeros 6 meses post-lanzamiento.

**Plan paso a paso:**

1. **Mes 1 — Red de contactos directa:** Contactar a las personas entrevistadas durante el desarrollo y ofrecerles 3 meses gratuitos a cambio de testimonial y retroalimentación. Meta: 2–3 pilotos.

2. **Mes 2 — Comunidad PostgreSQL LATAM:** Publicar un artículo técnico en Medium/Dev.to: *"Cómo auditar tu PostgreSQL para cumplir con LFPDPPP en 10 minutos"*. Compartir en grupos de Slack y Telegram de DBAs mexicanos. Meta: 50 instalaciones de prueba.

3. **Mes 3 — Fintech Mexico 2026:** Asistir al evento con 250+ fintechs presentes. Agendar 20 demos en el evento. Meta: 5 pilotos adicionales.

4. **Mes 4–6 — Conversión de pilotos:** Seguimiento a los pilotos gratuitos. Ofrecer migración a tier pagado con 20% de descuento. Meta: convertir 5 de 8 pilotos a clientes pagados.

**Timeline:** 10 clientes pagados en 6 meses.
**Costo estimado:** $3,500 USD (evento + viáticos + contenido).

### 8.2 Estrategia de growth (después de los 10)

**Canal 1 — Contenido técnico SEO:** Artículos sobre LFPDPPP + PostgreSQL posicionan PgVault en búsquedas orgánicas de equipos de TI buscando cumplimiento regulatorio.

**Canal 2 — Partnerships con consultoras:** Acuerdos con consultoras de cumplimiento regulatorio en México que recomienden PgVault a sus clientes como herramienta de evidencia.

**Canal 3 — Expansión LATAM:** Replicar el modelo en Colombia (SFC), Chile (CMF) y Argentina (BCRA) — regulaciones financieras similares con el mismo stack tecnológico.

---

## 9. Diferenciador defendible

**Nuestro diferenciador es:** Mapeo nativo a regulación mexicana (LFPDPPP y CNBV) con artículos específicos por hallazgo, en español, para PostgreSQL, a precio SMB.

**Es defendible en el tiempo porque:** La regulación mexicana es un conocimiento especializado que requiere inversión en investigación legal y actualización continua. Un competidor enterprise que quisiera entrar a este nicho tendría que localizar su producto, traducir su documentación, entrenar a su equipo de ventas en el mercado mexicano y bajar radicalmente su precio — todo esto para un segmento que consideran pequeño. No es rentable para ellos.

**Ejemplos concretos de cómo se manifiesta:**
- El reporte PDF cita el artículo exacto de LFPDPPP que cada hallazgo incumple
- Las recomendaciones están redactadas en el contexto de la regulación mexicana, no adaptadas de GDPR
- El soporte y la documentación están en español desde el día 1

---

## 10. Por qué nuestro equipo

Somos 5 ingenieros especializados, cada uno responsable de una capa crítica del sistema. Nuestra ventaja no es solo técnica — es la combinación de profundidad en PostgreSQL, entendimiento del contexto regulatorio mexicano y capacidad de ejecutar un MVP completo en 3 semanas.

Diego Vega construyó la capa de conexión y orquestación. Dowshell Smith implementó los checks de auditoría de configuración. Daniela Borquez diseñó el motor de detección de datos sensibles. Mariajose Rito construyó el sistema de reportes y el mapeo regulatorio. Cesar Mendez coordinó el producto, validó el mercado con entrevistas reales y estructuró la estrategia de negocio.

Entendemos el problema porque lo investigamos con personas reales antes de escribir una línea de código.

---

## 11. Roadmap a 12 meses

| Trimestre | Producto | Negocio | Operativo |
|---|---|---|---|
| **Q3 2026** | Soporte MySQL/MariaDB, alertas programadas, dashboard web | 10 clientes pagados, 3 testimoniales publicados | Documentación completa en español |
| **Q4 2026** | Integración con Slack/Teams para alertas, API pública | Expansion a Colombia y Chile, partnerships con 2 consultoras | Primer ingreso recurrente >$5,000 USD/mes |
| **Q1 2027** | Motor de remediación asistida (aplica SQL con aprobación), soporte multi-BD en un reporte | 50 clientes activos en LATAM | Equipo de 2 personas de soporte |
| **Q2 2027** | Módulo de cumplimiento continuo (escaneo automático semanal), integración CI/CD | Lanzamiento en Argentina, $15,000 USD ARR | Evaluación de ronda pre-seed |

---

## 12. Ask

Si esto fuera un pitch real de inversión, pediríamos:

- **$50,000 USD en pre-seed** para cubrir 12 meses de operación, asistencia a 3 eventos de fintechs en LATAM y desarrollo de los features Q3 2026.
- **3 mentores con red en fintechs mexicanas** que puedan abrir puertas a los primeros 10 clientes pagados.
- **2 fintechs piloto** dispuestas a usar PgVault en producción a cambio de influir en el roadmap durante los primeros 90 días.

---

## Mapeo regulatorio

### LFPDPPP

| Artículo | Obligación | Cómo PgVault ayuda |
|---|---|---|
| Art. 19 | Implementar medidas de seguridad técnicas | Identifica configuraciones inseguras y privilegios excesivos |
| Art. 20 | Mantener medidas de seguridad documentadas | Genera evidencia auditable del estado de seguridad |
| Art. 25 | Proteger datos contra tratamiento no autorizado | Detecta columnas con datos sensibles sin protección adecuada |

### PCI-DSS v4.0

| Requerimiento | Descripción | Cómo PgVault ayuda |
|---|---|---|
| Req. 3 | Proteger datos de tarjetahabientes almacenados | Detecta patrones de tarjetas en columnas y contenido |
| Req. 7 | Restringir acceso a componentes del sistema | Audita roles y privilegios excesivos |
| Req. 8 | Identificar y autenticar acceso | Revisa usuarios con SUPERUSER y permisos innecesarios |

### CNBV

| Disposición | Obligación | Cómo PgVault ayuda |
|---|---|---|
| Art. 71 LRITF | Medidas de seguridad de la información | Reporte ejecutivo con hallazgos priorizados |
| Anexo G | Controles de acceso lógico | Auditoría de privilegios y roles en PostgreSQL |

---

## Lo que PgVault NO hace (y por qué)

**No cifra los datos:**
PgVault identifica qué columnas necesitan cifrado y recomienda implementarlo con pgcrypto o TDE. El cifrado es una decisión del cliente — una herramienta de auditoría no debe modificar datos de producción.

**No remedia automáticamente:**
Entregamos el SQL exacto para corregir cada hallazgo, pero la ejecución es manual. Ningún equipo de seguridad serio permite que una herramienta externa ejecute cambios automáticos en su BD de producción.

**No reemplaza a un pen-tester humano:**
PgVault cubre el 80% del trabajo repetible y documentable de una auditoría: configuración, privilegios, datos sensibles y cumplimiento regulatorio. Las amenazas avanzadas y la lógica de negocio requieren criterio humano. Son herramientas complementarias, no competidoras.

**No soporta otras bases de datos en v1:**
PgVault está especializado en PostgreSQL. MySQL, MariaDB y Oracle están en el roadmap v2. La especialización nos permite mayor profundidad de checks que herramientas generalistas.
