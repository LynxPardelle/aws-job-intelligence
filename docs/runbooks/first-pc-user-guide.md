# Primer equipo: guía de uso de Alec

Estado verificado el 2026-10-20: la búsqueda diaria en AWS y la revisión diaria de Codex se ejecutaron en sus horarios. El titular confirmó que ve esta conversación desde Quick Remote. Sólo se preparan oportunidades para revisar; no hay envío automático ni postulaciones confirmadas. El handoff del segundo equipo está en pausa por instrucción del titular.

## Qué ocurre cada día

| Hora de Ciudad de México | Proceso | Resultado |
| --- | --- | --- |
| 08:00 | `aji-collect-dev` en AWS | Lee cuatro boards públicos Greenhouse: Utility Profit, Factored, Cobre e Inflect. Máximo cuatro fuentes por corrida; HTTPS, timeout, tamaño y reintentos acotados. La primera corrida con Inflect será posterior al despliegue del 20 de octubre. |
| 08:30 | `aji-alec-publish-dev` en AWS | Publica hasta diez vacantes en el bucket privado de Alec. Sólo un lote íntegro se marca `READY`. |
| 09:00 | Tarea local **AJI Alec — revisión diaria** de Codex | Comprueba identidad AWS, salud del Collector y lote privado con el rol temporal de Alec. Consulta Get on Board por separado con límites locales. Si el lote AWS es `READY`, ejecuta `--prepare` sólo para shortlist completa, con máximo tres borradores locales al día. Revisa sueldo y alertas Gmail, e informa aquí para Quick Remote. No toma el lock ni envía postulaciones. |

El PC debe estar encendido, con Codex Desktop operativo y este chat disponible para la tarea local de las 09:00. Las dos tareas de AWS funcionan independientemente del PC. El 20 de octubre se observaron ambas invocaciones programadas y el heartbeat local leyó un lote `READY` de diez vacantes, todas en revisión. El titular confirmó que ve este reporte en Quick Remote.

## Usarlo ahora

Desde la raíz del repositorio, en PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/run-alec-daily.py
```

`run-alec-daily.py` agrupa las comprobaciones anteriores, usa el entorno Python del proyecto y deja un resumen privado completo en `applications/alec/daily-report.json`. Su salida breve contiene estado, fecha/lote, presupuesto observado, salud de fuentes, conteos AWS/Get on Board, preparación y códigos seguros de error. `PARTIAL` puede indicar que el marcador aún está `NOT_INSTRUMENTED`; no se presenta como salud confirmada. Si el lote es inválido o falta, no ejecuta preparación ni reutiliza datos anteriores. Sólo prepara borradores locales de `shortlist` AWS válida, con perfil aprobado, revalidación del feed y cuota persistente de tres al día. Ejecutarlo varias veces no reclama el lote. **No usar `--claim` para la operación diaria**: el lock actual es permanente durante el día. Antes de las 08:30 puede faltar el lote.

La configuración AWS real vive en `private/local-aws.json`, la lista de fuentes/activación en `private/aws-activation.json` y las preferencias de Alec en `private/alec/search-policy.active.json`; todos están ignorados por Git. No publicar sus contenidos ni los CVs. El código público puede revisarse en [GitHub](https://github.com/LynxPardelle/aws-job-intelligence); el estado diario está en [progreso](../progress.md).

## Cómo interpretar los resultados

`review` significa que falta comprobar por vacante alguna condición de la política privada de Alec, como lugar de trabajo, modalidad, viajes, turnos o salario comparable. El resumen incluye el rango salarial público, si existe, su base bruta, neta, contractual o desconocida y los motivos de revisión. Las diez ofertas del lote del 20 de octubre no publican cifra numérica. La ausencia de una condición en el anuncio no demuestra que se cumpla; una estimación de otro sitio tampoco prueba el sueldo de la empresa. `shortlist` sólo se da si los filtros y la puntuación la permiten. La cuota de diez limita el lote, no los GET ni los CVs o envíos.

Caylent permanece en el catálogo de interés, pero fuera de la recolección automática porque sus condiciones actuales restringen el acceso automatizado al sitio. Puede revisarse manualmente o mediante alertas oficiales. Ninguna empresa está descartada por preferencia del candidato.

## CVs y postulaciones

Los dos CVs recientes de Alec fueron confirmados por él. El perfil `private/alec/verified-profile.json` contiene 36 afirmaciones con origen por PDF, página y línea; el contacto profesional queda también en privado. El generador selecciona hasta 12 afirmaciones pertinentes por CV y tres para la carta, con mapa de evidencia. Una prueba local con una oferta ficticia generó PDF de una página. El lote real de hoy produce **cero CVs** porque sus diez vacantes continúan en `review` por condiciones sin acreditar.

Cuando alguna vacante sea `shortlist` con todas las condiciones verificadas, `scripts/run-alec-pull.py --prepare` creará localmente hasta **tres** paquetes por día y sólo por encima del umbral privado. El contador se guarda en `applications/alec/.preparation-ledger.sqlite3`, fuera de Git, y persiste entre ejecuciones. Un paquete incompleto se reporta bloqueado, no preparado. Cada paquete incluye `requirements-evidence.json` con citas del anuncio, afirmaciones aprobadas relacionadas y lagunas sin verificar. Con el perfil aprobado y el lote real de hoy devolvió `prepared: 0` y `confirmed_applications: 0`, sin tomar el lock. La tarea programada de las 09:00 ya tiene esta instrucción; su primera ejecución está pendiente. Cada borrador real se informará aquí para revisión antes de cualquier postulación. La cuota tres es un límite técnico conservador y se puede ajustar por decisión posterior.

Las bases `applications/alec/.job-history.sqlite3`, `.compensation.sqlite3` y `.tracker.sqlite3` guardan respectivamente URLs vistas, cifras con fuente y eventos de candidatura. Son privadas y locales; el tracker sólo registra `DISCOVERED` al leer un lote y llega como máximo a `PREPARED` tras un paquete local íntegro. Una estimación salarial no se convierte en ingreso real. Una respuesta de Gmail requiere revisión humana antes de cambiar el estado. Si una base falla, el resumen dice `UNAVAILABLE` y no se infiere que su contenido exista.

La cuenta Gmail de Alec ya figura conectada en Codex. El 20 de octubre se leyó una muestra acotada mediante la sesión web de la misma cuenta porque las herramientas del conector siguen indisponibles en este chat. La tarea diaria intentará la lectura acotada por conector o navegador y reportará si falla. Los enlaces originales y la evaluación del piloto están sólo en `private/alec/`; no se copian mensajes ni tokens a AWS o Git. La primera ejecución programada con Gmail aún debe verificarse.

`AUTO_SUBMIT` sigue desactivado. Greenhouse permite leer el board público; su API de envío requiere una clave del empleador y respuestas específicas. Para una postulación por navegador se necesita un paquete revisado y una autorización **para esa vacante y ese portal**, junto con el formulario concreto, antes del envío. No se afirma que exista una integración universal ni se enviará una candidatura por inferencia de un score.

## Costos, pausa y fallos

El presupuesto `aji-project-dev` avisa al correo confirmado al llegar a USD 3 y 5 de gasto real etiquetado durante el mes; **no detiene AWS** ni garantiza incluir cargos sin etiqueta. Revise también los presupuestos generales de la cuenta. La estimación anterior de USD 0.69/mes es ilustrativa; el costo real de la operación se medirá tras varias corridas.

Para pausar la búsqueda, pida a Codex desactivar ambas programaciones y los flags de las dos Lambdas mediante CDK, además de pausar la tarea local de las 09:00; se verificará después el estado `DISABLED`/`false`. No borrar stacks ni datos como mecanismo de pausa. Consulte [operación y recuperación](operations.md).

Si el resumen indica `BATCH_UNAVAILABLE_OR_DENIED`, `BATCH_INVALID_OR_STALE` o `FAILED`, consulte el estado de ambos Scheduler, el marcador de recolección y los logs de Lambda. No fuerce `--claim` ni reutilice un lote viejo. Registre el incidente sin datos personales en [progreso](../progress.md).
