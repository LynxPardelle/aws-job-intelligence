# Operación y apagado seguro (borrador)

Estado: `aji-shared-dev` y `aji-alec-dev` desplegados con aprobación en `us-east-1`, sin ejecución programada. La etiqueta de costos `Project` está activa y el presupuesto filtrado `aji-project-dev` tiene avisos USD 3/5 al correo privado confirmado. Este archivo describe acciones futuras; **no autoriza activar servicios ni envíos**.

## Antes de habilitar una corrida diaria

1. Verificar con STS cuenta, región y principal. En este primer PC, el usuario autorizó expresamente el perfil administrador `default` como origen; la tarea de Alec deberá asumir el rol `aji-alec-access-dev` ya desplegado. No copiar la clave. En el segundo PC se validará una identidad distinta.
2. Probar con cada identidad que puede leer vacantes públicas y sus propios lote, estado y bucket; probar que no puede leer ni escribir los recursos del otro candidato.
3. Volver a confirmar `AJI_ENABLED=false`, `AJI_PUBLISH_ENABLED=false` y ambos Scheduler `DISABLED`; así quedaron tras el primer despliegue. Cargar la política JSON aprobada del candidato en `config/search-policy.json` de su bucket privado; confirmar fuentes autorizadas y activarlas por separado, con cuota, timeout y condiciones de uso revisadas.
4. Revisar el [escenario de Calculator](../costs/estimate.md) y costos reales. La clave `Project` está activa y el presupuesto `aji-project-dev` existe con avisos USD 3/5 al correo privado confirmado; comprobar que siguen configurados antes de activar. La atribución de gasto y la entrega de avisos aún no se han observado. La alerta no es un límite duro y el filtro puede omitir cargos sin etiqueta; revisar también los presupuestos generales de la cuenta.
5. En cada PC, confirmar zona `America/Mexico_City`, autenticación temporal, ruta local y acceso a Remote antes de crear la automatización nativa de las 09:00.

## Corrida normal

- AWS recolecta vacantes a las 08:00 y el publicador intenta crear el lote privado a las 08:30, sólo cuando ambos servicios estén autorizados y habilitados. Una fuente que falla deja el marcador de recolección incompleto; el publicador deja el manifiesto FAILED y no produce un lote READY falso.
- El pull de las 09:00 valida versión, titular, estado READY, vigencia del mismo día local, IDs y checksum antes de procesar. Si el lote falta o S3 deniega su lectura, informa `BATCH_UNAVAILABLE_OR_DENIED` y sale con error; no reutiliza un lote viejo ni adquiere lock.
- Un lock condicional en la tabla privada por candidato+lote evita reprocesamiento. La operación DynamoDB existe en `CandidateBatchStore`; la vista previa de `scripts/run-alec-pull.py` no lo reclama y `--claim` sí.
- Cada candidato usa únicamente su perfil privado aprobado. Los artefactos locales están en `applications/` fuera de Git. No se rellenan ni envían formularios en el MVP actual.
- El resumen diario distingue encontrados, shortlist, CVs, pendientes, confirmados y errores; un fallo AWS no reutiliza un lote viejo como si fuera nuevo.

## Kill switch y recuperación

Ante gasto inesperado, contenido malicioso, permisos cruzados o fallos repetidos, el operador autorizado deshabilita las programaciones `aji-collect-dev` y `aji-alec-publish-dev`, y pone `AJI_ENABLED=false` y `AJI_PUBLISH_ENABLED=false` en las Lambdas respectivas. Suspende luego las automatizaciones de cada PC y verifica que no haya ejecuciones activas. Esta secuencia requiere permisos y aprobación sobre la cuenta real; no se ejecutó en Fase 0.

Conservar logs y evidencia mínima del incidente sin PII. Revisar AWS Budgets/Cost Explorer y los recursos efectivamente desplegados. Reanudar sólo tras corregir causa, verificar pruebas negativas y contar con autorización de los titulares. Exportar datos privados antes de considerar eliminación. `cdk destroy` y cualquier borrado requieren aprobación separada; tablas y buckets usan `RETAIN`, de modo que una destrucción de stack no los elimina automáticamente.

## Retención y borrado

- Logs del collector y del publicador: 7 días en la plantilla CDK.
- Vacantes públicas: atributo TTL `expires_at` fijado a 30 días por el collector; DynamoDB puede tardar en borrar.
- Objetos privados bajo `batches/`: regla S3 de 30 días.
- Estado privado, perfiles, CVs y otros objetos: sin borrado automático general. Definir política por titular, exportación y eliminación comprobable antes de producción.
