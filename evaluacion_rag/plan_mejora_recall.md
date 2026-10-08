# Plan de mejora de Recall@5 (sin ejecutar)

**Condición previa:** revisar las 50 preguntas, sus referencias y todos los candidatos Top 10; resolver falsos negativos y documentar la vigencia de las fuentes. Congelar entonces una versión del gold standard y registrar su hash. Los 147 hard negatives son candidatos no verificados. No hay nuevos valores de Recall en esta etapa.

## Protocolo común

Mantener fijo el corpus autorizado y el conjunto de preguntas aprobado para cada comparación. Trabajar con **train** durante desarrollo; usar **validation** para seleccionar configuraciones dentro de una lista pequeña definida por anticipado. Registrar configuración, versión de corpus, etiquetas y costo/latencia. Reservar **test** congelado para una única evaluación final del método seleccionado; no elegir con él BM25, parámetros RRF, pesos, chunking ni modelo. Si se cambia el corpus, las preguntas o la definición de relevancia, versionar el benchmark y no comparar números como si fueran equivalentes.

## Orden de experimentación

A. **BM25 y preprocesamiento.** Revisar tokenización española, acentos, stopwords, expansión controlada de siglas GLF/SGAS y normalización de referencias. Ensayar una pequeña rejilla de `k1` y `b` sobre train/validation; medir Recall@5 y latencia. Conservar el baseline actual.

B. **Chunking.** Inspeccionar fragmentos cortados en medio de una respuesta, encabezados separados del texto y metadatos de página. Probar tamaños/solapamientos definidos de antemano; mantener la trazabilidad al documento y página. Reetiquetar las referencias afectadas antes de comparar, porque cambian los IDs y el denominador de Recall.

C. **Parámetros de fusión híbrida.** Con el mismo corpus y E5-base congelado, contrastar pocas profundidades de recuperación y constantes RRF usando únicamente train/validation. No escoger por test ni por el mejor resultado aislado de una pregunta.

D. **Weighted fusion o RRF.** Si C no basta, comparar RRF con una suma ponderada de scores normalizados. Definir pesos y normalización en train; escoger con validation y registrar sensibilidad a cambios pequeños.

E. **Reranking, si sigue siendo necesario.** Probar un reranker preentrenado sobre una lista candidata acotada, sin entrenarlo con test. Medir Recall@5, p95 de recuperación y costos; descartar si la latencia del sistema completo amenaza el límite de 7 s.

F. **Fine-tuning de E5, solo como último recurso.** Requiere suficientes pares positivos y negativos difíciles **verificados por humanos**, nueva partición sin fuga y comparación contra E5-base sin ajuste. No entrenar con etiquetas IA no revisadas. Registrar presupuesto total frente al límite de USD 200.

La meta oficial es Recall@5 >=80 % con p95 **de extremo a extremo** <=7 s y presupuesto total <=USD 200. Ninguna mejora se declarará conseguida hasta medirla sobre el gold standard validado y, al final, sobre test congelado.
