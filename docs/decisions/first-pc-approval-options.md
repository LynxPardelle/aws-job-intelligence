# Opciones para configurar el primer equipo de AWS Job Intelligence

Investigación al **2026-10-14**. Alcance: Alec y este PC; Héctor y el segundo equipo esperan el handoff. Especificación principal: plan maestro v3 en `private/specification/`. Este documento presenta decisiones, no activa servicios ni autoriza postulaciones. Puedes responder por códigos, en varios mensajes y sin completar todo de una vez. No envíes claves, contraseñas, tokens ni CVs al repositorio. **Actualización F2:** se revisaron los dos CVs distintos más recientes de Alec y se documentó un [catálogo público de boards candidatos](f2-public-board-candidates.md); el análisis personal queda en `private/`. El correo de alertas se asignó a Codex según [ADR-003](../architecture/adr-003-codex-gmail-alerts.md).

**Actualización 2026-10-18:** el titular confirmó los criterios de búsqueda, las empresas de interés y `max_jobs_per_day=10`; el detalle personal está sólo en `private/alec/`. La actualización de código de dos Lambdas ya se desplegó con Scheduler y flags apagados. La tabla siguiente se conserva como referencia de opciones y límites técnicos. La activación de fuentes y cualquier candidatura siguen pendientes de aprobaciones separadas.

## Lo que ya está decidido

- Región `us-east-1`, perfil administrador `default` como origen de este PC y rol temporal `aji-alec-access-dev` para las lecturas ordinarias. Stacks shared y Alec desplegados, presupuesto de proyecto de USD 5/mes con alertas reales a USD 3/5, y publicador v1.1. Los dos Scheduler y flags de ejecución siguen desactivados. El lote ficticio probó lectura y lock, sin CV ni envío. Véanse [estado](../progress.md) y [revisión AWS](../activation-review.md).
- `AUTO_SUBMIT` queda apagado. El modo aceptado por la política actual es `PREPARE`; ningún score, CV ni formulario rellenado autoriza una postulación. El perfil y los documentos profesionales de Alec requerirán aprobación del propio titular y evidencia por afirmación.
- No usaré datos de Héctor ni accederé a sus documentos desde esta identidad. La copia del plan maestro, las preferencias, CVs y artefactos reales van en `private/` o `applications/`, ambos ignorados por Git.

## Cinco decisiones necesarias para empezar a descubrir vacantes

| Código | Tu decisión | Opciones | Propuesta de arranque |
| --- | --- | --- | --- |
| F | ¿Qué empresas observar? | **F1:** dar 1–10 empresas y sus páginas oficiales de empleo; **F2:** dar roles, sectores y exclusiones para que yo proponga empresas y boards; **F3:** dar enlaces de vacantes o páginas de carreras para derivar las empresas; **F0:** sólo enlaces manuales, sin collector | F2 si todavía no tienes lista; después aprobar 1–3 boards para piloto |
| B | ¿Qué canal de origen? | **B1:** feeds públicos Greenhouse/Lever/Ashby, por board aprobado y tras revisar condiciones; **B2:** sitio corporativo, tras desarrollar conector específico; **B3:** alertas oficiales leídas localmente por Codex mediante el conector de Gmail del titular; **B4:** enlaces añadidos manualmente | B1 para boards permitidos; B3 para alertas del candidato una vez conectada su cuenta; B4 si quieres cero consultas automáticas |
| P | ¿Qué busca Alec? | Roles, tecnologías, seniority, modalidad, salario, exclusiones, umbral y cuota en la tabla de política de abajo | No completar con suposiciones del CV ni preferencias de otra persona |
| E | ¿Cómo tratar vacantes con datos faltantes? | **E1:** revisión humana; **E2:** excluir; **E3:** investigar la fuente original y sólo después decidir | E1 + E3; la elegibilidad desde México no se infiere de «Remote» |
| O | ¿Cómo operar el piloto? | **O1:** validación manual sin horarios; **O2:** una corrida controlada; **O3:** todos los días; **O4:** sólo días hábiles | O1 y luego O2, antes de O3 |

Puedes pedir que investigue y proponga empresas a partir de **3–5 títulos de puesto**, áreas o industrias, modalidad y países aceptables. La selección final de empresas y fuentes seguirá siendo tuya. Para cada board aprobado documentaré empresa, página oficial de carreras, ATS, identificador exacto, URL GET construida, fecha de comprobación, límites y resultado de revisión de términos. Una página pública o API GET no equivale por sí sola a permiso general para copiar, republicar o enviar candidaturas.

### Canales disponibles y límites reales

| Canal | Qué ofrece la fuente oficial | Estado del proyecto | Decisión práctica |
| --- | --- | --- | --- |
| Greenhouse | La [Job Board API](https://docs.greenhouse.io/job-board.html) publica GET de empleos sin autenticación; `content=true` incluye descripción. El POST de candidaturas es un endpoint separado que requiere clave. | Conector GET probado con fixture. No hay salario estructurado en el adaptador y la modalidad se marca `unknown`. | Aprobar boards exactos; revisar si la descripción y la página del empleador aclaran modalidad, compensación y elegibilidad. |
| Lever | La [Postings API](https://github.com/lever/postings-api) lista puestos publicados y ofrece filtros y paginación `skip`/`limit`; también existe un POST de aplicación separado con credenciales. | Conector GET probado con fixture; **todavía no pagina**. Boards grandes pueden quedar incompletos y deberán probarse antes de activarlos. | Aprobar boards exactos y exigir prueba de cobertura; implementar paginación si hace falta. |
| Ashby | La [Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) entrega puestos publicados; `includeCompensation=true` puede incluir componentes de salario, y el feed distingue `isListed`. | Conector GET probado con fixture; excluye `isListed=false`. Un salario no publicado sigue siendo desconocido. | Aprobar boards exactos y revisar si el tamaño del feed entra en el límite local. |
| Sitio corporativo fuera de esos ATS | Cada sitio puede tener estructura y términos distintos. | No existe conector genérico ni rastreador de páginas HTML. | Enviar la URL oficial; investigaré una vía permitida y crearé pruebas antes de proponerlo como fuente. |
| LinkedIn, Indeed y OCC | [LinkedIn permite alertas oficiales](https://www.linkedin.com/help/linkedin/answer/a511279/job-alerts-on-linkedin?intendedLocale=en&lang=en-us); [Indeed ofrece alertas por correo](https://support.indeed.com/hc/en-us/articles/204488890-Starting-Stopping-and-Managing-Job-Alerts). Sus condiciones no autorizan usar bots de extracción o postulación por el mero hecho de tener una cuenta: [LinkedIn](https://www.linkedin.com/legal/user-agreement), [Indeed](https://www.indeed.com/legal?hl=en_US). Para OCC no se verificó una API pública adecuada en esta revisión. | No hay conector a esos portales. | Usarlos manualmente o mediante alertas oficiales del titular; cualquier integración de correo se diseñará aparte. No activar scraping ni envío automatizado. |

El transporte actual usa HTTPS GET a hosts ATS predefinidos, sin seguir redirecciones, timeout de 8 s, hasta 3 intentos y tope de 2 MB por feed; el collector admite hasta 10 fuentes y 1,000 vacantes por corrida. Una fuente fallida deja la corrida incompleta; el publicador no debe crear un lote READY parcial. Esos son límites del código actual, no cuotas garantizadas por los proveedores. Antes de activar un board grande revisaré cobertura, tamaño, respuesta 429 y términos del empleador. [Código de transporte](../../src/aji/transport.py), [collector](../../src/aji/lambda_handler.py).

### Cómo se comprobaría cada board antes del piloto

1. Confirmar que el enlace que nos das pertenece a la empresa o lleva desde su página oficial de carreras al ATS correcto; identificar exactamente el slug del board. No basta una URL de un agregador o un resultado de búsqueda.
2. Revisar documentación del endpoint, condiciones aplicables del ATS y de la página del empleador, y acceso técnico sin autenticación ni evasión de controles. Si las condiciones son ambiguas, el board queda en espera o se usa sólo el enlace manual.
3. Hacer una lectura de prueba acotada, comparar número de anuncios y una muestra de URLs con la página visible, comprobar que el payload cabe en 2 MB y que no faltan páginas. Lever puede necesitar paginación; un fallo de cobertura bloquea su activación hasta corregir el conector.
4. Registrar la fuente, fecha de revisión, respuesta HTTP, cuota y errores sin guardar datos personales en Git o logs. La primera corrida nunca postula ni visita el enlace de aplicación como acción de envío.

**Criterio de salida del piloto:** elegir después si durará 1, 7 o 14 días. Revisar que cada lote corresponda al día local, que las vacantes sigan abiertas, que las etiquetas «revisión» expliquen datos faltantes y que no se mezclen historiales de candidatos. Comparar gasto atribuido y gasto general de la cuenta porque el presupuesto filtrado puede omitir cargos sin etiqueta. Si el feed cambia, responde 429, redirige inesperadamente o supera el límite, la fuente se pausa para investigación. El máximo de **vacantes publicadas** por día no limita por sí mismo el número de GET ni las vacantes que el collector lee; esas cuotas se gobiernan aparte.

## Política que debe aprobar Alec

La [política de ejemplo](../../config/search-policy.example.json) es un esquema sin preferencias reales. El [parser](../../src/aji/publisher_handler.py) rechaza claves desconocidas y sólo acepta `candidate_id=alec`, `eligible_countries=["MX"]` y `application_mode=PREPARE`. Las opciones de la tabla distinguen lo que funciona ahora de mejoras que habría que implementar.

| Campo / código | Opciones que puedes indicarme | Efecto real hoy |
| --- | --- | --- |
| **P1 Roles** | Títulos buscados y sinónimos, p. ej. «Data Engineer», «Analytics Engineer»; o «sin filtro de título» | Si hay lista, basta que un término aparezca en el título. Títulos equivalentes no escritos se pueden perder. |
| **P2 Tecnologías** | Lista de tecnologías, idealmente separando imprescindibles y deseables | Hoy todas las tecnologías listadas pesan igual dentro de 30 puntos. La distinción «obligatorio/deseable» requeriría código; lista vacía causa revisión por tecnología desconocida. |
| **P3 Seniority** | `junior`, `mid`, `senior`, `staff`, `principal`, varios, o cualquiera | Funciona como filtro cuando el puesto trae nivel explícito; nivel ausente queda para revisión. |
| **P4 Modalidad** | `remote`, `hybrid`, `onsite`, varias, o cualquiera | Funciona cuando el ATS expone modalidad reconocible. En Greenhouse el adaptador actual no la determina. «Remote» no confirma contratación desde México. |
| **P5 Ubicación y elegibilidad** | México remoto; ciudad concreta para híbrido/presencial; países para reubicación; restricción de zona horaria; necesidad de visa/patrocinio | Sólo se representa elegibilidad desde `MX`. Los adaptadores actuales la marcan `unknown`; no hay filtro estructurado por ciudad, visa o zona horaria. Una vacante desconocida queda en revisión, no shortlist ni CV automático. Si alguno de estos criterios es obligatorio, se implementará y probará antes de activar. |
| **P6 Compensación** | Sin mínimo; mínimo bruto o neto con cantidad, moneda (`MXN`/`USD` u otra) y periodo (`year`, `month` u otro) | Admite un mínimo, moneda, periodo y `salary_basis=net`. Para neto, toda cifra publicada sin verificación del neto queda en revisión; no convierte divisas ni estima impuestos. Con `salary_basis=reported`, compara cifras publicadas de la misma moneda y periodo, sin afirmar que sean netas. |
| **P7 Exclusiones** | Empresas concretas a excluir; industrias, clientes actuales o conflictos de interés | Hoy la exclusión por empresa compara nombre exacto sin distinguir mayúsculas. Industrias y conflictos requieren una regla nueva. |
| **P8 Calidad y volumen** | Umbral de shortlist 0–100; máximo 1–100 vacantes por día (sugerencia inicial: 70 y 10) | El score actual pesa stack 30, elegibilidad/modalidad 25, seniority 20, salario 15 y vigencia/calidad 10. Los filtros duros prevalecen. El máximo corta la lista ordenada por decisión y score. |
| **P9 Umbral de preparación** | Un valor igual o superior al de shortlist, o «decidir más tarde» | Se valida y guarda, pero **todavía no decide qué CV generar**. No lo trataré como control activo. |
| **P10 Tipo de contrato e idioma** | Tiempo completo, parcial, contractor, temporal; inglés/español u otros | No son filtros actuales. Aunque Ashby publica `employmentType`, el adaptador no lo conserva en el contrato interno. Se puede especificar como requisito para implementar antes de activar. |
| **P11 Vigencia** | Sólo últimos 7/14/30 días; o cualquier anuncio aún activo | La fecha participa en el score de calidad hasta 30 días, pero no existe un límite duro configurable por edad. |
| **P12 Viajes y turnos** | Aceptar o rechazar viajes y turnos rotativos | La política admite ambas restricciones. Cada vacante tiene estado `required`, `not_required` o `unknown`; `required` se excluye cuando no se acepta y `unknown` va a revisión. Los conectores actuales dejan ambos estados en `unknown` hasta comprobar el anuncio. |

**Tratamiento de datos faltantes (E):** el comportamiento actual es `review` cuando falta elegibilidad mexicana, salario exigido, modalidad o seniority filtrado. Excluir todo lo desconocido es posible como cambio, pero puede dejar cero resultados; inferir elegibilidad desde ubicación o etiqueta remota no es aceptable. Esto es una conclusión del [matcher](../../src/aji/matcher.py) y de los [adaptadores](../../src/aji/connectors.py), no una garantía del proveedor ATS.

Las preferencias confirmadas se guardan en `private/alec/`, fuera de Git. La cuota de vacantes publicadas por día es 10; quedan por precisar límites de consultas, CVs y envíos, y, si se quiere acotar el score, tecnologías imprescindibles/deseables y niveles aceptados. Las condiciones de viajes y turnos tienen campos estructurados, pero los conectores no infieren su ausencia por silencio del anuncio; requieren evidencia por oferta. No se usarán CVs de otro candidato.

## Operación, automatización y costos: decisiones posteriores

| Código | Opciones | Consecuencia y propuesta |
| --- | --- | --- |
| **O1 Frecuencia AWS** | Manual; una corrida piloto; diario a las 08:00/08:30; días hábiles; otro horario | El CDK actual expresa **diario** en `America/Mexico_City`, pero está `DISABLED`. Cambiar frecuencia u hora exige diff y despliegue. Propongo una corrida piloto controlada con 1–3 boards antes del diario. [AWS admite zona horaria IANA](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html). |
| **O2 Fallos de fuente** | Abortarlo todo si falla una fuente; o publicar parcial con estado explícito tras desarrollar esa opción | Hoy aborta y no publica READY cuando falta parte de la recolección. Mantenerlo en el piloto evita tratar una lista incompleta como completa. |
| **O3 Codex a las 09:00** | Manual; automatización de sólo vista previa; automatización que toma lock; automatización con preparación de paquetes después de implementar recuperación | Recomiendo **vista previa sin `--claim`** al principio. El `--claim` actual adquiere el lock antes de generar cualquier paquete real; si el proceso falla después, bloquea un nuevo intento del mismo día. Antes de automatizar el claim conviene añadir estado de procesamiento y recuperación. La disponibilidad desde Remote depende de la configuración de la PC y debe probarse; [OpenAI distingue tareas de escritorio y Codex Cloud](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex). |
| **O4 Resumen visible** | Sólo conteos/errores; conteos y títulos/empresas/URLs; detalles de análisis privado | Recomiendo conteos, nombres de empresas y títulos, sin CV, correo, salario personal ni perfil. El resumen de Desktop/Remote puede contener datos en contexto de tarea sincronizado; revisar el nivel de detalle antes de activarlo. |
| **O5 Costo** | Mantener presupuesto USD 5 con alertas USD 3/5; sumar revisión diaria del gasto; diseñar una acción automática de pausa | El presupuesto existente **no es un tope**. [AWS Budgets actualiza datos y alertas según su ciclo de facturación](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html), habitualmente cada 8–12 h; una [Budget Action](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html) puede aplicar ciertas políticas o detener instancias, pero no equivale a un corte instantáneo de todos los cargos. La estimación de [USD 0.69/mes](../costs/estimate.md) es un escenario, no una garantía. |
| **O6 Retención** | Mantener lotes S3 30 días y vacantes públicas ~30 días; pedir 7/90 días u otro periodo para futura configuración; fijar periodo aparte para `applications/` local | Hoy S3 usa lifecycle de 30 días y DynamoDB TTL en elementos que lo llevan; los archivos locales no se limpian automáticamente. [S3 elimina de forma asíncrona](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html) y [DynamoDB TTL puede tardar días](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html). Elegir plazo y procedimiento de borrado del perfil/CV requiere decisión del titular. |
| **O7 Alertas por correo** | Ninguna por ahora; enlaces manuales; tarea Codex con conector de Gmail de Alec para alertas oficiales | Decisión actual: Gmail se procesa en Codex, no en AWS. En esta sesión no se expuso la herramienta de Gmail; hay que conectar/verificar la cuenta y probar lectura acotada antes de automatizar. Cuerpos, tokens y Message-ID no van a AWS ni Git. Véase [ADR-003](../architecture/adr-003-codex-gmail-alerts.md). |

La retención, el informe Remote y el uso de correo deben definirse por candidato. El coste observado del presupuesto filtrado todavía no demuestra que todos los cargos estén etiquetados; se revisará también el gasto total de la cuenta. Ninguna alerta financiera convierte en segura una fuente prohibida o una postulación automática.

## CVs y postulaciones: decisiones para otra etapa

| Código | Opciones | Requisito antes de usar datos reales |
| --- | --- | --- |
| **R1 Perfil profesional** | Sólo búsqueda; preparar CV tras validar perfil; no permitir CV automático | Para CV real: `verified-profile.json` privado, cada afirmación vinculada a documento y referencia, fecha de validación y permiso de reutilización aprobado por Alec. No inventar títulos, fechas, métricas ni certificaciones. |
| **R2 Modo de candidatura** | `PREPARE` (paquete para revisión); `ASSISTED` (rellenar sin enviar, requiere diseño y prueba por portal); `AUTO_SUBMIT` (fuera del MVP) | La implementación actual sólo acepta `PREPARE` y no tiene cliente de envío. `ASSISTED` requeriría términos y adaptador del portal, revisión humana de preguntas y adjuntos. `AUTO_SUBMIT` requeriría consentimiento específico, revocable, por candidato, vacante y portal, más acuse verificable. Véase la [revisión de automatización](../automation-readiness.md). |
| **R3 Envío real** | Ninguno; autorizar individualmente después de revisar cada paquete | No se pide ahora. Ni una aprobación general de AWS ni un score sustituyen la autorización concreta de postulación. [Greenhouse](https://docs.greenhouse.io/job-board.html) y [Lever](https://github.com/lever/postings-api) separan sus APIs de lectura y de aplicación; [Indeed prohíbe el uso no autorizado de bots para Apply](https://www.indeed.com/legal?hl=en_US). |

## Secuencia que propongo

1. Tú eliges **F, B y P**. Si no conoces los boards, basta con roles/sectores y 3–10 empresas o vacantes de ejemplo; yo identifico los ATS, compruebo la fuente oficial y preparo una lista concreta para tu aprobación.
2. Construyo una política privada de Alec y una allowlist de 1–3 boards; pruebo cada feed en lectura controlada, cobertura y límites. Si aparecen requisitos no implementados (ubicación, tipo de contrato, paginación, elegibilidad), los implemento localmente con fixtures antes de proponer AWS.
3. Te presento el **diff exacto, cuota, calendario y estimación** para aprobar la activación AWS. El piloto comienza sin postulación y sin automatización de claim. Después de observar resultados y costo, decidimos O3–O7.
4. Los dos CVs recientes de Alec ya se revisaron para proponer enfoques y fuentes, pero el perfil profesional, preferencias y permiso de reutilización siguen sin aprobación. Gmail se procesará por Codex una vez disponible/conectado; segundo PC y formularios quedan en fases separadas.

### Respuesta fácil por bloques

```text
F: F1/F2/F3/F0; empresas, sectores o URLs: ...
B: B1/B2/B3/B4; fuentes que NO quieres usar: ...
P1 puestos: ... | P2 tecnologías imprescindibles/deseables: ...
P3 seniority: ... | P4 modalidad: ... | P5 ubicación y elegibilidad: ...
P6 salario mínimo: ninguno / cantidad + moneda + periodo + bruto/neto
P7 excluidas: ... | P8 umbral y máximo diario: 70/10 u otros
P10 contrato/idioma: ... | P11 antigüedad máxima: ...
E: E1/E2/E3 | O: O1/O2/O3/O4
```

Puedes empezar con **F y los puestos P1**; las demás respuestas pueden llegar luego. «No sé» significa que debo investigar o dejarlo en revisión, no inventar una preferencia.

## Evidencia y revisión crítica

Fuentes externas **oficiales y públicas**, consultadas el 2026-10-14: [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html), [Lever Postings API](https://github.com/lever/postings-api), [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api), [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement), [Indeed Terms](https://www.indeed.com/legal?hl=en_US), [LinkedIn Job Alerts](https://www.linkedin.com/help/linkedin/answer/a511279/job-alerts-on-linkedin?intendedLocale=en&lang=en-us), [Indeed Job Alerts](https://support.indeed.com/hc/en-us/articles/204488890-Starting-Stopping-and-Managing-Job-Alerts), [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html), [Budget Actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html), [EventBridge Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html), [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html), [S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html) y [OpenAI Desktop/Remote](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex). La investigación **inicial** de esta guía no consultó CVs; la revisión F2 posterior sí consultó exclusivamente los de Alec y se conserva fuera de Git. Las páginas de términos pueden cambiar; revisaré la versión vigente al autorizar cada fuente concreta.

Tres riesgos que cambian la recomendación: (1) un GET público documentado para careers pages no concede automáticamente permiso para cualquier reutilización; (2) «Remote» y un score alto no prueban elegibilidad desde México, y el código actual la deja `unknown`; (3) un presupuesto con alertas y TTL/lifecycle no garantizan costo máximo ni borrado instantáneo. Además, el lock actual hace seguro evitar duplicados, pero exige recuperación antes de automatizar un flujo largo. Confianza **alta** en el comportamiento actual, comprobado en código y pruebas; **media** en la viabilidad de cualquier empresa/board concreto hasta revisar su página y términos; **baja** en el costo real hasta observar varias corridas con volumen aprobado.
