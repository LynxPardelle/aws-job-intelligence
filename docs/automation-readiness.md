# Automatización diaria: alcance real

Actualizado el 2026-10-20. El plan maestro privado v3 rige este diseño. Sólo Alec y este PC están activos; los datos profesionales permanecen fuera de Git.

| Etapa | Estado actual | Siguiente requisito |
| --- | --- | --- |
| Recolección AWS | **Activa**, 08:00 Ciudad de México. Cuatro boards públicos Greenhouse: Utility Profit, Factored, Cobre e Inflect; máximo cuatro fuentes configuradas. La fuente nueva se desplegó el 20 de octubre y espera su primera corrida programada. | Observar calidad y costos durante varias corridas. Caylent continúa como revisión manual/alerta oficial por sus condiciones. |
| Publicación AWS | **Activa**, 08:30. Política privada de Alec, hasta diez vacantes por lote; primera corrida programada: `READY` con diez vacantes, una invocación y cero errores. | Vigilar gasto atribuido y continuidad. |
| Revisión Codex | Tarea local **AJI Alec — revisión diaria** ejecutada a las 09:00; lote del 20 de octubre: diez en `review`, cero CVs y cero postulaciones. El titular confirmó visibilidad desde Quick Remote. | Observar continuidad con el PC encendido y calidad de los reportes salariales. |
| Preparación de CV | Perfil privado de Alec aprobado con 36 afirmaciones rastreables a los dos PDF; `run-alec-pull.py --prepare` aplica umbral y cuota persistente de tres por día en SQLite privado y escribe paquetes atómicamente. Un perfil amplio se resume en un máximo de 12 afirmaciones por CV y tres por carta. La tarea de las 09:00 ya tiene instrucciones para ejecutar esta opción tras un lote `READY` válido. | Observar la primera ejecución programada de esta opción y revisar cualquier paquete real antes de postular. |
| Alertas Gmail | Cuenta de Alec conectada y piloto de lectura acotada en navegador completado; las funciones del conector rechazan llamadas en este chat. Sin lector AWS ni mensajes en Git. | Probar la lectura acotada en la próxima tarea diaria por conector o navegador y comprobar deduplicación/visibilidad en Remote. |
| Postulaciones | `AUTO_SUBMIT` apagado; no hay cliente de portal ni envíos reales. | Integración permitida, respuestas verificadas, autorización concreta por vacante y portal, recibo e idempotencia. |

`max_jobs_per_day=10` limita sólo las vacantes del lote. Los GET están acotados por cuatro fuentes, timeout, tamaño y reintentos. La cuota de preparación local ya persiste entre ejecuciones; la cuota de envíos queda pendiente porque no existe una integración de postulación habilitada. Ninguna alerta de presupuesto constituye un tope de gasto.

La política privada de Alec contiene filtros de ubicación, modalidad, condiciones y remuneración. Los diez anuncios oficiales del lote del 20 de octubre y sus campos Greenhouse `pay_input_ranges` no aportaron una cifra salarial. El conector ahora conserva rangos explícitos del empleador y su base bruta, neta, contractual o desconocida. Se halló una oferta oficial nueva de Inflect con USD 6,000–8,000/mes en B2B desde México; un escenario privado de impuestos permite priorizarla, pero no verifica el neto contractual ni las capacidades técnicas. La ausencia de información queda `unknown`/`review`; no se infiere que una condición se cumple. Los términos de ranking tecnológico y umbrales son elecciones operativas revisables, no nuevas preferencias del titular.

Las cuatro fuentes activas usan Greenhouse. Su [Job Board API](https://docs.greenhouse.io/job-board) permite GET públicos; el POST necesita una clave del empleador y preguntas propias del puesto. [Lever](https://github.com/lever/postings-api) y [Ashby](https://developers.ashbyhq.com/reference/applicationformsubmit) también exigen autenticación para el envío. La cuenta AWS del candidato y Gmail no conceden esas credenciales. Un portal podría permitir asistencia humana en navegador, sujeta a términos y a consentimiento concreto; no se prometen envíos universales.

## Trabajo pendiente para pasar de revisión a candidatura

1. Confirmar por vacante trabajo desde México, remoto, viajes, turnos y compensación **neta comparable**. Sólo entonces una vacante puede pasar de `review` a `shortlist` y superar el umbral de preparación.
2. La tarea diaria ejecutará `--prepare` sólo tras un lote `READY` válido; el perfil de Alec ya está aprobado y el generador se probó localmente con oferta ficticia y con el lote real. La prueba del 20 de octubre produjo cero CVs porque las diez vacantes siguen en revisión. Revisar el primer paquete real cuando exista, antes de cualquier envío. La cuota de tres es un límite técnico conservador. El `--claim` permanente queda fuera de la tarea.
3. Probar la tarea de Codex y Gmail en sus superficies reales. Mantener PII, CVs y correos fuera de Git, logs y CloudWatch.
4. Evaluar cada portal de envío, preguntas y consentimiento; probar sólo con fixtures o un entorno autorizado. No activar `AUTO_SUBMIT` ni enviar por un score o CV generado.

La [guía de uso del primer PC](runbooks/first-pc-user-guide.md) explica las horas, comandos y pausa. El [registro de avance](progress.md) conserva el piloto y bloqueos.
