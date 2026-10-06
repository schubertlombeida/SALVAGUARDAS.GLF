# Evaluación y optimización del RAG — gold operativo v2

## Estado

El asistente GLF usa un recuperador optimizado reproducible denominado
`BM25-heading-authority-v2`. La selección se realizó exclusivamente con
train y validation; test no se utilizó para escoger modelo ni parámetros.

## Corpus y gold

- Corpus normativo: 36 documentos y 585 fragmentos en español.
- SHA-256 del corpus: `37c8a747c32c069642f501ef967c9119175a3da7e8b71d14f2910118d3e11267`.
- Gold operativo v2: 50 preguntas y 82 relaciones relevantes.
- SHA-256 del gold v2: `f3421f2343f30930912c7499312fd2120b645b9c11b2e81632bc03bb62f21461`.
- Negativos adjudicados en train/validation: 186.
- Candidatos de test pendientes de adjudicación independiente: 60.

Los archivos con texto completo del corpus y el gold operativo permanecen
fuera del repositorio público.

## Comparación

| Método | Recall@5 train+validation |
|---|---:|
| BM25 baseline v2 | 68,9 % |
| E5-base v2 (rankings congelados) | 61,8 % |
| BM25 + E5 RRF v2 | 68,6 % |
| Recuperador web previo | 70,2 % |
| **BM25-heading-authority-v2** | **83,6 %** |

El método seleccionado obtiene:

- Recall@5 train: **80,6 %**.
- Recall@5 validation: **90,9 %**.
- Recall@5 train+validation: **83,6 %**.
- Hit@5 train+validation: **94,7 %**.

## Configuración

- BM25 de cuerpo: k1=0,8; b=0,2.
- BM25 de encabezados: k1=1,2; b=0,3.
- Peso adicional de encabezados: 0,30.
- Prioridad pequeña para fuente GLF: 0,15.
- Top-k: 5.

No contiene excepciones por `question_id`, respuestas fijas ni IDs de chunks.
La idea es dar mayor valor a encabezados normativos informativos y a la fuente
primaria GLF sin excluir las referencias internacionales.

Varias configuraciones cercanas también superaron 80 % simultáneamente en
train y validation, por lo que el resultado no depende de un único punto
aislado de la rejilla.

## Integración

La aplicación local carga `src/retrieval_optimized.py` desde
`app/server.py`. Se conserva el recuperador BM25 original para reproducir
baselines históricos.

Las consultas que comparan varias categorías aplican únicamente un desempate
genérico por cobertura de las categorías solicitadas. No se programa una
respuesta particular para A, B o C.

## KPI de latencia

La latencia de recuperación es del orden de milisegundos, pero esto no
certifica la meta p95 <= 7 s del sistema completo.

Para medir el KPI extremo a extremo con Ollama real se añadió:

- `scripts/benchmark_e2e.py`
- `scripts/run_local_final_validation.ps1`

El benchmark llama a `POST /api/ask` y mide recuperación + generación local
con Qwen. Por defecto utiliza solamente train/validation y excluye el
calentamiento.

## Regla de cierre

Antes de declarar el KPI final del proyecto:

1. medir p95 extremo a extremo en el equipo de demostración;
2. conservar la configuración seleccionada sin más ajuste por test;
3. obtener una adjudicación independiente del holdout/test o construir un
   holdout final nuevo y ciego;
4. realizar una única evaluación final predefinida;
5. documentar costo total frente al límite de USD 200.

El 83,6 % actual demuestra cumplimiento de Recall@5 en desarrollo/validación,
no una certificación independiente de producción.
