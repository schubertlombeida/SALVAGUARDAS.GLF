# Protocolo inicial de evaluación de recuperación

Estado: infraestructura implementada; no existen resultados de relevancia validados.

## Revisión humana

El archivo evaluation/queries_draft.jsonl propone diez consultas de desarrollo. No son preguntas de prueba ni etiquetas verdaderas. El especialista debe comprobar su utilidad para GLF, reformularlas si corresponde y buscar evidencia en el corpus completo. La web permite leer el texto y copiar el identificador de cada fragmento.

En una copia privada del archivo, registrar relevant_chunk_ids, reviewer y notes con la justificación de pertinencia; cambiar review_status a approved únicamente después de revisar. Conservar la copia en data/processed, excluida de Git. Las consultas sin respuesta requieren una evaluación separada de abstención; este evaluador rechaza conjuntos relevantes vacíos.

No etiquetar exclusivamente los primeros cinco resultados de BM25: eso favorece al sistema evaluado. Revisar documentos completos y, cuando esté disponible E5, un conjunto combinado de candidatos de varios recuperadores. Si la revisión no es exhaustiva, declarar que Recall se calcula respecto de relevancia conocida y que puede existir evidencia aún no anotada. Los fragmentos solapados pueden compartir contenido; la unidad adoptada aquí es fragmento, no documento.

## Particiones y métricas

Estas diez preguntas sirven para desarrollo. No representan los 18/4/4 expedientes ni reemplazan su división. Las preguntas derivadas de un expediente deben conservar la partición de ese expediente. Reservar consultas de prueba independientes antes de ajustar métodos. Ejecutar cada partición por separado; no ajustar después de consultar la prueba.

Recall@5 = relevantes recuperados en los primeros cinco / total de relevantes anotados. La agregación es media por consulta. Precision@5 usa denominador cinco aunque haya menos resultados. Hit Rate@5 indica si existe al menos un acierto; no es Recall. Con más de cinco fragmentos relevantes, Recall@5 no puede alcanzar uno: reportar la distribución de tamaños de los conjuntos relevantes al interpretar la meta del 80 %.

La p95 que registra el script usa el percentil de rango más próximo de los tiempos de búsqueda local. Excluye carga del índice, interfaz, red y generación: no permite declarar cumplida la meta de siete segundos del sistema completo. Diez consultas de desarrollo tampoco constituyen un benchmark final suficiente.

## Ejecución

```sh
python -m src.evaluation --archive /ruta/GLF_SGAS_Corpus_ES.zip --labels data/processed/queries_reviewed.jsonl --output results/metrics/bm25_development.json
```

El programa rechaza borradores, etiquetas vacías, identificadores inexistentes, duplicados y mezcla de particiones. Guarda métricas por consulta y hashes de ZIP y etiquetas para reproducibilidad. No se ha ejecutado una evaluación real con etiquetas aprobadas. Las pruebas automáticas usan ejemplos sintéticos únicamente para verificar cálculos.

Este protocolo evalúa recuperación. No sustituye las curvas de entrenamiento ni las dos intervenciones exigidas para semana 3.
