# Automatización diaria: alcance real

Actualizado el 2026-10-19. El plan maestro privado v3 rige este diseño. Sólo Alec y este PC están activos; los datos profesionales permanecen fuera de Git.

| Etapa | Estado actual | Siguiente requisito |
| --- | --- | --- |
| Recolección AWS | **Activa**, 08:00 Ciudad de México. Tres boards públicos Greenhouse: Utility Profit, Factored y Cobre; máximo tres fuentes configuradas. Primera corrida programada observada el 19 de octubre: una invocación y cero errores. | Observar calidad y costos durante varias corridas. Caylent continúa como revisión manual/alerta oficial por sus condiciones. |
| Publicación AWS | **Activa**, 08:30. Política privada de Alec, hasta diez vacantes por lote; primera corrida programada: `READY` con diez vacantes, una invocación y cero errores. | Vigilar gasto atribuido y continuidad. |
| Revisión Codex | Tarea local **AJI Alec — revisión diaria** ejecutada a las 09:00; lote del 19 de octubre: diez en `review`, cero CVs y cero postulaciones. | Confirmar visibilidad en Remote y continuidad con el PC encendido. |
| Preparación de CV | Perfil privado de Alec aprobado con 36 afirmaciones rastreables a los dos PDF; `run-alec-pull.py --prepare` aplica umbral y cuota de tres y escribe paquetes atómicamente. Un perfil amplio se resume en un máximo de 12 afirmaciones por CV y tres por carta. La tarea de las 09:00 no ejecuta esta opción. | Vacante con condiciones suficientes y revisión de un primer paquete real antes de habilitarla en la tarea. |
| Alertas Gmail | Diseño por candidato documentado, sin lector AWS. | Conectar el Gmail de Alec en Codex; el conector no está expuesto en este chat. |
| Postulaciones | `AUTO_SUBMIT` apagado; no hay cliente de portal ni envíos reales. | Integración permitida, respuestas verificadas, autorización concreta por vacante y portal, recibo e idempotencia. |

`max_jobs_per_day=10` limita sólo las vacantes del lote. Los GET están acotados por tres fuentes, timeout, tamaño y reintentos; aún no hay contadores diarios independientes para preparación y envío. Ninguna alerta de presupuesto constituye un tope de gasto.

La política privada de Alec contiene filtros de ubicación, modalidad, condiciones y remuneración. Los feeds públicos normalmente no prueban todas estas condiciones. La ausencia de información queda `unknown`/`review`; no se infiere que una condición se cumple. Los términos de ranking tecnológico y umbrales son elecciones operativas revisables, no nuevas preferencias del titular.

Los cuatro boards del catálogo F2 usan Greenhouse. Su [Job Board API](https://docs.greenhouse.io/job-board) permite GET públicos; el POST necesita una clave del empleador y preguntas propias del puesto. [Lever](https://github.com/lever/postings-api) y [Ashby](https://developers.ashbyhq.com/reference/applicationformsubmit) también exigen autenticación para el envío. La cuenta AWS del candidato y Gmail no conceden esas credenciales. Un portal podría permitir asistencia humana en navegador, sujeta a términos y a consentimiento concreto; no se prometen envíos universales.

## Trabajo pendiente antes de preparar o enviar

1. Confirmar por vacante trabajo desde México, remoto, viajes, turnos y compensación **neta comparable**. Sólo entonces una vacante puede pasar de `review` a `shortlist` y superar el umbral de preparación.
2. Revisar un primer paquete de una oferta real completa antes de activar `--prepare` en la tarea diaria. El perfil de Alec ya está aprobado y el generador se probó localmente con oferta ficticia y con el lote real; éste produjo cero CVs porque las diez vacantes siguen en revisión. La cuota de tres es un límite técnico conservador. El `--claim` permanente queda fuera de la tarea.
3. Probar la tarea de Codex y Gmail en sus superficies reales. Mantener PII, CVs y correos fuera de Git, logs y CloudWatch.
4. Evaluar cada portal de envío, preguntas y consentimiento; probar sólo con fixtures o un entorno autorizado. No activar `AUTO_SUBMIT` ni enviar por un score o CV generado.

La [guía de uso del primer PC](runbooks/first-pc-user-guide.md) explica las horas, comandos y pausa. El [registro de avance](progress.md) conserva el piloto y bloqueos.
