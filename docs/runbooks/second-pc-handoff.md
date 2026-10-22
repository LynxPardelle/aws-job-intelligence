# Handoff para Héctor: segundo equipo

**Fecha:** 2026-10-21. **Estado actualizado:** 2026-10-22. Héctor reportó auditoría local y pruebas en su equipo; no se ha verificado identidad AWS ni desplegado su stack. El enlace privado a la copia técnica del plan se entrega fuera de Git.

## Contexto comprobado

- Código público: [LynxPardelle/aws-job-intelligence](https://github.com/LynxPardelle/aws-job-intelligence). Leer `AGENTS.md`, `README.md`, `docs/architecture/adr-001-isolation.md`, `docs/automation-readiness.md` y `docs/progress.md` al comenzar.
- En `us-east-1` operan `aji-shared-dev` y `aji-alec-dev`. La recolección compartida, el publicador de Alec y su tarea local diaria están activos. **`aji-hector-dev` no se ha desplegado.** El gasto etiquetado observado el 21 de octubre fue USD 0.001 frente a avisos del proyecto de USD 3 y USD 5; los avisos no son un tope.
- El CDK puede sintetizar el stack de Héctor si recibe `hectorPrincipalArn`, pero los comandos `scripts/run-alec-pull.py`, `scripts/run-alec-daily.py` y `scripts/preview-getonbrd.py` están fijados a Alec. No ejecutarlos con datos de Héctor ni cambiar sólo una etiqueta de candidato para reutilizarlos.
- `AUTO_SUBMIT` permanece apagado. No existe cliente de portal para envíos reales. El handoff sólo habilita preparación y pruebas locales; infraestructura nueva, permisos IAM, costos adicionales y postulaciones reales requieren aprobación expresa. Cada envío exige consentimiento específico y revocable de Héctor por vacante y portal.

## Trabajo en el equipo de Héctor

1. Clonar el repositorio público y leer la copia técnica depurada de `AWS_Job_Intelligence_v3_Plan_Maestro_Codex.md` con el enlace privado compartido individualmente; Héctor debe comprobar su acceso desde su propia cuenta. La copia omite referencias personales de CV y conserva la especificación técnica. No copiar `private/`, `applications/`, claves AWS, sesiones de navegador ni perfiles de Alec desde el primer equipo.
2. Auditar Windows, Codex Desktop/Remote, Python 3.11+, Node/npm, Git, AWS CLI, región, identidad AWS, acceso a Drive y Gmail de **Héctor**. Crear su configuración privada sólo en `private/hector/` y sus salidas sólo en `applications/hector/`; verificar que Git las ignore. No asumir que el `default` administrador del equipo de Alec exista o esté autorizado aquí.
3. Ejecutar pruebas locales con fixtures antes de usar documentos reales:

   ```powershell
   git clone https://github.com/LynxPardelle/aws-job-intelligence.git
   cd aws-job-intelligence
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   .\.venv\Scripts\python.exe -m unittest discover -s tests -v
   cd infra
   npm ci
   npm test
   npm run synth -- -c account=111111111111 -c region=us-east-1 -c alecPrincipalArn=arn:aws:iam::111111111111:role/example-alec -c hectorPrincipalArn=arn:aws:iam::111111111111:role/example-hector --quiet
   ```

   Los ARN del ejemplo son ficticios y esta síntesis no despliega nada. Si hay un problema local de CA en Node, investigar antes de cambiar la verificación TLS; en el primer equipo funcionó `NODE_OPTIONS=--use-system-ca`.
4. Leer sólo los CVs más recientes de Héctor con su identidad y permiso; contrastar cada afirmación con los originales y pedirle aprobación del perfil verificado. Registrar sus preferencias de puesto, país desde el que trabajará, remoto, viajes, turnos, contratación y salario por separado. No reutilizar preferencias, régimen fiscal, umbrales ni CVs de Alec.
5. Adaptar y probar el flujo local para `candidate_id=hector`: configuración, lectura del lote, informe diario, historial, cuota de preparación y rutas privadas. Rechazar lotes de Alec y fechas antiguas. La vista Get on Board debe seguir separada del lote AWS. Gmail debe usar únicamente la cuenta de Héctor y guardar sólo datos mínimos de alertas en local.
6. Antes de proponer `aji-hector-dev`, acordar una identidad AWS propia de Héctor y preparar `cdk synth`/`cdk diff` con contexto real guardado fuera de Git. Mostrar recursos, IAM, calendario, cuota, estimación de costo, efecto sobre el presupuesto y rollback. **Detenerse antes de `cdk deploy`, de habilitar Scheduler/Lambda o de cargar una política real** y solicitar autorización expresa al titular para esos cambios.
7. Tras un despliegue aprobado, comprobar con STS acceso permitido al catálogo público y recursos propios, y acceso denegado a recursos privados de Alec; comprobar también la dirección opuesta con un rol de prueba autorizado. Validar un lote `READY` de la fecha sin `--claim` ni postulaciones. Crear después una tarea de Codex de Héctor visible en Remote, con un comando diario propio y reporte separado.

## Entregables del segundo equipo

- Auditoría y bloqueos del entorno; identidad y permisos propuestos, sin secretos en Git.
- Perfil y política de Héctor verificados por él y guardados sólo en privado.
- Pruebas locales, diff/costo/rollback para cualquier AWS nuevo y resultado de pruebas de aislamiento.
- Resumen diario propio con vacantes, salario acreditado o desconocido, preparación, gasto y errores; cero envíos hasta consentimiento específico.
- Avances y decisiones **sin PII** en `docs/progress.md` para seguimiento en Codex Remote.
