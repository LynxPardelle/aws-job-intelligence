# Revisión previa a la operación del primer equipo

Fecha: 2026-10-14. Especificación principal: plan maestro v3 en `private/specification/`. Esta revisión prepara decisiones; no habilita funciones, programaciones, gastos nuevos ni postulaciones.

## Estado comprobado

- `aji-shared-dev` y `aji-alec-dev` están desplegados en `us-east-1`; los Scheduler y flags Lambda siguen desactivados. `Project` está activa como etiqueta de costos y `aji-project-dev` tiene avisos de gasto real USD 3/5 al correo privado confirmado.
- El código local usa el manifiesto privado v1.1: verifica por separado los checksums de `jobs.json` y `matches.json`. También limita la lectura de cada objeto de lote a 32 MB y de la política privada a 64 KB; el pull resume errores AWS sin exponer el mensaje remoto. La versión desplegada del publicador todavía genera manifiestos v1.0. **No activar el flujo diario hasta actualizarla.**
- Los checksums detectan contenido alterado respecto al manifiesto; no autentican a quien puede sobrescribir tanto el manifiesto como los archivos. El aislamiento depende también de los permisos IAM y del bucket privado.
- Pasaron 57 pruebas Python y 9 pruebas CDK; la demo ficticia generó un paquete sin envío. La comparación de solo lectura `cdk diff --no-change-set` con el contexto privado mostró únicamente cambios del campo `Code` en las Lambdas `Collector` y `Publisher`, porque ambas empaquetan el mismo árbol `src/`. No mostró cambios IAM, Budgets ni Scheduler. El diff completo está en `private/activation-diff.txt`, fuera de Git.
- La actualización funcional necesaria ahora es la del publicador `aji-alec-dev`. `cdk deploy aji-alec-dev --exclusively` evita incluir su dependencia shared; el collector puede actualizarse cuando se configure su fuente. Esta orden **no se ha ejecutado**.

## Decisiones que requieren autorización expresa

| Paso | Acción propuesta | Efecto y límite | Información pendiente |
| --- | --- | --- | --- |
| A | Actualizar sólo el código de la Lambda publicadora mediante `cdk deploy aji-alec-dev --exclusively` desde el perfil `default` verificado | Publica un nuevo asset de código en el bucket de CDK y actualiza una Lambda; conserva `AJI_PUBLISH_ENABLED=false`, Scheduler `DISABLED`, IAM y presupuesto. Puede generar costos mínimos de almacenamiento/actualización; no invoca la función | Aprobación del despliegue de código del stack exacto |
| B | Hacer una prueba integrada AWS con datos inventados del día, lectura mediante el rol de Alec y lock condicional en su tabla | Antes de escribir se comprobará que no haya manifiesto del día. La prueba escribiría `manifest.json` (FAILED y luego READY), `jobs.json`, `matches.json` y un registro de lock; genera solicitudes S3/DynamoDB. El lote caduca por lifecycle a 30 días y el lock por TTL. No usa CVs, correo ni portales | Aprobación separada para esas escrituras de prueba y su retención temporal |
| C | Cargar política privada y fuentes permitidas; habilitar collector, publicador y sus Scheduler tras revisar el diff y costo | Ejecuta consultas HTTPS de lectura, escrituras DynamoDB/S3 y Lambda diariamente a las 08:00/08:30; puede generar gasto recurrente. El escenario ilustrativo es USD 0.69/mes, sin garantía. Budgets avisa, pero no detiene servicios | Empresas y boards ATS aprobados, términos de uso revisados, política de Alec aprobada por su titular, cuota diaria y aprobación de activación |
| D | Crear la automatización nativa de Codex Desktop a las 09:00 para Alec | El PC asumirá `aji-alec-access-dev`, leerá el lote y, si se aprueba `--claim`, escribirá el lock. Deben verificarse la ruta estable y la visibilidad en Codex Remote | Aprobación de la automatización y de su modalidad de lock tras la prueba B |

La política privada necesita roles, tecnologías, seniority, modalidad, compensación mínima y moneda si aplica, empresas excluidas, umbrales y máximo diario. Elegibilidad desde México sin confirmar permanece `unknown`; el modo es `PREPARE`. El ejemplo sin datos personales está en `config/search-policy.example.json`. Para fuentes se necesitan empresa, ATS, identificador de board, URL oficial y confirmación de que la lectura automatizada está permitida; el ejemplo está en `config/sources.example.yaml`.

El segundo equipo y `aji-hector-dev` esperan el handoff posterior. Este repositorio no tiene remoto Git; para transferir el código al otro equipo hará falta un repositorio privado aprobado o el medio de transferencia que indique el usuario. Los perfiles reales, CVs y cualquier postulación requieren consentimiento de cada titular y autorización específica por vacante y portal. `AUTO_SUBMIT` permanece desactivado.

## Costos y cobertura

El presupuesto filtra `user:Project$AWSJobIntelligence`. Una lectura del 2026-10-14 informó USD 0.00 de gasto atribuido; todavía no demuestra cobertura ni entrega de avisos. Las programaciones individuales de EventBridge Scheduler no aceptan etiquetas en CloudFormation; AWS permite etiquetar grupos de programaciones. No se ha comprobado que una etiqueta de grupo atribuya sus cargos al filtro, así que se revisará también el gasto general de la cuenta. Véanse la [plantilla AWS de Schedule](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-scheduler-schedule.html), la [API de etiquetado de Scheduler](https://docs.aws.amazon.com/cli/latest/reference/scheduler/tag-resource.html) y la [estimación del proyecto](costs/estimate.md).
