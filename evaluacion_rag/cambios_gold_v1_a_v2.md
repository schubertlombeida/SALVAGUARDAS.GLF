# Gold operativo v2: decisiones de train y validation

El CSV principal recibido el 4 de octubre de 2026 es la fuente de decisión. Sus 192 pares únicos coinciden exactamente con los 192 candidatos de train (133) y validation (59) de la revisión anterior. El CSV de diez dudas y el Excel consolidado coinciden con el principal. Sus SHA-256 y los de entrada y salida están en `validacion_revision_operativa_v2.json`. Los tres originales se conservan localmente en `evaluacion_rag/private/revision_train_validation_20261004/`; no se publican porque contienen texto del corpus.

| Estado | Gold v1 | Gold operativo v2 |
|---|---:|---:|
| Preguntas | 50 | 50 |
| Relaciones relevantes | 76 | 82 |
| Negativos operativos adjudicados | 0 | 186 |
| Candidatos de test pendientes | 60 | 60 |

Las seis altas positivas son GLF-003/`GLF_ANEXO_G_PLANTILLA_PGAS_ES::0004`, GLF-007/`GLF_ANEXO_F_CLAUSULAS_CONVENIOS_SUBVENCION_ES::0001`, GLF-015/`GLF_MANUAL_SGAS_ES::0004` y `::0005`, GLF-026/`GLF_MANUAL_SGAS_ES::0005`, y GLF-040/`GLF_MANUAL_SGAS_ES::0006`. No se quitó ninguna relación positiva v1. Entre las 192 decisiones nuevas, 166 proceden de propuestas de ChatGPT confirmadas por el usuario y 26 de revisión asistida delegada por el usuario; de las seis altas, cinco corresponden al primer grupo y una al segundo. `human_reviewed=true` en los pares nuevos solo indica confirmación individual del usuario. No se atribuye revisión independiente a especialistas ni se infieren sus nombres o credenciales.

`dataset_gold_human_reviewed_v1.csv`, `dataset_pairs_human_reviewed.csv`, el gold IA anterior, el historial de cambios y los resultados de evaluación v1 permanecen intactos. La nueva versión local `dataset_gold_operational_v2.csv` contiene procedencia por chunk; `dataset_pairs_operational_v2.csv` distingue las decisiones operativas del test pendiente. Ambos contienen texto del corpus y se excluyen de Git. El manifiesto público conserva hashes, recuentos y los ID de las seis altas, sin publicar el corpus.

Las tres relaciones señaladas en `diagnostico_cruces_y_test.md` se mantienen positivas y no son elegibles para entrenamiento. Ningún par de validation o test queda habilitado para entrenamiento; esta integración no ejecuta entrenamiento ni selección de parámetros. El test v1 ya fue consultado históricamente y **no es ciego**. Los 60 candidatos de test requieren adjudicación independiente; no se etiquetan por inferencia. No se recalcularon métricas: los números anteriores pertenecen al gold v1 y no deben describirse como rendimiento v2.

Para reproducir localmente, con el corpus autorizado y las tres fuentes privadas ya copiadas:

```powershell
python -m evaluacion_rag.integrate_operational_review --archive "C:\ruta\GLF_SGAS_Corpus_ES.zip"
```
