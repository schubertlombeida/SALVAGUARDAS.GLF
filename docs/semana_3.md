# Semana 3 Diagnóstico de sobreajuste y subajuste

## Estado

Preparación metodológica. No se ha entrenado un modelo, generado curvas de entrenamiento ni medido mejoras. E5 preentrenado y BM25 no producen por sí mismos la pérdida por época requerida por la actividad.

## Decisión que debe resolver el equipo con el docente

Propuesta: evaluar un componente entrenable pertinente para el asistente, como un reranker de pares consulta-evidencia, únicamente si se dispone de relevancia etiquetada y revisada por el especialista. Alternativa: acordar explícitamente un diagnóstico de generalización y sensibilidad de recuperación como adaptación de la actividad. Esta alternativa no sustituye automáticamente los requisitos de loss y entrenamiento.

No entrenar con etiquetas inferidas sin validación ni usar las respuestas de referencia como entrada de su propia prueba. Revisar suficiencia de etiquetas y separar por expediente. Los 4 casos de prueba se reservan hasta finalizar el ajuste.

## Entregables y aceptación

- `notebooks/overfitting_analysis.ipynb`: carga, exploración, tracking, modelo base, curvas, diagnóstico, dos mejoras, comparación y conclusiones; ejecución completa sin métricas inventadas.
- `results/reports/diagnostic_report.pdf`: resumen ejecutivo de una página (no todo el informe), metodología, diagnóstico, curvas, estrategias, conclusiones y referencias.
- Curvas de train/validation loss y score a 300 DPI como mínimo, con ejes, leyenda, cuadrícula y anotaciones.
- Registro de parámetros, semillas, particiones, métricas y duración de cada ejecución.
- Dos estrategias elegidas después del diagnóstico, con comparación en la misma partición. Regularización o complejidad son candidatas, no mejoras comprobadas.

## Secuencia experimental

1. Definir tarea y etiquetas con el especialista; confirmar correspondencia con la rúbrica.
2. Validar etiquetas y particiones; ajustar el preprocesamiento solo con desarrollo.
3. Entrenar baseline y guardar métricas por paso o época cuando el algoritmo lo permita.
4. Medir brechas de generalización y analizar curvas, sin forzar un diagnóstico.
5. Ejecutar dos intervenciones justificadas y comparar contra baseline.
6. Preparar notebook, informe y gráficos a partir de los registros reales.

La actividad asigna 25 % a tracking, 30 % a curvas, 25 % a diagnóstico y 20 % a mejoras. La fecha exacta de entrega no está indicada en el documento disponible.

## Preparación actual
Se creó notebooks/overfitting_analysis.ipynb con secciones de la consigna, validación de datos por grupo, tracking y exportación de gráficos a 300 DPI. Es una base incompleta: no hay entrenamiento ni resultados y no está lista para entregar. Falta confirmar tarea/dataset y fecha en Blackboard.
