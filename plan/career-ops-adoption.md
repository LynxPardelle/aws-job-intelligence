# Adopción selectiva de patrones de `career-ops`

Inicio: 2026-10-20. Referencia externa fijada en `c87e0f05a5bf3b0e7bff1f6c87fd0865191e7da7`; véase [la comparación](../docs/decisions/career-ops-benchmark-2026-10-20.md). Especificación superior: plan maestro privado v3 y `AGENTS.md`.

## Objetivo

Incorporar las ideas útiles para Alec en AJI con interfaces propias, pruebas locales y datos privados aislados. Mantener el lote diario de diez, la cuota de tres paquetes y `AUTO_SUBMIT` apagado. No copiar código externo, instalar plugins ni consultar datos de Héctor.

## Etapas y criterios de salida

| Etapa | Estado | Entrega comprobable |
| --- | --- | --- |
| 0. Línea base | Completa | 80 pruebas Python aprobadas; límites AWS, contratos y rutas privadas revisados. |
| 1. Fuentes | Completa | Salud por fuente, lector del marcador y vista local de tres categorías Get on Board probados. Código del Collector actualizado en AWS; el primer marcador nuevo se observará en la próxima corrida. |
| 2. Calidad de vacantes | Completa local | Revalidación mediante feed ATS antes de `PREPARE`; memoria SQLite privada de URLs por candidato y día. Ausencia en página parcial o error de red queda `unknown`. |
| 3. Datos de Alec | Completa local | Bitácora salarial y tracker privado con eventos, fuentes, idempotencia y estados; matriz de requisitos respaldada por afirmaciones aprobadas. |
| 4. Flujo diario | Completa local | Vista previa AWS, salud por fuente y Get on Board local separados; `PREPARE` revalida vigencia y cuenta sólo paquetes íntegros; automatización diaria actualizada sin envíos. |
| 5. Validación y publicación | Completa | 116 pruebas Python y 13 CDK aprobadas; síntesis real, auditoría de Git y diff limitado a dos assets Lambda. Commit `d57f0e1` público; stacks existentes actualizados y diff posterior cero. |

## Límites de despliegue

Get on Board queda local mientras añadirlo en AWS incremente la cuota de fuentes activa. Cualquier ampliación que genere gastos requiere propuesta concreta y aprobación expresa. Un cambio de código de los stacks existentes sólo se desplegará si el diff no añade recursos, IAM, horarios ni servicios, y conserva cuota y presupuesto. Las postulaciones siguen requiriendo consentimiento específico por candidato, vacante y portal.

## Registro de decisiones y errores de esta tarea

| Fecha | Etapa | Hecho o decisión | Resolución |
| --- | --- | --- | --- |
| 2026-10-20 | 0 | Se reutiliza la estructura `plan/`, `docs/decisions/` y `docs/progress.md` del repositorio para el plan persistente. | Evita duplicar `progress.md` en la raíz; mantiene la supervisión en Codex Remote. |
| 2026-10-20 | 0 | Las 80 pruebas Python anteriores al cambio pasaron. Cuatro fuentes Greenhouse activas, límite de diez vacantes y tres paquetes, sin tracker local ni salud por board. | Se inicia por fuentes sin activar un quinto board en AWS. |
| 2026-10-20 | 1 | Pruebas nuevas fallaron como se esperaba por ausencia de Get on Board y `source_health`; luego pasaron 26 pruebas focalizadas tras la implementación inicial. | Se añadieron lector diario y vista local de tres categorías. |
| 2026-10-20 | 1 | La vista local consultó tres categorías por HTTPS GET: 207 vacantes únicas, diez mostradas, cero `shortlist` por condiciones no acreditadas; `programming` llenó la primera página de 100 y puede tener más. | Se etiqueta posible truncamiento y se conservan los 207 resultados totales en el conteo; no se generan CVs desde esa fuente. |
| 2026-10-20 | 2 | 103 pruebas Python pasaron. El marcador actual de AWS es `NOT_INSTRUMENTED` (35 vacantes) porque el código nuevo aún no se desplegó; no se confundió con salud verificada. | La lectura del marcador fue de sólo lectura. La vigencia y memoria histórica operan localmente cuando se ejecute la próxima vista previa o preparación. |
| 2026-10-20 | 3–4 | El lote AWS siguió `READY` con diez vacantes en revisión y `--prepare` devolvió cero paquetes. Get on Board devolvió 207 vacantes únicas, 67 en revisión y diez visibles; la categoría `programming` puede estar truncada. El tracker privado contiene 20 descubrimientos y cero envíos. | La cuota de AWS sigue diez; Get on Board no alimenta el lote ni crea CVs. La bitácora salarial añadió cero cifras porque el lote no contiene rangos oficiales completos. |
| 2026-10-20 | 4 | Una prueba detectó que un PDF faltante se reportaba como paquete existente; otra, que una empresa malformada del feed causaba un error no controlado. | Ambos casos fallaron antes de la corrección y pasaron después; el paquete incompleto queda bloqueado. |
| 2026-10-20 | 5 | Preflight AWS, 116 pruebas Python, 13 CDK y síntesis real pasaron. `cdk diff --no-change-set` mostró sólo `Code`/metadata de Collector y Publisher; fuentes, límite cuatro, presupuesto, IAM y horarios no cambian. | Diff completo guardado en `private/`; se puede actualizar código de los stacks existentes según `AGENTS.md` tras la auditoría final. |
| 2026-10-20 | 5 | `d57f0e1` se publicó en `main`. Ambos stacks terminaron `UPDATE_COMPLETE`, el diff posterior dio cero cambios, las cuatro fuentes y dos Scheduler siguieron activos y Get on Board quedó fuera de AWS. Budgets observó USD 0.001 atribuido, bajo avisos USD 3/5. | Se actualizó sólo código de Lambdas; rollback: desplegar el código del commit previo `67ddb6d` tras preflight y diff, sin cambiar activación ni datos privados. El primer marcador con salud por fuente espera la corrida programada siguiente. |
