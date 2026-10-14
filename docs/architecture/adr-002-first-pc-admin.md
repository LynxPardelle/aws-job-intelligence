# ADR-002: primera instalación en este equipo

Estado: aceptada por instrucción directa del usuario el 2026-10-13. Reemplaza para **este equipo** la preferencia inicial por no usar la credencial IAM permanente como origen. No autoriza despliegue, cambios IAM, gastos ni postulaciones.

## Decisión

Usar el perfil AWS `default` ya configurado en esta computadora y el usuario administrador existente para comprobaciones y, después de aprobación concreta, para gestionar los recursos de desarrollo. La clave permanece en el almacén local de AWS CLI; no se copia a Git, scripts, prompts ni archivos de despliegue.

Preparar ahora `aji-shared-dev` y `aji-alec-dev`. `aji-hector-dev` sigue disponible en CDK, pero se omite cuando no se indica `hectorPrincipalArn`. Su configuración y pruebas en el segundo equipo quedan para un handoff futuro, cuando la parte AWS de este equipo esté lista.

Para la corrida diaria futura de Alec, `scripts/run-alec-pull.py` asumirá `aji-alec-access-dev` desde `default` mediante STS y usará las credenciales temporales sólo en memoria. El rol puede leer su lote privado, pero no sobrescribir manifiestos del publicador. Esto **no impide** que quien controle el usuario administrador acceda a otros recursos. Es un límite de aislamiento aceptado para la primera instalación; las identidades de Héctor deberán validarse por separado. [AWS documenta el uso de perfiles y roles asumidos](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html).

## Controles actuales

- `scripts/check-aws-local.ps1` comprueba por STS cuenta, región y principal frente a `private/local-aws.json`, ignorado por Git. Se verificó el perfil `default` de la cuenta terminada en `4577`, región configurada `us-east-1`.
- Con aprobación expresa se desplegaron shared+Alec en `us-east-1`; ambos Scheduler están `DISABLED` y los flags `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`.
- El rol `aji-alec-access-dev` existe y se probó con una sesión STS; el script local asume ese rol. Todavía no se creó la automatización de Codex Desktop de las 09:00.
- La actualización local del contrato de lote v1.1 aún no se ha desplegado. Los próximos despliegues, la activación de servicios, los gastos adicionales y las postulaciones requieren aprobación concreta.

## Consecuencias

Se elimina el bloqueo operativo de buscar una identidad temporal nueva para **administrar este equipo**. El uso de un administrador mantiene riesgo de privilegios amplios y no prueba aislamiento frente a ese administrador. Las pruebas de permisos cruzados deben hacerse con roles de candidato cuando existan, antes de habilitar el flujo de ambos usuarios.
