# AWS Job Intelligence

Prototipo local de descubrimiento de vacantes y preparación controlada de candidaturas para dos usuarios. La especificación principal es el plan maestro privado de Drive del 12 de octubre de 2026. La copia local está en `private/specification/` y se excluye de Git para proteger referencias privadas.

## Estado

Fase 0 auditada y prototipo local de Fases 1–3 probado con datos inventados. El repositorio está en [GitHub privado](https://github.com/LynxPardelle/aws-job-intelligence). Con aprobación expresa se desplegaron `aji-shared-dev` y `aji-alec-dev` en `us-east-1`, se activó `Project` para asignación de costos y se creó el presupuesto filtrado `aji-project-dev` de USD 5/mes con avisos a USD 3/5. El publicador de Alec ya tiene el contrato de lote v1.1. Una prueba AWS con una vacante ficticia validó lectura, checksum y lock diario mediante el rol de Alec. Ambos Scheduler están `DISABLED` y las Lambdas tienen sus flags de ejecución en `false`; el segundo equipo queda pendiente. **No se han enviado postulaciones.** Consultar [progreso](docs/progress.md), [revisión de activación](docs/activation-review.md), [resultado del despliegue](docs/deployment-review.md), [auditoría](docs/setup/environment-audit.md), [plan](plan/feature-local-mvp-1.md) y [costos](docs/costs/estimate.md).

## Estructura

- `src/aji/`: contratos, adaptadores ATS, normalización, deduplicación, scoring, publicador privado, pull de lotes y paquete de revisión.
- `schemas/`: contratos JSON de vacante, lote y perfil privado.
- `tests/`: fixtures y pruebas sin AWS ni portales reales.
- `examples/`: demostración completamente ficticia y sin llamadas externas.
- `config/`: ejemplos sin preferencias ni identificadores reales; la Lambda lee JSON privado en `config/search-policy.json` del bucket de Alec.
- `docs/`: arquitectura, seguridad, costos y operación.
- `infra/`: CDK de desarrollo y aserciones sobre las plantillas sintetizadas; shared+Alec primero, Héctor opcional.
- `codex/`: diseño de la futura corrida de las 09:00; aún sin automatización creada.

## Pruebas locales

Requiere Python 3.11 o posterior. Desde la raíz en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m coverage run --source=src/aji -m unittest discover -s tests
.\.venv\Scripts\python.exe -m coverage report -m
```

`reportlab` genera el PDF, `pypdf` comprueba que contiene los hechos verificados y `tzdata` aporta `America/Mexico_City` en Windows. No es necesario configurar AWS para estas pruebas.

Para sintetizar las plantillas con identidades **ficticias**, sin contactar AWS:

```powershell
cd infra
$env:NODE_OPTIONS='--use-system-ca'
npm ci
npm test
npm run synth -- -c account=111111111111 -c region=us-east-1 -c alecPrincipalArn=arn:aws:iam::111111111111:user/example-admin --quiet
```

El ejemplo usa una cuenta y un principal **ficticios**; omite el presupuesto para mostrar la primera síntesis. La actualización posterior aprobada pasó el contexto privado `budgetEmail` y creó `aji-project-dev` filtrado por `Project`, ya activa como etiqueta de asignación de costos. El correo confirmado sólo está en `private/local-aws.json`. Más adelante `hectorPrincipalArn` añadirá el tercer stack. Antes de cada operación AWS real, `powershell -File scripts/check-aws-local.ps1` verifica la identidad `default` frente a una configuración privada ignorada. Véanse [ADR-002](docs/architecture/adr-002-first-pc-admin.md) y el [resultado del despliegue](docs/deployment-review.md).

El script `scripts/run-alec-pull.py` está listo para el primer equipo. Los outputs `alec_role_arn` y `alec_bucket` están en `private/local-aws.json`, ignorado por Git. Instalar `requirements-aws.txt` habilita Boto3 local. Sin `--claim`, el script sólo inspecciona el lote; con `--claim` adquiere el lock en DynamoDB y guarda un resumen privado en `applications/alec/` sólo si hay un lote READY. La prueba AWS del 2026-10-14 devolvió `READY` en vista previa y primer claim, y `ALREADY_PROCESSED` en el segundo. El lote fue ficticio y no representa una búsqueda real.

Demostración local inventada, que produce un paquete bajo `applications/` (ignorado por Git):

```powershell
cd ..
.\.venv\Scripts\python.exe examples/run_fictional_demo.py
```

La demo simula una verificación de elegibilidad sólo para el fixture. No establece elegibilidad de ninguna oferta real. El plan de la futura automatización está en [codex/daily-run.md](codex/daily-run.md).

## Control de cambios externos

El usuario autorizó usar en este equipo el perfil `default` de administrador existente; su clave no se copia al repositorio. La tarea diaria futura asumirá un rol específico de Alec desde ese perfil. La actualización del publicador y el lote ficticio en AWS se ejecutaron con la autorización del 2026-10-14. La activación diaria requiere fuentes y política de Alec revisadas; los cambios de IAM, nuevos gastos y cualquier postulación real requieren aprobación expresa sobre su alcance. La implementación actual no tiene cliente de envío a portales.
