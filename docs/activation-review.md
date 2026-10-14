# Revisión previa a la operación del primer equipo

Fecha: 2026-10-14. Especificación principal: plan maestro v3 en `private/specification/`. Las acciones A y B fueron autorizadas y ejecutadas el 2026-10-14; esta revisión conserva el alcance y los resultados. No se habilitaron funciones, programaciones ni postulaciones.

## Estado comprobado

- `aji-shared-dev` y `aji-alec-dev` están desplegados en `us-east-1`; los Scheduler y flags Lambda siguen desactivados. `Project` está activa como etiqueta de costos y `aji-project-dev` tiene avisos de gasto real USD 3/5 al correo privado confirmado.
- El código local y el publicador desplegado usan el manifiesto privado v1.1: verifica por separado los checksums de `jobs.json` y `matches.json`. También limita la lectura de cada objeto de lote a 32 MB y de la política privada a 64 KB; el pull resume errores AWS sin exponer el mensaje remoto.
- Los checksums detectan contenido alterado respecto al manifiesto; no autentican a quien puede sobrescribir tanto el manifiesto como los archivos. El aislamiento depende también de los permisos IAM y del bucket privado.
- Pasaron 57 pruebas Python y 9 pruebas CDK; la demo ficticia generó un paquete sin envío. La comparación de solo lectura `cdk diff --no-change-set` con el contexto privado mostró únicamente cambios del campo `Code` en las Lambdas `Collector` y `Publisher`, porque ambas empaquetan el mismo árbol `src/`. No mostró cambios IAM, Budgets ni Scheduler. El diff completo está en `private/activation-diff.txt`, fuera de Git.
- El usuario autorizó actualizar el publicador y ejecutar una prueba AWS ficticia. `cdk deploy aji-alec-dev --exclusively` terminó en `UPDATE_COMPLETE`; un diff posterior exclusivo de Alec mostró cero diferencias. El stack shared siguió en `UPDATE_COMPLETE`. El collector no se actualizó.

## Prueba AWS autorizada

- Antes de escribir se verificaron identidad, región, outputs del stack, Scheduler `DISABLED`, flags Lambda `false`, ausencia de los tres objetos del día y ausencia del lock.
- Se publicó una única vacante inventada del fixture Ashby, sin política profesional real, CV ni consultas a portales. S3 contiene `manifest.json`, `jobs.json` y `matches.json` cifrados con AES256; el prefijo `batches/` tiene caducidad a 30 días.
- La vista previa y el primer `--claim` mediante sesión asumida de `aji-alec-access-dev` devolvieron `READY`; el segundo `--claim` devolvió `ALREADY_PROCESSED`. El lock se confirmó en DynamoDB. El resumen informó 1 vacante para revisión, 0 CVs y 0 postulaciones.

## Estado de decisiones

| Paso | Acción propuesta | Efecto y límite | Información pendiente |
| --- | --- | --- | --- |
| A | Actualizar sólo el código de la Lambda publicadora mediante `cdk deploy aji-alec-dev --exclusively` desde el perfil `default` verificado | Ejecutado y verificado en `UPDATE_COMPLETE`; `AJI_PUBLISH_ENABLED=false`, Scheduler `DISABLED`, IAM y presupuesto sin cambios | Completado con autorización del usuario |
| B | Hacer una prueba integrada AWS con datos inventados del día, lectura mediante el rol de Alec y lock condicional en su tabla | Ejecutado: manifiesto READY v1.1, lectura y lock confirmados; retención S3 de 30 días y TTL del lock | Completado con autorización del usuario |
| C | Cargar política privada y fuentes permitidas; habilitar collector, publicador y sus Scheduler tras revisar el diff y costo | Ejecuta consultas HTTPS de lectura, escrituras DynamoDB/S3 y Lambda diariamente a las 08:00/08:30; puede generar gasto recurrente. El escenario ilustrativo es USD 0.69/mes, sin garantía. Budgets avisa, pero no detiene servicios | Empresas y boards ATS aprobados, términos de uso revisados, política de Alec aprobada por su titular, cuota diaria y aprobación de activación |
| D | Crear la automatización nativa de Codex Desktop a las 09:00 para Alec | El PC asumirá `aji-alec-access-dev`, leerá el lote y, si se aprueba `--claim`, escribirá el lock. Deben verificarse la ruta estable y la visibilidad en Codex Remote | Aprobación de la automatización y de su modalidad de lock tras la prueba B |

La política privada necesita roles, tecnologías, seniority, modalidad, compensación mínima y moneda si aplica, empresas excluidas, umbrales y máximo diario. Elegibilidad desde México sin confirmar permanece `unknown`; el modo es `PREPARE`. El ejemplo sin datos personales está en `config/search-policy.example.json`. Para fuentes se necesitan empresa, ATS, identificador de board, URL oficial y confirmación de que la lectura automatizada está permitida; el ejemplo está en `config/sources.example.yaml`.

El segundo equipo y `aji-hector-dev` esperan el handoff posterior. El código está en un [repositorio privado de GitHub](https://github.com/LynxPardelle/aws-job-intelligence); el segundo equipo necesitará acceso aprobado. Los perfiles reales, CVs y cualquier postulación requieren consentimiento de cada titular y autorización específica por vacante y portal. `AUTO_SUBMIT` permanece desactivado.

## Costos y cobertura

El presupuesto filtra `user:Project$AWSJobIntelligence`. Una lectura del 2026-10-14 informó USD 0.00 de gasto atribuido; todavía no demuestra cobertura ni entrega de avisos. Las programaciones individuales de EventBridge Scheduler no aceptan etiquetas en CloudFormation; AWS permite etiquetar grupos de programaciones. No se ha comprobado que una etiqueta de grupo atribuya sus cargos al filtro, así que se revisará también el gasto general de la cuenta. Véanse la [plantilla AWS de Schedule](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-scheduler-schedule.html), la [API de etiquetado de Scheduler](https://docs.aws.amazon.com/cli/latest/reference/scheduler/tag-resource.html) y la [estimación del proyecto](costs/estimate.md).
