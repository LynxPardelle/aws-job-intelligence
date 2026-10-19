# Operación y pausa del primer equipo

Estado comprobado el 2026-10-18: `aji-shared-dev` y `aji-alec-dev` están en `UPDATE_COMPLETE` en `us-east-1`. `aji-collect-dev` y `aji-alec-publish-dev` están `ENABLED` a las 08:00/08:30 `America/Mexico_City`, y sus flags Lambda están en `true`. La tarea local **AJI Alec — revisión diaria** está activa a las 09:00. Sólo Alec; Héctor espera handoff.

## Corrida normal

1. El collector consulta tres boards Greenhouse con HTTPS, timeout de 8 s, límite de 2 MB, sin redirecciones y reintentos acotados. Un fallo de fuente deja la colección incompleta.
2. El publicador exige el marcador COMPLETE del mismo día y escribe `manifest.json`, `jobs.json` y `matches.json` en el bucket privado de Alec. Marca `READY` sólo después de todas las escrituras; cuota diez vacantes. Si falla, deja `FAILED`.
3. Codex Desktop verifica este PC y la identidad AWS, asume `aji-alec-access-dev` y ejecuta vista previa sin `--claim`. El pull valida el manifiesto v1.1, fecha/vigencia, IDs y checksums. Informa el resultado en este chat para Codex Remote.
4. La política privada de Alec contiene filtros de ubicación, modalidad, condiciones y remuneración. Los datos que el feed no acredita quedan en revisión. El primer lote real tuvo diez vacantes en revisión y cero CVs.
5. Ni la tarea ni AWS envían postulaciones. `AUTO_SUBMIT` está apagado; no usar formularios reales como prueba.

El PC y Codex Desktop deben permanecer operativos para la tarea de las 09:00. Un fallo local no detiene los dos Scheduler de AWS. La primera ejecución programada se verificará tras su horario; el piloto manual probó el flujo de AWS y el pull.

## Diagnóstico

- Ejecutar `powershell -File scripts/check-aws-local.ps1` desde la raíz. Debe confirmar el perfil `default`, la cuenta autorizada y `us-east-1`.
- Ejecutar `.\.venv\Scripts\python.exe scripts/run-alec-pull.py` sin `--claim`. Antes de las 08:30 puede faltar el lote. `BATCH_UNAVAILABLE_OR_DENIED`, `BATCH_INVALID_OR_STALE` y `FAILED` no autorizan usar datos de otro día.
- Verificar en AWS el estado de `aji-collect-dev`/`aji-alec-publish-dev`, los flags de las Lambdas y los logs de siete días. Revisar el gasto atribuido y el gasto general.
- Registrar el fallo y la corrección en [progreso](../progress.md), sin CV, correo completo, secretos ni PII.

## Pausa y recuperación

Para una pausa operativa, deshabilitar ambos Scheduler **y** poner `AJI_ENABLED=false`/`AJI_PUBLISH_ENABLED=false` mediante una actualización CDK que conserve el presupuesto y los demás parámetros. El archivo `private/aws-activation.json` permite poner `collectionScheduleEnabled`, `publicationScheduleEnabled`, `collectionEnabled` y `publicationEnabled` en `false`; revisar primero `cdk diff` con la cuenta, región, principal y correo de presupuesto de `private/local-aws.json`, luego desplegar shared+Alec y verificar `DISABLED`/`false`. Pausar también la tarea local en Codex si se quiere detener el informe diario. No borrar stacks ni el bucket como mecanismo de pausa.

Reanudar sólo tras resolver el motivo, revisar las fuentes, costos y el diff, y confirmar identidad. Nunca activar Héctor desde este PC por accidente. El presupuesto `aji-project-dev` avisa por gasto real etiquetado a USD 3/5 al correo confirmado: no es un tope ni garantiza cubrir cargos sin etiqueta. Revisar también los presupuestos generales de la cuenta.

## Retención

- Logs Lambda: siete días.
- Vacantes públicas: TTL de 30 días; DynamoDB puede eliminarlas después del vencimiento.
- Objetos S3 bajo `batches/`: regla de expiración a 30 días.
- Estado privado, perfiles y CVs: sin borrado general automático; acordar retención por titular antes de producir paquetes reales.
- `cdk destroy` y borrado de datos requieren autorización separada. Las tablas y el bucket tienen `RETAIN`.

La [guía de uso](first-pc-user-guide.md) explica los pasos cotidianos. El [plan](../../plan/feature-local-mvp-1.md) mantiene el trabajo técnico pendiente.
