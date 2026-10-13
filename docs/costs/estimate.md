# Estimación preliminar de costos AWS

Fecha: 2026-10-13. Estado: **escenario de planeación, no cotización ni aprobación de gasto**. Región ilustrativa: `us-east-1`; la región final y el uso compartido de cuotas gratuitas siguen pendientes. No hay recursos desplegados por este repositorio.

## Volumen ilustrativo mensual

- Primer equipo: 30 ejecuciones del collector y 30 del publicador de Alec, cada una de hasta 60 segundos y 256 MB; máximo 10 fuentes activas y 1,000 vacantes por ejecución.
- 30,000 escrituras de vacantes de 4 KB en tabla base y una copia de 4 KB en el índice `collection-run-index`; 50,000 lecturas eventuales de 4 KB en total.
- 0.5 GB promedio en la tabla, 0.5 GB en el índice y 0.5 GB en S3; 3,000 PUT y 10,000 GET S3.
- 0.1 GB de logs ingeridos y dos alarmas estándar de CloudWatch, una por Lambda.
- Sin NAT, EC2, RDS, servicios permanentes, APIs de pago externas ni transferencias significativas entre regiones.

La tabla usa tarifas públicas como **suposiciones de cálculo** y omite descuentos, créditos y Free Tier salvo Scheduler. Se debe cargar el volumen real en [AWS Pricing Calculator](https://calculator.aws/) cuando se confirme la región. Las dimensiones de lectura/escritura y tarifas de ejemplo se basan en la [página de DynamoDB](https://aws.amazon.com/dynamodb/pricing/); el almacenamiento incluye sobrecarga por elemento, por lo que 0.5 GB es una hipótesis de facturación, no una conversión exacta del JSON.

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
| **Subtotal modelado** | Redondeado, primer equipo | **0.70** |

Las referencias de tarifas y cuotas son: [S3](https://aws.amazon.com/s3/pricing/), [Lambda](https://aws.amazon.com/lambda/pricing/), [EventBridge Scheduler](https://aws.amazon.com/eventbridge/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) y [AWS Budgets](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/). [AWS documenta que un índice GSI con proyección `ALL` duplica los atributos y añade escrituras y almacenamiento](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html). El precio S3 Standard ilustrativo y las solicitudes deben confirmarse en Calculator para la región elegida.

## Límites de la estimación

El subtotal incluye **un** publicador pero no el segundo candidato, tamaños reales de descripciones/documentos, tráfico saliente, costos de bootstrap CDK, impuestos, otras cargas de la cuenta ni uso que exceda cuotas gratuitas. La proyección `ALL` puede superar los 4 KB supuestos y elevar escrituras y almacenamiento. Tampoco cubre electricidad, Codex ni APIs externas. El objetivo de menos de USD 5/mes no está demostrado para producción. El presupuesto CDK de USD 5 se configura para **toda la cuenta**, con avisos a USD 3 y 5, porque una alerta filtrada por etiqueta puede omitir cargos mientras `Project` no esté activada como etiqueta de asignación de costos. Eso puede incluir gastos ajenos al proyecto; se revisará el presupuesto existente de la cuenta antes de desplegar. [AWS explica que las etiquetas requieren activación y pueden tardar en aparecer](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html).

Las alertas de AWS Budgets no detienen servicios automáticamente. El kill switch operativo será deshabilitar ambos Scheduler y mantener `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`; luego revisar funciones, almacenamiento y costos reales. La concurrencia Lambda está limitada a 1 por función, el timeout a 60 segundos, CloudWatch a 7 días y los lotes S3 de `batches/` a 30 días. El TTL DynamoDB sólo elimina elementos que reciban `expires_at`; no constituye una política de borrado de todo dato privado.

## Antes de aprobar un despliegue

1. Confirmar región y residencia, fuentes, volumen real y cuota gratuita disponible de la cuenta.
2. Completar Calculator por servicio y anexar su enlace/exportación revisable.
3. Confirmar destinatario de alertas, presupuestos preexistentes y alcance de los avisos de cuenta completa.
4. Revisar límites de fuentes/solicitudes y el costo del publicador de lotes cuando exista.
5. Pedir aprobación explícita para stacks, región, presupuesto, IAM y gasto esperable. Ninguno de esos cambios se ejecuta desde esta estimación.
