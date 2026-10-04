# Asistente de riesgos y salvaguardas GLF

**Etapa actual:** [Semana 3 auditada y ZIP académico limpio](docs/auditoria_entrega_semana3.md); [negativos pendientes y cruces documentales](evaluacion_rag/diagnostico_cruces_y_test.md). El primer bloque de 25 candidatos se guarda localmente para revisión; test v1 no se usa para escoger parámetros.

**Gold humano v1 registrado:** 50 preguntas y 76 relaciones relevantes según decisiones manuales comunicadas por el usuario. [Impacto de la revisión](evaluacion_rag/impacto_revision_humana.md) y [trazabilidad para el proyecto final](evaluacion_rag/trazabilidad_proyecto_final.md). La entrega de [Semana 3](docs/auditoria_entrega_semana3.md) permanece separada; test no se usó para optimizar. Los CSV con texto del corpus se guardan localmente, fuera del GitHub público.

**Revisión del gold standard en preparación:** [guía y generador del paquete humano](evaluacion_rag/README.md), [diagnóstico de particiones](evaluacion_rag/diagnostico_particiones.md) y [plan de mejora de Recall](evaluacion_rag/plan_mejora_recall.md). Los CSV con texto del corpus están disponibles localmente y no se publican en este repositorio público. Test permanece congelado.

**Empezar aquí: [Avance del equipo, pendientes y cómo abrir la web](docs/AVANCE_EQUIPO.md).**

## Estado de recuperación - 3 de octubre de 2026

[Evaluación RAG](evaluacion_rag/README.md): 585 fragmentos normativos en español, 50 preguntas y 316 pares con etiquetas IA sin revisión humana. Se ejecutaron BM25, E5-base preentrenado e híbrido RRF con las mismas preguntas. Recall@5 provisional: 74,7 %, 68,7 % y 73,7 %; ninguno alcanza el objetivo de 80 %. BM25 es el candidato provisional por validación. Los tiempos informados corresponden a búsqueda local, no al sistema completo. El paquete académico de Semana 3 permanece separado y conservado.

Los CSV con citas y textos se mantienen locales y excluidos de Git público. Para interpretaciones y reproducción, ver el README de evaluación y su reporte generado.

---

## Estado histórico al 28 de septiembre de 2026

La documentación de semana 1 que figura más abajo es histórica. La referencia actual es [Decisiones vigentes](docs/decisiones_vigentes.md): Recall@5 ≥ 80 %, p95 ≤ 7 segundos y presupuesto máximo USD 200. Los datos comprobados contienen 26 expedientes y la partición 18/4/4. Estas cifras son metas y composición del dataset, no rendimiento medido.

- [Control de versiones](docs/control_versiones.md)
- [EDA con seis figuras](docs/analisis_datos.md) y [notebook ejecutado](notebooks/01_exploracion.ipynb)
- [Plan de trabajo](docs/planificacion.md)
- [Preparación de semana 3](docs/semana_3.md)
- [Protocolo de evaluación y etiquetado](docs/protocolo_evaluacion.md)
- [Diseño inicial de interfaz](docs/diseno_interfaz.md)

### Reproducir el EDA

Python 3.11. Instalar dependencias y ejecutar desde la raíz, indicando la ruta de un ZIP autorizado. Los datos privados no están incluidos.

```sh
python -m pip install -r requirements.txt
python -m src.eda --archive /ruta/GLF_Galapagos_Datasets_Iniciales.zip
python -m unittest discover -s tests -v
```

El notebook también puede ejecutarse con Jupyter configurando `GLF_DATASET_ZIP`. Los resultados agregados se guardan en `results/`. Hay trece pruebas de consistencia, recuperación y API. La web local permite consultar el corpus normativo con BM25; el experimento académico de Semana 3 y una evaluación provisional de recuperación se prepararon después de esta sección histórica. Los requisitos finales siguen en desarrollo.

### Abrir la web local

Desde la raíz del repositorio, con Python 3.11 o superior:

```sh
python -m app.server --archive /ruta/GLF_SGAS_Corpus_ES.zip
```

Abrir http://127.0.0.1:8765. El servidor lee 585 fragmentos del ZIP local sin subirlos a servicios externos. Detener con Ctrl+C. No exponer este servidor de desarrollo a Internet. Véase [guía de la web](docs/web_local.md).

## Documentación histórica de semana 1


Documentación académica del proyecto, organizada por semana. La primera entrega corresponde al Workshop de Metodología SMART.

**Equipo:** Schubert Lombeida Manjarrez y Niko Dimitri Jiménez Bruno.  
**Estado:** propuesta y planificación; todavía no contiene una aplicación ni resultados experimentales.

## Objetivo

Diseñar y evaluar un prototipo que recupere fichas pertinentes de riesgos y salvaguardas, muestre sus fuentes y apoye la revisión de la nueva matriz GLF de 17 campos. El especialista conserva las valoraciones y decisiones.

Se propone comparar una búsqueda BM25 con un modelo de embeddings multilingüe E5 y complementar ambos con reglas de revisión de campos y cálculos.

## Estructura

~~~text
.
|-- README.md
|-- .gitignore
|-- .gitattributes
|-- manifest.json
|-- Semana 1- Workshop de Metodología SMART/
    |-- 01_Matriz_evaluacion_SMART.xlsx
    |-- 02_Analisis_y_solucion_recomendada.docx
    |-- 03_Canvas_SMART_GLF.docx
    |-- 04_Checklist_SMART_GLF.docx
    |-- 05_Guion_pitch_GLF.docx
    |-- 06_Formulario_especialista_Sostenibilidad.docx
~~~

Cada nueva semana tendrá una carpeta al mismo nivel, con el formato **Semana N- Nombre de la actividad**, y contendrá directamente todos sus entregables. Las carpetas siguientes se incorporarán cuando se conozcan sus actividades.

## Semana 1: documentos y orden de lectura

| Documento | Contenido |
|---|---|
| [Análisis y solución recomendada](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/02_Analisis_y_solucion_recomendada.docx) | Comparación de opciones, fuentes, alcance, métricas, presupuesto y cronograma. |
| [Matriz de evaluación SMART](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/01_Matriz_evaluacion_SMART.xlsx) | Tres alternativas, puntuaciones ponderadas y 15 justificaciones. |
| [Canvas SMART](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/03_Canvas_SMART_GLF.docx) | Objetivo, recursos, riesgos y planificación. |
| [Checklist SMART](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/04_Checklist_SMART_GLF.docx) | Validación documental y condiciones pendientes. |
| [Guion del pitch](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/05_Guion_pitch_GLF.docx) | Texto para ensayar una presentación de aproximadamente tres minutos. |
| [Formulario para el especialista](Semana%201-%20Workshop%20de%20Metodolog%C3%ADa%20SMART/06_Formulario_especialista_Sostenibilidad.docx) | Entrevista con Ulf, referencia experta, medición y acuerdos. |

Descargar los archivos para editarlos en Word y Excel o herramientas compatibles. GitHub conserva los archivos, pero la revisión de diferencias de estos formatos binarios es limitada.

## Resultado de la selección

| Alternativa | Puntuación sobre 5 |
|---|---:|
| GLF | 4,40 |
| PreClass AI | 4,00 |
| PoliScope AI | 3,40 |

Las puntuaciones son una valoración técnica argumentada. No representan el rendimiento medido de modelos.

El checklist obtiene **24/31, amarillo**. Quedan pendientes la línea base de tiempos, la verificación del corpus, la dedicación semanal del equipo y la capacidad de cómputo.

## Restricciones y calendario

- Seis semanas totales, con cinco semanas restantes en la planificación preparada.
- Hasta 30 expedientes declarados, pendientes de inventario y anonimización.
- Presupuesto directo estimado por el equipo: USD 100.
- Ulf disponible como especialista; agenda y criterios específicos por acordar.
- Calendario propuesto: 19 de septiembre a 23 de octubre de 2026.
- Entrega del workshop prevista para el domingo 20 de septiembre a las 21:00; zona horaria de la plataforma pendiente de comprobar.

Las metas de recuperación, alertas, trazabilidad y ahorro de tiempo son propuestas para el piloto. No se presentan como resultados logrados.

## Manejo de documentos

Este paquete contiene únicamente los seis entregables preparados y los archivos de organización del repositorio. Los expedientes, documentos fuente institucionales, datos personales, archivos de trabajo y resultados temporales permanecen fuera del paquete.

Antes de habilitar acceso público, revisar que la difusión de los nombres y del contenido institucional incluido en los entregables esté autorizada. Un repositorio privado permite coordinar la revisión inicial.

El archivo .gitignore previene incorporaciones accidentales en las rutas habituales; no anonimiza documentos ni elimina información del historial de Git.

## Actualización

1. Editar el documento correspondiente sin cambiar su ruta.
2. Mantener coherencia entre matriz, análisis, Canvas, checklist y guion.
3. Registrar en el mensaje del commit el cambio y su motivo.
4. Actualizar los hashes de manifest.json si se modifica algún entregable.

manifest.json permite comprobar la integridad de esta copia inicial y relacionar sus nombres con los originales.

## Subir a GitHub

Crear un repositorio vacío y subir **el contenido de esta carpeta**, conservando su estructura. Si se usa Git, ejecutar desde esta carpeta:

~~~bash
git init
git add .
git commit -m "Añadir entregables del workshop SMART"
git branch -M main
git remote add origin https://github.com/USUARIO/NOMBRE-REPOSITORIO.git
git push -u origin main
~~~

Sustituir USUARIO y NOMBRE-REPOSITORIO por los datos reales. No se ha creado ni publicado un repositorio remoto como parte de esta preparación.

## Alcance de uso

Documentación académica de trabajo. No constituye aprobación institucional, certificación de cumplimiento ni autorización para reutilizar documentos de terceros. No se incorpora una licencia de redistribución porque sus condiciones todavía no han sido definidas.


## Preparación de publicación

Servidor WSGI y contenedor preparados. Consulta [despliegue](docs/despliegue.md). Waitress probado localmente con 585 fragmentos; Docker y publicación remota pendientes.

[Búsqueda semántica E5: implementación y pendientes](docs/busqueda_semantica.md). La web continúa usando BM25.

## Notebook de Colab

[02_recuperacion_E5_Colab.ipynb](notebooks/02_recuperacion_E5_Colab.ipynb) es autónomo: instala dependencias, carga ZIP, descarga E5, construye el índice, compara búsquedas y exporta el registro. Preparado y validado estructuralmente; ejecución real pendiente. No sustituye overfitting_analysis.ipynb de semana 3.
