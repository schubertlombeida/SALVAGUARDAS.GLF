# Manual de usuario

## 1. Requisitos

- Windows, macOS o Linux con Python 3.11 o superior.
- Ollama instalado.
- Modelo local `qwen2.5:7b`.
- ZIP autorizado `GLF_SGAS_Corpus_ES.zip`.

## 2. Instalación

Desde la raíz del repositorio:

```powershell
python -m pip install -r requirements.txt
ollama pull qwen2.5:7b
```

## 3. Iniciar la aplicación

```powershell
$corpus = "C:\ruta\GLF_SGAS_Corpus_ES.zip"
$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = "qwen2.5:7b"
python -m app.server --archive "$corpus" --port 8765
```

Abrir:

`http://127.0.0.1:8765`

## 4. Acceder al asistente

1. Abrir **Módulo 2: Panel Personal GLF**.
2. En el selector superior elegir **Asistente RAG**.
3. Escribir una pregunta documental.
4. Pulsar **Consultar Corpus**.

## 5. Cómo interpretar la respuesta

La pantalla muestra:

- **Respuesta del Asistente RAG:** síntesis generada por Qwen.
- **Cita:** identificador como `GLF_MANUAL_SGAS_ES::0005`.
- **Evidencia recuperada:** fragmento documental que sustenta la respuesta.
- **Tiempo:** duración extremo a extremo de la consulta.
- **Aviso técnico:** recordatorio de que la decisión institucional sigue siendo humana.

## 6. Ejemplos

### Instrumentos obligatorios
`¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?`

El sistema debe recuperar evidencia del Manual SGAS y citar el fragmento correspondiente.

### Evaluación de la detección
`¿Qué debe hacer el GLF durante la evaluación de la detección?`

La respuesta debe explicar acciones concretas, no mostrar únicamente una cita.

### Comparación
`¿Qué diferencia existe entre los proyectos de Categoría B y Categoría C?`

La respuesta debe nombrar explícitamente ambas categorías y explicar la diferencia respaldada por la fuente.

### Pregunta fuera de dominio
`¿Quién ganó el Mundial de fútbol de 2022?`

El comportamiento esperado es **abstención segura** porque el corpus GLF no contiene evidencia suficiente.

## 7. Mensajes y estados

### Respuesta generada con evidencia
Significa que la salida contiene citas válidas a fragmentos recuperados.

### Abstención segura
El sistema no encontró soporte documental suficiente. No debe interpretarse como error de servidor.

### Error de Ollama
Comprobar que Ollama esté abierto y que `qwen2.5:7b` esté instalado.

## 8. Arranque en frío

La primera consulta después de iniciar Ollama puede tardar más porque el modelo se carga en memoria. Las consultas posteriores suelen ser más rápidas. El benchmark formal, con calentamiento excluido, obtuvo p95 de 4.617 s.

## 9. Ejecutar pruebas

```powershell
python -m pytest -q
```

Resultado verificado de la versión actual:

- 26 passed.
- 2 skipped.
- 0 failed.

Los tests omitidos necesitan artefactos privados/locales de evaluación que no se publican en GitHub.

## 10. Solución de problemas

| Problema | Solución |
|---|---|
| `No module named pytest` | `python -m pip install -r requirements.txt` |
| No abre el sitio | comprobar que `app.server` siga ejecutándose |
| Error de Ollama | abrir Ollama y ejecutar `ollama pull qwen2.5:7b` |
| ZIP no encontrado | corregir la ruta de `$corpus` |
| Primera consulta lenta | esperar carga inicial del modelo y repetir |
| Respuesta insuficiente | revisar evidencia o reformular la consulta |

## 11. Uso responsable

La herramienta es asistencia documental. Verificar siempre la fuente original antes de tomar una decisión institucional.
