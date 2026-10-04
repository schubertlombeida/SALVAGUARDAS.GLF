# Evidencia reutilizable para el proyecto final

| Elemento | Valor / fuente |
|---|---|
| Corpus | ZIP GLF SGAS español, SHA-256 `37c8a747c32c069642f501ef967c9119175a3da7e8b71d14f2910118d3e11267` |
| Composición | 36 documentos y 585 chunks normativos en español |
| Gold v1 | `dataset_gold_human_reviewed_v1.csv`; hash en `validacion_gold_humano.json` y `metricas_recuperacion_human_v1.json` |
| Gold IA anterior | `dataset_gold.csv`, SHA-256 `c3cdc04cc06a9ed2936491498aa373e22f61bea87e8095bd2e9cbb02abe4fe3b` |
| Modelo semántico | `intfloat/multilingual-e5-base`, revisión `d128750597153bb5987e10b1c3493a34e5a4502a`; solo inferencia, sin fine-tuning |
| BM25 | `src.retrieval.BM25`, k1=1,5; b=0,75; tokenización española existente |
| Híbrido | RRF con profundidad 20 y constante 60, sin ajuste |
| Evaluación | 50 preguntas; Top 5; Recall@1/3/5, Hit@1/3/5, MRR@5, media/p50/p95 de latencia local; global y por split |
| Fecha | Fecha de evaluación y hashes generados en `metricas_recuperacion_human_v1.json` |
| Resultado global | BM25 Recall@5 75,0 %, Hit@5 88,0 %; E5 68,3 %/80,0 %; híbrido 75,0 %/84,0 % |
| Decisión actual | Mantener baselines sin optimizar hasta cerrar auditoría de negativos, cruces documentales y datos del revisor |

Limitaciones: el usuario confirmó revisión manual de **positivos** y cambios de preguntas, pero no entregó una lista de negativos aprobados ni nombre/fecha real del revisor. Hay tres positivos que cruzan la asignación documental de splits para pares. La latencia p95 es solo de búsqueda local precargada; no demuestra el KPI extremo a extremo de 7 s. El límite total de USD 200 no está medido. El test se mantiene congelado para selección. El corpus y los CSV con texto permanecen fuera del GitHub público.

Este registro es insumo de trazabilidad, no la entrega final ni una declaración de cumplimiento institucional.
