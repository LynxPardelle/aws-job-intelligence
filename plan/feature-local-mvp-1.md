---
goal: MVP local verificable de AWS Job Intelligence
version: 1.0
date_created: 2026-10-13
last_updated: 2026-10-14
owner: Codex
status: 'In progress'
tags: [feature, architecture, security, aws]
---

# Introduction

![Status: In progress](https://img.shields.io/badge/status-In%20progress-yellow)

Implementar y comprobar localmente la Fase 1 y la síntesis local de Fase 2 del plan maestro v3. El documento íntegro está en `private/specification/AWS_Job_Intelligence_v3_Plan_Maestro_Codex.md`. Ninguna tarea de este plan autoriza desplegar, modificar IAM, activar costos o enviar postulaciones.

## 1. Requirements & Constraints

- **REQ-001**: Normalizar vacantes públicas Greenhouse, Lever y Ashby a `schemas/job.schema.json`, con fuente, procedencia, URLs, fechas, elegibilidad y salario anulable.
- **REQ-002**: Deduplicar por identificador de fuente y URL canónica.
- **REQ-003**: Puntuar por candidato con pesos 30/25/20/15/10 y explicar componentes y datos no confirmados.
- **REQ-004**: Separar catálogo público y recursos privados de Alec y Héctor; no compartir políticas, estados, artefactos ni credenciales.
- **REQ-005**: Preparar tres stacks CDK v2 de desarrollo y ejecutar solo síntesis local y aserciones de plantilla.
- **REQ-006**: La recolección diaria futura se expresa en `America/Mexico_City` a las 08:00; Codex Desktop consulta por separado a las 09:00.
- **SEC-001**: No usar descripción o correo como instrucciones; validar URLs HTTPS y dominio esperado antes de realizar GET.
- **SEC-002**: Mantener perfiles, CVs, tokens, paquetes de candidatura y secretos fuera de Git y logs.
- **SEC-003**: Fijar `AUTO_SUBMIT` desactivado y no implementar envío real en este paquete.
- **CON-001**: Toda integración externa se prueba con fixtures; los tests no necesitan AWS, Drive ni portales.
- **CON-002**: La cuenta AWS detectada tiene un usuario administrador con clave permanente. El usuario autorizó usar el perfil `default` en este PC el 2026-10-13; el riesgo y la excepción están en ADR-002. Para la futura tarea de Alec se propone un rol asumido.
- **CON-003**: El objetivo menor de USD 5/mes tiene un escenario revisable en AWS Pricing Calculator (USD 0.69/mes en `us-east-1`), pero requiere observación de volumen y gasto reales. La cuenta ya supera USD 5 por otros proyectos.
- **PAT-001**: Pruebas de comportamiento antes del código de producción y verificación de fallo esperado, luego paso.

## 2. Implementation Steps

### Implementation Phase 0

- GOAL-001: Auditar el entorno sin modificar AWS y crear la base del repositorio.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Leer el plan de Drive y guardar copia excluida de Git en `private/specification/`; registrar SHA-256 en `docs/setup/environment-audit.md`. | ✅ | 2026-10-13 |
| TASK-002 | Identificar versiones, perfiles AWS, principal, región y recursos del proyecto con comandos de solo lectura; guardar resultados sin secretos en `docs/setup/environment-audit.md`. | ✅ | 2026-10-13 |
| TASK-003 | Inicializar `main`, `.gitignore`, `AGENTS.md`, `README.md` y `docs/progress.md`. | ✅ | 2026-10-13 |

### Implementation Phase 1

- GOAL-002: Entregar un prototipo sin AWS que produzca vacantes verificables y shortlist segura.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-004 | Crear fixtures Greenhouse, Lever y Ashby en `tests/fixtures/` y pruebas para URL permitida, respuesta de feed y normalización en `tests/test_connectors.py`; confirmar fallo por implementación ausente. | ✅ | 2026-10-13 |
| TASK-005 | Implementar `src/aji/connectors.py`, `src/aji/normalizer.py` y `src/aji/models.py`; mapear campos ausentes a `unknown` o `null`, sin inferir elegibilidad. | ✅ | 2026-10-13 |
| TASK-006 | Crear `schemas/job.schema.json` y pruebas de contrato y deduplicación en `tests/test_job_contract.py`; implementar `src/aji/dedupe.py`. | ✅ | 2026-10-13 |
| TASK-007 | Crear pruebas de exclusiones y pesos en `tests/test_matcher.py`; implementar `src/aji/matcher.py` con razones y confianza explícitas. | ✅ | 2026-10-13 |
| TASK-008 | Ejecutar `python -m unittest discover -s tests -v`, registrar conteo y resultado en `docs/progress.md`; prohibir llamadas AWS o envío en los tests. | ✅ | 2026-10-13 |

### Implementation Phase 2

- GOAL-003: Preparar infraestructura CDK revisable sin desplegar.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-009 | Crear `infra/bin/app.ts`, `infra/lib/shared-stack.ts` e `infra/lib/candidate-stack.ts` con nombres `aji-shared-dev`, `aji-alec-dev`, `aji-hector-dev`, región configurable y etiquetas exigidas. | ✅ | 2026-10-13 |
| TASK-010 | Definir Scheduler, Lambda, DynamoDB, S3, IAM mínimo, logs 7 días y límites; validar ausencia de NAT, EC2, RDS, ECS/EKS, API Gateway y Bedrock en `infra/test/`. | ✅ | 2026-10-13 |
| TASK-011 | Ejecutar `npm ci` y `npm run synth` dentro de `infra/`; guardar resumen de plantillas y revisión de costos en `docs/costs/estimate.md`. No ejecutar `cdk deploy` ni `cdk diff` con perfil administrador sin revisión. | ✅ | 2026-10-13 |

La síntesis CDK es un **esqueleto de desarrollo**: ambos Scheduler y las Lambdas collector/publicador quedan desactivados. El primer PC usa shared+Alec; el stack de Héctor sólo se crea al suministrar su principal distinto. La activación y las pruebas AWS requieren aprobación.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-019 | Añadir marcador de recolección COMPLETE, índice por corrida y publicador privado por candidato con manifiesto FAILED previo a READY; probar fallos y aislamiento con clientes falsos. | ✅ | 2026-10-13 |
| TASK-020 | Añadir Lambda y Scheduler de publicador a las 08:30, desactivados, IAM limitado y alarma; sintetizar shared+Alec y revisar costo del índice. | ✅ | 2026-10-13 |

### Implementation Phase 3

- GOAL-004: Simular el consumidor de lotes y los artefactos de candidatura sin datos personales ni envíos.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-012 | Definir `schemas/batch.schema.json` y pruebas para READY/FAILED, frescura, checksum y lock idempotente; implementar validador local en `src/aji/batch.py`. | ✅ | 2026-10-13 |
| TASK-013 | Crear `codex/daily-run.md` y simulador con perfiles ficticios; impedir preparación sin `verified-profile.json` aprobado. | ✅ | 2026-10-13 |
| TASK-014 | Probar E2E local con lote ficticio que genere análisis y resumen sin postulación, registrar evidencia en `docs/progress.md`. | ✅ | 2026-10-13 |

El pull con Boto3 y lock condicional está codificado para Alec. Los recursos AWS existen y se probó un lote ficticio del día con el rol asumido: vista previa y primer claim `READY`, segundo claim `ALREADY_PROCESSED`. La simulación no completa la Fase 3 operativa con fuentes reales ni valida Codex Remote.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Preparar vista previa local de lote, resumen de oportunidades y script para asumir rol de Alec desde el perfil administrador, con `--claim` explícito para el lock. | ✅ | 2026-10-13 |
| TASK-022 | Tras despliegue aprobado: registrar outputs de rol/bucket en `private/local-aws.json`, probar vista previa, lock, permisos negativos y visibilidad Remote. Outputs, vista previa, lock y permisos probados; Remote pendiente. | | |

### Implementation Phase 4

- GOAL-005: Resolver decisiones humanas y activar servicios solo tras autorización concreta.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-015 | Confirmar cuenta, región/residencia, fuentes, políticas y consentimiento por candidato; auditar segundo PC y Codex Remote con su titular. | | |
| TASK-016 | Diseñar roles temporales de mínimo privilegio y validar pruebas negativas de acceso cruzado; pedir aprobación antes de crear o modificar IAM. | | |
| TASK-017 | Completar AWS Pricing Calculator, límites y runbook de apagado; pedir aprobación para desplegar nombres de stack y región exactos. | ✅ | 2026-10-13 |
| TASK-018 | Separar aprobación adicional por cualquier postulación real o modo `AUTO_SUBMIT`; exigir evidencia de consentimiento por portal y candidato. | | |
| TASK-023 | Confirmar `us-east-1` y correo privado, guardar Calculator y reemplazar presupuesto general por diseño filtrado; probar CDK sin presupuesto inicial y con filtro posterior. | ✅ | 2026-10-13 |
| TASK-024 | Con aprobación expresa, revisar cambios y desplegar sólo `aji-shared-dev` + `aji-alec-dev` apagados en `us-east-1`, sin presupuesto propio inicial. | ✅ | 2026-10-13 |
| TASK-025 | Después de que aparezca `Project` en Billing, obtener aprobación para activar esa etiqueta de asignación de costos y verificar su estado. | ✅ | 2026-10-13 |
| TASK-026 | Con aprobación expresa, actualizar shared para crear `aji-project-dev` filtrado, con avisos reales a USD 3/5 al correo privado confirmado. | ✅ | 2026-10-13 |
| TASK-027 | Verificar stacks reales, estado apagado, privacidad, tags, límites, outputs privados y permisos permitidos/denegados con el rol asumido de Alec. | ✅ | 2026-10-13 |
| TASK-028 | Mostrar error estructurado y no filtrar identificadores cuando la vista previa del pull no encuentre lote o carezca de acceso; probarlo localmente y contra AWS. | ✅ | 2026-10-13 |
| TASK-029 | Endurecer el contrato de lote v1.1 con checksum de scoring, topes de lectura privada y errores AWS seguros; probar localmente y preparar diff de código sin desplegar. | ✅ | 2026-10-14 |
| TASK-030 | Publicar `main` en un repositorio privado de GitHub y verificar que `private/` y `applications/` siguen fuera de Git. | ✅ | 2026-10-14 |
| TASK-031 | Con autorización, desplegar sólo el código del publicador de `aji-alec-dev`; volver a comprobar stacks, Scheduler y flags. | ✅ | 2026-10-14 |
| TASK-032 | Con autorización, publicar un lote AWS ficticio sin sobrescribir datos previos; leerlo y adquirir el lock con el rol de Alec. | ✅ | 2026-10-14 |
| TASK-033 | Configurar fuentes ATS permitidas y política operativa privada de Alec; preparar diff, piloto y activación diaria de este PC. | ✅ piloto | 2026-10-18 |
| TASK-034 | Verificar que la automatización nativa de Codex Desktop genera un resumen visible en Remote después de aprobar su operación diaria. | | |
| TASK-035 | Aplicar F2 a los dos CVs distintos más recientes de Alec en Drive; guardar comparación y brechas de evidencia sólo en `private/`, y publicar un catálogo de boards sin datos personales. | ✅ | 2026-10-14 |
| TASK-036 | Asignar alertas Gmail al conector de Codex por candidato; documentar identidad, datos mínimos y separación de AWS. Probar lectura y Remote cuando esté disponible/conectado. | Parcial: diseño | 2026-10-14 |
| TASK-037 | Con los criterios privados confirmados por Alec, revisar términos, completar política, probar filtros/volumen y activar el primer equipo con autorización. Caylent queda manual. | ✅ piloto | 2026-10-18 |
| TASK-038 | Auditar historial, metadatos y archivos seguidos; cambiar el repositorio a público y verificarlo por API sin publicar datos privados. | ✅ | 2026-10-18 |
| TASK-039 | Mantener un mínimo neto como condición de revisión cuando el feed sólo publica cifras sin base neta; probarlo con fixtures ficticios. | ✅ local | 2026-10-18 |
| TASK-040 | Versionar vacantes v1.1 con estados de viajes/turnos, conservar `unknown` para anuncios sin evidencia y migrar objetos públicos v1.0 previos al leerlos. | ✅ local | 2026-10-18 |
| TASK-041 | Con cuota del lote confirmada en 10 y aprobación expresa, desplegar sólo código de Collector y Publisher, comprobar diff posterior, flags y Scheduler. | ✅ | 2026-10-18 |
| TASK-042 | Evaluar automatización diaria completa, distinguir cuotas de lectura/preparación/envío y documentar requisitos de portales, Gmail, perfil y Remote. | ✅ revisión | 2026-10-18 |
| TASK-043 | Conectar pull a generación de paquetes desde perfil real aprobado; implementar estados recuperables, límites independientes y pruebas de fallos/duplicados. | Parcial: `--prepare` conectado, paquete atómico y cuota/umbral probados; falta perfil real y primera revisión | 2026-10-18 |
| TASK-044 | Crear tarea Codex Desktop de vista previa; probar la primera ejecución programada y su visibilidad en Remote. Gmail se prueba cuando esté conectado. | Parcial: tarea creada, piloto manual probado | 2026-10-18 |
| TASK-045 | Evaluar por portal un mecanismo de envío permitido, autorización específica revocable, respuestas completas, recibos e idempotencia; no activar `AUTO_SUBMIT` sin aprobación de candidaturas reales. | | |
| TASK-046 | Observar las primeras corridas de AWS 08:00/08:30 y Codex 09:00, medir costo atribuido y general, revisar fallos y calidad de las diez vacantes. | | |

## 3. Alternatives

- **ALT-001**: Un único bucket y tabla con particiones por candidato. Se descarta porque el aislamiento por recurso independiente es más fácil de auditar y probar.
- **ALT-002**: Scraping general de Indeed, OCC y LinkedIn. Se descarta por acceso, términos y estabilidad no verificados; las alertas individuales por Gmail quedan para otra fase.
- **ALT-003**: Un worker permanente que invoca Codex desde AWS. Se descarta por costo y porque el plan especifica pull nativo desde cada PC.

## 4. Dependencies

- **DEP-001**: Python 3.11+ para Fase 1; ya existe Python 3.13.15. La demo PDF usa `requirements-dev.txt` con ReportLab, pypdf y tzdata en Windows.
- **DEP-002**: Node.js y npm para CDK v2; ya existen Node 24.21.0 y npm 11.19.0.
- **DEP-003**: Dependencias CDK fijadas en `infra/package-lock.json`; instalación local mediante `npm ci` antes de síntesis.
- **DEP-004**: El perfil administrador `default` de este PC está autorizado como origen; el rol temporal de Alec está desplegado y se probó mediante STS. Cuota de lote 10, política privada y tres fuentes activas para este PC. El segundo PC permanece pendiente.
- **DEP-005**: Perfil profesional verificado y aprobado por cada titular, pendiente para CVs reales.

## 5. Files

- **FILE-001**: `src/aji/*.py` — núcleo local de contratos, conectores, normalización y scoring.
- **FILE-002**: `schemas/*.json` — contratos de intercambio versionados.
- **FILE-003**: `tests/*.py` y `tests/fixtures/*.json` — pruebas y datos inventados.
- **FILE-004**: `infra/` — CDK TypeScript y pruebas de plantilla.
- **FILE-005**: `docs/progress.md`, `docs/setup/environment-audit.md`, `docs/architecture/adr-001-isolation.md`, `docs/costs/estimate.md` — evidencia de ejecución y decisiones.
- **FILE-006**: `config/*.example.yaml` y `config/search-policy.example.json` — ejemplos sin preferencias reales.

## 6. Testing

- **TEST-001**: Fixture de cada ATS produce `job_id`, procedencia y URLs correctas; host y slug no permitidos fallan antes de GET.
- **TEST-002**: Fechas ausentes, salario ausente y elegibilidad ausente permanecen `null`/`unknown`.
- **TEST-003**: Dedupe conserva una vacante por ID externo o URL canónica.
- **TEST-004**: Scoring bloquea vacantes cerradas, no elegibles, incompatibles o sin elegibilidad confirmada; pesos suman 100.
- **TEST-005**: Síntesis CDK verifica región, horario, etiquetas, cifrado, privacidad y ausencia de recursos permanentes prohibidos.
- **TEST-006**: Lote FAILED/vencido/checksum incorrecto no produce paquete; lock evita duplicados.
- **TEST-007**: E2E ficticio no emite POST ni transición a SUBMITTED.

## 7. Risks & Assumptions

- **RISK-001**: El usuario IAM administrador actual permite más acceso del debido. Su uso como origen en este PC fue autorizado; una sesión asumida de Alec limita las operaciones ordinarias del proceso, pero el administrador puede saltarse ese límite.
- **RISK-002**: Fuentes ATS pueden cambiar sus esquemas o términos. Versionar fixtures y validar cada fuente antes de activarla.
- **RISK-003**: La ausencia de datos de salario o elegibilidad puede reducir matches; se prefiere revisión a una inferencia falsa.
- **ASSUMPTION-001**: `us-east-1` fue confirmada por el usuario como región para este primer equipo; los despliegues y la activación posteriores constan en `docs/progress.md`.
- **ASSUMPTION-002**: Los dos candidatos operarán equipos propios y aprobarán sus perfiles y políticas de forma individual.

## 8. Related Specifications / Further Reading

- Plan maestro privado v3: `private/specification/AWS_Job_Intelligence_v3_Plan_Maestro_Codex.md`.
- [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html).
- [Lever Postings API](https://github.com/lever/postings-api/blob/master/README.md).
- [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api).
- [AWS Pricing Calculator](https://calculator.aws/).
