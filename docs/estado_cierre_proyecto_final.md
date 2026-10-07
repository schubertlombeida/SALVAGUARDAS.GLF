# Estado de cierre del proyecto final

Actualizado: 2026-10-07.

| Bloque | Estado | Evidencia / siguiente acción |
|---|---|---|
| Corpus RAG en español | COMPLETO | 36 documentos, 585 fragmentos |
| Gold operativo v2 | COMPLETO PARA DESARROLLO | 50 preguntas, 82 relaciones; test histórico no se usa para ajustar |
| Recuperación BM25/E5/híbrido | COMPLETO | Comparación documentada |
| Recuperador optimizado | COMPLETO | Recall@5 desarrollo 83,6%; validation 90,9% |
| Workshop S5 / hiperparámetros | **COMPLETO** | `docs/optimizacion.md`, notebook, dependencia parcial, importancia e interacciones |
| Generación local con Qwen | COMPLETO | Ollama qwen2.5:7b, citas verificadas y abstención segura |
| Latencia local | COMPLETO | 40/40 exitosas; p50 1,815 s; p95 4,617 s |
| Congelamiento técnico | COMPLETO | Código congelado antes del holdout |
| Holdout post-congelamiento | COMPLETO COMO AUDITORÍA | Recall@5 85,0%; pre-revisión IA confirmada por usuario, no validación humana independiente |
| Presupuesto <= USD 200 | PENDIENTE DE CIERRE DOCUMENTAL | Consolidar gastos reales del proyecto |
| Integración con portal del equipo | **SIGUIENTE BLOQUE** | Conectar frontend existente con API del RAG |
| Despliegue accesible por HTTPS | PENDIENTE | GitHub Pages no ejecuta Python/Ollama; definir backend |
| Documentación final docs/ | EN PROGRESO | Completar arquitectura, ética, manual y consistencia final |
| Pruebas automáticas finales | EN PROGRESO | Ejecutar suite sobre commit final y registrar resultado |
| Video pitch <= 5 min | PENDIENTE | Grabar después de despliegue estable |
| Video de preguntas del profesor | PENDIENTE | Depende de preguntas asignadas |
| Auditoría del repositorio público | PENDIENTE | Verificar secretos, corpus privado, rutas y reproducibilidad |

## Próxima secuencia

1. **Integrar el RAG con el portal web del equipo.**
2. Resolver un despliegue HTTPS que permita usar la demo fuera del PC local.
3. Completar los documentos obligatorios restantes de `docs/` y el README.
4. Consolidar presupuesto real del proyecto.
5. Ejecutar pruebas automáticas finales y auditoría del repositorio.
6. Hacer merge de la rama final a `main`.
7. Grabar video pitch de 5 minutos.
8. Preparar el video de preguntas cuando el profesor entregue las preguntas.
