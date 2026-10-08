# Demo pública segura del RAG GLF

Esta carpeta contiene una variante aislada para publicación académica.

## Diferencias frente a la versión local

- No usa `GLF_SGAS_Corpus_ES.zip`.
- No tiene acceso a la PC del equipo.
- Descarga únicamente una lista fija de documentos oficiales publicados por GLF.
- No acepta archivos del usuario.
- Genera respuestas con Hugging Face Inference Providers usando un token guardado como secreto de Render.
- Incluye código de acceso, límite de consultas, validación de entrada y cabeceras de seguridad.
- Las consultas no se escriben en archivos ni bases de datos.

## Fuentes públicas

Los PDFs se descargan directamente de `galapagoslifefund.org.ec` al iniciar el servicio. La lista es fija en `PUBLIC_DOCS` y no se acepta una URL proporcionada por el usuario.

## Despliegue en Render

1. Crear una cuenta gratuita en Render.
2. Crear un **Web Service** desde el repositorio público.
3. Seleccionar la rama `deploy/secure-public-demo`.
4. Build command:
   ```
   pip install -r public_demo/requirements.txt
   ```
5. Start command:
   ```
   gunicorn public_demo.app:app --workers 1 --threads 4 --timeout 90
   ```
6. Elegir el plan **Free**.
7. Crear en Render la variable secreta `HF_TOKEN`.
8. Crear otra variable secreta `DEMO_ACCESS_CODE` con una clave que solo compartirá el equipo con el profesor.
9. Opcional: `HF_MODEL=Qwen/Qwen2.5-7B-Instruct-1M:fastest`.
10. Health check: `/healthz`.

También se incluye `render.yaml` para Blueprint.

## Seguridad

No introducir tokens en GitHub. El token de Hugging Face debe configurarse exclusivamente como secret/environment variable en Render.

La versión pública es una demo académica; no debe procesar expedientes, datos personales ni archivos institucionales privados.
