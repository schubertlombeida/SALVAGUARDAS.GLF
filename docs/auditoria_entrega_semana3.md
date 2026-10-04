# Auditoría de la entrega oficial de Semana 3

Paquete conservado: `outputs/semana_3/ENTREGA_SEMANA_3.zip` en el proyecto local, separado del PR público y del benchmark RAG. La actividad es **Diagnóstico de Overfitting/Underfitting**; el modelo experimental es TF-IDF + SGD. No es BM25, E5 ni un LLM. Sus etiquetas siguen siendo valoraciones IA anteriores, no las 50 decisiones humanas del gold RAG v1.

| Requisito | Evidencia comprobada | Estado |
|---|---|---|
| Tracking de métricas | `base_history.csv`, `regularizacion_l2_history.csv`, `early_stopping_history.csv` y `metrics.json` | Presente |
| Training vs Validation Loss | Figuras 01–03 y historiales por época | Presente |
| Training vs Validation Accuracy/Score | Figuras 01–03; accuracy y balanced accuracy | Presente |
| Diagnóstico de overfitting/underfitting | Notebook secciones 4–7; PDF pp. 1 y 6–7 | Presente |
| Análisis cuantitativo | Tabla de losses y balanced accuracy en el PDF; `comparison.csv` | Presente |
| Dos estrategias implementadas | L2 y parada temprana en `src/experiment.py` | Presente |
| Comparación antes/después | `comparison.csv`, figura 05 y tabla del PDF | Presente |
| Conclusiones y recomendaciones | PDF sección 6; notebook sección 7 | Presente |
| Código modular | `src/experiment.py` y `src/build_delivery.py` | Presente |
| Notebook completo | `overfitting_analysis.ipynb`: 18 celdas, 9 de código con conteo de ejecución y sin salidas de error | Presente; ejecución guardada |
| Reporte técnico PDF | `results/reports/diagnostic_report.pdf`: 7 páginas; resumen, método, resultados, curvas, estrategias, conclusiones y referencias | Presente |
| Visualizaciones profesionales | Cinco PNG con títulos, ejes, leyendas y grid en el código; metadatos de 300 DPI (299,9994 por redondeo) | Presente |

Se comprobó la lista del ZIP, las salidas guardadas del notebook, el contenido extraíble del PDF y sus páginas 1 y 7 renderizadas visualmente. Las cinco figuras tienen resoluciones entre 2370×1317 y 3120×1278 píxeles y metadatos cercanos a 300 DPI. El notebook no se volvió a ejecutar durante esta auditoría; los resultados entregados ya están guardados y no se alteró el paquete.

El hallazgo central se mantiene: el modelo base terminó con loss train 0,0026 frente a loss validation 0,8662 y exactitud balanceada de validación de 50 %. L2 redujo la pérdida de validación a 0,6801 y Early Stopping a 0,6235, pero ambas estrategias conservaron 50 % de exactitud balanceada. La exactitud de test de 88,9 % refleja una partición con ocho positivos de nueve; no prueba buen rendimiento. Estos números corresponden exclusivamente a Semana 3 y no se mezclan con Recall@5 del prototipo RAG.

**Pendiente académico:** confirmar aceptación de etiquetas IA como evidencia para esta actividad y realizar el envío en Blackboard. El nuevo gold humano del RAG no reescribe retrospectivamente los resultados de este clasificador. Si el docente exige rehacer Semana 3 con las etiquetas humanas, debe crearse una versión nueva y volver a ejecutar el experimento, conservando esta entrega histórica.
