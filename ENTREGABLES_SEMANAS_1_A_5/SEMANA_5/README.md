# Semana 5 — Optimización

Estado: ✅ COMPLETADA

## Archivos principales

- Documento: `/docs/optimizacion.md`
- Notebook: `/notebooks/04_optimizacion.ipynb`
- Métricas: `/results/metrics/`
- Gráficos: `/results/figures/`

## Trabajo realizado

- evaluación de hiperparámetros;
- 320 configuraciones de sensibilidad;
- análisis de sensibilidad;
- partial dependence adaptado a Recall@5;
- importancia de hiperparámetros;
- interacciones;
- comparación baseline vs configuración final.

Configuración final congelada:

- k1 cuerpo: 0.8
- b cuerpo: 0.2
- k1 encabezados: 1.2
- b encabezados: 0.3
- peso encabezados: 0.30
- prioridad GLF: 0.15
- Top-k: 5

Resultado final de desarrollo:

`Recall@5 = 83.6%`
