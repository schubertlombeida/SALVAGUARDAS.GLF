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
