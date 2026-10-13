# Propuesta de despliegue: primer equipo

Estado: **para revisión; no aprobada ni ejecutada**. Fecha: 2026-10-13. Especificación principal: copia privada del plan maestro v3 en `private/specification/`. El segundo equipo y el stack de Héctor quedan fuera de esta propuesta.

## Alcance exacto

- Cuenta verificada por STS terminada en `4577`, perfil local `default` y usuario administrador autorizado en este PC. La clave existente permanece en el almacén local de AWS CLI; ninguna clave se copiará al repositorio.
- Región propuesta `us-east-1`, **pendiente de confirmación de residencia de datos**.
- Stacks `aji-shared-dev` y `aji-alec-dev` solamente. El primero crea tabla pública DynamoDB on-demand con GSI `collection-run-index`, Lambda collector, Scheduler a las 08:00 `America/Mexico_City`, log de 7 días, alarma de error y AWS Budget de cuenta completa con avisos USD 3/5. El segundo crea bucket S3 privado de Alec, tabla de estado privada, rol `aji-alec-access-dev`, Lambda publicador, Scheduler a las 08:30, log de 7 días y alarma de error.
- Destinatario del presupuesto: **pendiente de confirmar**. El contexto CDK exige una dirección explícita y no la guarda en Git. Los avisos de cuenta completa pueden incluir gastos ajenos al proyecto.
- Primer despliegue con ambos Scheduler `DISABLED` y variables `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false`; no habrá recolección programada ni publicación hasta una activación posterior aprobada. Las fuentes reales y la política JSON privada de Alec aún no están cargadas.
- No se modifica ni crea infraestructura de Héctor, automatización de Codex Desktop, acceso al segundo PC, datos profesionales reales ni postulaciones.

## IAM y datos

El perfil administrador crea los stacks sólo tras aprobación. El rol diario de Alec confía en el usuario actual y se asume mediante STS en `scripts/run-alec-pull.py`; su política puede leer lotes de **su** bucket, consultar vacantes públicas y escribir su estado privado, pero no sobrescribir manifiestos del publicador. El publicador tiene acceso de lectura al marcador y al índice público, lectura de `config/search-policy.json` de Alec y escritura sólo bajo `batches/*` en el bucket de Alec. El administrador conserva acceso total por su política existente; las pruebas de roles no demuestran aislamiento frente al administrador.

Los buckets usan Block Public Access, S3 managed encryption y HTTPS. DynamoDB usa cifrado administrado por AWS, tablas separadas y TTL para elementos que incluyen `expires_at`. `batches/*` caduca por lifecycle a 30 días. No se suben CVs, perfiles ni correos completos en esta etapa.

## Costo y comprobaciones

El [modelo ilustrativo](costs/estimate.md) para este primer equipo es **USD 0.70/mes** bajo volumen bajo y los tamaños supuestos, más cualquier cargo de la cuenta o diferencia real. No es límite de gasto. Faltan región final, cuota gratuita restante, tamaños reales de las ofertas, costos existentes de la cuenta y una cotización guardada de AWS Pricing Calculator. Esos datos se revisarán antes del despliegue.

Ya pasaron 51 pruebas Python con clientes falsos, 8 aserciones CDK, síntesis local de dos y tres stacks con identidades ficticias y auditorías de dependencias sin vulnerabilidades conocidas. `scripts/check-aws-local.ps1` confirmó la cuenta/región/principal en este PC. No se probó ningún permiso de recurso real porque los recursos no existen.

## Secuencia posterior a una aprobación explícita

1. Confirmar región, residencia, correo de alertas y cotización Calculator; registrar la decisión aquí y en `docs/progress.md`.
2. Revisar `cdk diff` y recursos IAM/budget/alarma exactos; detenerse si aparece una sustitución, recurso inesperado o gasto fuera del alcance aprobado.
3. Desplegar sólo `aji-shared-dev` y `aji-alec-dev`, todavía apagados. Registrar outputs de rol y bucket en `private/local-aws.json`, no en Git.
4. Probar acceso permitido y denegado con el rol de Alec. Probar vista previa del pull y, con lote de prueba aprobado, el lock. Observar alarmas/costos.
5. Solicitar autorización separada para activar fuentes, collector, publicador y automatización nativa de las 09:00. Solicitar otra autorización específica para cualquier postulación real.

El [runbook](runbooks/operations.md) contiene el apagado operativo. El [registro de progreso](progress.md) contiene los bloqueos vigentes y el handoff posterior al segundo equipo.
