# AWS Job Intelligence

Prototipo local de descubrimiento de vacantes y preparación controlada de candidaturas para dos usuarios. La especificación principal es el plan maestro privado de Drive del 12 de octubre de 2026. La copia local está en `private/specification/` y se excluye de Git para proteger referencias privadas.

## Estado

Fase 0 auditada y prototipo local de Fases 1–3 probado con datos inventados. El CDK sólo se sintetizó localmente y deja desactivados Scheduler y Lambda. **No hay infraestructura desplegada por este repositorio ni postulaciones enviadas.** Consultar [progreso](docs/progress.md), [auditoría](docs/setup/environment-audit.md), [plan](plan/feature-local-mvp-1.md) y [costos](docs/costs/estimate.md).

## Estructura

- `src/aji/`: contratos, adaptadores ATS, normalización, deduplicación, scoring, lotes y paquete de revisión.
- `schemas/`: contratos JSON de vacante, lote y perfil privado.
- `tests/`: fixtures y pruebas sin AWS ni portales reales.
- `examples/`: demostración completamente ficticia y sin llamadas externas.
- `config/`: ejemplos sin preferencias ni identificadores reales.
- `docs/`: arquitectura, seguridad, costos y operación.
- `infra/`: CDK de desarrollo y aserciones sobre las plantillas sintetizadas.
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
npm run synth -- -c account=111111111111 -c region=us-east-1 -c alecPrincipalArn=arn:aws:iam::111111111111:role/example-alec -c hectorPrincipalArn=arn:aws:iam::111111111111:role/example-hector -c budgetEmail=alerts@example.invalid --quiet
```

Demostración local inventada, que produce un paquete bajo `applications/` (ignorado por Git):

```powershell
cd ..
.\.venv\Scripts\python.exe examples/run_fictional_demo.py
```

La demo simula una verificación de elegibilidad sólo para el fixture. No establece elegibilidad de ninguna oferta real. El plan de la futura automatización está en [codex/daily-run.md](codex/daily-run.md).

## Control de cambios externos

La cuenta AWS detectada usa un perfil de administrador con clave permanente. No se usará para automatizaciones. Los cambios de IAM, el despliegue, cualquier costo nuevo y las postulaciones reales requieren aprobación explícita del usuario. La implementación actual no tiene cliente de envío a portales.
