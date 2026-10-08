# Semana 2 — EDA + Decisión Técnica y Arquitectura

Estado: ✅ COMPLETADA EN CONTENIDO

La Semana 2 pedía conectar el EDA con una decisión técnica y una arquitectura de IA.

## Archivos principales

- EDA / análisis de datos: `/docs/analisis_datos.md`
- Arquitectura final: `/docs/arquitectura.md`
- Notebook exploratorio: `/notebooks/01_exploracion.ipynb`
- Comparación semántica E5: `/notebooks/02_recuperacion_E5_Colab.ipynb`
- Selección del recuperador: `/docs/evaluacion_rag_v2.md`

## Decisión técnica final

Se evaluaron alternativas de recuperación y se seleccionó:

`BM25-heading-authority-v2`

El generador final es:

`Qwen 2.5 7B`

La solución es un sistema RAG: recuperación documental + LLM generativo con citas.

> Si la profesora exige específicamente la ficha de 1 página en PDF/Word, exportar un resumen de `arquitectura.md` + `analisis_datos.md`. No hay que repetir experimentos.
