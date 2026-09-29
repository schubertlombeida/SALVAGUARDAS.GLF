# Web local GLF 0.1

Implementada el 28 de septiembre de 2026. Ejecutar desde la raíz:

```sh
python -m app.server --archive /ruta/GLF_SGAS_Corpus_ES.zip
python -m unittest discover -s tests -v
```

Visitar http://127.0.0.1:8765. Puerto opcional: --port 8766. El ZIP se proporciona localmente; no se incluye en GitHub. El servidor solo escucha en 127.0.0.1 y no está preparado para despliegue público.

## Funciones disponibles
- Búsqueda BM25 en los 585 fragmentos normativos en español.
- Hasta cinco resultados con documento, fragmento, idioma, tipo de fuente, puntuación y texto completo.
- Consultas de ejemplo, validación, procesamiento, errores y ausencia de coincidencias.
- Interfaz adaptable y contenido de resultados insertado como texto, no HTML.
- Sin APIs externas, almacenamiento de consultas ni logs del texto consultado.

## Validación
Siete pruebas automáticas aprobadas: cuatro de EDA y tres de recuperación/API. Prueba de navegador con consulta de participación y quejas: cinco resultados reales y referencias visibles. El tiempo mostrado corresponde únicamente a esa consulta; no es latencia p95 ni una evaluación de relevancia. Revisión visual de la interfaz en el navegador integrado.

## Límites
BM25 usa coincidencia de términos con normalización de acentos, sin embeddings ni generación. No incluye carga de PDF, matriz de 17 campos, evaluación de riesgo o recomendaciones. La puntuación no es una probabilidad. No se dispone de páginas verificadas por fragmento. Recall@5 permanece sin medir hasta contar con consultas y relevancia revisadas. Las curvas y mejoras de semana 3 siguen pendientes de una tarea entrenable y etiquetas adecuadas.
