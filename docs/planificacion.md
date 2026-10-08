# Planificación del proyecto

## 1. Problema y objetivo

El proyecto desarrolla un asistente RAG para localizar y explicar salvaguardas ambientales y sociales del Galápagos Life Fund (GLF) a partir de un corpus normativo controlado. El objetivo es reducir el tiempo de búsqueda documental y mejorar la trazabilidad de las respuestas sin sustituir la decisión humana.

## 2. Alcance

Incluye:

- corpus normativo SGAS en español;
- recuperación Top-5;
- generación local con Qwen;
- citas verificables;
- abstención segura;
- interfaz web;
- evaluación de Recall@5 y latencia;
- documentación técnica y ética.

No incluye:

- aprobación automática de proyectos;
- decisiones de desembolso;
- asesoría jurídica vinculante;
- evaluación autónoma de personas;
- publicación de expedientes privados;
- despliegue institucional en producción.

## 3. Planificado vs. realizado

| Etapa | Plan inicial | Resultado real |
|---|---|---|
| Definición SMART | definir problema, métricas y alcance | completado |
| EDA | inventario, particiones y visualizaciones | completado con 6 figuras |
| Selección técnica | comparar BM25 y E5 | completado; BM25 rindió mejor en este corpus |
| Diagnóstico Semana 3 | overfitting/underfitting | completado con notebook y reporte |
| Ética Semana 4 | impacto social y responsabilidad | completado |
| Optimización Semana 5 | hiperparámetros y sensibilidad | completado con rejilla y 7 gráficos |
| RAG final | recuperación + generación con citas | completado |
| Interfaz | conectar RAG a portal | completado localmente |
| Tests | unitarios e integración | 26 passed, 2 skipped, 0 failed |
| Evaluación final | Recall y latencia | objetivos técnicos cumplidos |
| Videos finales | pitch + preguntas del profesor | pendiente |
| Publicación remota | demo accesible por Internet | pendiente de decisión y permisos |

## 4. Recursos

### Datos
- 585 fragmentos normativos en español para recuperación.
- 50 preguntas del gold operativo v2.
- 82 relaciones relevantes.
- artefactos privados mantenidos fuera del repositorio público.

### Hardware y software
- Python 3.11.
- Ollama.
- Qwen 2.5 7B.
- Git/GitHub.
- navegador web.
- ejecución local con GPU opcional; el recuperador no depende de GPU.

## 5. KPIs vigentes

| KPI | Meta | Resultado |
|---|---:|---:|
| Recall@5 desarrollo | ≥80% | 83.6% |
| Recall@5 validation | ≥80% | 90.9% |
| p95 extremo a extremo | ≤7 s | 4.617 s |
| Corrida funcional | 100% sin error HTTP | 40/40 |
| Presupuesto directo | ≤USD 200 | sin gasto de API generativa en la versión local |

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| alucinación generativa | citas obligatorias + validación + abstención |
| corpus desactualizado | versionado y revisión periódica |
| filtración de información | corpus/artefactos sensibles fuera de GitHub |
| sobreajuste | congelamiento antes de auditoría post-freeze |
| primera consulta lenta | distinguir arranque en frío de p95 en caliente |
| dependencia excesiva del asistente | aviso visible y decisión humana obligatoria |
| redistribución no autorizada | no publicar corpus hasta verificar permisos |

## 7. Estado actual

La versión técnica local está cerrada para la entrega académica. Los pendientes de presentación son el despliegue remoto si se decide realizarlo, las capturas finales del manual, el video pitch y el video de respuestas a preguntas del profesor.
