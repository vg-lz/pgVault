# Guión Línea por Línea — PgVault
> Duración total: 8 minutos | 5 integrantes | Demo Day
> El video demo (3-5 min) se presenta por separado, fuera del pitch
> 🎤 = quien habla | ⏱️ = tiempo aproximado

---

## Slide 1 — Gancho
⏱️ 0:00 - 0:45 | 🎤 Cesar

"Imaginen que hoy, a las 9 de la mañana, llega un correo de la CNBV."

"Tienen 48 horas para demostrar que su base de datos cumple con la LFPDPPP."

"¿Qué hacen?"

"La mayoría de los equipos de TI en México no tiene una respuesta clara."

"Preparar esa evidencia de forma manual toma días, a veces semanas, y puede costar hasta $30,000 dólares en consultoría."

"Nosotros lo resolvemos en minutos."

"Esto es PgVault."

---

## Slide 2 — El problema
⏱️ 0:45 - 1:40 | 🎤 Diego

"El problema tiene tres caras."

"Primera: las fintechs mexicanas no saben con certeza qué datos sensibles tienen almacenados ni dónde están."

"Segunda: cuando llega una auditoría, el proceso de recopilar evidencia es completamente manual y reactivo."

"Tercera: los privilegios de la base de datos rara vez se revisan hasta que ocurre un incidente."

"No lo decimos nosotros."

"Eduardo Pacheco, consultor DBA con años de experiencia, nos dijo textualmente:"

"'Desconozco qué datos sensibles hay. Solo se sabe cuando hay un requerimiento del área de seguridad.'"

"Eso es exactamente el problema que PgVault resuelve."

---

## Slide 3 — El mercado
⏱️ 1:40 - 2:30 | 🎤 Cesar

"¿Para quién es PgVault?"

"Para las más de 500 fintechs registradas ante la CNBV en México."

"Específicamente las de 20 a 200 empleados que usan PostgreSQL en producción."

"Estas empresas tienen tres obligaciones regulatorias simultáneas: LFPDPPP, CNBV y en muchos casos PCI-DSS."

"Y las herramientas que existen para esto cuestan entre 50,000 y 200,000 dólares al año."

"Ese segmento está completamente desatendido."

"Ahí está PgVault."

---

## Slide 4 — La solución
⏱️ 2:30 - 3:20 | 🎤 Diego

"PgVault se conecta a su base de datos PostgreSQL en modo solo lectura."

"Nunca escribe nada. Nunca modifica nada. Solo escucha."

"A partir de esa conexión, orquesta tres módulos en paralelo."

"El primero detecta datos sensibles en columnas y contenido real."

"El segundo audita la configuración de seguridad y privilegios."

"El tercero genera un reporte con score de seguridad y mapeo a regulación mexicana."

"Todo esto en minutos, no en semanas."

---

## Slide 5 — Cómo funciona por dentro
⏱️ 3:20 - 4:20

🎤 Daniela:

"Yo me encargo de encontrar lo que no debería estar expuesto."

"Detectamos CURP, RFC, correos, números de tarjeta, teléfonos y tokens."

"Lo hacemos de dos formas: por el nombre de la columna y por el contenido real con muestreo."

"Cada hallazgo tiene un score de confianza para evitar falsos positivos."

"Si hay un RFC en una columna llamada 'notas_cliente', PgVault lo encuentra."

🎤 Dowshell:

"Yo me encargo de que nadie tenga más acceso del que necesita."

"Revisamos privilegios excesivos, usuarios con SUPERUSER innecesario y funciones SECURITY DEFINER mal configuradas."

"Y no solo reportamos el problema — entregamos el SQL exacto para corregirlo."

"El cliente decide cuándo aplicarlo. Nosotros no tocamos nada."

---

## Slide 6 — Análisis competitivo
⏱️ 4:20 - 5:10 | 🎤 Dowshell

"Revisamos el mercado a fondo."

"Hay cuatro competidores relevantes: Satori, Cyral, Immuta y BigID."

"Satori cuesta en promedio 95,000 dólares al año."

"Immuta arranca en 5,000 dólares por usuario al mes."

"BigID puede llegar a 175,000 dólares anuales."

"Y Cyral — uno de los cuatro — fue adquirida por Varonis en marzo de 2025. Ya no existe como producto independiente."

"El mercado enterprise se consolida hacia arriba y deja desatendido al segmento SMB latinoamericano."

"Ninguno está disponible en español."

"Ninguno tiene mapeo a regulación mexicana."

"Ninguno está especializado en PostgreSQL."

"PgVault cubre exactamente ese hueco."

---

## Slide 7 — Mapeo regulatorio
⏱️ 5:10 - 5:50 | 🎤 Mariajose

"Cada hallazgo que genera PgVault está vinculado a un artículo regulatorio específico."

"LFPDPPP, Artículos 19 y 20: obligan a implementar medidas de seguridad técnicas y mantener evidencia de ellas."

"PgVault genera esa evidencia automáticamente."

"PCI-DSS, Requerimientos 3, 7 y 8: protección de datos de tarjetahabientes y control de acceso."

"PgVault detecta patrones de tarjeta y audita los privilegios que los requerimientos exigen revisar."

"CNBV, Artículo 71 de la LRITF y Anexo G: controles de acceso lógico para Instituciones de Tecnología Financiera."

"PgVault audita exactamente eso."

"Si el INAI o la CNBV les audita mañana, tienen el reporte listo en minutos."

---

## Slide 8 — Validación con usuarios
⏱️ 5:50 - 6:30 | 🎤 Daniela

"Antes de construir, hablamos con personas reales."

"Maybel Noguera, DBA Senior en una empresa de telecomunicaciones, administra alrededor de 300 bases de datos."

"Su proceso de auditoría es completamente reactivo y manual."

"Eduardo Pacheco, consultor DBA, nos confirmó que la visibilidad sobre datos sensibles depende de que alguien externo la solicite."

_[ Agregar línea de Entrevista 3 aquí ]_

"El patrón es consistente: el problema es real, está validado y no tiene solución accesible hoy."

"La principal objeción que encontramos no fue el precio — fue la confianza."

"Por eso PgVault es open source y su conexión read-only es verificable en el código."

---

## Slide 9 — Modelo de negocio
⏱️ 6:30 - 7:15 | 🎤 Cesar

"El mercado ya existe. Las obligaciones regulatorias ya existen. El problema ya existe."

"Nosotros entramos por el segmento que nadie atiende, con un precio que sí pueden pagar."

"Precio objetivo: entre 50 y 150 dólares al mes."

"Eso es menos de 1,800 dólares al año."

"Comparado con los 95,000 dólares anuales de Satori, somos entre 50 y 1,000 veces más baratos."

"¿Por qué podemos ofrecer ese precio? Porque somos open source, sin agente, sin infraestructura propia — el cliente lo corre en su servidor."

"Modelo de suscripción mensual o licencia anual con descuento."

"Canal: venta directa a fintechs y comunidad PostgreSQL en LATAM."

---

## Slide 10 — Equipo y cierre
⏱️ 7:15 - 8:00

🎤 Mariajose presenta al equipo:

"PgVault fue construido por cinco personas, cada una responsable de una pieza crítica del sistema."

"Diego Vega construyó la conexión read-only y la orquestación de todos los módulos."

"Dowshell Smith implementó los checks de privilegios, SUPERUSER y configuración insegura."

"Daniela Borquez diseñó el motor de detección con patrones de CURP, RFC, tarjetas y más."

"Mariajose Rito construyó el reporte PDF, el score de seguridad y el mapeo regulatorio."

"Y Cesar Mendez coordinó el producto, validó el mercado y estructuró esta presentación."

🎤 Cesar cierra:

"PgVault no cifra tus datos — te dice cuáles necesitan protección."

"No remedia automáticamente — te da el SQL exacto para que tú decidas."

"No reemplaza a un pen-tester — hace el 80% del trabajo repetible que hoy se hace a mano."

"En minutos, no en semanas. En menos de 1,800 dólares al año, no en 95,000."

"En español, con regulación mexicana, especializado en PostgreSQL."

"Eso es PgVault."

"Gracias."

---

## Notas de coordinación

- Ensayar completo al menos una vez con los 5 integrantes antes del Demo Day
- El video demo (3-5 min) se presenta por separado — coordinar con Diego quién lo presenta
- Completar Slide 8 con la línea de Entrevista 3 antes de la presentación