# Registro de avance

Actualizado: 2026-10-14. Especificación principal: plan maestro v3 leído del Drive del titular, copia privada en `private/specification/` excluida de Git. Este archivo resume el estado para revisión desde Codex Remote y se publica en el [repositorio privado](https://github.com/LynxPardelle/aws-job-intelligence). **Con aprobación expresa se desplegaron sólo `aji-shared-dev` y `aji-alec-dev` en `us-east-1`, se activó `Project` como etiqueta de costos, se creó `aji-project-dev` con avisos USD 3/5 y se actualizó el publicador de Alec al contrato v1.1. La prueba AWS con una vacante ficticia confirmó lectura y lock. Ambos Scheduler siguen desactivados, ambas funciones tienen flag de ejecución `false` y no se envió ninguna postulación.** El segundo equipo permanece pospuesto.

## Avances verificables

| Fecha | Área | Resultado | Evidencia local |
| --- | --- | --- | --- |
| 2026-10-13 | Fase 0 | Equipo, CLI, AWS, seguridad y estado de Codex Desktop auditados con AWS de solo lectura | `docs/setup/environment-audit.md` |
| 2026-10-13 | Repositorio | Git `main`, `AGENTS.md`, archivos privados ignorados, plan y ADR creados | `AGENTS.md`, `plan/feature-local-mvp-1.md`, `docs/architecture/adr-001-isolation.md` |
| 2026-10-13 | Fase 1 local | Greenhouse, Lever y Ashby con fixtures; normalización, dedupe, filtros, score 30/25/20/15/10 y contratos JSON | `src/aji/`, `schemas/`, `tests/` |
| 2026-10-13 | Fase 2 local | CDK v2 sintetiza shared+Alec para el primer PC y permite añadir Héctor después; collector y publicador de 08:30 con programación desactivada; recursos privados separados | `infra/`, 9 pruebas CDK, `cdk synth` local |
| 2026-10-13 | Fase 3 simulada | READY/frescura/checksum/lock local, perfil ficticio aprobado, paquete PDF y resumen sin envío | `examples/run_fictional_demo.py`, `applications/fictional/` (ignorado), `codex/daily-run.md` |
| 2026-10-13 | Costos/operación | Cálculo manual de USD 0.70/mes para el primer PC, ilustrativo, con índice y publicador | `docs/costs/estimate.md`, `docs/runbooks/operations.md` |
| 2026-10-13 | Primer equipo | Perfil AWS `default` comprobado por STS y preflight local; CDK puede sintetizar sólo shared+Alec, con Héctor opcional | `scripts/check-aws-local.ps1`, `docs/architecture/adr-002-first-pc-admin.md` |
| 2026-10-13 | Flujo diario preparado | Marcador COMPLETE de recolección, índice por corrida, lote privado READY/FAILED, política estricta por candidato, pull y lock condicional con clientes simulados | `src/aji/aws_batch_io.py`, `src/aji/publisher_handler.py`, `src/aji/daily_pull.py`, `scripts/run-alec-pull.py` |
| 2026-10-13 | Confirmaciones | “CS” era una transcripción errónea de AWS; usuario confirmó `us-east-1` y el correo de alertas, guardado sólo en archivo privado ignorado | `private/local-aws.json`, `docs/deployment-review.md` |
| 2026-10-13 | Presupuestos existentes | Siete presupuestos visibles; los dos generales ya superan USD 5 de gasto real mensual. Se descartó el aviso nuevo de cuenta completa a USD 3/5 | Consulta AWS Budgets de solo lectura; `docs/costs/estimate.md` |
| 2026-10-13 | Calculator y CDK | Estimación pública de USD 0.69/mes en `us-east-1`; presupuesto posterior filtrado por `Project`, omitido en primera síntesis. `CDKToolkit` existente v31 | [Calculator](https://calculator.aws/#/estimate?id=7cb2aa5f807fc711290c42c815d33de5ed9e11b8), `infra/`, `docs/deployment-review.md` |
| 2026-10-13 | Primer despliegue aprobado | Preflight de identidad y `cdk diff --no-change-set` comparados con la propuesta; dos stacks terminan `CREATE_COMPLETE`. Outputs del rol y bucket guardados sólo en `private/local-aws.json` | CloudFormation y `private/cdk-outputs.json` ignorado; `docs/deployment-review.md` |
| 2026-10-13 | Verificación AWS | Dos Scheduler `DISABLED`, flags Lambda `false`, tablas `ACTIVE` on-demand, bucket privado cifrado, etiquetas `Project` en tablas, bucket, Lambdas, logs, alarmas y rol de Alec; logs 7 días, concurrencia 1 y presupuesto del proyecto ausente. Las plantillas de Scheduler no incluyen etiqueta | Consultas AWS de solo lectura y plantillas; `docs/deployment-review.md` |
| 2026-10-13 | Rol y pull de Alec | STS asumió `aji-alec-access-dev`; `GetItem` público y privado permitido, `Scan` privado y `ListBucket` denegados. Sin lote del día, la vista previa devuelve error JSON seguro y código distinto de cero; no se adquirió lock | `scripts/run-alec-pull.py`, `tests/test_run_alec_pull.py` |
| 2026-10-13 | Presupuesto preparado | `cdk diff --no-change-set` con el correo privado mostró únicamente un recurso `AWS::Budgets::Budget` filtrado por `user:Project$AWSJobIntelligence` | `private/budget-diff-authorized.txt` ignorado, `docs/costs/estimate.md` |
| 2026-10-13 | Etiqueta y presupuesto autorizados | `Project` apareció `Inactive`; activación mediante API aceptada y estado verificado `Active`. `aji-shared-dev` pasó a `UPDATE_COMPLETE`; AWS Budgets confirmó límite USD 5/mes, filtro de proyecto y avisos de gasto real USD 3/5 al correo privado | Consultas de Cost Allocation Tags, CloudFormation y AWS Budgets; `docs/deployment-review.md` |
| 2026-10-14 | Endurecimiento local del lote | Manifiesto v1.1 verifica también checksum de scoring; lectura de lote S3 limitada a 32 MB y política privada a 64 KB; errores AWS del pull se resumen sin detalle remoto. Se corrigió el riesgo de aceptar una puntuación alterada | `src/aji/`, `tests/`, `schemas/batch.schema.json`; `docs/activation-review.md` |
| 2026-10-14 | Revisión de la siguiente actualización | Preflight AWS pasó; `cdk diff --no-change-set` mostró sólo dos assets de código Lambda cambiados, sin IAM, Budgets ni Scheduler. Se propone actualizar únicamente el publicador cuando exista aprobación expresa | `private/activation-diff.txt` ignorado; `docs/activation-review.md` |
| 2026-10-14 | Estado remoto de solo lectura | Shared `UPDATE_COMPLETE`, Alec `CREATE_COMPLETE`, ambos Scheduler `DISABLED`, flags Lambda `false`; Budgets informó USD 0.00 de gasto atribuido, sin prueba de cobertura o entrega de avisos | STS, CloudFormation, Scheduler, Lambda y AWS Budgets; `docs/activation-review.md` |
| 2026-10-14 | GitHub privado | Se creó `LynxPardelle/aws-job-intelligence`, visibilidad `PRIVATE`, rama `main` subida; `private/` y `applications/` permanecen ignorados | GitHub CLI, `git remote -v`, `.gitignore` |
| 2026-10-14 | Publicador v1.1 en AWS | El diff mostró sólo assets de código; `cdk deploy aji-alec-dev --exclusively` terminó en `UPDATE_COMPLETE` y el diff posterior exclusivo de Alec mostró cero diferencias; shared, Scheduler e IAM no se actualizaron | `private/alec-authorized-diff.txt`, `private/alec-authorized-deploy.log` y `private/alec-post-deploy-diff.txt` ignorados; CloudFormation |
| 2026-10-14 | Prueba integrada ficticia | Un lote v1.1 de una vacante inventada se publicó en S3 privado; vista previa y primer claim `READY`, segundo `ALREADY_PROCESSED`; lock DynamoDB presente y 0 postulaciones | `scripts/run-alec-pull.py`, S3/DynamoDB, `applications/alec/daily-summary.json` ignorado |

## Pruebas y auditorías

- `python -m unittest discover -s tests -p "test_*.py" -q` desde `.venv`: **57 pruebas aprobadas**; la mayoría usan fixtures y clientes falsos. Las nuevas pruebas verifican puntuación alterada, tamaño de objetos/política y error AWS seguro.
- La corrida de cobertura anterior al endurecimiento midió **89% de líneas** (633/710); esa cifra no se extrapola al código actualizado ni mide permisos o comportamiento real de AWS.
- `npm test` en `infra/`: **9 pruebas CDK aprobadas**, entre ellas presupuesto filtrado y primera síntesis sin presupuesto, identidad separada, roles limitados, cifrado, horarios desactivados y ausencia de NAT/EC2/RDS/ECS/EKS/API Gateway/Bedrock. Se observó el fallo esperado antes de corregir cada comportamiento de presupuesto.
- `npm run synth ... --quiet` con cuenta/principal/correo ficticios: **2 stacks sintetizados** para el primer PC (shared+Alec), con roles, bucket, tablas, índice, Lambdas y alarmas. Sin despliegue.
- Síntesis local adicional con el contexto real privado de este PC y **sin** `budgetEmail`: dos stacks, cero presupuestos, dos Scheduler `DISABLED` y ambas variables de habilitación en `false`. Los identificadores privados no se registraron en Git.
- `scripts/check-aws-local.ps1`: pasó con perfil `default`, cuenta terminada en `4577` y `us-east-1`; configuración con identificadores y outputs en `private/local-aws.json`, ignorada por Git.
- Integración AWS autorizada: shared y Alec `UPDATE_COMPLETE`; lectura permitida y operaciones no autorizadas denegadas desde la sesión asumida de Alec. Se escribieron sólo tres objetos de lote ficticio y un lock del día. No se invocaron Lambdas ni se activaron programaciones. AWS Budgets confirmó el destinatario privado y los dos umbrales, pero aún no se ha probado la entrega de un correo ni el gasto atribuido.
- Prueba AWS del 2026-10-14: 1 vacante ficticia para revisión; `READY` en vista previa y primer claim; `ALREADY_PROCESSED` en segundo claim; 0 CVs, 0 postulaciones. Los objetos tienen cifrado AES256 y regla de caducidad a 30 días; DynamoDB confirmó el lock. Se volvieron a ejecutar **57 pruebas Python** con resultado correcto.
- La demo ficticia volvió a generar un paquete local bajo `private/` con manifiesto v1.1 y ambos checksums. `npm test` volvió a pasar 9 pruebas CDK y `cdk synth` sintetizó shared+Alec con identidades ficticias y presupuesto de ejemplo.
- Demo ficticia: PDF de una página, texto extraíble, render revisado visualmente; `submission-record.json` ausente. El resumen marca 0 postulaciones confirmadas.
- `npm audit --audit-level=high`: **0 vulnerabilidades** con CA del sistema. `pip-audit` para `requirements-dev.txt` y el nuevo `requirements-aws.txt`: **0 vulnerabilidades conocidas**; TLS validado con el almacén de Windows.
- Antes de subir este registro se revisaron 66 archivos seguidos y 6 commits por valores privados exactos, patrones de claves AWS y encabezados de claves privadas: **0 coincidencias**. `private/` y `applications/` siguen ignorados. `npm test` volvió a pasar **9 pruebas CDK** y `git diff --check` no encontró errores de formato.

## Bloqueos que requieren decisión o participación humana

| ID | Asunto | Impacto | Acción necesaria |
| --- | --- | --- | --- |
| B-02 | Segundo PC, titular de Héctor y su visibilidad en Codex Remote no verificados | Alcance de Héctor pospuesto por instrucción del usuario | Handoff posterior desde el repositorio privado, con acceso del titular y auditoría de su equipo; ver `docs/runbooks/second-pc-handoff.md` |
| B-04 | CVs reales sin reconciliación ni aprobación de cada titular | No se preparan paquetes reales | Crear perfiles privados con evidencia y consentimiento de reutilización |
| B-05 | Empresas, feeds, términos y políticas privadas aún sin validar | Collector permanece desactivado y sin fuentes reales | Curar catálogo y criterios separados por candidato |
| B-06 | El objetivo AWS < USD 5/mes aún no está validado con volumen real ni cuotas restantes | La estimación Calculator de USD 0.69/mes es hipotética, no límite | Observar consumo real; mantener servicios desactivados hasta decisión posterior |
| B-09 | El presupuesto ya existe, pero la asignación de costos y la entrega de avisos no se han observado con gasto real; los Scheduler no están etiquetados | El filtro por `Project` puede omitir cargos sin etiqueta y las alertas no son un tope | Observar Budgets y gasto general durante la operación autorizada; no afirmar cobertura completa hasta tener datos |

## Trabajo técnico todavía pendiente

- El rol de Alec, el lote ficticio, el lock persistente y el pull completo se probaron contra AWS. Aún faltan fuentes y política privada real aprobadas; el lote ficticio del 2026-10-14 no representa una oportunidad real.
- La lectura local rechaza lotes o scoring modificados y limita el tamaño de los objetos. El publicador corregido ya está en AWS, pero permanece desactivado. El collector shared mantiene su código anterior hasta configurar fuentes reales.
- Generación automática de CVs reales desde el pull requiere perfil verificado y aprobado; el pull actual informa oportunidades y no prepara documentos reales.
- Pruebas de permisos cruzados sobre recursos AWS reales, y activación controlada de Scheduler/collector después de aprobación. La plantilla actual deja ambos desactivados.
- Perfiles reales aprobados, retención/borrado por titular, operación en ambos PCs, comprobación de Remote y métricas de costos observados.
- Integraciones Gmail/portales y cualquier envío pertenecen a fases posteriores con consentimiento y revisión específica.

## Decisiones

| ID | Fecha | Decisión | Motivo |
| --- | --- | --- | --- |
| D-01 | 2026-10-13 | Copia completa del plan en `private/`, fuera de Git | Contiene referencias privadas de candidatos |
| D-02 | 2026-10-13 | Núcleo local Python y CDK TypeScript con dependencias fijadas | Reproducción sin AWS; Lambda ligera para lectura pública |
| D-03 | 2026-10-13 | Elegibilidad desde México ausente = `unknown` | No inferir derecho de postulación |
| D-04 | 2026-10-13 | Conectores de lectura sólo sobre feeds ATS públicos permitidos | Los feeds no autorizan envíos |
| D-05 | 2026-10-13 | Presupuesto de aviso para toda la cuenta, no filtrado por etiqueta; **reemplazado por D-12** | La etiqueta de costos requiere activación y podría dejar cargos sin alerta inicial |
| D-06 | 2026-10-13 | Datos IANA `tzdata` fijados para Windows | Falla real hallada en un entorno virtual limpio |
| D-07 | 2026-10-13 | Volver a comprobar consentimiento al pasar a SUBMITTED | Puede revocarse después de autorizar y antes de enviar |
| D-08 | 2026-10-13 | Usar el perfil administrador `default` de este PC como origen AWS autorizado, sin duplicar claves | Instrucción directa del usuario; ver ADR-002. Las aprobaciones de cambios remotos continúan |
| D-09 | 2026-10-13 | Preparar shared+Alec primero y dejar Héctor opcional en CDK | El segundo equipo se configurará después mediante handoff |
| D-10 | 2026-10-13 | Programar el publicador de Alec a las 08:30, desactivado junto con collector | Da margen para la recolección de 08:00 y exige marcador COMPLETE antes de READY |
| D-11 | 2026-10-13 | Rechazar políticas JSON con filtros desconocidos o modo de envío distinto de PREPARE | Evita ignorar preferencias o habilitar un envío por configuración |
| D-12 | 2026-10-13 | Presupuesto `aji-project-dev` filtrado por `user:Project$AWSJobIntelligence`, sólo después de activar la etiqueta; primer despliegue sin ese presupuesto | El gasto de cuenta general ya supera USD 5 y haría inútiles los avisos a USD 3/5; activar la etiqueta requiere recursos y aprobación |
| D-13 | 2026-10-13 | Región `us-east-1` y correo de alertas confirmados; “CS” interpretado como AWS | Instrucción directa del usuario. El correo queda fuera de Git |
| D-14 | 2026-10-13 | Primer despliegue shared+Alec aprobado y ejecutado, con servicios apagados y sin presupuesto específico | Aprobación expresa del usuario al alcance de `docs/deployment-review.md`; validación posterior en AWS |
| D-15 | 2026-10-13 | Si falta el lote, el pull devuelve error JSON genérico y código distinto de cero, sin ampliar `ListBucket` | S3 puede responder `AccessDenied` si el objeto falta y el rol no puede listar; no confundirlo con éxito ni exponer identificadores |
| D-16 | 2026-10-13 | Activar la clave de costos `Project` y actualizar sólo shared con `aji-project-dev` después de comprobar que el diff añadía un único presupuesto | Aprobación expresa del usuario; AWS confirmó estado `Active`, filtro, USD 5/mes y avisos reales USD 3/5 |
| D-17 | 2026-10-14 | Elevar el contrato privado del lote a v1.1 para comprobar también `matches.json` y limitar lecturas S3; mantener AWS apagado hasta publicar el código | La versión v1.0 sólo verificaba vacantes y aceptaba una puntuación alterada. Se probó localmente antes del despliegue registrado en D-19 |
| D-18 | 2026-10-14 | Subir `main` a `LynxPardelle/aws-job-intelligence` como repositorio privado | El usuario autorizó subir el código; `private/` y `applications/` quedan excluidos de Git |
| D-19 | 2026-10-14 | Actualizar sólo `aji-alec-dev` al publicador v1.1 y probar un lote ficticio con lock | Autorización del usuario para GitHub/AWS; diff de código aislado y preflight sin lote previo; Scheduler y flags permanecen apagados |

## Próxima revisión

Revisar este registro y la [revisión de activación del primer equipo](activation-review.md). Para preparar la operación diaria faltan el catálogo de fuentes permitido y la política de búsqueda aprobada por Alec; después se presentará el diff y el costo de activar collector, publicador y automatización de las 09:00. El segundo equipo sigue a la espera del handoff; cualquier postulación real requiere autorización específica.
