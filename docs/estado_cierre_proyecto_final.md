# Estado de cierre del proyecto final

Actualizado: 2026-10-07.

| Bloque | Estado | Evidencia / siguiente acción |
|---|---|---|
| Corpus RAG en español | COMPLETO | 36 documentos, 585 fragmentos |
| Gold operativo v2 | COMPLETO PARA DESARROLLO | 50 preguntas, 82 relaciones; test histórico no se usa para ajustar |
| Recuperación BM25/E5/híbrido | COMPLETO | Comparación documentada |
| Recuperador optimizado | COMPLETO | Recall@5 desarrollo 83,6%; validation 90,9% |
| Generación local con Qwen | COMPLETO | Ollama qwen2.5:7b, citas verificadas y abstención segura |
| Latencia local | COMPLETO | 40/40 exitosas; p50 1,815 s; p95 4,617 s |
| Congelamiento técnico | COMPLETO | Código congelado antes del holdout |
| Holdout post-congelamiento | EN REVISIÓN | 20 preguntas; requiere revisión independiente antes de evaluar |
| Presupuesto <= USD 200 | PENDIENTE DE CIERRE DOCUMENTAL | Consolidar gastos reales del proyecto |
| Integración con portal del equipo | PENDIENTE | Conectar frontend existente con API del RAG |
| Despliegue accesible por HTTPS | PENDIENTE | GitHub Pages no ejecuta Python/Ollama; definir backend |
| Documentación final docs/ | EN PROGRESO | Integrar arquitectura, evaluación, ética, despliegue y manual |
| Pruebas automáticas finales | EN PROGRESO | Ejecutar suite sobre commit final y registrar resultado |
| Video pitch <= 5 min | PENDIENTE | Grabar después de despliegue estable |
| Video de preguntas del profesor | PENDIENTE | Depende de preguntas asignadas |
| Auditoría del repositorio público | PENDIENTE | Verificar secretos, corpus privado, rutas y reproducibilidad |

## Próxima secuencia

1. Revisión independiente del holdout.
2. Congelar el gold externo y ejecutar una única evaluación final.
3. Integrar el RAG con el portal web.
4. Resolver despliegue HTTPS.
5. Cerrar documentación y presupuesto.
6. Ejecutar pruebas finales y auditar el repositorio.
7. Grabar videos.
