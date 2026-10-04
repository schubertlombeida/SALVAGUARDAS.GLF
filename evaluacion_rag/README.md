# Evaluación del recuperador RAG de Salvaguardas GLF

## Baseline con gold humano v1 — 3 de octubre de 2026

El usuario confirmó revisión manual de las 50 preguntas GLF-001–050 y entregó 26 decisiones de cambio. `dataset_gold_human_reviewed_v1.csv` conserva 76 relaciones relevantes aprobadas, con `human_reviewed=true`; `dataset_gold.csv` mantiene sin cambios las 66 relaciones IA originales. `cambios_revision_humana.md` enumera 19 altas, 13 bajas y la reformulación de GLF-005. El nombre del revisor y la fecha real de revisión aún no fueron comunicados: en el gold figuran como pendientes; se registra aparte la fecha en que Codex recibió la confirmación.

Los baselines BM25, E5-base e híbrido se ejecutaron con parámetros idénticos a la evaluación inicial. [Impacto de la revisión](impacto_revision_humana.md), [comparación de métricas](comparacion_ia_vs_humano.csv), [resultados por split](resultados_recuperacion_human_v1.csv) y [validación del gold](validacion_gold_humano.json) documentan los resultados. Recall@5 global: BM25 75,0 %, E5-base 68,3 %, híbrido 75,0 %. Hit@5: 88,0 %, 80,0 % y 84,0 %. Ninguno cumple aún Recall@5 global >=80 %.

`dataset_pairs_human_reviewed.csv` incluye 76 positivos aprobados y 252 negativos **candidatos**, pendientes de juicio humano. Ocho negativos previos se promovieron a positivos. Tres positivos cruzan la asignación documental usada para pares; están en el gold para evaluar pero tienen `eligible_for_training=false`. Los negativos también están inhabilitados para entrenamiento. El test se leyó una sola vez para describir este baseline y permanece congelado para seleccionar parámetros.

Desde la raíz, con el ZIP autorizado:

```powershell
python -m evaluacion_rag.build_human_gold --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.build_human_pairs --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.evaluate_human_baseline --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.verify_human --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m pytest -q
```

El evaluador escribe resultados nuevos y preserva los anteriores. Los CSV con citas o texto completo del corpus permanecen locales y excluidos del GitHub público. El PR publica código, hashes, agregados y reportes sin esos textos. El experimento académico de Semana 3 se audita [por separado](../docs/auditoria_entrega_semana3.md): TF-IDF + SGD, L2 y parada temprana para diagnosticar sobreajuste; BM25 es una búsqueda léxica, E5-base es preentrenado y no fue ajustado por nosotros.

---

## Historial conservado: evaluación inicial con etiquetas IA

Esta carpeta evalúa **recuperación de fragmentos**, separada del experimento académico de Semana 3. Trabaja con el corpus SGAS en español que ya entregó el equipo: 585 fragmentos de 36 documentos. También se inventarían los otros conjuntos, pero no se mezclan en el índice normativo. Los textos originales quedan en el ZIP local.

**Estado:** 50 preguntas y 316 pares con etiquetas propuestas por IA, **sin revisión humana**. El archivo `dataset_gold.csv` es un borrador revisable, no un gold standard aprobado. Los resultados son provisionales. Lee `reporte_resultados.md` para la tabla medida y las limitaciones.

**Revisión humana preparada:** `revision_humana_gold.csv` reúne las 50 preguntas, cita y chunk propuesto completos, Top 10 de BM25/E5-base/híbrido con scores y una lista consolidada de candidatos con extractos. El CSV complementario `revision_humana_candidatos.csv` contiene una fila por pregunta–chunk con el texto completo de cada candidato y los tres rangos; así ninguna celda supera el límite de Excel y no se necesitan PDFs ni el ZIP para revisar. Hay 240 chunks candidatos únicos. `casos_revision_prioritaria.csv` registra 201 incidencias de revisión (54 señales de pregunta y 147 hard negatives); varias incidencias pueden corresponder a la misma pregunta. Se deben revisar los 147 negativos difíciles: 37 también aparecen en el Top 10 de E5 y son especialmente sospechosos. Los campos manuales están vacíos. Consulta `diagnostico_particiones.md` antes de sacar conclusiones de validation y test.

Los tres CSV de revisión contienen texto del corpus y se conservan **solo en el equipo local**; están excluidos del repositorio público. Los scripts, diagnósticos agregados y plan se publican en el PR. Compartir los CSV completos con el especialista requiere un canal privado autorizado.

BM25 ordena los fragmentos según términos compartidos y su frecuencia. E5-base convierte preguntas y fragmentos en vectores de significado; utiliza un [modelo multilingüe preentrenado](https://huggingface.co/intfloat/multilingual-e5-base), con prefijos `query: ` y `passage: ` y ventanas de hasta 512 tokens. El híbrido combina las posiciones de ambos listados con Reciprocal Rank Fusion (RRF). No se entrenó ni ajustó E5 ni un LLM. Los pares están preparados para revisión y un posible experimento futuro, no para afirmar calidad de producción.

## Ejecutar

Desde la raíz de `glf-proyecto`, con Python 3.12 y conexión inicial para descargar E5-base:

```powershell
python -m pip install -r evaluacion_rag/requirements.txt
python -m evaluacion_rag.prepare_dataset --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.audit_pairs
python -m evaluacion_rag.evaluate_retrieval --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.build_report
python -m evaluacion_rag.prepare_human_review --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
python -m evaluacion_rag.verify --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
```

La primera ejecución de E5 descarga pesos y codifica el corpus; después reutiliza `evaluacion_rag/.cache/` mientras ZIP, contenido, modelo y algoritmo sigan iguales. La caché y CSV con texto están excluidos de Git. Se necesita aproximadamente espacio para el modelo, dependencias y embeddings; las pruebas aquí se hicieron en CPU. Cada método evalúa las mismas 50 preguntas y el mismo corpus.

## Archivos útiles

- `inventario_corpus.csv`: documentos, cantidad de fragmentos, idioma, ruta y metadatos de página/sección presentes.
- `dataset_gold.csv`: 50 preguntas, IDs relevantes conocidos, documento/sección, referencia textual, revisión humana `false`.
- `dataset_pairs.csv`: 316 pares propuestos, positivos y candidatos negativos, tipo de negativo y partición. Leer antes de usar para entrenamiento.
- `resultados_recuperacion.csv`: comparación agregada BM25/E5/híbrido.
- `resultados_por_pregunta.csv`: rangos, aciertos y latencia individuales.
- `metricas_recuperacion.json`: configuración, hashes, versiones, resultados y alcance de latencia.
- `auditoria_pares.json`: separación de documentos/consultas/fragmentos y similitud entre particiones.
- `reporte_resultados.md`: interpretación y pendientes de validación.
- `revision_humana_gold.csv`: formulario autocontenido para confirmar preguntas y chunks; campos manuales vacíos.
- `revision_humana_candidatos.csv`: una fila por candidato, con texto íntegro y decisión manual vacía.
- `casos_revision_prioritaria.csv`: incidencias ordenadas para revisión.
- `diagnostico_particiones.md`: análisis de la diferencia entre validation y test; `diagnostico_particiones.json` contiene el detalle local.
- `plan_mejora_recall.md`: experimentos propuestos, pendientes de validación humana.

**Modelo vigente del benchmark:** `intfloat/multilingual-e5-base` (revisión fijada en `e5_index.py`). `src/semantic.py` conserva `intfloat/multilingual-e5-small` únicamente como prototipo legado de compatibilidad; no interviene en estas métricas. Train es para desarrollo, validation para futura selección de parámetros y test permanece congelado.

**Resultado observado:** BM25 alcanza Recall@5 de 74,7%; E5-base 68,7%; híbrido 73,7%. Los p95 exactos de la ejecución registrada están en `resultados_recuperacion.csv`; todos quedan bajo 7 s solo para búsqueda local precargada. BM25 es el candidato provisional por Recall@5 de validación. Ninguno alcanza la meta de 80% en este conjunto, y todavía faltan etiquetas humanas. El p95 de extremo a extremo y el costo total no están medidos.

El paquete de Semana 3 permanece aparte en la carpeta local `outputs/semana_3/ENTREGA_SEMANA_3.zip`. La web GLF y la generación mediante LLM quedan fuera de este trabajo.
