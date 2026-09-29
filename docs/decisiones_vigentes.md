# Decisiones vigentes de GLF

Actualización del 27 de septiembre de 2026. Esta referencia consolida las decisiones explícitas del equipo y los datos comprobados; los documentos de semana 1 se conservan como entregas históricas.

| Elemento | Referencia vigente | Estado |
|---|---|---|
| Recall@5 | ≥ 80 % | Meta sin medición |
| Latencia p95 | ≤ 7 segundos | Meta sin medición |
| Presupuesto | Máximo USD 200 | Consumo pendiente de registro |
| Expedientes emparejados | 26 | Verificado en CSV y JSONL |
| Partición | 18 desarrollo, 4 validación, 4 prueba | Verificada por expediente |
| Documentos de casos | 56, incluidos 2 de contexto | Verificado |
| Fragmentos de casos | 250 | Verificado |
| Corpus normativo español | 585 fragmentos | Verificado |
| Corpus normativo general | 1.272 fragmentos de 88 textos normalizados | Verificado |
| Arquitectura | BM25, E5 multilingüe, fusión, reglas, RAG con citas y revisión humana | Diseño; implementación pendiente |

No presentar 30 expedientes como disponibles: son una ampliación prevista, no acreditada por los archivos. No presentar 148.082 palabras del inventario como recuento del texto procesado: este último suma 147.470. Los 166.870 términos de los fragmentos de casos incluyen solapamiento.

Recall@5 se calculará como relevantes recuperados entre los cinco primeros dividido por el total de relevantes para cada consulta. Se debe fijar la unidad de relevancia y la agregación antes de evaluar. No equivale a Hit Rate@5.

Los objetivos adicionales de documentos previos, como Precision@5 y F1 de alertas, requieren un protocolo y etiquetas propios; no se declaran evaluados.
