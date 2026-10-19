# Preparación para una operación diaria de candidaturas

Revisión: 2026-10-18. Alcance: primer equipo y candidato Alec. El plan maestro v3 en `private/specification/` rige este diseño. Los datos profesionales y preferencias personales permanecen en `private/` y `applications/`, fuera de Git.

## Qué puede hacerse hoy

| Etapa | Estado comprobado | Condición para operar sin intervención |
| --- | --- | --- |
| Recolectar vacantes | Collector desplegado con flag y Scheduler apagados; transporte HTTPS restringido y probado con fixtures | Aprobar cada fuente, su cuota de lectura, la política privada y la activación que genera gasto |
| Publicar lote privado | Publisher desplegado con flag y Scheduler apagados; contrato v1.1, checksum, READY y límite de 10 vacantes por día en la política propuesta | Probar una corrida controlada, costos, elegibilidad y restricciones reales |
| Leer lote en este PC | Pull con rol temporal y vista previa probados contra lote ficticio; sin automatización de Desktop | Crear y probar horario local con el PC encendido y la app abierta; comprobar resumen en Remote |
| Preparar CV adaptado | Generador local probado con perfil ficticio aprobado | Validar el perfil real y cada afirmación reutilizable, conectar el generador al pull, resolver incógnitas por oferta y recuperar trabajos fallidos sin duplicar |
| Leer alertas Gmail | Diseño local por candidato; el conector Gmail no está disponible en esta sesión | Conectar la cuenta correcta y probar permisos, filtrado y deduplicación antes de programar lecturas |
| Rellenar y enviar formularios | No hay cliente de portal ni pruebas de envío; `AUTO_SUBMIT` apagado | Integración permitida por portal, preguntas y consentimientos resueltos, límite propio de envíos, autorización específica y revocable por candidato, vacante y portal, recibo técnico |

La cuota confirmada de **10** se aplica a `max_jobs_per_day`: limita las vacantes publicadas en el lote privado, no las consultas GET a los boards, los CVs preparados ni las postulaciones. Esas tres actividades necesitan controles separados. En especial, el collector admite hasta 10 fuentes y reintenta consultas; la cuota del lote no es un límite de gasto ni de acceso externo.

## Flujo objetivo por etapas

1. AWS consulta únicamente fuentes aprobadas a las 08:00 y publica un lote READY a las 08:30. Si una fuente falla, marca la corrida como incompleta y no inventa resultados. Las dos programaciones siguen apagadas hasta una activación aprobada.
2. Codex Desktop en el equipo de Alec lee el lote a las 09:00, valida identidad, fecha, checksum y elegibilidad, y deja un resumen visible desde Remote. Una [tarea programada local](https://learn.chatgpt.com/docs/automations) requiere que este PC permanezca encendido, con la app en ejecución y el proyecto disponible. Una tarea web no accede directamente a los archivos privados de este PC.
3. Tras validar el perfil real, Codex crea paquetes sólo cuando la vacante y todas las condiciones necesarias están verificadas. El umbral `prepare_threshold` hoy se guarda pero **no gobierna** la generación; el pull actual tampoco llama al generador. Una vacante con salario neto, viajes, turnos o elegibilidad sin verificar queda para revisión.
4. Las alertas oficiales de Gmail se leen con el conector de Codex de este candidato, con permisos acotados. Un evento de Gmail puede activar tareas web en planes compatibles, pero [los disparadores de eventos no están disponibles en Desktop](https://learn.chatgpt.com/docs/automations) y una tarea web no dispone del perfil local. Por ello el primer flujo puede leer alertas en una tarea Desktop programada; una eventual integración por eventos exige diseño y prueba aparte.
5. Una candidatura real avanza por `APPROVED -> PREPARED -> REVIEWED -> SUBMISSION_AUTHORIZED -> SUBMITTED -> CONFIRMED`. Antes de enviar, se vuelve a comprobar que el consentimiento coincide con candidato, vacante y portal, no fue revocado, que la oferta sigue abierta y que no existe envío previo. `SUBMITTED` exige recibo técnico y `CONFIRMED` un acuse. El código actual contiene guardas de estado, pero no un ejecutor de portales ni persistencia completa de ese flujo.

Una operación recurrente significa corridas acotadas y deduplicadas, no solicitudes continuas sin límite. Si el portal exige CAPTCHA, MFA, una respuesta desconocida o intervención humana, se detiene y deja el paquete para revisión. En Windows, la [automatización de interfaz de Codex usa el escritorio activo](https://learn.chatgpt.com/use-cases/use-your-computer-with-codex); no equivale a un servicio desatendido que pueda enviar por cualquier portal.

## Viabilidad de envío por portal

Los cuatro boards de la lista F2 son Greenhouse. Su [Job Board API](https://docs.greenhouse.io/job-board) permite GET públicos, pero el POST de candidaturas exige una **Job Board API Key** del empleador y preguntas específicas de cada puesto. La documentación advierte que el cliente debe validar campos requeridos y proteger esa clave en servidor. La cuenta AWS del candidato y el conector Gmail no otorgan esa clave. [Lever](https://github.com/lever/postings-api) también requiere una clave para el POST de su Postings API; [Ashby](https://developers.ashbyhq.com/reference/applicationformsubmit) exige `candidatesWrite` y autenticación. Por tanto, una API de lectura no basta para prometer envíos automáticos universales.

Para cada empleador caben tres resultados después de revisar sus condiciones actuales: integración oficial concedida y probada; formulario asistido con revisión humana; o preparación de CV y enlace para postulación manual. No se usarán rutas privadas, ingeniería inversa de endpoints de envío ni evasión de controles antibot. Caylent permanece en lectura manual/alerta oficial hasta resolver la restricción de automatización ya documentada en el catálogo F2.

## Trabajo y pruebas antes de activar

1. Validar y aprobar el perfil real de Alec, con evidencia y permiso de reutilización por afirmación; probar que un perfil incompleto no produce CV. Mantener `applications/` ignorado y fijar retención local.
2. Implementar enriquecimiento verificable por oferta para país, remoto, viajes, turnos y salario comparable. Con la política actual, esos desconocidos impiden pasar de `review` a `shortlist`. No inferir `not_required` del silencio de una oferta.
3. Conectar el pull al generador y usar estados persistidos con lease/reintento: el `--claim` actual consume el lock antes de preparar paquetes, de modo que una falla impide reintentar ese lote. Probar caída a mitad del proceso, duplicados y expiración con fixtures.
4. Registrar auditoría mínima local: lote, candidato, vacante, revisión, versión de perfil/política, consentimiento, intento, resultado y recibo, sin CV ni correo completo en Git o CloudWatch. Definir un límite diario independiente para preparaciones y otro para envíos futuros.
5. Probar una tarea programada Desktop en modo vista previa, su resumen en Remote y la disponibilidad de Gmail. La automatización no debe tomar el lock ni publicar candidaturas en este piloto.
6. Para cualquier portal futuro, revisar condiciones y disponibilidad de integración, mapear preguntas y consentimiento, probar con fixtures y un entorno autorizado, verificar límites y respuesta 429, y exigir recibo e idempotencia antes de proponer una primera candidatura real.

**Autorización vigente:** se aprobó publicar sólo dos assets de código Lambda y se confirmó `max_jobs_per_day=10`. Ese despliegue terminó sin activar fuentes, flags, Scheduler ni envíos. La activación diaria con gasto y cualquier postulación real son decisiones posteriores, conforme a `AGENTS.md` y al plan maestro.
