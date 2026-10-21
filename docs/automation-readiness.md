# Automatización diaria: alcance real

Actualizado el 2026-10-21. El plan maestro privado v3 rige este diseño. Sólo Alec y este PC están activos; los datos profesionales permanecen fuera de Git.

| Etapa | Estado actual | Siguiente requisito |
| --- | --- | --- |
| Recolección AWS | **Activa**, 08:00 Ciudad de México. Cuatro boards públicos Greenhouse: Utility Profit, Factored, Cobre e Inflect; máximo cuatro fuentes configuradas. La corrida del 21 de octubre registró 42 anuncios y salud `COMPLETE` en las cuatro fuentes. | Observar calidad y costos durante varias corridas. Caylent continúa como revisión manual/alerta oficial por sus condiciones. |
| Publicación AWS | **Activa**, 08:30. Política privada de Alec, hasta diez vacantes por lote; primera corrida programada: `READY` con diez vacantes, una invocación y cero errores. | Vigilar gasto atribuido y continuidad. |
| Revisión Codex | Tarea local **AJI Alec — revisión diaria** activa a las 09:00. Su primera ejecución programada del comando integrado leyó el lote del 21 de octubre en `READY`: diez en `review`, cero shortlist, CVs y postulaciones. El titular confirmó visibilidad desde Quick Remote. | Observar continuidad con el PC encendido y los próximos lotes diarios. |
| Preparación de CV | Perfil privado de Alec aprobado con 36 afirmaciones rastreables a los dos PDF. `run-alec-daily.py` activa `--prepare` sólo tras lote y marcador válidos; conserva umbral, revalidación de vigencia y cuota persistente de tres paquetes por día. En la corrida programada del 21 de octubre produjo cero paquetes porque las diez vacantes siguen en revisión. | Acreditar condiciones por vacante y revisar el primer paquete real antes de postular. |
| Alertas Gmail | Piloto de lectura acotada en navegador completado en sesión anterior; el 21 de octubre las funciones del conector volvieron a rechazar llamadas en este chat y el navegador integrado pidió inicio de sesión. Ningún correo se leyó hoy. Sin lector AWS ni mensajes en Git. | Restablecer la sesión web de la misma cuenta de Alec o la disponibilidad del conector y comprobar lectura acotada en otra corrida. |
| Postulaciones | `AUTO_SUBMIT` apagado; no hay cliente de portal ni envíos reales. | Integración permitida, respuestas verificadas, autorización concreta por vacante y portal, recibo e idempotencia. |

`max_jobs_per_day=10` limita sólo las vacantes del lote. Los GET están acotados por cuatro fuentes, timeout, tamaño y reintentos. La cuota de preparación local ya persiste entre ejecuciones; la cuota de envíos queda pendiente porque no existe una integración de postulación habilitada. Ninguna alerta de presupuesto constituye un tope de gasto.

La política privada de Alec contiene filtros de ubicación, modalidad, condiciones y remuneración. Los diez anuncios oficiales del lote del 20 de octubre y sus campos Greenhouse `pay_input_ranges` no aportaron una cifra salarial. El conector ahora conserva rangos explícitos del empleador y su base bruta, neta, contractual o desconocida. Se halló una oferta oficial nueva de Inflect con USD 6,000–8,000/mes en B2B desde México; un escenario privado de impuestos permite priorizarla, pero no verifica el neto contractual ni las capacidades técnicas. La ausencia de información queda `unknown`/`review`; no se infiere que una condición se cumple. Los términos de ranking tecnológico y umbrales son elecciones operativas revisables, no nuevas preferencias del titular.

Las cuatro fuentes activas usan Greenhouse. Su [Job Board API](https://docs.greenhouse.io/job-board) permite GET públicos; el POST necesita una clave del empleador y preguntas propias del puesto. [Lever](https://github.com/lever/postings-api) y [Ashby](https://developers.ashbyhq.com/reference/applicationformsubmit) también exigen autenticación para el envío. La cuenta AWS del candidato y Gmail no conceden esas credenciales. Un portal podría permitir asistencia humana en navegador, sujeta a términos y a consentimiento concreto; no se prometen envíos universales.

## Trabajo pendiente para pasar de revisión a candidatura

1. Confirmar por vacante trabajo desde México, remoto, viajes, turnos y compensación **neta comparable**. Sólo entonces una vacante puede pasar de `review` a `shortlist` y superar el umbral de preparación.
2. La tarea diaria ejecuta el comando único probado, que valida el lote de la fecha y sólo entonces prepara. Su primera corrida programada del 21 de octubre produjo cero CVs porque las diez vacantes siguen en revisión. Revisar el primer paquete real cuando exista, antes de cualquier envío. La cuota de tres es un límite técnico conservador. El `--claim` permanente queda fuera de la tarea.
3. Resolver el acceso diario a Gmail de Alec y verificar la lectura acotada en la tarea programada. Mantener PII, CVs y correos fuera de Git, logs y CloudWatch.
4. Evaluar cada portal de envío, preguntas y consentimiento; probar sólo con fixtures o un entorno autorizado. No activar `AUTO_SUBMIT` ni enviar por un score o CV generado.

La [guía de uso del primer PC](runbooks/first-pc-user-guide.md) explica las horas, comandos y pausa. El [registro de avance](progress.md) conserva el piloto y bloqueos.
