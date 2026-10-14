# Propuesta de despliegue: primer equipo

Estado: **para revisión; no aprobada ni ejecutada**. Fecha: 2026-10-13. Especificación principal: copia privada del plan maestro v3 en `private/specification/`. El segundo equipo y el stack de Héctor quedan fuera de esta propuesta.

## Alcance exacto

- Cuenta verificada por STS terminada en `4577`, perfil local `default` y usuario administrador autorizado en este PC. La clave existente permanece en el almacén local de AWS CLI; ninguna clave se copiará al repositorio.
- Región `us-east-1`, **confirmada por el usuario** para este primer equipo.
- Stacks `aji-shared-dev` y `aji-alec-dev` solamente. El primero crea tabla pública DynamoDB on-demand con GSI `collection-run-index`, Lambda collector, Scheduler a las 08:00 `America/Mexico_City`, log de 7 días y alarma de error. El segundo crea bucket S3 privado de Alec, tabla de estado privada, rol `aji-alec-access-dev`, Lambda publicador, Scheduler a las 08:30, log de 7 días y alarma de error.
- Primer despliegue **sin presupuesto propio**: el CDK lo omite si no recibe `budgetEmail`. El correo para los futuros avisos fue confirmado por el usuario y está sólo en `private/local-aws.json`, ignorado por Git. El presupuesto posterior `aji-project-dev` será de USD 5/mes, con avisos reales a USD 3/5 y filtro `user:Project$AWSJobIntelligence`, después de activar y verificar esa etiqueta de costos.
- Primer despliegue con ambos Scheduler `DISABLED` y variables `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`; no habrá recolección programada ni publicación hasta una activación posterior aprobada. Las fuentes reales y la política JSON privada de Alec aún no están cargadas.
- No se modifica ni crea infraestructura de Héctor, automatización de Codex Desktop, acceso al segundo PC, datos profesionales reales ni postulaciones.

La síntesis local de esta primera etapa contiene exactamente **2 tablas DynamoDB, 1 bucket S3 y su política, 2 Lambdas, 2 log groups, 2 alarmas, 2 Scheduler desactivados, 5 roles IAM y 5 políticas IAM**, además de metadatos CDK. Contiene **0 presupuestos AWS** y ningún recurso de Héctor.

## IAM y datos

El perfil administrador crea los stacks sólo tras aprobación. El rol diario de Alec confía en el usuario actual y se asume mediante STS en `scripts/run-alec-pull.py`; su política puede leer lotes de **su** bucket, consultar vacantes públicas y escribir su estado privado, pero no sobrescribir manifiestos del publicador. El publicador tiene acceso de lectura al marcador y al índice público, lectura de `config/search-policy.json` de Alec y escritura sólo bajo `batches/*` en el bucket de Alec. El administrador conserva acceso total por su política existente; las pruebas de roles no demuestran aislamiento frente al administrador.

Los buckets usan Block Public Access, S3 managed encryption y HTTPS. DynamoDB usa cifrado administrado por AWS, tablas separadas y TTL para elementos que incluyen `expires_at`. `batches/*` caduca por lifecycle a 30 días. No se suben CVs, perfiles ni correos completos en esta etapa.

## Costo y comprobaciones

El [escenario guardado en AWS Pricing Calculator](https://calculator.aws/#/estimate?id=7cb2aa5f807fc711290c42c815d33de5ed9e11b8) da **USD 0.69/mes** para el primer equipo bajo volumen bajo y tamaños supuestos; el [cálculo manual](costs/estimate.md) redondea a USD 0.70/mes. No es un límite de gasto ni incluye otros proyectos de la cuenta. La consulta de solo lectura a Budgets encontró siete presupuestos existentes: los dos generales ya superan USD 5 de gasto real mensual, de modo que no sirven como aviso temprano para este proyecto. Quedan por observar tamaños y volumen reales, cuotas disponibles y cobertura de las etiquetas de costo. El bootstrap `CDKToolkit` ya existe en `us-east-1` (versión 31), así que esta propuesta no incluye `cdk bootstrap`.

Ya pasaron 51 pruebas Python con clientes falsos, 9 pruebas CDK, síntesis local de dos y tres stacks con identidades ficticias y auditorías de dependencias sin vulnerabilidades conocidas. `scripts/check-aws-local.ps1` confirmó la cuenta/región/principal en este PC. La primera síntesis sin correo omite el presupuesto; la plantilla con correo contiene el filtro de proyecto. No se probó ningún permiso de recurso real porque los recursos no existen.

## Secuencia posterior a una aprobación explícita

1. Obtener aprobación expresa para crear sólo `aji-shared-dev` y `aji-alec-dev` en `us-east-1`, con sus IAM, tablas, bucket, Lambdas, alarmas y programaciones desactivadas. El costo recurrente mínimo incluye las dos alarmas (~USD 0.20/mes antes de cuotas); el escenario activo ilustrativo es USD 0.69/mes. No se incluye el presupuesto propio en esta primera creación.
2. Revisar la plantilla final y las diferencias de CloudFormation antes de aplicar; detenerse si aparece una sustitución, recurso inesperado o gasto fuera del alcance aprobado. `cdk diff` con change set puede escribir en AWS, por lo que se ejecutará sólo dentro de la aprobación del despliegue.
3. Desplegar sólo esos dos stacks, todavía apagados. Registrar outputs de rol y bucket en `private/local-aws.json`, no en Git. Probar acceso permitido y denegado con el rol de Alec y observar gasto real.
4. Cuando `Project` aparezca en Billing, solicitar aprobación expresa para activarla como etiqueta de asignación de costos. AWS indica que puede tardar hasta 24 horas en aparecer y hasta 24 horas más en activarse. Tras verificarla, solicitar aprobación para actualizar shared con `aji-project-dev` y los avisos al correo confirmado. Revisar también costos generales porque el filtro no incluye cargos sin etiqueta.
5. Solicitar autorización separada para activar fuentes, collector, publicador y automatización nativa de las 09:00. Solicitar otra autorización específica para cualquier postulación real.

El [runbook](runbooks/operations.md) contiene el apagado operativo. El [registro de progreso](progress.md) contiene los bloqueos vigentes y el handoff posterior al segundo equipo.
