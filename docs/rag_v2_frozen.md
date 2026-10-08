# Congelamiento técnico del RAG v2

**Fecha:** 2026-10-07  
**Rama:** `codex/avances-glf-semana3`  
**Commit congelado de código RAG:** `da4b2c1f49379e4f743e64e0ae0b92913ad14027`

A partir de este punto no se deben modificar parámetros, pesos de ranking, chunking,
preprocesamiento, prompt de generación ni reglas de selección usando información del
holdout/test final.

## Configuración congelada

- Recuperador: `BM25-heading-authority-v2`
- Corpus: 585 fragmentos en español
- Generador local: `qwen2.5:7b` mediante Ollama
- Top-k: 5
- BM25 cuerpo: k1=0,8; b=0,2
- BM25 encabezados: k1=1,2; b=0,3
- Peso de encabezados: 0,30
- Prioridad de fuente GLF: 0,15

## Resultados de desarrollo/validación

- Recall@5 train: **80,6 %**
- Recall@5 validation: **90,9 %**
- Recall@5 train + validation: **83,6 %**
- Hit@5 train + validation: **94,7 %**

Estos resultados pertenecen a desarrollo/validación y no constituyen por sí solos una
certificación independiente final.

## Validación local de latencia

Corrida local con 40 consultas de train/validation y 3 consultas de calentamiento
excluidas:

- Consultas procesadas: **40**
- Respuestas técnicas exitosas: **40/40**
- Fallos HTTP: **0**
- Abstenciones seguras por evidencia insuficiente: **2/40**
- p50 extremo a extremo: **1,815 s**
- p95 extremo a extremo: **4,617 s**
- Meta p95 <= 7 s: **cumplida**

La medición cubre `POST /api/ask`: recuperación + generación local con Qwen. No incluye
latencia de red pública ni navegador.

## Regla de evaluación final

1. Crear el holdout después del congelamiento.
2. No mostrar rankings del sistema al revisor.
3. Obtener revisión humana independiente de claridad y relevancia.
4. Congelar el gold externo y su hash.
5. Ejecutar una única evaluación del commit congelado.
6. No reajustar el sistema con el resultado de esa evaluación.
7. Reportar por separado Recall@5, Hit@5, cobertura de respuesta, abstenciones y latencia.

El test histórico v1 no se considera completamente ciego porque sus resultados fueron
consultados previamente. Puede conservarse como auditoría secundaria, pero no como única
certificación final.
