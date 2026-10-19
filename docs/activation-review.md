# Revisión previa a la operación del primer equipo

Actualizado: 2026-10-18. Especificación principal: plan maestro v3 en `private/specification/`. Las acciones A y B fueron autorizadas el 2026-10-14 y la actualización de código el 2026-10-18. Posteriormente el titular autorizó completar la operación de este equipo: se activaron fuentes, flags y ambos Scheduler de AWS, más la tarea local de Codex. **No se habilitó el envío de postulaciones.**

## Activación verificada del primer equipo

- Política privada de Alec y tres boards Greenhouse configurados: Utility Profit, Factored y Cobre. Caylent sigue en el catálogo, pero manual/alerta oficial por sus condiciones de acceso.
- Diff de piloto: sólo entornos de dos Lambdas, sin IAM ni recursos nuevos. Ambos stacks terminaron `UPDATE_COMPLETE`. Invocaciones manuales: Collector `OK`, 36 vacantes; Publisher `READY`, diez. Pull con sesión asumida de Alec sin `--claim`: diez `review`, cero shortlist, cero CVs y cero postulaciones.
- Diff de horarios: sólo dos Scheduler de `DISABLED` a `ENABLED`. Despliegue correcto, ambos horarios confirmados a las 08:00/08:30 `America/Mexico_City`, flags Lambda `true`. El diff posterior mostró cero diferencias.
- Tarea Codex **AJI Alec — revisión diaria** creada a las 09:00 en este chat. La primera ejecución programada y su visibilidad en Remote quedan pendientes de observar. Presupuesto filtrado USD 5, avisos USD 3/5; el gasto atribuido consultado seguía en USD 0.00, sin probar cobertura futura.
- Después del commit público `f873366`, un diff mostró sólo dos assets de código Lambda del nuevo flujo local; se publicaron en ambos stacks. CloudFormation informó `UPDATE_COMPLETE`, el diff posterior cero diferencias y Scheduler/flags siguieron activos. La corrida real no se repitió ese día.

Los detalles de cuenta, correo, respuestas y configuración están sólo en `private/`. Véase la [guía de uso](runbooks/first-pc-user-guide.md). Las secciones siguientes conservan el historial previo a esta activación.

## Estado comprobado antes de la activación

- `aji-shared-dev` y `aji-alec-dev` están desplegados en `us-east-1`; los Scheduler y flags Lambda siguen desactivados. `Project` está activa como etiqueta de costos y `aji-project-dev` tiene avisos de gasto real USD 3/5 al correo privado confirmado.
- El código local y el publicador desplegado usan el manifiesto privado v1.1: verifica por separado los checksums de `jobs.json` y `matches.json`. También limita la lectura de cada objeto de lote a 32 MB y de la política privada a 64 KB; el pull resume errores AWS sin exponer el mensaje remoto.
- Los checksums detectan contenido alterado respecto al manifiesto; no autentican a quien puede sobrescribir tanto el manifiesto como los archivos. El aislamiento depende también de los permisos IAM y del bucket privado.
- Pasaron 63 pruebas Python y 9 pruebas CDK; la demo ficticia generó un paquete sin envío. La comparación de solo lectura `cdk diff --no-change-set` con el contexto privado mostró únicamente cambios del campo `Code` en las Lambdas `Collector` y `Publisher`, porque ambas empaquetan el mismo árbol `src/`. No mostró cambios IAM, Budgets ni Scheduler. Los diffs están en `private/`, fuera de Git.
- El usuario autorizó actualizar el publicador y ejecutar una prueba AWS ficticia. `cdk deploy aji-alec-dev --exclusively` terminó en `UPDATE_COMPLETE`; un diff posterior exclusivo de Alec mostró cero diferencias. El stack shared siguió en `UPDATE_COMPLETE`. El collector no se actualizó.
- El 2026-10-18 el usuario autorizó actualizar el código de Collector y Publisher y confirmó `max_jobs_per_day=10`. Se verificaron cuenta, región, diff exacto, flags y Scheduler antes del despliegue. `cdk deploy aji-shared-dev aji-alec-dev --exclusively` terminó con ambos stacks en `UPDATE_COMPLETE`. El diff posterior mostró **cero cambios**; ambas funciones conservan su flag en `false` y ambos Scheduler siguen `DISABLED`. Logs y diffs están en `private/`.

## Prueba AWS autorizada

- Antes de escribir se verificaron identidad, región, outputs del stack, Scheduler `DISABLED`, flags Lambda `false`, ausencia de los tres objetos del día y ausencia del lock.
- Se publicó una única vacante inventada del fixture Ashby, sin política profesional real, CV ni consultas a portales. S3 contiene `manifest.json`, `jobs.json` y `matches.json` cifrados con AES256; el prefijo `batches/` tiene caducidad a 30 días.
- La vista previa y el primer `--claim` mediante sesión asumida de `aji-alec-access-dev` devolvieron `READY`; el segundo `--claim` devolvió `ALREADY_PROCESSED`. El lock se confirmó en DynamoDB. El resumen informó 1 vacante para revisión, 0 CVs y 0 postulaciones.

## Estado de decisiones antes de la activación

| Paso | Acción propuesta | Efecto y límite | Información pendiente |
| --- | --- | --- | --- |
| A | Actualizar sólo el código de la Lambda publicadora mediante `cdk deploy aji-alec-dev --exclusively` desde el perfil `default` verificado | Ejecutado y verificado en `UPDATE_COMPLETE`; `AJI_PUBLISH_ENABLED=false`, Scheduler `DISABLED`, IAM y presupuesto sin cambios | Completado con autorización del usuario |
| B | Hacer una prueba integrada AWS con datos inventados del día, lectura mediante el rol de Alec y lock condicional en su tabla | Ejecutado: manifiesto READY v1.1, lectura y lock confirmados; retención S3 de 30 días y TTL del lock | Completado con autorización del usuario |
| C | Cargar política privada y fuentes permitidas; habilitar collector, publicador y sus Scheduler tras revisar el diff y costo | Ejecuta consultas HTTPS de lectura, escrituras DynamoDB/S3 y Lambda diariamente a las 08:00/08:30; puede generar gasto recurrente. El escenario ilustrativo es USD 0.69/mes, sin garantía. Budgets avisa, pero no detiene servicios | `max_jobs_per_day=10` confirmado; faltan boards ATS autorizables, cuotas GET, política operativa completa, prueba de condiciones por oferta y aprobación expresa de activación |
| D | Crear la automatización nativa de Codex Desktop a las 09:00 para Alec | El PC asumirá `aji-alec-access-dev`. Se propone vista previa sin `--claim` en el piloto; el claim automático exige recuperación porque el lock actual se toma antes de preparar paquetes reales. Deben verificarse la ruta estable y la visibilidad en Codex Remote | Aprobar modalidad y horario tras revisar la [guía de opciones](decisions/first-pc-approval-options.md) |

La política privada ya recoge las preferencias confirmadas y el máximo diario de 10, pero roles exactos, tecnologías, seniority y umbrales conservan valores de propuesta. Elegibilidad desde México sin confirmar permanece `unknown`; el modo es `PREPARE`. El ejemplo sin datos personales está en `config/search-policy.example.json`. Para fuentes se necesitan empresa, ATS, identificador de board, URL oficial y confirmación de que la lectura automatizada está permitida; el ejemplo está en `config/sources.example.yaml`.

Actualización 2026-10-18: los criterios personales recibidos están en `private/alec/`; la cuota del lote ya está fijada en 10, pero faltan cuotas de lectura y envío. El matcher admite `salary_basis=net` y el contrato de vacante v1.1 representa viajes y turnos como `required/not_required/unknown`; deja las incógnitas en revisión. El código correspondiente está desplegado, con ejecución desactivada. Véase la [revisión de automatización](automation-readiness.md).

El `cdk diff --no-change-set` previo a la activación mostró **dos cambios de código Lambda**: Collector en `aji-shared-dev` y Publisher en `aji-alec-dev`. No mostró cambios de IAM, Scheduler, Budgets ni recursos nuevos. El detalle quedó en `private/approved-code-diff-2026-10-18.txt`, fuera de Git. Una primera lectura anterior falló por la CA de Node y se repitió con `NODE_OPTIONS=--use-system-ca`. Tras la aprobación del usuario se publicó sólo ese código; `private/approved-code-post-deploy-diff-2026-10-18.txt` mostró cero diferencias. La activación posterior se documenta al inicio de este archivo.

El segundo equipo y `aji-hector-dev` esperan el handoff posterior. El código está en un [repositorio público de GitHub](https://github.com/LynxPardelle/aws-job-intelligence); el segundo equipo necesitará sus propios permisos AWS, Drive y Codex. Los perfiles reales, CVs y cualquier postulación requieren consentimiento de cada titular y autorización específica por vacante y portal. `AUTO_SUBMIT` permanece desactivado.

## Costos y cobertura

El presupuesto filtra `user:Project$AWSJobIntelligence`. Una lectura del 2026-10-14 informó USD 0.00 de gasto atribuido; todavía no demuestra cobertura ni entrega de avisos. Las programaciones individuales de EventBridge Scheduler no aceptan etiquetas en CloudFormation; AWS permite etiquetar grupos de programaciones. No se ha comprobado que una etiqueta de grupo atribuya sus cargos al filtro, así que se revisará también el gasto general de la cuenta. Véanse la [plantilla AWS de Schedule](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-scheduler-schedule.html), la [API de etiquetado de Scheduler](https://docs.aws.amazon.com/cli/latest/reference/scheduler/tag-resource.html) y la [estimación del proyecto](costs/estimate.md).
