# Primer equipo: guía de uso de Alec

Estado verificado el 2026-10-19: la búsqueda diaria en AWS y la revisión diaria de Codex se ejecutaron en sus horarios. Sólo se preparan oportunidades para revisar; no hay envío automático ni postulaciones confirmadas. El segundo equipo espera el handoff.

## Qué ocurre cada día

| Hora de Ciudad de México | Proceso | Resultado |
| --- | --- | --- |
| 08:00 | `aji-collect-dev` en AWS | Lee tres boards públicos Greenhouse: Utility Profit, Factored y Cobre. Máximo tres fuentes por corrida; HTTPS, timeout, tamaño y reintentos acotados. |
| 08:30 | `aji-alec-publish-dev` en AWS | Publica hasta diez vacantes en el bucket privado de Alec. Sólo un lote íntegro se marca `READY`. |
| 09:00 | Tarea local **AJI Alec — revisión diaria** de Codex | Comprueba identidad AWS y lee una vista previa con el rol temporal de Alec. Informa vacantes y bloqueos en esta conversación, visible desde Codex Remote. No toma el lock. |

El PC debe estar encendido, con Codex Desktop operativo y este chat disponible para la tarea local de las 09:00. Las dos tareas de AWS funcionan independientemente del PC. El 19 de octubre se observaron ambas invocaciones programadas y el heartbeat local leyó un lote `READY` de diez vacantes, todas en revisión. El titular aún debe confirmar que ve este reporte en la interfaz Remote.

## Usarlo ahora

Desde la raíz del repositorio, en PowerShell:

```powershell
powershell -File scripts/check-aws-local.ps1
.\.venv\Scripts\python.exe scripts/run-alec-pull.py
```

El segundo comando es una vista previa de solo lectura. Muestra `READY`, fecha/lote, empresas, títulos, URLs, score y motivo de revisión cuando el lote del día existe. Ejecutarlo varias veces no reclama el lote. **No usar `--claim` para la operación diaria**: el lock actual es permanente durante el día y la preparación real aún no está conectada. El resultado puede estar vacío o fallar antes de las 08:30. No se reutiliza un lote de otro día.

La configuración AWS real vive en `private/local-aws.json`, la lista de fuentes/activación en `private/aws-activation.json` y las preferencias de Alec en `private/alec/search-policy.active.json`; todos están ignorados por Git. No publicar sus contenidos ni los CVs. El código público puede revisarse en [GitHub](https://github.com/LynxPardelle/aws-job-intelligence); el estado diario está en [progreso](../progress.md).

## Cómo interpretar los resultados

`review` significa que falta comprobar por vacante alguna condición de la política privada de Alec, como lugar de trabajo, modalidad, viajes, turnos o salario comparable. La ausencia de una condición en el anuncio no demuestra que se cumpla. `shortlist` sólo se da si los filtros y la puntuación la permiten. La cuota de diez limita el lote, no los GET ni los CVs o envíos.

Caylent permanece en el catálogo de interés, pero fuera de la recolección automática porque sus condiciones actuales restringen el acceso automatizado al sitio. Puede revisarse manualmente o mediante alertas oficiales. Ninguna de las cuatro empresas está descartada por preferencia del candidato.

## CVs y postulaciones

Los dos CVs recientes de Alec fueron confirmados por él. El perfil `private/alec/verified-profile.json` contiene 36 afirmaciones con origen por PDF, página y línea; el contacto profesional queda también en privado. El generador selecciona hasta 12 afirmaciones pertinentes por CV y tres para la carta, con mapa de evidencia. Una prueba local con una oferta ficticia generó PDF de una página. El lote real de hoy produce **cero CVs** porque sus diez vacantes continúan en `review` por condiciones sin acreditar.

Cuando alguna vacante sea `shortlist` con todas las condiciones verificadas, `scripts/run-alec-pull.py --prepare` podrá crear localmente hasta **tres** paquetes por día y sólo por encima del umbral privado. Con el perfil aprobado y el lote real de hoy devolvió `prepared: 0` y `confirmed_applications: 0`, sin tomar el lock. No está habilitado en la tarea programada de las 09:00; primero se revisará un paquete de una oferta real completa. La cuota tres es un límite técnico conservador y se puede ajustar por decisión posterior.

Gmail se reservó para Codex, pero su conector no está disponible en este chat. Cuando esté conectado con la cuenta de Alec se probará lectura acotada de alertas; no se copiarán mensajes ni tokens a AWS.

`AUTO_SUBMIT` sigue desactivado. Greenhouse permite leer el board público; su API de envío requiere una clave del empleador y respuestas específicas. Para una postulación por navegador se necesita un paquete revisado y una autorización **para esa vacante y ese portal**, junto con el formulario concreto, antes del envío. No se afirma que exista una integración universal ni se enviará una candidatura por inferencia de un score.

## Costos, pausa y fallos

El presupuesto `aji-project-dev` avisa al correo confirmado al llegar a USD 3 y 5 de gasto real etiquetado durante el mes; **no detiene AWS** ni garantiza incluir cargos sin etiqueta. Revise también los presupuestos generales de la cuenta. La estimación anterior de USD 0.69/mes es ilustrativa; el costo real de la operación se medirá tras varias corridas.

Para pausar la búsqueda, pida a Codex desactivar ambas programaciones y los flags de las dos Lambdas mediante CDK, además de pausar la tarea local de las 09:00; se verificará después el estado `DISABLED`/`false`. No borrar stacks ni datos como mecanismo de pausa. Consulte [operación y recuperación](operations.md).

Si el resumen indica `BATCH_UNAVAILABLE_OR_DENIED`, `BATCH_INVALID_OR_STALE` o `FAILED`, consulte el estado de ambos Scheduler, el marcador de recolección y los logs de Lambda. No fuerce `--claim` ni reutilice un lote viejo. Registre el incidente sin datos personales en [progreso](../progress.md).
