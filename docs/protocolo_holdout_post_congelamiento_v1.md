# Protocolo de holdout post-congelamiento v1

## Objetivo

Obtener una evaluación final que no intervenga en la selección de parámetros del RAG.

El código del RAG quedó congelado en:

`da4b2c1f49379e4f743e64e0ae0b92913ad14027`

Las modificaciones posteriores al repositorio pueden añadir documentación o herramientas de
evaluación, pero no deben cambiar recuperación, chunking, prompt, reglas de evidencia ni
configuración del generador antes de ejecutar el holdout.

## Construcción

El 7 de octubre de 2026 se preparó un conjunto nuevo de 20 preguntas a partir de 20
fragmentos fuente distintos que no estaban utilizados como relaciones relevantes del gold
operativo v2.

La selección se realizó después del congelamiento. El conjunto incluye documentación primaria
del GLF y referencias técnicas del corpus.

## Revisión independiente

El archivo entregado al revisor contiene:

- identificador de pregunta;
- pregunta;
- documento fuente;
- fragmento de evidencia;
- campos vacíos de decisión y respuesta de referencia.

No contiene:

- ranking BM25;
- ranking E5;
- ranking híbrido;
- resultados del RAG;
- respuesta generada por Qwen;
- score del recuperador;
- métricas anteriores.

El revisor debe marcar:

1. si la pregunta es clara;
2. si el fragmento realmente responde;
3. una respuesta de referencia breve basada solo en el fragmento;
4. observaciones, nombre y fecha.

Valores permitidos: `SI`, `NO`, `DUDOSO`.

## Regla para congelar el gold externo

Solo entrarán al gold final preguntas con:

- `pregunta_clara = SI`;
- `fragmento_responde = SI`;
- respuesta de referencia validada;
- identidad y fecha del revisor registradas.

Los casos `NO` o `DUDOSO` se documentarán y excluirán de la métrica principal sin
sustituirlos después de observar resultados del modelo.

Una vez cerrada la revisión:

1. se generará el CSV final del holdout;
2. se calculará su SHA-256;
3. se registrará el hash antes de consultar el RAG;
4. se ejecutará una única evaluación con el código congelado;
5. no se reajustará el sistema usando ese resultado.

## Métricas finales

Se reportarán, como mínimo:

- Recall@5;
- Hit@5;
- MRR@5;
- cobertura de respuesta;
- abstenciones seguras;
- fallos técnicos;
- p50 y p95 extremo a extremo.

El KPI de desarrollo actual (Recall@5 83,6 %) y la latencia local (p95 4,617 s) se
mantendrán separados de los resultados del holdout.

## Protección del test histórico

El test histórico v1 se conserva únicamente como auditoría secundaria porque sus resultados
fueron observados previamente. No se utilizará para reajustar el sistema ni como única prueba
de generalización final.
