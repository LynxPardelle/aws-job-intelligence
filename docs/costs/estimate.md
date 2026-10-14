# Estimación preliminar de costos AWS

Fecha: 2026-10-13. Estado: **escenario de planeación, no cotización ni autorización para cambios posteriores**. Región confirmada por el usuario: `us-east-1`. Los stacks `aji-shared-dev` y `aji-alec-dev` ya están desplegados con Scheduler desactivados. `Project` está activa como etiqueta de asignación de costos y existe el presupuesto filtrado `aji-project-dev`; aún no hay gasto propio observado.

## Volumen ilustrativo mensual

- Primer equipo: 30 ejecuciones del collector y 30 del publicador de Alec, cada una de hasta 60 segundos y 256 MB; máximo 10 fuentes activas y 1,000 vacantes por ejecución.
- 30,000 escrituras de vacantes de 4 KB en tabla base y una copia de 4 KB en el índice `collection-run-index`; 50,000 lecturas eventuales de 4 KB en total.
- 0.5 GB promedio en la tabla, 0.5 GB en el índice y 0.5 GB en S3; 3,000 PUT y 10,000 GET S3.
- 0.1 GB de logs ingeridos y dos alarmas estándar de CloudWatch, una por Lambda.
- Sin NAT, EC2, RDS, servicios permanentes, APIs de pago externas ni transferencias significativas entre regiones.

Se cargó este escenario en [AWS Pricing Calculator, estimación pública revisable](https://calculator.aws/#/estimate?id=7cb2aa5f807fc711290c42c815d33de5ed9e11b8) el 2026-10-13. El enlace no contiene identidad de cuenta ni datos personales y caduca al año. La calculadora muestra **USD 0.69/mes** para DynamoDB (0.40), S3 (0.03), Lambda (0.01) y CloudWatch (0.25), con precios de `us-east-1`. No se imputó cuota gratuita a esos cuatro conceptos principales; la salida redondea cada servicio. DynamoDB se configuró con 1 GB total, 4 KB por elemento, 60,000 escrituras lógicas (tabla e índice) y 50,000 lecturas; S3 con 0.5 GB, 3,000 PUT/LIST y 10,000 GET; Lambda con 60 invocaciones de 60 s y 256 MB; CloudWatch con 0.1 GB de logs y dos alarmas estándar. El almacenamiento de DynamoDB incluye sobrecarga por elemento, por lo que 0.5 GB por tabla/índice es una hipótesis de facturación, no una conversión exacta del JSON.

La tabla siguiente conserva el cálculo manual transparente. Omite descuentos, créditos y Free Tier salvo Scheduler. Las dimensiones y tarifas de ejemplo se basan en la [página de DynamoDB](https://aws.amazon.com/dynamodb/pricing/).

| Concepto | Cálculo ilustrativo | USD/mes |
| --- | ---: | ---: |
| DynamoDB escrituras tabla | 30,000 × 4 WRU × $0.625/millón | 0.075 |
| DynamoDB escrituras índice | 30,000 × 4 WRU × $0.625/millón | 0.075 |
| DynamoDB lecturas eventuales | 50,000 × 0.5 RRU × $0.125/millón | 0.003 |
| DynamoDB almacenamiento tabla e índice | 1.0 GB × $0.25/GB-mes | 0.250 |
| S3 almacenamiento y solicitudes | 0.5 GB × $0.023 + 3,000 PUT × $0.005/1,000 + 10,000 GET × $0.0004/1,000 | 0.031 |
| Lambda | 60 × 60 s × 0.25 GB × $0.0000166667/GB-s, más 60 solicitudes | 0.015 |
| EventBridge Scheduler | 60 invocaciones, dentro de cuota gratuita si queda disponible | 0.000 |
| CloudWatch Logs | 0.1 GB × $0.50/GB, supuesto conservador sin cuota gratuita | 0.050 |
| Alarmas CloudWatch | 2 alarmas estándar × $0.10/mes | 0.200 |
| AWS Budgets | Una alerta de costo sin acciones | 0.000 |
| **Subtotal modelado manualmente** | Redondeado, primer equipo | **0.70** |

Las referencias de tarifas y cuotas son: [S3](https://aws.amazon.com/s3/pricing/), [Lambda](https://aws.amazon.com/lambda/pricing/), [EventBridge Scheduler](https://aws.amazon.com/eventbridge/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) y [AWS Budgets](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/). [AWS documenta que un índice GSI con proyección `ALL` duplica los atributos y añade escrituras y almacenamiento](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html). El precio S3 Standard ilustrativo y las solicitudes deben confirmarse en Calculator para la región elegida.

## Límites de la estimación

El subtotal incluye **un** publicador pero no el segundo candidato, tamaños reales de descripciones/documentos, tráfico saliente, posibles costos del bootstrap existente, impuestos, otras cargas de la cuenta ni uso que exceda cuotas gratuitas. La calculadora no modeló EventBridge Scheduler ni AWS Budgets; el cálculo manual los deja en USD 0 para este volumen y para un presupuesto sin acciones. La proyección `ALL` puede superar los 4 KB supuestos y elevar escrituras y almacenamiento. Tampoco cubre electricidad, Codex ni APIs externas. El objetivo de menos de USD 5/mes no está demostrado para producción.

Una consulta de solo lectura encontró **siete presupuestos preexistentes** en la cuenta, incluidos dos de alcance general que ya superan USD 5 de gasto real mensual por otros proyectos. Un presupuesto nuevo de cuenta completa con avisos a USD 3/5 daría una señal ya rebasada. La plantilla CDK omitió `aji-project-dev` en el primer despliegue porque no se proporcionó `budgetEmail`. Con aprobación posterior, se activó la clave `Project` para asignación de costos y se actualizó shared con el presupuesto filtrado por `user:Project$AWSJobIntelligence`. AWS confirmó su estado `Active`, USD 5/mes y avisos de gasto real a USD 3 y USD 5 al correo privado confirmado. Se verificó `Project=AWSJobIntelligence` en tablas, bucket, Lambdas, logs, alarmas y rol de Alec; las plantillas de los dos Scheduler no incluyen `Tags`, por lo que sus posibles cargos pueden quedar fuera del filtro. La atribución de gasto y la entrega de correos siguen sin observarse. Un filtro por etiqueta puede omitir cargos sin esa etiqueta, por lo que también se revisarán los costos generales de la cuenta. [AWS: activación de etiquetas](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html) y [filtros de Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-create-filters.html).

Las alertas de AWS Budgets no detienen servicios automáticamente. El kill switch operativo será deshabilitar ambos Scheduler y mantener `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`; luego revisar funciones, almacenamiento y costos reales. La concurrencia Lambda está limitada a 1 por función, el timeout a 60 segundos, CloudWatch a 7 días y los lotes S3 de `batches/` a 30 días. El TTL DynamoDB sólo elimina elementos que reciban `expires_at`; no constituye una política de borrado de todo dato privado.

## Estado y próximos cambios

1. El usuario aprobó y se completó el primer despliegue de `aji-shared-dev` y `aji-alec-dev` en `us-east-1`, con ambos Scheduler desactivados y **sin** presupuesto específico del proyecto.
2. Con aprobación posterior se activó `Project` y se actualizó `aji-shared-dev` con el presupuesto filtrado de USD 5 y avisos a USD 3/5 al correo confirmado, almacenado sólo en `private/local-aws.json`.
3. Observar costos reales y comparar con el [escenario de Calculator](https://calculator.aws/#/estimate?id=7cb2aa5f807fc711290c42c815d33de5ed9e11b8). Se usó Cost Explorer para consultar y activar la etiqueta; todavía no se consultó `GetCostAndUsage` para medir gasto atribuido.
4. Verificar con gasto real la cobertura del filtro y la entrega de avisos; revisar también el gasto general de la cuenta por posibles cargos sin etiqueta.
5. Pedir autorización separada antes de activar fuentes, programaciones o cualquier envío real. Ninguno de esos cambios se ejecuta desde esta estimación.
