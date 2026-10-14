# Auditoría de entorno — Fase 0

Fecha: 2026-10-13. Todas las acciones AWS fueron de solo lectura. No se cambiaron recursos ni configuración remota.

## Especificación y repositorio

- Se localizó el archivo solicitado en el Drive de la cuenta titular indicada, dentro de `AWS Job Intelligence - Codex`.
- Se leyó íntegro y se exportó una copia de trabajo a `private/specification/AWS_Job_Intelligence_v3_Plan_Maestro_Codex.md` (SHA-256 `ED68FAB62A6BAE655E3A2B5FCCB83FED6BDCDB0DE8885468196203BAF3F7F187`).
- El directorio de trabajo estaba vacío y sin Git; se inicializó `main` localmente.

## Equipo y dependencias

| Componente | Resultado |
| --- | --- |
| Sistema | Windows 10 IoT Enterprise LTSC, compilación 19044 |
| Git | 2.55.0.windows.5 |
| Node.js / npm | 24.21.0 / 11.19.0 |
| Python / pip | 3.13.15 / 26.2.1 |
| AWS CLI | 2.36.30 |
| Codex CLI | 0.158.0-alpha.2.1 |
| CDK CLI / pytest / Docker | No encontrados como comandos globales |

La versión binaria de Codex Desktop no pudo establecerse mediante el registro de aplicaciones; `Get-AppxPackage` no funciona en este entorno. El CLI sí está operativo. No se encontró un directorio local con automatizaciones configuradas bajo `.codex/automations`; esto no demuestra que no existan automatizaciones en otras superficies.

Se instaló un entorno virtual **sólo local** con `requirements-dev.txt`: ReportLab 4.4.9, pypdf 6.20.1 y tzdata 2026.5; el cliente local opcional añade Boto3 1.43.112 mediante `requirements-aws.txt`. En Windows, `zoneinfo` requiere los datos IANA de `tzdata` para validar `America/Mexico_City`; una instalación limpia sin esa dependencia falló y se corrigió. El CDK CLI se usa desde `infra/node_modules`, no globalmente. Dependencias fijadas: CDK lib 2.273.0, CDK CLI 2.1139.0, constructs 10.8.1 y TypeScript 5.9.3.

`npm audit` detectó inicialmente una versión vulnerable de `brace-expansion` embebida en CDK lib 2.272.0; al actualizar a 2.273.0, `npm audit --audit-level=high` terminó con **0 vulnerabilidades**. `pip-audit -r requirements-dev.txt` detectó avisos en pypdf 6.10.0; la versión 6.20.1 terminó con **0 vulnerabilidades conocidas**. Para las consultas HTTPS se usó el almacén de certificados de Windows (`NODE_OPTIONS=--use-system-ca` y `truststore` en la invocación de auditoría Python), sin desactivar la validación TLS. Estos resultados son una revisión puntual al 2026-10-13, no una garantía futura.

## AWS

- Perfil disponible: `default`; el perfil `aji-admin` mencionado como ejemplo en el plan no existe.
- Región configurada y confirmada por el usuario: `us-east-1`. La cuenta responde a STS; identificador terminado en `4577`.
- Principal: usuario IAM de CLI en grupo `ADMIN` con `AdministratorAccess` heredado. Hay una clave de acceso activa guardada en el archivo local de credenciales y no se observó MFA asociada a ese usuario.
- No se encontraron stacks CloudFormation, tablas DynamoDB, programaciones EventBridge Scheduler, funciones Lambda ni buckets S3 con prefijo `aji-` en las consultas realizadas. Tampoco recursos con etiqueta `Project=AWSJobIntelligence` en `us-east-1` ni presupuesto `aji-` visible.
- Esta búsqueda usa prefijo/etiqueta y no constituye un inventario exhaustivo de la cuenta. No se inspeccionaron recursos de otras regiones.
- Revisión adicional de solo lectura: `CDKToolkit` existe en `us-east-1` y terminó `UPDATE_COMPLETE` con bootstrap v31. AWS Budgets mostró siete presupuestos preexistentes; los dos generales ya superan USD 5 de gasto real mensual. No se consultó Cost Explorer API, cuya lectura tiene tarifa.

**Hallazgo de seguridad:** el perfil actual no satisface por sí solo la preferencia inicial por credenciales temporales ni el principio de mínimo privilegio del plan. **Actualización 2026-10-13:** el usuario autorizó expresamente usar este perfil administrador en esta computadora. Se conservará la clave sólo en el almacén local de AWS CLI y se propone asumir un rol de Alec para la tarea diaria. Los cambios de IAM, despliegue y gastos siguen requiriendo aprobación concreta. Véase `docs/architecture/adr-002-first-pc-admin.md`.

## Seguridad y Codex Remote

- No se imprimieron ni copiaron valores de claves, CVs o tokens al repositorio.
- Aún no se verifican el segundo PC, autenticación AWS de cada candidato, acceso privado cruzado ni visibilidad de sesiones programadas en Codex Remote.
- La automatización de las 09:00 no se crea en Fase 0; requiere ruta estable del proyecto, identidad por usuario y prueba de lectura/escritura privada.
- La sesión local tiene acceso amplio al sistema y no hay una barrera de aprobación automática para comandos; las restricciones del proyecto y la autorización humana explícita siguen siendo controles necesarios antes de AWS o postulaciones. No se verificó desde el teléfono que las sesiones de este proyecto aparezcan en Codex Remote.

## Reproducibilidad de las comprobaciones

```powershell
git --version
node --version
npm --version
python --version
aws --version
codex --version
aws configure list-profiles
aws configure get region
aws sts get-caller-identity
```

No publicar el resultado sin revisar identificadores de cuenta y principal.
