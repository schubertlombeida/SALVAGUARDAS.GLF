# E5 y búsqueda híbrida

Estado: código integrado en el evaluador; inferencia real pendiente. Este equipo no tiene torch, transformers ni sentence-transformers instalados. La web continúa usando BM25.

Modelo previsto: intfloat/multilingual-e5-small, CPU. Se usan prefijos query: y passage:, embeddings normalizados y producto escalar. Cada fragmento largo se divide recursivamente por palabras hasta que sus pasajes caben en 512 tokens incluyendo prefijo y tokens especiales. Su puntuación es el máximo de sus pasajes. Esta agregación puede favorecer fragmentos largos y debe contrastarse en evaluación.

Fusión RRF: sumar 1/(60+rango) para los primeros 20 resultados de cada recuperador. Son parámetros iniciales, no valores optimizados ni mejoras demostradas.

La ficha del modelo respalda los prefijos y el límite de tokens:
https://huggingface.co/intfloat/multilingual-e5-small

## Próxima ejecución

Crear un entorno separado, instalar sentence-transformers y PyTorch CPU desde sus distribuidores oficiales y registrar las versiones resueltas. La primera carga descarga los pesos. No usa una API de pago, pero necesita espacio en disco y tiempo de descarga. Fijar también la revisión del modelo antes de los experimentos finales.

```sh
python -m src.evaluation --method e5 --archive /ruta/corpus.zip --labels data/processed/queries_reviewed.jsonl --output results/metrics/e5_development.json
python -m src.evaluation --method hybrid --archive /ruta/corpus.zip --labels data/processed/queries_reviewed.jsonl --output results/metrics/hybrid_development.json
```

Las pruebas actuales verifican división sin pérdida y fusión de rankings con datos sintéticos. No prueban la calidad del modelo ni su velocidad. Antes de conectarlo a la web se requiere probar carga e inferencia real, registrar memoria/latencia, almacenar embeddings reproducibles y revisar relevancia. No afirmar que E5 mejora BM25 hasta medirlo con las mismas etiquetas.
