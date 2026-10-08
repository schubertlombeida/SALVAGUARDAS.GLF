# Evaluación de recuperación GLF - resultados provisionales

Evaluación local ejecutada sobre el corpus real SGAS español. **Todas las relevancias son propuestas de IA; ninguna fue verificada por una persona.** Por tanto `dataset_gold.csv` es un borrador para construir el gold standard, no un gold standard aprobado. La evaluación mide aciertos frente a referencias conocidas, posiblemente incompletas.

## Corpus y trazabilidad

- ZIP fuente SHA-256: `37c8a747c32c069642f501ef967c9119175a3da7e8b71d14f2910118d3e11267`.
- Corpus indexado: `Corpus_GLF_SGAS_ES.jsonl`, 585 fragmentos de 36 documentos en español. `inventario_corpus.csv` registra documento, idioma, tipo, ruta normalizada y disponibilidad de localizadores. Ninguno carece de documento, ID, texto o ruta normalizada; 422 conservan marcadores de página y 81 contienen encabezados de sección. La sección puede comenzar en un fragmento anterior y no está normalizada como campo propio.
- El ZIP incluye además un corpus bilingüe de 1.272 fragmentos / 88 documentos, no indexado en esta comparación para no duplicar traducciones. El otro ZIP del equipo contiene 56 documentos de casos, 250 fragmentos y 26 expedientes; **no** se mezclaron con el benchmark normativo ni se publicaron.
- 50 preguntas construidas desde anclas textuales verificadas en el corpus, con uno o varios IDs relevantes conocidos y una cita literal corta de referencia. Archivo para revisión: `dataset_gold.csv`; `human_reviewed=false` en todas.
- 316 pares para trabajo futuro de clasificación: 66 positivos propuestos y 250 negativos candidatos; 147 negativos se eligieron por alta semejanza léxica. Su condición negativa requiere revisión; pueden contener respuestas alternativas. No se entrenó un clasificador con estos pares.

## Métricas comparables

| Método | Recall@1 | Recall@3 | Recall@5 | MRR@5 | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 40.0 % | 64.7 % | 74.7 % | 0.611 | 1.8 ms | 3.6 ms |
| E5-base | 30.7 % | 54.7 % | 68.7 % | 0.544 | 37.4 ms | 42.6 ms |
| BM25+E5-RRF | 50.7 % | 67.7 % | 73.7 % | 0.721 | 39.8 ms | 50.4 ms |

Recall@k es la media por pregunta de relevantes conocidos recuperados entre los primeros k, dividida por todos los relevantes conocidos de esa pregunta. MRR@5 es la media del recíproco del rango del primer relevante conocido entre los primeros cinco; vale 0 si no hay acierto. Son métricas **respecto de relevancia conocida**, no exhaustiva. La selección inicial del fragmento objetivo desde la fuente ayuda a evitar que BM25 dicte todas las referencias, pero la revisión de otros fragmentos no fue exhaustiva y la formulación de algunas preguntas se parece al encabezado de su fuente.

Los tiempos incluyen búsqueda sobre índices precargados. E5 incluye codificar cada consulta; el híbrido incluye ambas búsquedas y RRF (profundidad 20, constante 60). Se excluyen descarga/carga del modelo, creación de embeddings, red, interfaz y generación. p50/p95 son percentiles de rango más próximo de **50 consultas**, medidos una vez por método después de calentamiento. La caché E5 contiene 1212 ventanas, construidas desde los 585 fragmentos sin truncado silencioso; el modelo fue `intfloat/multilingual-e5-base` con revisión `d128750597153bb5987e10b1c3493a34e5a4502a`. Los prefijos usados son `query: ` y `passage: `, conforme a [la ficha oficial del modelo](https://huggingface.co/intfloat/multilingual-e5-base).

## Particiones y selección

| Partición | Preguntas | BM25 Recall@5 | E5 Recall@5 | Híbrido Recall@5 |
|---|---:|---:|---:|---:|
| train | 27 | 66.7 % | 64.8 % | 68.5 % |
| validation | 11 | 71.2 % | 48.5 % | 57.6 % |
| test | 12 | 95.8 % | 95.8 % | 100.0 % |

Los pares separan preguntas y documentos entre desarrollo, validación y prueba. La auditoría encontró 0 pares de fragmentos entre particiones con coseno de n-gramas de caracteres >= 0.85 (máximo observado 0.643); no se repite ningún ID de consulta, documento o fragmento entre particiones. Solo 58 fragmentos únicos aparecen en los 316 pares: múltiples preguntas reutilizan fuentes, por lo que 316 no equivalen a 316 ejemplos independientes.

Con la regla de priorizar Recall@5 de **validación** y usar MRR@5 para desempate, el candidato seleccionado para continuar es **BM25**. Esta selección es provisional hasta revisar las referencias. En prueba, el híbrido obtiene un valor mayor que BM25, pero no se cambia el método usando ese conjunto pequeño de 12 preguntas.

## KPI y límites

- Meta Recall@5 >= 80%: **ningún método la alcanza en las 50 preguntas propuestas**; mejor valor global 74.7 %. El cumplimiento oficial queda **sin verificar** porque faltan juicios humanos y un conjunto relevante más completo.
- Meta p95 <= 7 s: los tres métodos quedan por debajo en **búsqueda local precargada**. La latencia p95 del sistema completo sigue **sin medir**.
- Presupuesto total <= USD 200: **no verificado**; no se registró un presupuesto operativo completo ni costos de infraestructura. E5 se ejecutó localmente en CPU, sin entrenamiento.
- Una respuesta útil puede estar en un fragmento no anotado; también puede haberse propuesto una relevancia incorrecta. En particular, revisar los casos donde los tres recuperadores fallan y la vigencia/autoridad de las traducciones. No usar estas cifras como rendimiento certificado.

## Siguiente revisión manual

1. Para cada fila de `dataset_gold.csv`, verificar pregunta, referencia literal y todos los fragmentos que realmente responden, incluidos top 10 de BM25 y E5 y documentos relacionados. Registrar revisor y fecha; solo entonces cambiar `human_reviewed` y estado.
2. Revisar todos los `hard_candidate` en `dataset_pairs.csv`. Convertir en negativo solo los que no respondan a la pregunta; añadir positivos descubiertos y conservar particiones por documento.
3. Congelar un conjunto de prueba nuevo antes de ajustar pesos, RRF, consultas o fragmentación. Repetir las mismas métricas y medir el flujo completo del sistema para el KPI de 7 s.

El experimento académico de Semana 3 (TF-IDF + SGD, L2 y parada temprana) permanece separado. Aquí no se entrenó E5 ni un LLM; tampoco se creó generación o interfaz.
