# Web local del asistente GLF

## Estado

La interfaz local está integrada con el RAG real. Se sirve desde `app/index.html` y consulta `POST /api/ask` en `app/server.py`.

## Inicio

```powershell
$corpus = "C:\ruta\GLF_SGAS_Corpus_ES.zip"
$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = "qwen2.5:7b"
python -m app.server --archive "$corpus" --port 8765
```

Abrir `http://127.0.0.1:8765`.

## Funciones verificadas

- portal visual completo;
- módulo de personal GLF;
- vista “Asistente RAG”;
- recuperación con `BM25-heading-authority-v2`;
- generación local con Qwen 2.5 7B;
- citas por `chunk_id`;
- evidencia visible;
- tiempos de respuesta;
- abstención segura en preguntas fuera del corpus;
- manejo de errores de Ollama;
- validación de longitud de entrada.

## Casos de aceptación manual

Se probaron correctamente:

1. instrumentos obligatorios;
2. evaluación de la detección;
3. comparación Categoría B vs C;
4. pregunta fuera de dominio sobre fútbol.

La primera consulta tras cargar Ollama puede ser más lenta por arranque en frío. Una repetición posterior de la consulta de instrumentos respondió en 1.41 s. El benchmark formal de 40 consultas obtuvo p95 de 4.617 s excluyendo calentamiento.

## Seguridad

El servidor de desarrollo escucha únicamente en `127.0.0.1`. Las preguntas no se guardan en logs. No debe exponerse directamente a Internet.

## Pruebas

```powershell
python -m pytest -q
```

Resultado verificado: **26 passed, 2 skipped, 0 failed**. Los dos tests omitidos requieren artefactos privados de evaluación no incluidos en GitHub.
