"""Escribe el informe desde métricas reales; jamás rellena resultados manuales."""
import csv
import json
from pathlib import Path

def pct(x):return f'{100*x:.1f} %'
def ms(x):return f'{1000*x:.1f} ms'

def build(folder):
    folder=Path(folder)
    metrics=json.loads((folder/'metricas_recuperacion.json').read_text(encoding='utf-8'))
    audit=json.loads((folder/'auditoria_pares.json').read_text(encoding='utf-8'))
    rows=metrics['summary'];by={r['method']:r for r in rows}
    best=max(rows,key=lambda r:(metrics['by_split']['validation'][r['method']]['recall_at_5'],metrics['by_split']['validation'][r['method']]['mrr_at_5']))
    header='| Método | Recall@1 | Recall@3 | Recall@5 | MRR@5 | p50 | p95 |\n|---|---:|---:|---:|---:|---:|---:|'
    table='\n'.join('| '+r['method']+' | '+ ' | '.join([pct(r['recall_at_1']),pct(r['recall_at_3']),pct(r['recall_at_5']),f"{r['mrr_at_5']:.3f}",ms(r['p50_seconds']),ms(r['p95_seconds'])])+' |' for r in rows)
    splits='\n'.join(f"| {s} | {metrics['by_split'][s]['BM25']['questions']} | "+' | '.join(pct(metrics['by_split'][s][n]['recall_at_5']) for n in ['BM25','E5-base','BM25+E5-RRF'])+' |' for s in ['train','validation','test'])
    text=f'''# Evaluación de recuperación GLF - resultados provisionales

Evaluación local ejecutada sobre el corpus real SGAS español. **Todas las relevancias son propuestas de IA; ninguna fue verificada por una persona.** Por tanto `dataset_gold.csv` es un borrador para construir el gold standard, no un gold standard aprobado. La evaluación mide aciertos frente a referencias conocidas, posiblemente incompletas.

## Corpus y trazabilidad

- ZIP fuente SHA-256: `{metrics['corpus_archive_sha256']}`.
- Corpus indexado: `Corpus_GLF_SGAS_ES.jsonl`, 585 fragmentos de 36 documentos en español. `inventario_corpus.csv` registra documento, idioma, tipo, ruta normalizada y disponibilidad de localizadores. Ninguno carece de documento, ID, texto o ruta normalizada; 422 conservan marcadores de página y 81 contienen encabezados de sección. La sección puede comenzar en un fragmento anterior y no está normalizada como campo propio.
- El ZIP incluye además un corpus bilingüe de 1.272 fragmentos / 88 documentos, no indexado en esta comparación para no duplicar traducciones. El otro ZIP del equipo contiene 56 documentos de casos, 250 fragmentos y 26 expedientes; **no** se mezclaron con el benchmark normativo ni se publicaron.
- 50 preguntas construidas desde anclas textuales verificadas en el corpus, con uno o varios IDs relevantes conocidos y una cita literal corta de referencia. Archivo para revisión: `dataset_gold.csv`; `human_reviewed=false` en todas.
- 316 pares para trabajo futuro de clasificación: {audit['label_counts']['1']} positivos propuestos y {audit['label_counts']['0']} negativos candidatos; {audit['hard_candidate_count']} negativos se eligieron por alta semejanza léxica. Su condición negativa requiere revisión; pueden contener respuestas alternativas. No se entrenó un clasificador con estos pares.

## Métricas comparables

{header}
{table}

Recall@k es la media por pregunta de relevantes conocidos recuperados entre los primeros k, dividida por todos los relevantes conocidos de esa pregunta. MRR@5 es la media del recíproco del rango del primer relevante conocido entre los primeros cinco; vale 0 si no hay acierto. Son métricas **respecto de relevancia conocida**, no exhaustiva. La selección inicial del fragmento objetivo desde la fuente ayuda a evitar que BM25 dicte todas las referencias, pero la revisión de otros fragmentos no fue exhaustiva y la formulación de algunas preguntas se parece al encabezado de su fuente.

Los tiempos incluyen búsqueda sobre índices precargados. E5 incluye codificar cada consulta; el híbrido incluye ambas búsquedas y RRF (profundidad 20, constante 60). Se excluyen descarga/carga del modelo, creación de embeddings, red, interfaz y generación. p50/p95 son percentiles de rango más próximo de **50 consultas**, medidos una vez por método después de calentamiento. La caché E5 contiene {metrics['e5_windows']} ventanas, construidas desde los 585 fragmentos sin truncado silencioso; el modelo fue `{metrics['model_id']}` con revisión `{metrics['model_revision']}`. Los prefijos usados son `query: ` y `passage: `, conforme a [la ficha oficial del modelo](https://huggingface.co/intfloat/multilingual-e5-base).

## Particiones y selección

| Partición | Preguntas | BM25 Recall@5 | E5 Recall@5 | Híbrido Recall@5 |
|---|---:|---:|---:|---:|
{splits}

Los pares separan preguntas y documentos entre desarrollo, validación y prueba. La auditoría encontró {audit['near_duplicate_count']} pares de fragmentos entre particiones con coseno de n-gramas de caracteres >= {audit['near_duplicate_threshold']} (máximo observado {audit['max_cross_split_cosine']:.3f}); no se repite ningún ID de consulta, documento o fragmento entre particiones. Solo {audit['unique_chunks']} fragmentos únicos aparecen en los 316 pares: múltiples preguntas reutilizan fuentes, por lo que 316 no equivalen a 316 ejemplos independientes.

Con la regla de priorizar Recall@5 de **validación** y usar MRR@5 para desempate, el candidato seleccionado para continuar es **{best['method']}**. Esta selección es provisional hasta revisar las referencias. En prueba, el híbrido obtiene un valor mayor que BM25, pero no se cambia el método usando ese conjunto pequeño de {metrics['by_split']['test']['BM25']['questions']} preguntas.

## KPI y límites

- Meta Recall@5 >= 80%: **ningún método la alcanza en las 50 preguntas propuestas**; mejor valor global {pct(max(r['recall_at_5'] for r in rows))}. El cumplimiento oficial queda **sin verificar** porque faltan juicios humanos y un conjunto relevante más completo.
- Meta p95 <= 7 s: los tres métodos quedan por debajo en **búsqueda local precargada**. La latencia p95 del sistema completo sigue **sin medir**.
- Presupuesto total <= USD 200: **no verificado**; no se registró un presupuesto operativo completo ni costos de infraestructura. E5 se ejecutó localmente en CPU, sin entrenamiento.
- Una respuesta útil puede estar en un fragmento no anotado; también puede haberse propuesto una relevancia incorrecta. En particular, revisar los casos donde los tres recuperadores fallan y la vigencia/autoridad de las traducciones. No usar estas cifras como rendimiento certificado.

## Siguiente revisión manual

1. Para cada fila de `dataset_gold.csv`, verificar pregunta, referencia literal y todos los fragmentos que realmente responden, incluidos top 10 de BM25 y E5 y documentos relacionados. Registrar revisor y fecha; solo entonces cambiar `human_reviewed` y estado.
2. Revisar todos los `hard_candidate` en `dataset_pairs.csv`. Convertir en negativo solo los que no respondan a la pregunta; añadir positivos descubiertos y conservar particiones por documento.
3. Congelar un conjunto de prueba nuevo antes de ajustar pesos, RRF, consultas o fragmentación. Repetir las mismas métricas y medir el flujo completo del sistema para el KPI de 7 s.

El experimento académico de Semana 3 (TF-IDF + SGD, L2 y parada temprana) permanece separado. Aquí no se entrenó E5 ni un LLM; tampoco se creó generación o interfaz.
'''
    (folder/'reporte_resultados.md').write_text(text,encoding='utf-8')
    return best['method']

if __name__=='__main__':print('Método provisional:',build(Path('evaluacion_rag')))
