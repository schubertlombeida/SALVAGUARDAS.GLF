# Impacto de la revisión humana v1 — baselines sin optimizar

La revisión manual de las 50 preguntas fue declarada por el usuario y aplicada exactamente según sus decisiones. El gold IA original permanece intacto. El gold v1 registra 76 relaciones pregunta–chunk frente a 66 originales: **19 relaciones agregadas** (11 previamente no anotadas y 8 que figuraban como negativos candidatos) y **13 relaciones eliminadas** que antes figuraban como positivos. Hubo cambios en 26 preguntas; GLF-005 también se reformuló. El cambio neto es +10 relaciones.

La fecha exacta y el nombre de quien realizó la revisión no constan en las decisiones recibidas; el CSV distingue la fecha de registro de la fecha real pendiente. `human_reviewed=true` registra la confirmación explícita del usuario, no una segunda auditoría independiente realizada por Codex.

## Comparación global

| Método | Recall@5 IA | Recall@5 humano v1 | Cambio | Hit@5 IA | Hit@5 humano v1 | Cambio |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 74,7 % | **75,0 %** | +0,3 pp | 86,0 % | **88,0 %** | +2,0 pp |
| E5-base | 68,7 % | **68,3 %** | −0,3 pp | 80,0 % | **80,0 %** | 0,0 pp |
| BM25 + E5 RRF | 73,7 % | **75,0 %** | +1,3 pp | 86,0 % | **84,0 %** | −2,0 pp |

Recall@5 es la proporción de **todos** los relevantes aprobados recuperados; Hit@5 solo exige **uno** entre los primeros cinco. Por eso Hit@5 puede ser alto aunque falten fuentes válidas. La comparación completa de Recall@1/3/5, Hit@1/3/5 y MRR está en `comparacion_ia_vs_humano.csv`. GLF-005 cambió de redacción y de etiqueta, de modo que la diferencia agregada no es exclusivamente efecto de las etiquetas.

## Baseline v1 por partición

| Split | Método | Recall@5 | Hit@5 |
|---|---|---:|---:|
| Train (27) | BM25 | 63,0 % | 81,5 % |
| Train (27) | E5-base | 61,1 % | 74,1 % |
| Train (27) | Híbrido | 66,7 % | 81,5 % |
| Validation (11) | BM25 | 81,8 % | 90,9 % |
| Validation (11) | E5-base | 65,2 % | 72,7 % |
| Validation (11) | Híbrido | 68,2 % | 72,7 % |
| Test (12; informativo) | BM25 | 95,8 % | 100,0 % |
| Test (12; informativo) | E5-base | 87,5 % | 100,0 % |
| Test (12; informativo) | Híbrido | 100,0 % | 100,0 % |

Se ejecutaron exactamente los baselines existentes: BM25 del repositorio (k1=1,5, b=0,75), E5 `intfloat/multilingual-e5-base` preentrenado, RRF profundidad 20/constante 60 y el mismo corpus de 585 chunks. No se seleccionó método ni parámetro con test. La meta **global** Recall@5 >=80 % sigue sin cumplirse: BM25 e híbrido llegan a 75,0 %. La latencia registrada mide recuperación local precargada, no el sistema completo; el presupuesto tampoco está auditado.

Las métricas IA eran provisionales porque mezclaban positivos no confirmados, negativos que podían responder y relevantes omitidos. Los cambios siguieron la lista manual suministrada, no el ranking de BM25/E5 ni la conveniencia de mejorar un método. Test conserva sus 12 preguntas y su split; los valores se presentan solo como información del baseline.

## Pares y fuga

`dataset_pairs_human_reviewed.csv` contiene los **76 positivos aprobados** y 252 **candidatos negativos aún no verificados**. Ocho negativos anteriores se convirtieron en positivos. Los 13 positivos eliminados quedaron como candidatos por revisar: quitar una etiqueta positiva no equivale automáticamente a certificar una negativa. Ningún negativo se marca `human_reviewed=true` ni se habilita para entrenamiento.

Tres relaciones positivas cruzan la asignación documental usada para los pares: GLF-001 → Anexo J (train/validation), GLF-038 → Anexo H (train/test; ya existía) y GLF-031 → documento CREF sin split propio (test). Permanecen en el gold para evaluar recuperación, pero sus filas de pares tienen `eligible_for_training=false`. Los documentos/splits de preguntas no se reasignaron. Antes de entrenar un clasificador de pares hace falta resolver estos cruces y obtener juicios explícitos de no relevancia. Esta restricción evita fingir ausencia de fuga.
