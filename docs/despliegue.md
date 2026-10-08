# Presentación y despliegue gratuito

Propuesta al 28 de septiembre de 2026; aún no desplegado.

## Opción principal
Hugging Face Spaces CPU Basic: documentación consultada indica 2 vCPU y 16 GB RAM gratuitos. Puede suspenderse por inactividad. Preparar contenedor Docker y servidor de aplicación adecuado; el servidor actual app/server.py es exclusivamente de desarrollo local y no debe exponerse directamente.

Referencia: https://huggingface.co/docs/hub/spaces-overview

## Distribución de responsabilidades
- GitHub: código, documentación y resultados agregados.
- Drive del equipo: fuentes originales y archivos privados, con acceso restringido. No ejecuta el servidor Python.
- Hugging Face Space: aplicación web de demostración y corpus cuya publicación esté autorizada.
- PC local: respaldo de la presentación si hay problemas de Internet o arranque del servicio.

## Datos
La versión de consulta no necesita una base de datos externa: JSONL para textos y metadatos e índice en memoria. Los 585 fragmentos normativos son manejables con esta arquitectura. E5 requerirá embeddings e índice precalculados, cuya memoria y latencia se medirán antes de prometer rendimiento.

Si posteriormente se guardan usuarios, revisiones, expedientes e historial compartido, seleccionar almacenamiento persistente y control de acceso. No colocar SQLite ni archivos de usuario en almacenamiento efímero suponiendo que persistirán.

## Pasos pendientes
1. Sustituir el servidor de desarrollo por una aplicación y servidor adecuados para despliegue, con límites y manejo de errores.
2. Separar corpus autorizado para demostración de expedientes privados. Que una fuente esté accesible no prueba permiso de redistribución.
3. Preparar Dockerfile, configuración de puerto, comprobación de salud y prueba local del contenedor.
4. Crear el Space en una cuenta del equipo y verificar CPU Basic gratuito; no contratar GPU ni recursos pagados.
5. Publicar solo el material autorizado, comprobar búsqueda y fuentes desde otro equipo.
6. Medir arranque en frío y operación normal por separado. Abrir la demo con antelación a la defensa y conservar copia local y video.

El alojamiento gratuito no implica que una API externa de generación sea gratuita. BM25 actual no usa una API de pago. El modelo generativo sigue pendiente de selección y evaluación bajo el presupuesto máximo USD 200.

Alternativas verificadas: Streamlit Community Cloud gratuito (requiere adaptar la interfaz a Streamlit); Render gratuito (suspende tras 15 minutos sin tráfico y usa disco efímero).
https://docs.streamlit.io/deploy/streamlit-community-cloud
https://render.com/docs/free

## Preparación implementada

Servidor WSGI en app/wsgi.py con Waitress 3.0.2, Dockerfile sin datos, lista explícita de archivos permitidos en .dockerignore y plantilla docs/SPACE_README.md. No se ha publicado un Space ni probado el contenedor: Docker no está disponible en este equipo.

Prueba local del servidor (PowerShell, desde la raíz del repositorio):

```powershell
python -m pip install -r requirements-web.txt
$env:GLF_CORPUS_ZIP = 'C:\ruta\GLF_SGAS_Corpus_ES.zip'
python -m app.wsgi
```

Abrir http://127.0.0.1:7860. Sin corpus configurado, /healthz y /api/status responden 503: el sistema no debe presentarse como listo.

Para Docker local, cuando esté disponible:

```sh
docker build -t glf-demo .
docker run --rm -p 127.0.0.1:7860:7860 --mount type=bind,source=/ruta/corpus.zip,target=/data/corpus.zip,readonly -e GLF_CORPUS_ZIP=/data/corpus.zip glf-demo
```

El montaje anterior sirve para pruebas locales. En Spaces todavía falta elegir y configurar la entrega del corpus autorizado al contenedor; no existe descarga automática desde Drive ni se incluyen credenciales. La aplicación pública no guarda historial y sirve evidencia a cualquier visitante: solo debe recibir datos aptos para mostrarse públicamente.

Validación realizada: once pruebas automáticas aprobadas y prueba HTTP real con Waitress 3.0.2, salud 200, 585 fragmentos cargados y cinco resultados de búsqueda. No constituye medición de Recall ni p95.
