# AWS Job Intelligence

Prototipo local de descubrimiento de vacantes y preparación controlada de candidaturas para dos usuarios. La especificación principal es el plan maestro privado de Drive del 12 de octubre de 2026. La copia local está en `private/specification/` y se excluye de Git para proteger referencias privadas.

## Estado

Fase 0 auditada y prototipo local de Fases 1–3 probado con datos inventados. El código está en [GitHub público](https://github.com/LynxPardelle/aws-job-intelligence); CVs, preferencias y credenciales permanecen fuera de Git. Con aprobación expresa se desplegaron `aji-shared-dev` y `aji-alec-dev` en `us-east-1`, se activó `Project` para asignación de costos y se creó el presupuesto filtrado `aji-project-dev` de USD 5/mes con avisos a USD 3/5. Desde el 2026-10-18 los Scheduler de recolección y publicación están `ENABLED` a las 08:00/08:30, y la tarea de Codex de Alec está activa a las 09:00. El piloto manual encontró 36 vacantes y publicó diez para revisión; no hubo shortlist, CV ni postulación. La primera ejecución programada y su visibilidad en Remote quedan por comprobar. El segundo equipo permanece pendiente. Consultar la [guía de uso del primer PC](docs/runbooks/first-pc-user-guide.md), [progreso](docs/progress.md), [revisión de activación](docs/activation-review.md), [resultado del despliegue](docs/deployment-review.md), [auditoría](docs/setup/environment-audit.md), [plan](plan/feature-local-mvp-1.md) y [costos](docs/costs/estimate.md).

Para definir fuentes y preferencias sin exponer datos privados, usar la [guía de decisiones del primer equipo](docs/decisions/first-pc-approval-options.md). Presenta opciones por códigos y señala qué filtros funcionan hoy y cuáles requieren desarrollo adicional.

## Estructura

- `src/aji/`: contratos, adaptadores ATS, normalización, deduplicación, scoring, publicador privado, pull de lotes y paquete de revisión.
- `schemas/`: contratos JSON de vacante, lote y perfil privado.
- `tests/`: fixtures y pruebas sin AWS ni portales reales.
- `examples/`: demostración completamente ficticia y sin llamadas externas.
- `config/`: ejemplos sin preferencias ni identificadores reales; la Lambda lee JSON privado en `config/search-policy.json` del bucket de Alec.
- `docs/`: arquitectura, seguridad, costos y operación.
- `infra/`: CDK de desarrollo y aserciones sobre las plantillas sintetizadas; shared+Alec primero, Héctor opcional.
- `codex/`: instrucciones de la tarea local diaria de las 09:00, ya creada para Alec.

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

El script `scripts/run-alec-pull.py` está listo para el primer equipo. Los outputs `alec_role_arn` y `alec_bucket` están en `private/local-aws.json`, ignorado por Git. Instalar `requirements-aws.txt` habilita Boto3 local. **Usar la vista previa sin `--claim` para la operación diaria**; el claim adquiere un lock sin recuperación y no prepara CVs. El piloto AWS real devolvió `READY` con diez vacantes en revisión. La [guía](docs/runbooks/first-pc-user-guide.md) contiene el comando exacto.

`--prepare` sólo funciona con `private/alec/verified-profile.json` aprobado y ofertas `shortlist` completas; crea hasta tres paquetes locales por día, con escritura atómica y sin enviar postulaciones. Está disponible para una prueba supervisada, pero no forma parte de la tarea programada hasta revisar el primer paquete real.

Demostración local inventada, que produce un paquete bajo `applications/` (ignorado por Git):

```powershell
cd ..
.\.venv\Scripts\python.exe examples/run_fictional_demo.py
```

La demo simula una verificación de elegibilidad sólo para el fixture. No establece elegibilidad de ninguna oferta real. Las instrucciones de la tarea diaria están en [codex/daily-run.md](codex/daily-run.md).

## Control de cambios externos

El usuario autorizó usar en este equipo el perfil `default` de administrador existente; su clave no se copia al repositorio. El pull diario asume el rol específico de Alec desde ese perfil. La activación diaria de AWS y Codex se ejecutó con la autorización posterior del titular; el archivo de activación y la política personal están ignorados por Git. `AUTO_SUBMIT` sigue apagado; el código no tiene cliente de envío. Un CV real requiere perfil profesional verificado y una postulación real requiere consentimiento concreto por vacante y portal.
