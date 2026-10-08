# Evaluación del RAG — versión final académica

## Sistema evaluado

Recuperador: **BM25-heading-authority-v2**  
Corpus: **585 fragmentos normativos en español**  
Generador: **Qwen 2.5 7B local vía Ollama**  
Top-k: **5**

La selección de parámetros se realizó solo con train y validation. El test histórico no se utilizó para escoger la configuración.

## Resultados de recuperación

| Método | Recall@5 train+validation |
|---|---:|
| E5-base | 61.8% |
| BM25 + E5 RRF | 68.6% |
| BM25 baseline | 68.9% |
| Recuperador web previo | 70.2% |
| **BM25-heading-authority-v2** | **83.6%** |

Configuración final:

- Recall@5 train: **80.6%**
- Recall@5 validation: **90.9%**
- Recall@5 desarrollo: **83.6%**
- Hit@5 desarrollo: **94.7%**
- MRR@5 desarrollo: **0.752**

## Auditoría post-congelamiento

Después de congelar el recuperador se evaluó un holdout nuevo de 20 preguntas:

- Recall@5: **85.0%**
- Hit@5: **85.0%**

Las preguntas y respuestas de referencia fueron pre-revisadas por IA y confirmadas por el usuario. Por transparencia, este resultado se reporta como auditoría post-congelamiento y **no** como validación humana independiente.

## Latencia extremo a extremo

Benchmark local:

- consultas: 40;
- calentamiento excluido: 3;
- exitosas: 40/40;
- fallos HTTP: 0;
- abstenciones seguras: 2;
- p50: **1.815 s**;
- p95: **4.617 s**;
- meta: **p95 ≤7 s**;
- resultado: **cumple**.

El alcance de la medición fue `POST /api/ask`: recuperación + generación local. No incluye latencia de una red pública.

## Robustez funcional

La interfaz se probó manualmente con consultas representativas y una pregunta fuera de dominio. La pregunta fuera del corpus produjo abstención segura en vez de inventar una respuesta.

La suite automática actual obtuvo:

- **26 passed**
- **2 skipped**
- **0 failed**

Los tests omitidos requieren CSV privados/locales de evaluación que no se publican.

## Interpretación

Los KPIs técnicos definidos para la entrega académica se cumplen:

- Recall@5 ≥80%: cumplido.
- p95 ≤7 s: cumplido.

Esto no equivale a certificación institucional ni garantiza que cada respuesta sea completa. La herramienta requiere verificación de las fuentes por una persona autorizada.
