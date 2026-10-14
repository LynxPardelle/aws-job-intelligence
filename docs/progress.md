# Registro de avance

Actualizado: 2026-10-13. Especificación principal: plan maestro v3 leído del Drive del titular, copia privada en `private/specification/` excluida de Git. Este archivo resume el estado para revisión desde Codex Remote. **El usuario aprobó y se desplegaron sólo `aji-shared-dev` y `aji-alec-dev` en `us-east-1`. Ambos Scheduler siguen desactivados, ambas funciones tienen flag de ejecución `false`, no se creó el presupuesto del proyecto ni se envió ninguna postulación.** El segundo equipo permanece pospuesto.

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
| 2026-10-13 | Siguiente presupuesto preparado | `cdk diff --no-change-set` con el correo privado muestra únicamente un futuro recurso `AWS::Budgets::Budget` filtrado por `user:Project$AWSJobIntelligence`; no se aplicó | `private/budget-diff.txt` ignorado, `docs/costs/estimate.md` |

## Pruebas y auditorías

- `python -m unittest discover -s tests -p "test_*.py" -q` desde `.venv`: **53 pruebas aprobadas**; la mayoría usan fixtures y clientes falsos. Las dos nuevas pruebas verifican que el pull informa fallos de lote sin filtrar detalles AWS.
- `coverage run --source=src/aji -m unittest discover -s tests -p "test_*.py"`: **89% de cobertura de líneas** (633/710); la cobertura mide código local, no permisos ni comportamiento real de AWS.
- `npm test` en `infra/`: **9 pruebas CDK aprobadas**, entre ellas presupuesto filtrado y primera síntesis sin presupuesto, identidad separada, roles limitados, cifrado, horarios desactivados y ausencia de NAT/EC2/RDS/ECS/EKS/API Gateway/Bedrock. Se observó el fallo esperado antes de corregir cada comportamiento de presupuesto.
- `npm run synth ... --quiet` con cuenta/principal/correo ficticios: **2 stacks sintetizados** para el primer PC (shared+Alec), con roles, bucket, tablas, índice, Lambdas y alarmas. Sin despliegue.
- Síntesis local adicional con el contexto real privado de este PC y **sin** `budgetEmail`: dos stacks, cero presupuestos, dos Scheduler `DISABLED` y ambas variables de habilitación en `false`. Los identificadores privados no se registraron en Git.
- `scripts/check-aws-local.ps1`: pasó con perfil `default`, cuenta terminada en `4577` y `us-east-1`; configuración con identificadores y outputs en `private/local-aws.json`, ignorada por Git.
- Integración AWS autorizada: ambos stacks `CREATE_COMPLETE`; lectura permitida y operaciones no autorizadas denegadas desde la sesión asumida de Alec. No se escribieron datos de prueba, se invocaron Lambdas ni se activaron programaciones.
- Demo ficticia: PDF de una página, texto extraíble, render revisado visualmente; `submission-record.json` ausente. El resumen marca 0 postulaciones confirmadas.
- `npm audit --audit-level=high`: **0 vulnerabilidades** con CA del sistema. `pip-audit` para `requirements-dev.txt` y el nuevo `requirements-aws.txt`: **0 vulnerabilidades conocidas**; TLS validado con el almacén de Windows.

## Bloqueos que requieren decisión o participación humana

| ID | Asunto | Impacto | Acción necesaria |
| --- | --- | --- | --- |
| B-02 | Segundo PC, titular de Héctor y su visibilidad en Codex Remote no verificados | Alcance de Héctor pospuesto por instrucción del usuario | Handoff posterior, tras terminar AWS y este PC; ver `docs/runbooks/second-pc-handoff.md` |
| B-04 | CVs reales sin reconciliación ni aprobación de cada titular | No se preparan paquetes reales | Crear perfiles privados con evidencia y consentimiento de reutilización |
| B-05 | Empresas, feeds, términos y políticas privadas aún sin validar | Collector permanece desactivado y sin fuentes reales | Curar catálogo y criterios separados por candidato |
| B-06 | El objetivo AWS < USD 5/mes aún no está validado con volumen real ni cuotas restantes | La estimación Calculator de USD 0.69/mes es hipotética, no límite | Observar consumo real; mantener servicios desactivados hasta decisión posterior |
| B-08 | La mayoría de recursos tienen `Project`, pero la clave aún no está activada como etiqueta de asignación de costos; las plantillas de Scheduler no incluyen etiqueta | Todavía no existe presupuesto específico ni alerta USD 3/5; el filtro podría omitir cargos sin etiqueta | Esperar a que la clave aparezca en Billing; solicitar aprobación para activarla, verificar cobertura, vigilar cargos generales y luego crear el presupuesto filtrado |

## Trabajo técnico todavía pendiente

- El rol de Alec y las lecturas permitidas/denegadas se probaron contra AWS. Faltan publicación de un lote aprobado, validación del lock persistente y prueba completa del pull; las fuentes y la política privada real siguen sin cargarse. No se añadió un lote ficticio al bucket real.
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

## Próxima revisión

Revisar este registro y el [resultado del primer despliegue](deployment-review.md). El próximo cambio AWS pendiente es activar `Project` como etiqueta de asignación de costos cuando Billing la muestre y, después de verificarla, crear el presupuesto filtrado con alertas; ambos requieren aprobación expresa antes de ejecutarse. La confirmación del primer despliegue no autoriza activar Scheduler, fuentes, automatizaciones, el segundo equipo ni postulaciones.
