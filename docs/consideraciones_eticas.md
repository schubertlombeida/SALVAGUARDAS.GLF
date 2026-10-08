# Consideraciones éticas

## 1. Alcance ético

El asistente RAG del GLF apoya la búsqueda y comprensión de documentación de salvaguardas ambientales y sociales. No determina elegibilidad, no asigna financiamiento, no reemplaza al especialista ni produce decisiones vinculantes.

## 2. Sesgos

El corpus no representa una muestra neutral de toda la actividad social y ambiental de Galápagos. Está compuesto por normativa, anexos y documentos de referencia seleccionados para el SGAS. Pueden existir sesgos de:

- cobertura documental;
- idioma y traducción;
- vigencia normativa;
- mayor representación de ciertas categorías de riesgo;
- énfasis institucional de las fuentes disponibles.

Un error de recuperación puede omitir una salvaguarda relevante. Por ello, el sistema muestra la evidencia y no presenta su respuesta como decisión definitiva.

## 3. Equidad y fairness

El sistema no clasifica personas ni utiliza atributos demográficos para tomar decisiones. Por ello, métricas tradicionales de fairness de clasificación no son directamente aplicables.

El riesgo de inequidad aparece de forma indirecta: una recuperación incompleta podría perjudicar a comunidades o grupos vulnerables si una persona toma una decisión sin revisar las fuentes. La mitigación principal es mantener revisión humana y hacer visibles las citas.

## 4. Privacidad

La versión actual consulta un corpus normativo. Los expedientes y archivos sensibles no se publican en el repositorio.

Controles:

- procesamiento local;
- servidor enlazado a `127.0.0.1`;
- preguntas no registradas en logs de aplicación;
- corpus completo fuera de GitHub;
- límites de tamaño de entrada;
- ninguna llamada obligatoria a una API generativa externa.

En un despliegue institucional deberán aplicarse las políticas internas del GLF y la normativa ecuatoriana de protección de datos correspondiente.

## 5. Transparencia y explicabilidad

Cada respuesta sustentada incluye el identificador exacto del fragmento recuperado. La interfaz muestra tanto la respuesta como la evidencia.

El recuperador final es interpretable: combina BM25 del cuerpo, BM25 de encabezados y una prioridad pequeña para fuentes GLF. Sus hiperparámetros y resultados están documentados en `docs/optimizacion.md`.

## 6. Riesgo de alucinación

Qwen puede producir texto incorrecto incluso con contexto documental. Para reducir este riesgo:

- solo recibe evidencia recuperada;
- debe citar `chunk_id` válidos;
- las citas se verifican contra los fragmentos realmente recuperados;
- las respuestas sin contenido útil se reintentan una sola vez;
- ante evidencia insuficiente el sistema se abstiene;
- la interfaz advierte que la decisión final corresponde al especialista.

## 7. Impacto social

Beneficios potenciales:

- reducir tiempo de búsqueda normativa;
- mejorar trazabilidad de consultas;
- facilitar acceso consistente a salvaguardas;
- disminuir omisiones documentales.

Riesgos potenciales:

- exceso de confianza en una respuesta generada;
- falsa sensación de exhaustividad;
- uso de documentos desactualizados;
- publicación accidental de material no autorizado;
- uso de la herramienta como sustituto de revisión profesional.

## 8. Responsabilidad

El sistema es una herramienta de apoyo. La responsabilidad de una decisión institucional permanece en las personas autorizadas y en los procesos formales del GLF.

El equipo del proyecto es responsable de documentar limitaciones, controlar versiones, mantener tests y no presentar resultados experimentales como certificación institucional.

## 9. Uso dual y mal uso

El asistente no debe utilizarse para:

- aprobar o rechazar automáticamente proyectos;
- asignar categorías definitivas sin revisión;
- producir asesoría jurídica definitiva;
- evaluar personas;
- procesar información sensible no autorizada;
- sustituir consultas a la normativa original.

## 10. Monitoreo

Para un piloto real se recomienda:

1. registrar versión del corpus y del recuperador;
2. revisar periódicamente preguntas con abstención;
3. auditar muestras de citas;
4. repetir métricas después de cambios del corpus;
5. separar claramente métricas de desarrollo, validación y holdout;
6. congelar versiones antes de evaluaciones finales.

## 11. Limitaciones reconocidas

- El corpus puede quedar desactualizado.
- Recall@5 no garantiza que toda respuesta sea completa.
- El holdout post-congelamiento fue pre-revisado por IA y confirmado por el usuario; no constituye validación humana independiente.
- El servidor actual es local.
- El arranque en frío de Ollama puede ser más lento que las consultas posteriores.
- La herramienta no sustituye revisión experta.
