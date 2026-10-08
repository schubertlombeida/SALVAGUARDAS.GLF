# Instrucciones para continuar y desplegar el proyecto GLF

## Estado del proyecto

La parte técnica principal del proyecto ya está terminada:

- Semanas 1 a 5 completadas en contenido.
- RAG funcional.
- Recuperador `BM25-heading-authority-v2`.
- Generación con Qwen 2.5 7B.
- Citas verificables y abstención segura.
- Interfaz web integrada.
- Optimización y evaluación documentadas.
- 26 tests aprobados, 2 omitidos por depender de artefactos privados/locales.
- Recall@5 desarrollo: 83,6%.
- Recall@5 validation: 90,9%.
- Latencia p95 local: 4,617 s.

Lo pendiente pertenece al cierre final: despliegue público seguro, capturas/manual, video pitch y video de preguntas del profesor.

---

## Ruta rápida — lo mínimo que debe hacer el compañero

### 1. Instalar Ollama en Windows

Descarga oficial directa:

https://ollama.com/download/windows

O, más fácil, abrir PowerShell y ejecutar:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Ollama requiere Windows 10 o posterior.

### 2. Descargar el modelo exacto usado por el proyecto

Página oficial del modelo:

https://ollama.com/library/qwen2.5:7b

Comando:

```powershell
ollama pull qwen2.5:7b
```

El modelo ocupa aproximadamente 4.7 GB.

### 3. Clonar el proyecto

```powershell
git clone https://github.com/schubertlombeida/SALVAGUARDAS.GLF.git
cd SALVAGUARDAS.GLF
python -m pip install -r requirements.txt
```

### 4. Recibir el corpus privado

El equipo debe enviarle aparte:

`GLF_SGAS_Corpus_ES.zip`

No está publicado en GitHub.

### 5. Ejecutar

```powershell
$corpus = "C:\GLF\GLF_SGAS_Corpus_ES.zip"
$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = "qwen2.5:7b"
python -m app.server --archive "$corpus" --port 8765
```

Abrir:

`http://127.0.0.1:8765`

### Tiempo orientativo

Con una conexión normal y Python ya instalado:

- Ollama: 2–5 minutos.
- Clonar GitHub + dependencias: 3–8 minutos.
- Qwen 2.5 7B: depende de Internet; son ~4.7 GB.
  - 100 Mbps: ~7–10 minutos reales.
  - 50 Mbps: ~15 minutos.
  - 20 Mbps: ~30–40 minutos.
- Configurar y abrir el RAG: 2–5 minutos.

En una PC normal y con Internet razonable, calcular **20–40 minutos** para tenerlo funcionando. Con Internet lento, **45–60 minutos**.

---

# 1. Probar la versión completa en otra PC

## Requisitos

Instalar:

- Git
- Python 3.11+
- Ollama

Clonar el repositorio:

```powershell
git clone https://github.com/schubertlombeida/SALVAGUARDAS.GLF.git
cd SALVAGUARDAS.GLF
python -m pip install -r requirements.txt
```

Descargar el mismo modelo usado por el equipo:

```powershell
ollama pull qwen2.5:7b
```

El archivo privado del corpus no está en GitHub. Debe recibirse por un canal privado:

`GLF_SGAS_Corpus_ES.zip`

Ejemplo de ubicación:

```text
C:\GLF\GLF_SGAS_Corpus_ES.zip
```

Arrancar la aplicación:

```powershell
$corpus = "C:\GLF\GLF_SGAS_Corpus_ES.zip"
$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = "qwen2.5:7b"

python -m app.server --archive "$corpus" --port 8765
```

Abrir:

```text
http://127.0.0.1:8765
```

Ejecutar pruebas:

```powershell
python -m pytest -q
```

Resultado esperado en la versión validada:

```text
26 passed, 2 skipped, 0 failed
```

---

# 2. Qué contiene GitHub

La rama `main` contiene la versión académica completa:

- `app/`: interfaz y servidor local.
- `src/`: recuperador y lógica.
- `notebooks/`: exploración, modelado, optimización y evaluación.
- `docs/`: documentación final obligatoria.
- `results/`: métricas, gráficos y reportes.
- `tests/`: pruebas automatizadas.
- `evaluacion_rag/`: artefactos y scripts de evaluación.

El modelo Qwen no está guardado dentro de GitHub. Cada PC lo descarga con Ollama.

El corpus privado tampoco se publica en GitHub.

---

# 3. Rama para demo pública segura

Existe una rama separada:

`deploy/secure-public-demo`

No debe confundirse con la versión completa local.

Esta variante:

- no usa el ZIP privado;
- no tiene acceso a la PC del equipo;
- utiliza únicamente documentos oficiales públicos del GLF;
- exige código de acceso;
- limita consultas por IP;
- limita el número global diario de consultas;
- no permite subir archivos;
- usa Hugging Face para la generación;
- está preparada para Render.

Existe un PR en borrador para esta rama. No mezclarlo con `main` antes de comprobar que la demo funciona correctamente.

---

# 4. Despliegue público

Objetivo:

```text
Profesor
   ↓
URL pública de Render
   ↓
Código de acceso
   ↓
RAG con documentos públicos
   ↓
Hugging Face / Qwen
```

La PC de ningún integrante queda expuesta.

## Render

Crear un Web Service desde el repositorio y seleccionar:

`deploy/secure-public-demo`

Build command:

```text
pip install -r public_demo/requirements.txt && python -m py_compile public_demo/app.py && python -m public_demo.smoke_test
```

Start command:

```text
gunicorn public_demo.app:app --workers 1 --threads 4 --timeout 90
```

Health check:

```text
/healthz
```

Variables secretas:

- `HF_TOKEN`
- `DEMO_ACCESS_CODE`

Variables normales recomendadas:

- `HF_MODEL=Qwen/Qwen2.5-7B-Instruct-1M:fastest`
- `RATE_LIMIT_PER_HOUR=15`
- `GLOBAL_DAILY_LIMIT=60`

No guardar tokens ni claves en GitHub.

---

# 5. Pruebas de aceptación antes de entregar

Probar desde un dispositivo diferente, preferiblemente celular usando datos móviles:

1. Abrir la URL pública.
2. Introducir el código de acceso.
3. Preguntar por la Lista de Exclusión.
4. Preguntar por evaluación de la detección.
5. Preguntar por Categoría B vs C.
6. Probar una pregunta fuera de dominio.
7. Confirmar que aparecen:
   - respuesta;
   - citas;
   - evidencia;
   - páginas;
   - enlaces a fuentes oficiales;
   - abstención segura cuando corresponde.
8. Confirmar que una clave incorrecta devuelve acceso denegado.

---

# 6. Qué NO hacer

- No subir `GLF_SGAS_Corpus_ES.zip` al repositorio público.
- No subir tokens de Hugging Face.
- No subir contraseñas.
- No abrir puertos del router.
- No usar ngrok permanente sobre una PC personal.
- No cambiar los hiperparámetros del recuperador final sin repetir evaluación.
- No presentar el holdout como validación humana independiente.
- No decir que el asistente aprueba proyectos o financiamiento.

---

# 7. Pendientes finales de presentación

Después de tener la URL pública funcionando:

1. Añadir 1–2 capturas reales al manual de usuario.
2. Añadir la URL pública al README.
3. Crear QR de la aplicación para el pitch.
4. Grabar video pitch máximo 5 minutos.
5. Añadir link del pitch al README.
6. Cuando lleguen las preguntas del profesor, grabar segundo video.
7. Añadir link del segundo video al README.

---

# 8. Resumen rápido

La parte de IA ya está construida. El trabajo restante es principalmente:

```text
Clonar → probar localmente → publicar demo segura → probar URL → capturas → videos → entrega
```
