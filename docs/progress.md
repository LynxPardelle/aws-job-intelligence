# Registro de avance

Actualizado: 2026-10-13. Especificación principal: plan maestro v3 leído del Drive del titular, copia privada en `private/specification/` excluida de Git. Este archivo resume el estado para revisión desde Codex Remote. **No se desplegó AWS, no se modificó IAM, no se activó ninguna programación y no se envió ninguna postulación.** El usuario autorizó utilizar el perfil administrador existente de este PC y pospuso el segundo equipo.

## Avances verificables

| Fecha | Área | Resultado | Evidencia local |
| --- | --- | --- | --- |
| 2026-10-13 | Fase 0 | Equipo, CLI, AWS, seguridad y estado de Codex Desktop auditados con AWS de solo lectura | `docs/setup/environment-audit.md` |
| 2026-10-13 | Repositorio | Git `main`, `AGENTS.md`, archivos privados ignorados, plan y ADR creados | `AGENTS.md`, `plan/feature-local-mvp-1.md`, `docs/architecture/adr-001-isolation.md` |
| 2026-10-13 | Fase 1 local | Greenhouse, Lever y Ashby con fixtures; normalización, dedupe, filtros, score 30/25/20/15/10 y contratos JSON | `src/aji/`, `schemas/`, `tests/` |
| 2026-10-13 | Fase 2 local | CDK v2 sintetiza shared+Alec para el primer PC y permite añadir Héctor después; collector y publicador de 08:30 con programación desactivada; recursos privados separados | `infra/`, 8 pruebas CDK, `cdk synth` local |
| 2026-10-13 | Fase 3 simulada | READY/frescura/checksum/lock local, perfil ficticio aprobado, paquete PDF y resumen sin envío | `examples/run_fictional_demo.py`, `applications/fictional/` (ignorado), `codex/daily-run.md` |
| 2026-10-13 | Costos/operación | Escenario de USD 0.70/mes para el primer PC **ilustrativo**, con índice y publicador; alertas USD 3/5 para toda la cuenta | `docs/costs/estimate.md`, `docs/runbooks/operations.md` |
| 2026-10-13 | Primer equipo | Perfil AWS `default` comprobado por STS y preflight local; CDK puede sintetizar sólo shared+Alec, con Héctor opcional | `scripts/check-aws-local.ps1`, `docs/architecture/adr-002-first-pc-admin.md` |
| 2026-10-13 | Flujo diario preparado | Marcador COMPLETE de recolección, índice por corrida, lote privado READY/FAILED, política estricta por candidato, pull y lock condicional con clientes simulados | `src/aji/aws_batch_io.py`, `src/aji/publisher_handler.py`, `src/aji/daily_pull.py`, `scripts/run-alec-pull.py` |

## Pruebas y auditorías

- `python -m unittest discover -s tests -p "test_*.py" -q` desde `.venv`: **51 pruebas aprobadas**; sólo fixtures, clientes falsos y archivos temporales.
- `coverage run --source=src/aji -m unittest discover -s tests -p "test_*.py"`: **89% de cobertura de líneas** (633/710); la cobertura mide código local, no permisos ni comportamiento real de AWS.
- `npm test` en `infra/`: **8 pruebas CDK aprobadas**, entre ellas identidad separada, roles de acceso y publicador limitados, cifrado, horarios desactivados y ausencia de NAT/EC2/RDS/ECS/EKS/API Gateway/Bedrock.
- `npm run synth ... --quiet` con cuenta/principal/correo ficticios: **2 stacks sintetizados** para el primer PC (shared+Alec), con roles, bucket, tablas, índice, Lambdas y alarmas. Sin despliegue.
- `scripts/check-aws-local.ps1`: pasó con perfil `default`, cuenta terminada en `4577` y `us-east-1`; configuración con identificadores en `private/local-aws.json`, ignorada por Git.
- Demo ficticia: PDF de una página, texto extraíble, render revisado visualmente; `submission-record.json` ausente. El resumen marca 0 postulaciones confirmadas.
- `npm audit --audit-level=high`: **0 vulnerabilidades** con CA del sistema. `pip-audit` para `requirements-dev.txt` y el nuevo `requirements-aws.txt`: **0 vulnerabilidades conocidas**; TLS validado con el almacén de Windows.

## Bloqueos que requieren decisión o participación humana

| ID | Asunto | Impacto | Acción necesaria |
| --- | --- | --- | --- |
| B-02 | Segundo PC, titular de Héctor y su visibilidad en Codex Remote no verificados | Alcance de Héctor pospuesto por instrucción del usuario | Handoff posterior, tras terminar AWS y este PC; ver `docs/runbooks/second-pc-handoff.md` |
| B-03 | Región `us-east-1` sólo propuesta; residencia no confirmada | Impide fijar despliegue final | Confirmar región y restricciones de datos |
| B-04 | CVs reales sin reconciliación ni aprobación de cada titular | No se preparan paquetes reales | Crear perfiles privados con evidencia y consentimiento de reutilización |
| B-05 | Empresas, feeds, términos y políticas privadas aún sin validar | Collector permanece desactivado y sin fuentes reales | Curar catálogo y criterios separados por candidato |
| B-06 | El objetivo AWS < USD 5/mes aún no está validado con volumen, región y uso real de cuenta | No hay presupuesto operativo garantizado | Completar AWS Pricing Calculator, confirmar correo de alertas y presupuestos existentes |
| B-07 | La sigla “CS” aún requiere definición del usuario | No se atribuye una configuración a un producto equivocado | Confirmar si significa Codex Desktop/CLI u otro sistema |

## Trabajo técnico todavía pendiente

- Los componentes de publicador, pull y lock persistente están implementados y probados con clientes falsos; falta validación contra AWS después de aprobar despliegue, rol, bucket y política privada real. El script de Alec exige los outputs de CloudFormation en `private/local-aws.json`.
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
| D-05 | 2026-10-13 | Presupuesto de aviso para toda la cuenta, no filtrado por etiqueta | La etiqueta de costos requiere activación y podría dejar cargos sin alerta inicial |
| D-06 | 2026-10-13 | Datos IANA `tzdata` fijados para Windows | Falla real hallada en un entorno virtual limpio |
| D-07 | 2026-10-13 | Volver a comprobar consentimiento al pasar a SUBMITTED | Puede revocarse después de autorizar y antes de enviar |
| D-08 | 2026-10-13 | Usar el perfil administrador `default` de este PC como origen AWS autorizado, sin duplicar claves | Instrucción directa del usuario; ver ADR-002. Las aprobaciones de cambios remotos continúan |
| D-09 | 2026-10-13 | Preparar shared+Alec primero y dejar Héctor opcional en CDK | El segundo equipo se configurará después mediante handoff |
| D-10 | 2026-10-13 | Programar el publicador de Alec a las 08:30, desactivado junto con collector | Da margen para la recolección de 08:00 y exige marcador COMPLETE antes de READY |
| D-11 | 2026-10-13 | Rechazar políticas JSON con filtros desconocidos o modo de envío distinto de PREPARE | Evita ignorar preferencias o habilitar un envío por configuración |

## Próxima revisión

Revisar este registro y el [plan detallado](../plan/feature-local-mvp-1.md). La siguiente aprobación solicitada será para una propuesta concreta de identidades, región, costos y stacks; ninguna aprobación de despliegue o postulación se presume a partir de las pruebas locales.
