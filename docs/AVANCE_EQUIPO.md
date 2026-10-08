# Actualización de recuperación - 3 de octubre de 2026

**Cierre técnico 4 de octubre:** se verificó el notebook de Semana 3 dentro de una copia temporal (9/9 celdas, cero errores) y se generó localmente `outputs/semana_3/SEMANA_3_ENTREGA_ACADEMICA.zip` con solo 20 archivos académicos. Para RAG, `evaluacion_rag/prepare_negative_review.py` preparó 252 negativos candidatos, un primer bloque local de 25 para train/validation y 60 de test en archivo ciego separado. Ver [diagnóstico de cruces y protección de test](../evaluacion_rag/diagnostico_cruces_y_test.md). Test v1 ya fue consultado y no es un holdout plenamente independiente para decisiones futuras. No se alteraron las 50 preguntas, 76 relaciones ni métricas.

Gold humano v1 aplicado según confirmación del usuario: 50 preguntas, 76 relaciones, 19 agregadas y 13 eliminadas. Baselines sin cambios: BM25 Recall@5 75,0 %/Hit@5 88,0 %; E5-base 68,3 %/80,0 %; híbrido 75,0 %/84,0 %. Ninguno alcanza 80 % global. [Informe de impacto](../evaluacion_rag/impacto_revision_humana.md). Los negativos y los cruces documentales de pares siguen pendientes; nombre y fecha real del revisor no comunicados. La [auditoría de Semana 3](auditoria_entrega_semana3.md) confirma que su paquete académico sigue intacto.

Paquete de revisión humana preparado: 50 preguntas y Top 10 de los tres métodos, consolidados en `evaluacion_rag/revision_humana_gold.csv` local; 240 chunks candidatos únicos. `casos_revision_prioritaria.csv` local contiene 201 incidencias (54 señales sobre preguntas y 147 hard negatives). Ambos contienen texto de fuente y están fuera del GitHub público. El diagnóstico de la diferencia validation/test y el plan de mejora están publicados en `evaluacion_rag/`. E5-base es el modelo de esta evaluación; E5-small es un prototipo histórico. No se optimizó con test ni se entrenó E5.

`evaluacion_rag/` contiene el primer benchmark ejecutado del retrieval GLF: 50 preguntas propuestas por IA, 316 pares, BM25/E5-base/híbrido sobre 585 fragmentos normativos. Ningún método alcanzó 80 % de Recall@5; el p95 medido cubre solo búsqueda local. BM25 queda como candidato provisional por validación. Antes de afirmar KPI hace falta revisar etiquetas, ampliar relevantes y medir extremo a extremo. Semana 3 permanece separada en su paquete local.

---

# Actualización del 3 de octubre de 2026

Semana 3: entrega exploratoria preparada localmente en outputs/semana_3/ENTREGA_SEMANA_3.zip, relativa a la carpeta del proyecto ChatGPT que contiene este checkout. Usar ese paquete vigente, no el notebook inicial de este checkout. Contiene notebook ejecutado, PDF de 7 páginas, cinco figuras a 300 DPI, código y registros. Etiquetas IA sin revisión humana; sobreajuste observado; L2 y parada temprana evaluados. Exactitud balanceada 50% en validación y prueba. No se entrenó E5 ni se validaron KPI RAG.

Pendiente: revisión y envío a Blackboard. Este paquete no se ha publicado en GitHub. Los textos del corpus deben mantenerse fuera del repositorio público. Ver docs/semana_3.md. El estado siguiente es histórico, anterior al experimento.

---

# Avance del equipo — 28 de septiembre de 2026

Punto de entrada único para colaborar. Prioridad: semana 3; fecha comunicada por Niko: mañana al final del día, pendiente de confirmar en Blackboard.

| Componente | Estado real |
|---|---|
| EDA | Ejecutado: 56 documentos, 26 expedientes, seis figuras |
| Web | Búsqueda BM25 local funcional sobre 585 fragmentos normativos |
| Servidor de publicación | Waitress probado; Docker preparado, no probado; sin alojamiento remoto |
| E5 e híbrido | Código implementado; pesos no descargados ni inferencia real ejecutada |
| Notebook Colab E5 | Autónomo, preparado; no ejecutado |
| Semana 3 | Notebook inicial incompleto; sin entrenamiento, curvas ni informe final |
| Evaluación | Evaluador implementado; relevancia humana pendiente |
| Pruebas | 13 pruebas automáticas aprobadas; no acreditan calidad del RAG |

## Archivos que se deben usar
- notebooks/01_exploracion.ipynb: EDA.
- notebooks/02_recuperacion_E5_Colab.ipynb: ejecución de E5 en Colab.
- notebooks/overfitting_analysis.ipynb: único notebook de semana 3; completar este mismo archivo.
- docs/semana_3.md: consigna y pendientes.
- docs/decisiones_vigentes.md: metas 80 %, 7 segundos y USD 200; no resultados.

## Ver la página en el equipo del compañero
Clonar el repositorio y seleccionar la rama de avances. Desde su raíz, con Python 3.11 o superior:

```sh
python -m app.server --archive "/ruta/GLF_SGAS_Corpus_ES.zip"
```

Abrir http://127.0.0.1:8765. El ZIP se obtiene de la carpeta compartida del equipo, no de GitHub. Esta dirección funciona en la computadora que ejecuta el servidor; no es un enlace público. Para ver únicamente el diseño, se puede abrir app/index.html en un navegador; la búsqueda necesita el servidor anterior.

## Pendientes prioritarios de semana 3
1. Confirmar tarea supervisada dentro de GLF y revisar etiquetas.
2. Revisar los 50 pares pregunta-fragmento preparados localmente. Son candidatos BM25, no etiquetas válidas ni conjunto exhaustivo. Coordinar su transferencia privada; no se publican textos en este repositorio.
3. Definir particiones independientes por consulta o expediente, tamaño suficiente y balance; diez preguntas no garantizan un experimento robusto.
4. Ejecutar baseline con tracking; diagnosticar; implementar y evaluar dos intervenciones.
5. Exportar gráficas a 300 DPI y completar diagnostic_report.pdf. Solo su resumen ejecutivo debe ocupar una página.
6. Revisar y entregar notebook ejecutado, informe, figuras y código.

No usar la clasificación propuesta/evaluación como atajo: idioma y tipo documental están fuertemente asociados. No presentar inferencia de E5 como entrenamiento ni inventar curvas.

## Colaboración
Trabajar mediante ramas y pull requests. Revisar este estado antes de editar; actualizar los mismos archivos en lugar de crear copias final/final2. Los originales de semana 1 son históricos. No subir ZIP, expedientes, credenciales ni salidas con textos privados.
