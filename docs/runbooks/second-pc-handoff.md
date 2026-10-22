# Handoff para Héctor: segundo equipo

**Fecha:** 2026-10-21. **Estado actualizado:** 2026-10-22. Héctor reportó auditoría local, pruebas e identidad AWS propia verificada por STS. Con autorización expresa del titular, el primer equipo desplegó `aji-hector-dev` en `us-east-1` y verificó sus controles. El ARN, el bucket exacto y los enlaces privados permanecen fuera de Git; se entregan en el handoff privado al titular.

## Contexto comprobado

- Código público: [LynxPardelle/aws-job-intelligence](https://github.com/LynxPardelle/aws-job-intelligence). Leer `AGENTS.md`, `README.md`, `docs/architecture/adr-001-isolation.md`, `docs/automation-readiness.md` y `docs/progress.md` al comenzar.
- En `us-east-1` operan `aji-shared-dev` y `aji-alec-dev`. La recolección compartida, el publicador de Alec y su tarea local diaria están activos. `aji-hector-dev` terminó `CREATE_COMPLETE`, con tabla y bucket privados propios, rol de acceso limitado, Lambda con `AJI_PUBLISH_ENABLED=false` y Scheduler `DISABLED`. El gasto etiquetado observado el 22 de octubre fue USD 0.002 frente a avisos del proyecto de USD 3 y USD 5; el dato puede demorarse y los avisos no son un tope.
- El CDK puede sintetizar el stack de Héctor si recibe `hectorPrincipalArn`, pero los comandos `scripts/run-alec-pull.py`, `scripts/run-alec-daily.py` y `scripts/preview-getonbrd.py` están fijados a Alec. No ejecutarlos con datos de Héctor ni cambiar sólo una etiqueta de candidato para reutilizarlos.
- Héctor eligió reutilizar su principal administrador existente en la misma cuenta como origen. El rol `aji-hector-access-dev` confía sólo en ese usuario. El diff previo mostró cero cambios en shared+Alec y el posterior dio cero diferencias en los tres stacks. El perfil CLI de AJI se crea únicamente en su PC, separado del de otro proyecto.
- Ese principal administrador conserva permisos amplios en la cuenta; el aislamiento cotidiano exige que el cliente asuma el rol limitado de Héctor y verifique su identidad por STS antes de leer o escribir. Si la sesión temporal vence, la corrida debe fallar de manera segura.
- `AUTO_SUBMIT` permanece apagado. No existe cliente de portal para envíos reales. La autorización amplia del titular permite continuar con la infraestructura necesaria del proyecto tras comprobar diff, costo y aislamiento; no autoriza enviar una candidatura sin consentimiento específico y revocable de Héctor por vacante y portal.

## Trabajo en el equipo de Héctor

1. Mantener actualizado el repositorio público y la copia privada del plan maestro ya recibida y comprobada por hash. La copia técnica omite referencias personales de CV y conserva la especificación técnica. No copiar `private/`, `applications/`, claves AWS, sesiones de navegador ni perfiles de Alec desde el primer equipo.
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
6. Usar sólo la identidad propia ya verificada por Héctor para el perfil local AJI, sin seleccionar el perfil de otro proyecto. Configurar un perfil separado que asuma `aji-hector-access-dev` desde su perfil fuente y comprobar con STS tanto el usuario origen como la sesión asumida. Si expira la sesión, fallar sin recurrir silenciosamente a un perfil administrativo o de otro proyecto. El rol tiene duración máxima de una hora. **El stack ya existe; no volver a desplegarlo con contextos ficticios ni desactivar los stacks vigentes.**
7. Con la sesión real del rol, comprobar acceso permitido al catálogo público y recursos propios, y denegado a recursos privados de Alec; la simulación IAM desde el primer equipo no sustituye esta prueba. Validar después un lote `READY` de la fecha sin `--claim` ni postulaciones. Por ahora no existe política personal de Héctor en su bucket y su publicador no produce lotes. Cuando su perfil y preferencias estén verificados y el cliente aislado probado, preparar el diff de activación con el contexto vigente, conservar la cuota y el presupuesto, y sólo entonces habilitar la publicación. Crear una tarea de Codex de Héctor visible en Remote con un comando diario propio y reporte separado.

## Entregables del segundo equipo

- Auditoría y bloqueos del entorno; identidad y permisos propuestos, sin secretos en Git.
- Perfil y política de Héctor verificados por él y guardados sólo en privado.
- Pruebas locales, diff/costo/rollback para cualquier AWS nuevo y resultado de pruebas de aislamiento.
- Resumen diario propio con vacantes, salario acreditado o desconocido, preparación, gasto y errores; cero envíos hasta consentimiento específico.
- Avances y decisiones **sin PII** en `docs/progress.md` para seguimiento en Codex Remote.
