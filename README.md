# Asistente RAG de Salvaguardas GLF

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)
![Recall@5](https://img.shields.io/badge/Recall%405-83.6%25-brightgreen)
![p95](https://img.shields.io/badge/p95-4.617%20s-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Sistema académico de IA para consultar salvaguardas ambientales y sociales del **Galápagos Life Fund (GLF)** mediante recuperación documental y generación local con citas verificables.

El asistente **no aprueba ni rechaza proyectos**. Recupera evidencia y ayuda a localizar requisitos; la decisión final permanece en el especialista humano.

## Contenido

- [Problema](#problema)
- [Solución](#solución)
- [Resultados](#resultados)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Uso](#uso)
- [Pruebas](#pruebas)
- [Estructura](#estructura)
- [Documentación](#documentación)
- [Privacidad y ética](#privacidad-y-ética)
- [Limitaciones](#limitaciones)
- [Presentación final](#presentación-final)
- [Equipo](#equipo)
- [Licencia](#licencia)

## Problema

La documentación de salvaguardas del GLF, sus anexos y referencias normativas contiene requisitos distribuidos entre múltiples fuentes. Localizar rápidamente el fundamento correcto puede requerir revisar documentos extensos.

El proyecto busca reducir ese tiempo de búsqueda manteniendo trazabilidad documental.

## Solución

El sistema implementa un flujo RAG:

1. el usuario escribe una consulta;
2. `BM25-heading-authority-v2` recupera hasta cinco fragmentos;
3. Qwen 2.5 7B genera una respuesta local usando únicamente el contexto recuperado;
4. cada afirmación debe incluir un `chunk_id` verificable;
5. el sistema valida las citas;
6. si no existe evidencia suficiente, se abstiene.

Corpus actual: **585 fragmentos normativos en español**.

## Resultados

### Recuperación

| Métrica | Resultado | Meta |
|---|---:|---:|
| Recall@5 train | 80.6% | ≥80% |
| Recall@5 validation | 90.9% | ≥80% |
| Recall@5 train + validation | **83.6%** | ≥80% |
| Hit@5 desarrollo | 94.7% | — |
| MRR@5 desarrollo | 0.752 | — |
| Holdout post-congelamiento | 85.0% | evidencia adicional |

El holdout post-congelamiento fue pre-revisado por IA y confirmado por el usuario; se reporta como auditoría adicional y no como validación humana independiente.

### Latencia extremo a extremo

Benchmark local de 40 consultas, con tres consultas de calentamiento excluidas:

| Métrica | Resultado |
|---|---:|
| Exitosas | 40/40 |
| Fallos HTTP | 0 |
| p50 | 1.815 s |
| p95 | **4.617 s** |
| Meta p95 | ≤7 s |
| Estado | **Cumple** |

La primera consulta después de cargar Ollama puede ser más lenta por arranque en frío.

## Arquitectura

```text
Usuario
   │
   ▼
Interfaz web
   │ POST /api/ask
   ▼
BM25-heading-authority-v2
   │
   ├── cuerpo BM25
   ├── encabezados BM25
   └── prioridad moderada de fuentes GLF
   │
   ▼
Top 5 fragmentos
   │
   ▼
Qwen 2.5 7B · Ollama local
   │
   ▼
Validador de citas / calidad
   │
   ├── respuesta sustentada
   └── abstención segura
```

Detalles completos: [docs/arquitectura.md](docs/arquitectura.md).

## Instalación

### Requisitos

- Python 3.11 o superior.
- Ollama.
- ZIP autorizado del corpus `GLF_SGAS_Corpus_ES.zip`.

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Instalar el modelo local:

```powershell
ollama pull qwen2.5:7b
```

## Uso

Desde PowerShell:

```powershell
$corpus = "C:\ruta\GLF_SGAS_Corpus_ES.zip"
$env:GLF_OLLAMA_URL = "http://127.0.0.1:11434"
$env:GLF_OLLAMA_MODEL = "qwen2.5:7b"

python -m app.server --archive "$corpus" --port 8765
```

Abrir:

`http://127.0.0.1:8765`

Dentro del portal:

**Módulo 2 → Asistente RAG → Consultar Corpus**

Ejemplos:

- `¿Qué instrumentos ambientales y sociales son obligatorios para todos los proyectos?`
- `¿Qué debe hacer el GLF durante la evaluación de la detección?`
- `¿Qué diferencia existe entre los proyectos de Categoría B y Categoría C?`

Una pregunta fuera del dominio debe producir abstención segura.

## Pruebas

Ejecutar:

```powershell
python -m pytest -q
```

Resultado verificado de la versión actual:

```text
26 passed, 2 skipped, 0 failed
```

Los dos tests omitidos requieren artefactos privados/locales de evaluación que no se publican en GitHub.

## Estructura

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── app/
├── data/
├── docs/
│   ├── planificacion.md
│   ├── analisis_datos.md
│   ├── arquitectura.md
│   ├── optimizacion.md
│   ├── consideraciones_eticas.md
│   └── manual_usuario.md
├── notebooks/
│   ├── 01_exploracion.ipynb
│   ├── 02_recuperacion_E5_Colab.ipynb
│   ├── 03_modelado.ipynb
│   ├── 04_optimizacion.ipynb
│   └── 05_evaluacion.ipynb
├── src/
├── tests/
├── results/
└── evaluacion_rag/
```

## Documentación

Documentos principales de la entrega:

- [Planificación](docs/planificacion.md)
- [Análisis de datos](docs/analisis_datos.md)
- [Arquitectura](docs/arquitectura.md)
- [Optimización](docs/optimizacion.md)
- [Consideraciones éticas](docs/consideraciones_eticas.md)
- [Manual de usuario](docs/manual_usuario.md)
- [Evaluación RAG](docs/evaluacion_rag_v2.md)
- [Congelamiento del RAG](docs/rag_v2_frozen.md)

La optimización de Semana 5 incluye 320 configuraciones de sensibilidad, partial dependence adaptado a Recall@5, importancia de hiperparámetros e interacciones.

## Privacidad y ética

- El corpus completo y los artefactos sensibles permanecen fuera del repositorio público.
- El servidor de desarrollo escucha únicamente en `127.0.0.1`.
- Las consultas no se almacenan en logs de texto.
- La generación se ejecuta localmente.
- El sistema muestra citas y evidencia.
- No se permite presentar el resultado como una decisión institucional automática.

Ver [consideraciones éticas](docs/consideraciones_eticas.md).

## Limitaciones

- El corpus puede quedar desactualizado.
- Recall@5 no garantiza exhaustividad de cada respuesta.
- Qwen puede producir errores; por eso se validan citas y se mantiene revisión humana.
- El arranque en frío de Ollama puede superar la latencia normal.
- El servidor actual es una versión local de demostración, no un servicio institucional de producción.
- La publicación remota del corpus depende de permisos de redistribución.

## Presentación final

Pendientes de la entrega académica:

- video pitch de máximo 5 minutos;
- video de respuestas a las preguntas asignadas por la profesora;
- enlace público de demostración, si se autoriza y se decide desplegar remotamente.

Los enlaces se añadirán aquí cuando estén disponibles.

## Equipo

- **Niko Dimitri Jiménez Bruno**
- **Schubert Lombeida Manjarrez**

Proyecto Integrador de Inteligencia Artificial · 2026.

## Licencia

El código original del proyecto se publica bajo licencia MIT. La licencia **no** concede derechos sobre documentos, logos, normativa, datasets o materiales de terceros referenciados por el proyecto. Ver [LICENSE](LICENSE).
