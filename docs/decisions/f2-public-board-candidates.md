# F2: boards públicos candidatos para el primer equipo

Revisión: **2026-10-14**. Este catálogo contiene sólo información pública de empresas y vacantes. El análisis de los CVs de Alec y cualquier preferencia propuesta están en `private/`, fuera de Git. No constituye una lista de fuentes activas ni una autorización para consultar feeds de forma recurrente, activar AWS o postularse.

## Puestos observados

| Empresa / board Greenhouse | Puesto público de ejemplo | Ubicación y condición relevante | Estado para el proyecto |
| --- | --- | --- | --- |
| [Utility Profit](https://www.utilityprofit.com/careers) / `utilityprofit` | [Full Stack Software Engineer — AI & Automation](https://job-boards.greenhouse.io/utilityprofit/jobs/4412541009) | Remoto mundial, con preferencia por México y EE. UU.; **contratista independiente**, sin prestaciones patrocinadas por la empresa. | Candidato a piloto de lectura, sujeto a política, límites y revisión final de condiciones. |
| [Caylent](https://caylent.com/careers) / `caylent` | [Cloud Senior Engineer](https://job-boards.greenhouse.io/caylent/jobs/5787522004) | México, remoto; exige autorización laboral vigente en el país y puede incluir turnos rotativos. | **Revisión manual/alerta oficial por ahora.** Sus [condiciones del sitio](https://caylent.com/terms-of-service) prohíben acceso automatizado y extracción sistemática; antes de programar el feed se debe resolver expresamente su alcance respecto del ATS externo. |
| [Factored](https://www.factored.ai/careers) / `factored` | [Senior AI Engineer](https://job-boards.greenhouse.io/factored/jobs/4514946008) | América Latina, remoto; foco en Python, sistemas GenAI de producción y AWS. | Candidato a piloto de lectura, sujeto a política, límites y revisión final de condiciones. |
| [Cobre](https://job-boards.greenhouse.io/cobre) / `cobre` | [Senior AI Engineer — Internal Solutions](https://job-boards.greenhouse.io/cobre/jobs/4392110009) | LATAM; backend **Go primero**, AWS, sistemas distribuidos y aislamiento de datos. México no se declara por separado en el anuncio. | Alternativa; verificar país admisible y condiciones antes de cualquier piloto. |

La [API pública de Greenhouse](https://docs.greenhouse.io/job-board.html) ofrece lecturas GET sin autenticación para ofertas publicadas. Esa documentación no sustituye las condiciones de cada empleador ni autoriza envíos. No se usó la API de postulación.

## Comprobación técnica acotada

Una lectura local de **un GET por board** el 2026-10-14, mediante `src/aji/transport.py` (HTTPS, host/ruta fija, timeout de 8 s, máximo 2 MB y sin redirecciones), devolvió 6 anuncios para `utilityprofit`, 57 para `caylent`, 14 para `factored` y 16 para `cobre`. Los cuatro puestos enlazados arriba estaban presentes en sus feeds. Los conteos son una instantánea, no una promesa de vigencia o elegibilidad. El listado de Caylent se consultó una sola vez para evaluar la fuente; la restricción de sus condiciones impide programarlo sin aclaración.

## Antes de aprobar un piloto

1. Elegir empresas y puestos de interés, contrato aceptable, modalidad, salario mínimo si aplica, exclusiones y cuota. No inferir estos criterios de un CV.
2. Revisar condiciones del empleador y del ATS para **cada board** y documentar el resultado. Donde haya restricción o ambigüedad, mantener revisión manual o alerta oficial.
3. Confirmar país/permiso laboral y si el anuncio sigue activo antes de preparar documentos. El adaptador Greenhouse actual deja `mexico_eligibility=unknown` y `modality=unknown`, incluso cuando el texto público menciona México; se requiere una comprobación humana o un enriquecimiento explícito y probado.
4. Preparar política privada aprobada, pruebas locales, diff/costo y aprobación separada antes de subir configuración o activar Scheduler/Lambda. `AUTO_SUBMIT` permanece apagado.

Las ofertas pueden cambiar o cerrarse. Antes de usar un anuncio concreto, volver a verificar su página oficial.
