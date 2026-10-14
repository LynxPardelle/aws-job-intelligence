# Despliegue y presupuesto: primer equipo

Estado: **primer despliegue y actualización del presupuesto aprobados por el usuario y ejecutados** el 2026-10-13. Especificación principal: copia privada del plan maestro v3 en `private/specification/`. El segundo equipo y el stack de Héctor quedan fuera de este alcance.

## Alcance exacto

- Cuenta verificada por STS terminada en `4577`, perfil local `default` y usuario administrador autorizado en este PC. La clave existente permanece en el almacén local de AWS CLI; ninguna clave se copiará al repositorio.
- Región `us-east-1`, **confirmada por el usuario** para este primer equipo.
- Stacks `aji-shared-dev` y `aji-alec-dev` solamente. El primero crea tabla pública DynamoDB on-demand con GSI `collection-run-index`, Lambda collector, Scheduler a las 08:00 `America/Mexico_City`, log de 7 días y alarma de error. El segundo crea bucket S3 privado de Alec, tabla de estado privada, rol `aji-alec-access-dev`, Lambda publicador, Scheduler a las 08:30, log de 7 días y alarma de error.
- Primer despliegue **sin presupuesto propio**: el CDK lo omitió porque no recibió `budgetEmail`. La actualización posterior, también aprobada, activó la etiqueta de costos `Project` y creó `aji-project-dev` de USD 5/mes, con avisos de gasto real a USD 3/5 y filtro `user:Project$AWSJobIntelligence`. El correo confirmado está sólo en `private/local-aws.json`, ignorado por Git.
- Primer despliegue con ambos Scheduler `DISABLED` y variables `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`; no habrá recolección programada ni publicación hasta una activación posterior aprobada. Las fuentes reales y la política JSON privada de Alec aún no están cargadas.
- No se modifica ni crea infraestructura de Héctor, automatización de Codex Desktop, acceso al segundo PC, datos profesionales reales ni postulaciones.

La síntesis comprobada antes de desplegar contenía exactamente **2 tablas DynamoDB, 1 bucket S3 y su política, 2 Lambdas, 2 log groups, 2 alarmas, 2 Scheduler desactivados, 5 roles IAM y 5 políticas IAM**, además de metadatos CDK. Contenía **0 presupuestos AWS** y ningún recurso de Héctor. `cdk diff --no-change-set` mostró únicamente la creación de esos recursos y los permisos previstos.

## IAM y datos

El perfil administrador crea los stacks sólo tras aprobación. El rol diario de Alec confía en el usuario actual y se asume mediante STS en `scripts/run-alec-pull.py`; su política puede leer lotes de **su** bucket, consultar vacantes públicas y escribir su estado privado, pero no sobrescribir manifiestos del publicador. El publicador tiene acceso de lectura al marcador y al índice público, lectura de `config/search-policy.json` de Alec y escritura sólo bajo `batches/*` en el bucket de Alec. El administrador conserva acceso total por su política existente; las pruebas de roles no demuestran aislamiento frente al administrador.

Los buckets usan Block Public Access, S3 managed encryption y HTTPS. DynamoDB usa cifrado administrado por AWS, tablas separadas y TTL para elementos que incluyen `expires_at`. `batches/*` caduca por lifecycle a 30 días. No se suben CVs, perfiles ni correos completos en esta etapa.

## Costo y comprobaciones

El [escenario guardado en AWS Pricing Calculator](https://calculator.aws/#/estimate?id=7cb2aa5f807fc711290c42c815d33de5ed9e11b8) da **USD 0.69/mes** para el primer equipo bajo volumen bajo y tamaños supuestos; el [cálculo manual](costs/estimate.md) redondea a USD 0.70/mes. No es un límite de gasto ni incluye otros proyectos de la cuenta. La consulta de solo lectura a Budgets encontró siete presupuestos existentes: los dos generales ya superan USD 5 de gasto real mensual, de modo que no sirven como aviso temprano para este proyecto. Quedan por observar tamaños y volumen reales, cuotas disponibles y cobertura de las etiquetas de costo. El bootstrap `CDKToolkit` ya existe en `us-east-1` (versión 31), así que esta propuesta no incluye `cdk bootstrap`.

Pasaron 53 pruebas Python y 9 pruebas CDK, síntesis local de dos y tres stacks con identidades ficticias y auditorías de dependencias sin vulnerabilidades conocidas. `scripts/check-aws-local.ps1` confirmó la cuenta/región/principal en este PC. La primera síntesis sin correo omite el presupuesto; la plantilla con correo contiene el filtro de proyecto.

## Ejecución y verificación

1. El usuario aprobó expresamente crear sólo `aji-shared-dev` y `aji-alec-dev` en `us-east-1` con sus recursos IAM y costos, ambos Scheduler desactivados y sin presupuesto específico inicial. El preflight de STS y el `cdk diff --no-change-set` confirmaron identidad y alcance. Un primer diff falló por la CA local; se repitió con `NODE_OPTIONS=--use-system-ca`, sin omitir TLS ni aplicar cambios inesperados.
2. `cdk deploy` terminó con ambos stacks en `CREATE_COMPLETE`. Los outputs del rol y bucket de Alec están en `private/local-aws.json`; el archivo completo de outputs está en `private/cdk-outputs.json`. Ambos quedan fuera de Git.
3. AWS confirmó ambos Scheduler `DISABLED`, `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`, tablas `ACTIVE` on-demand y cifradas, bucket con Block Public Access y AES256, `Project=AWSJobIntelligence` en tablas, bucket, Lambdas, logs, alarmas y rol de Alec, logs de 7 días, concurrencia reservada 1, dos alarmas y **ningún presupuesto `aji-project-dev`**. Las plantillas de Scheduler no incluyen `Tags`; sus posibles cargos deberán vigilarse en el gasto general.
4. Desde una sesión STS del rol `aji-alec-access-dev`, `GetItem` en las tablas pública y propia fue permitido; `Scan` de la tabla privada y `ListBucket` fueron denegados. La vista previa del pull, sin lote del día, devuelve JSON `BATCH_UNAVAILABLE_OR_DENIED` y código distinto de cero. No se subieron datos de prueba ni se adquirió lock.

## Segunda actualización: etiqueta y presupuesto

- El usuario aprobó activar `Project` como etiqueta de asignación de costos y crear el presupuesto filtrado. Cost Explorer mostró la clave `Inactive` antes de la activación; la API de actualización no devolvió errores y la consulta posterior la mostró `Active`.
- El preflight de identidad volvió a pasar. `cdk diff --no-change-set` con el correo privado mostró **un único recurso nuevo `AWS::Budgets::Budget`** y el filtro `user:Project$AWSJobIntelligence`; el diff quedó en `private/budget-diff-authorized.txt`, fuera de Git. `cdk deploy aji-shared-dev` terminó en `UPDATE_COMPLETE`; Alec siguió en `CREATE_COMPLETE`.
- AWS Budgets confirmó USD 5 mensuales, el filtro exacto, dos avisos de gasto real al superar USD 3 y USD 5, y el correo privado confirmado como destinatario de ambos. Se volvieron a verificar ambos Scheduler `DISABLED` y ambos flags Lambda en `false`. No se ha observado gasto atribuido ni entrega de correos.

## Cambios AWS pendientes

- Observar gasto real antes de activar las funciones. El costo recurrente mínimo modelado incluye las dos alarmas (~USD 0.20/mes antes de cuotas); el escenario activo ilustrativo es USD 0.69/mes y no es un tope.
- Verificar cobertura del presupuesto con gasto real y revisar también costos generales porque los Scheduler carecen de etiqueta y el filtro puede omitir cargos sin `Project`.
- Solicitar autorización separada para activar fuentes, collector, publicador y automatización nativa de las 09:00. Solicitar otra autorización específica para cualquier postulación real. El stack y equipo de Héctor esperan el handoff posterior.

El [runbook](runbooks/operations.md) contiene el apagado operativo. El [registro de progreso](progress.md) contiene los bloqueos vigentes y el handoff posterior al segundo equipo.
