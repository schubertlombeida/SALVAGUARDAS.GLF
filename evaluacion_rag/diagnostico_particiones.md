# Diagnóstico de particiones antes de optimizar

La diferencia observada entre validation y test se interpreta como una propiedad de **este conjunto de etiquetas IA**, no como evidencia de que test sea representativo o de que el recuperador generalice mejor allí. No se cambió ninguna partición ni se usó test para elegir parámetros.

| Split | Preguntas | Documentos primarios | Relevantes propuestos por pregunta | Longitud media de pregunta | Parecida al encabezado* | Fallan los tres en Top 5 |
|---|---:|---:|---|---:|---:|---:|
| Train | 27 | 6 | 14 con 1; 13 con 2 | 6,30 términos | 5 | 3 |
| Validation | 11 | 3 | 7 con 1; 3 con 2; 1 con 3 | 6,27 términos | 3 | 2 |
| Test | 12 | 4 | 10 con 1; 2 con 2 | 5,58 términos | 4 | 0 |

*Indicador de cribado: similitud de caracteres >=0,72 entre la pregunta y algún encabezado Markdown **en el chunk primario**. No capta encabezados de fragmentos anteriores ni prueba filtración por sí solo.

La asignación documental es:

- Train: manual SGAS (7 preguntas), Anexo B lista de exclusión (7), Anexo C normas (1), Anexo E herramienta ESSA (4), Anexo F cláusulas (2), Anexo G plantilla PGAS (6).
- Validation: Anexo A política (4), Anexo D marco jurídico/permisos (5), Anexo J definiciones (2).
- Test: Anexo G1 participación (4), Anexo G2 reclamaciones (4), Anexo H responsabilidades (2), Anexo I seguimiento (2).

**Razones plausibles de la brecha.** Test concentra plantillas y herramientas con preguntas más breves y 10 de 12 con un solo relevante conocido. Validation concentra política, marco jurídico y definiciones; cuatro preguntas tienen dos o tres relevantes propuestos. Con Recall@5 macro, una sola omisión en una pregunta de tres relevantes resta un tercio, mientras un acierto en una de un relevante da 100 %. Para BM25, las preguntas con un relevante dan 85,7 % en validation y 100 % en test; con dos o más dan 45,8 % en validation y 75 % en test. Para E5, los valores correspondientes son 57,1 % y 100 %, frente a 33,3 % y 75 %. Las diferencias también pueden reflejar tema, formulación y etiquetas incompletas; no se atribuyen a una sola causa.

**Sesgo por documentos.** La separación evita que el mismo documento primario aparezca en varios splits dentro de los 316 pares. Esto favorece una prueba por transferencia entre familias documentales, pero cada split tiene muy pocos documentos y composición temática distinta. La correlación entre preguntas del mismo documento reduce el tamaño efectivo de muestra. Las 50 preguntas fueron formuladas a partir de fragmentos conocidos; varias se parecen a encabezados (3/11 en validation, 4/12 en test), lo cual puede facilitar recuperar la fuente exacta, especialmente en test.

**Fuga semántica y cobertura.** La auditoría previa descartó IDs compartidos y fragmentos casi idénticos entre los 58 chunks incluidos en los pares (umbral de coseno de caracteres 0,85; máximo observado 0,643). Entre preguntas de distintos splits, la mayor similitud literal normalizada por SequenceMatcher fue 0,690 (GLF-003 frente a GLF-043). Estos controles no descartan paráfrasis, contenidos repetidos en otros chunks del corpus ni respuestas válidas que no figuren en las etiquetas. Los Anexos G, G1 y G2 comparten temas de participación y reclamaciones; el manual y varias plantillas describen procesos relacionados. Un especialista debe revisar esas coincidencias y todos los resultados Top 10 antes de certificar el gold standard. La falta de todos los relevantes puede penalizar injustamente un resultado correcto o inflar un acierto por título.

**Regla de uso:** train sirve para desarrollo; validation se podrá usar para escoger parámetros una vez revisadas las etiquetas; test queda congelado y solo se consultará al final para la evaluación predefinida. Ni BM25, RRF, pesos, chunking ni modelo se elegirán con test. Los valores de test aquí se describen solo para diagnosticar el sesgo ya observado.

El detalle por pregunta, recuentos por documento, similitud de encabezado y desacuerdo de rankings está en el archivo local `diagnostico_particiones.json`. La revisión prioritaria se encuentra en `casos_revision_prioritaria.csv`.
