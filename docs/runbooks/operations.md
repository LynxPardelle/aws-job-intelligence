# Operación y apagado seguro (borrador)

Estado: preparado localmente; requiere identidades, región y recursos reales aprobados. Este archivo describe acciones futuras, **no autoriza ejecutarlas**.

## Antes de habilitar una corrida diaria

1. Verificar con STS el rol temporal esperado de cada candidato, cuenta y región. Rechazar usuario IAM con clave permanente.
2. Probar con cada identidad que puede leer vacantes públicas y sus propios lote, estado y bucket; probar que no puede leer ni escribir los recursos del otro candidato.
3. Confirmar `AJI_ENABLED=false` y Scheduler `DISABLED` en el primer despliegue. Confirmar fuentes autorizadas y activarlas por separado, con cuota, timeout y condiciones de uso revisadas.
4. Verificar presupuesto de USD 3/5, correo de alertas, costos de cuenta existentes y Calculator. La alerta no es un límite duro.
5. En cada PC, confirmar zona `America/Mexico_City`, autenticación temporal, ruta local y acceso a Remote antes de crear la automatización nativa de las 09:00.

## Corrida normal

- AWS publica vacantes a las 08:00 cuando esté autorizado y habilitado. Una fuente que falla debe producir error visible y no un lote READY falso.
- El pull de las 09:00 valida versión, titular, estado READY, vigencia del mismo día local, IDs y checksum antes de procesar.
- Un lock condicional por candidato+lote evita reprocesamiento. `BatchLock` actual es sólo simulación en memoria; falta la operación condicional DynamoDB.
- Cada candidato usa únicamente su perfil privado aprobado. Los artefactos locales están en `applications/` fuera de Git. No se rellenan ni envían formularios en el MVP actual.
- El resumen diario distingue encontrados, shortlist, CVs, pendientes, confirmados y errores; un fallo AWS no reutiliza un lote viejo como si fuera nuevo.

## Kill switch y recuperación

Ante gasto inesperado, contenido malicioso, permisos cruzados o fallos repetidos, el operador autorizado deshabilita primero la programación `aji-collect-dev` y pone `AJI_ENABLED=false` en `aji-collector-dev`. Suspende luego las automatizaciones de cada PC y verifica que no haya ejecuciones activas. Esta secuencia requiere permisos y aprobación sobre la cuenta real; no se ejecutó en Fase 0.

Conservar logs y evidencia mínima del incidente sin PII. Revisar AWS Budgets/Cost Explorer y los recursos efectivamente desplegados. Reanudar sólo tras corregir causa, verificar pruebas negativas y contar con autorización de los titulares. Exportar datos privados antes de considerar eliminación. `cdk destroy` y cualquier borrado requieren aprobación separada; tablas y buckets usan `RETAIN`, de modo que una destrucción de stack no los elimina automáticamente.

## Retención y borrado

- Logs del collector: 7 días en la plantilla CDK.
- Vacantes públicas: atributo TTL `expires_at` fijado a 30 días por el collector; DynamoDB puede tardar en borrar.
- Objetos privados bajo `batches/`: regla S3 de 30 días.
- Estado privado, perfiles, CVs y otros objetos: sin borrado automático general. Definir política por titular, exportación y eliminación comprobable antes de producción.
