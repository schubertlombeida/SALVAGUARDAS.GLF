# Revisión de negativos, cruces documentales y protección de test

## Paquete de negativos pendiente

`revision_negativos_pendientes.csv` contiene **252 pares pregunta–chunk aún sin decisión humana de no relevancia**: 133 de train, 59 de validation y 60 de test. Se generó desde los pares versionados; ninguna etiqueta ni métrica se cambió. Las posiciones BM25/E5/híbrido proceden del Top 10 histórico. Si faltan, el candidato quedó fuera de ese Top 10; no significa score cero. GLF-005 fue reformulada después de ese ranking histórico.

El primer archivo para trabajar es `bloque_revision_01.csv`, con **25 candidatos de train/validation**. Contiene pregunta, texto completo del fragmento, fuente/localizador, extracto de apoyo y motivos de prioridad. Los campos de decisión, observaciones, revisor y fecha están vacíos. Escribir solo en una copia del bloque y devolverla al equipo; mantener intactos los datos originales y el gold v1 hasta conciliar decisiones. Valores sugeridos para `decision_humana`: `RELEVANTE`, `NO_RELEVANTE`, `DUDOSO`. Una sugerencia de posible relevancia es una pista de revisión, no una aprobación.

`inventario_bloques_negativos.csv` enumera ocho bloques de desarrollo/validación, de hasta 25 filas, y un bloque test independiente. Las 60 filas de test están además en `revision_negativos_test_independiente.csv`, ordenadas por pregunta y **sin rankings visibles** para adjudicar sus etiquetas sin influencia del sistema. El archivo maestro conserva las posiciones solo para auditoría posterior. Ninguna prioridad de train/validation utilizó información de test.

## Tres relaciones positivas con conflicto de asignación

| Pregunta | Relación aprobada | Asignación actual | Diagnóstico | Tratamiento actual |
|---|---|---|---|---|
| GLF-001: área de influencia territorial y marina | `GLF_ANEXO_J_DEFINICIONES_ES::0001` | Pregunta train; Anexo J validation | La definición adicional es una fuente válida según el gold, pero usar el chunk como positivo de entrenamiento expondría al modelo a un documento reservado para validation. | Se conserva como relevante para evaluar; par `eligible_for_training=false`. |
| GLF-038: funciones y responsabilidades del PGAS | `GLF_ANEXO_H_FUNCIONES_RESPONSABILIDADES_SGAS_ES::0001` | Pregunta train; Anexo H test | La relación ya existía antes del gold v1. Entrenar con este texto filtraría contenido de una fuente asignada a test. | Se conserva como relevante; par inhabilitado para entrenamiento. |
| GLF-031: cronograma de participación | `CREF-03_ES_20210614-ifc-ps-guidance-note-1-es::0052` | Pregunta test; documento CREF sin asignación documental train/validation/test | Es una referencia adicional aprobada, pero **no cruza hoy con otro split asignado**. El riesgo aparece si este documento se utiliza más tarde para desarrollo sin asignarlo de manera exclusiva. | Se conserva como relevante; par inhabilitado hasta decidir asignación. |

Compartir una fuente documental que responde una pregunta **no es por sí mismo fuga** en la evaluación de un recuperador preentrenado. La fuga ocurre si se entrena, ajusta o selecciona con texto/etiquetas de un conjunto reservado. El índice de recuperación abarca el corpus completo por diseño; los límites documentales se aplican al desarrollo supervisado y a la selección de parámetros.

**Alternativas para aprobación, sin aplicarlas ahora:** (1) mantener estas tres relaciones para evaluación y excluirlas de cualquier conjunto de entrenamiento, como hoy; (2) crear una partición documental v2 que asigne cada fuente a un único split, con nuevas métricas no comparables directamente con v1; (3) diseñar un esquema de evaluación por consultas con control explícito de fuentes compartidas y auditoría de similitud semántica. No eliminar positivos aprobados por conveniencia estadística. Para CREF, una asignación test-only futura es posible, pero requiere revisar todos sus usos.

## Test ya consultado

Los resultados de test v1 aparecieron en los informes de diagnóstico y en la comparación posterior a la revisión. Por tanto **test v1 no es un conjunto completamente independiente para nuevas decisiones**. Se congela su uso para selección: no elegir BM25/E5, pesos, RRF, chunking, preprocesamiento o estrategia por sus resultados. Las filas de test se adjudicarán aparte y a ciegas respecto de rankings.

Cuando haya que validar el proyecto final, preparar **un nuevo conjunto externo** de preguntas y documentos autorizados, recopilados después de cerrar la configuración; obtener juicios de relevancia de revisores sin mostrar rankings, comprobar duplicados y solapamientos semánticos con train/validation, versionar hashes y congelarlo antes de ejecutar una única evaluación final. Ese conjunto todavía no existe; no se calculan métricas nuevas aquí.

## Procedencia del gold

Las 50 preguntas y 76 relaciones se registraron a partir de decisiones propuestas durante revisión asistida por ChatGPT y **confirmadas por el usuario**. `human_reviewed=true` representa esa confirmación; no certifica revisión independiente por un especialista en salvaguardas. El gold v1 registra fecha de recepción/registro `2026-10-03`; nombre, especialidad y fecha histórica exacta del revisor siguen pendientes de confirmar y no se infieren. Se preservan el gold IA, el historial de cambios y sus SHA-256.
