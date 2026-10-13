# Registro de avance

Actualizado: 2026-10-13. Especificación principal: plan maestro v3 leído del Drive del titular, copia privada en `private/specification/` excluida de Git. Este archivo resume el estado para revisión desde Codex Remote. **No se desplegó AWS, no se modificó IAM, no se activó ninguna programación y no se envió ninguna postulación.**

## Avances verificables

| Fecha | Área | Resultado | Evidencia local |
| --- | --- | --- | --- |
| 2026-10-13 | Fase 0 | Equipo, CLI, AWS, seguridad y estado de Codex Desktop auditados con AWS de solo lectura | `docs/setup/environment-audit.md` |
| 2026-10-13 | Repositorio | Git `main`, `AGENTS.md`, archivos privados ignorados, plan y ADR creados | `AGENTS.md`, `plan/feature-local-mvp-1.md`, `docs/architecture/adr-001-isolation.md` |
| 2026-10-13 | Fase 1 local | Greenhouse, Lever y Ashby con fixtures; normalización, dedupe, filtros, score 30/25/20/15/10 y contratos JSON | `src/aji/`, `schemas/`, `tests/` |
| 2026-10-13 | Fase 2 local | CDK v2 sintetiza `aji-shared-dev`, `aji-alec-dev`, `aji-hector-dev`; Scheduler y collector desactivados; recursos privados separados | `infra/`, 5 pruebas CDK, `cdk synth` local |
| 2026-10-13 | Fase 3 simulada | READY/frescura/checksum/lock local, perfil ficticio aprobado, paquete PDF y resumen sin envío | `examples/run_fictional_demo.py`, `applications/fictional/` (ignorado), `codex/daily-run.md` |
| 2026-10-13 | Costos/operación | Escenario de USD 0.39/mes **ilustrativo**, alertas USD 3/5 para toda la cuenta, runbook de apagado | `docs/costs/estimate.md`, `docs/runbooks/operations.md` |

## Pruebas y auditorías

- `python -m unittest discover -s tests -v` desde `.venv`: **33 pruebas aprobadas**; sólo fixtures, clientes falsos y archivos temporales.
- `coverage run --source=src/aji -m unittest discover -s tests`: **88% de cobertura de líneas** (429/486); la cobertura mide código local, no permisos ni comportamiento real de AWS.
- `npm test` en `infra/`: **5 pruebas CDK aprobadas**, entre ellas identidad separada, cifrado, horario y ausencia de NAT/EC2/RDS/ECS/EKS/API Gateway/Bedrock.
- `npm run synth ... --quiet` con cuenta/roles/correo ficticios: **3 stacks sintetizados** sin despliegue.
- Demo ficticia: PDF de una página, texto extraíble, render revisado visualmente; `submission-record.json` ausente. El resumen marca 0 postulaciones confirmadas.
- `npm audit --audit-level=high`: **0 vulnerabilidades** tras actualizar CDK lib a 2.273.0. `pip-audit -r requirements-dev.txt`: **0 vulnerabilidades conocidas** tras actualizar pypdf a 6.20.1.

## Bloqueos que requieren decisión o participación humana

| ID | Asunto | Impacto | Acción necesaria |
| --- | --- | --- | --- |
| B-01 | AWS CLI disponible con usuario IAM administrador, clave permanente y sin MFA observada | No apto para automatización segura ni despliegue con la identidad actual | Diseñar y aprobar roles temporales de mínimos privilegios; probar acceso cruzado negativo |
| B-02 | Sólo se inspeccionó este equipo; segundo PC, titular de Héctor y visibilidad real en Codex Remote no verificados | No se pueden activar dos corridas privadas a las 09:00 | Auditar con cada titular, identidad y sesión Remote propias |
| B-03 | Región `us-east-1` sólo propuesta; residencia no confirmada | Impide fijar despliegue final | Confirmar región y restricciones de datos |
| B-04 | CVs reales sin reconciliación ni aprobación de cada titular | No se preparan paquetes reales | Crear perfiles privados con evidencia y consentimiento de reutilización |
| B-05 | Empresas, feeds, términos y políticas privadas aún sin validar | Collector permanece desactivado y sin fuentes reales | Curar catálogo y criterios separados por candidato |
| B-06 | El objetivo AWS < USD 5/mes aún no está validado con volumen, región y uso real de cuenta | No hay presupuesto operativo garantizado | Completar AWS Pricing Calculator, confirmar correo de alertas y presupuestos existentes |

## Trabajo técnico todavía pendiente

- Publicador de lotes privados por candidato, cliente AWS de pull de las 09:00 y lock condicional persistente. El lock actual sólo sirve para simulaciones de proceso único.
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

## Próxima revisión

Revisar este registro y el [plan detallado](../plan/feature-local-mvp-1.md). La siguiente aprobación solicitada será para una propuesta concreta de identidades, región, costos y stacks; ninguna aprobación de despliegue o postulación se presume a partir de las pruebas locales.
