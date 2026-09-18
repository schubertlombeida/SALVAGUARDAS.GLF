# Asistente de riesgos y salvaguardas GLF

Documentación académica del Workshop de Metodología SMART, Semana 1.

**Equipo:** Schubert Lombeida Manjarrez y Niko Dimitri Jiménez Bruno.  
**Estado:** propuesta y planificación; todavía no contiene una aplicación ni resultados experimentales.

## Objetivo

Diseñar y evaluar un prototipo que recupere fichas pertinentes de riesgos y salvaguardas, muestre sus fuentes y apoye la revisión de la nueva matriz GLF de 17 campos. El especialista conserva las valoraciones y decisiones.

Se propone comparar una búsqueda BM25 con un modelo de embeddings multilingüe E5 y complementar ambos con reglas de revisión de campos y cálculos.

## Estructura

~~~text
.
|-- README.md
|-- .gitignore
|-- .gitattributes
|-- manifest.json
|-- entregables/
    |-- 01-evaluacion/
    |   |-- matriz-evaluacion-smart.xlsx
    |   |-- checklist-smart-glf.docx
    |-- 02-diseno/
    |   |-- analisis-y-solucion-recomendada.docx
    |   |-- canvas-smart-glf.docx
    |-- 03-presentacion/
    |   |-- guion-pitch-glf.docx
    |-- 04-validacion/
        |-- formulario-especialista-sostenibilidad.docx
~~~

## Documentos y orden de lectura

| Documento | Contenido |
|---|---|
| [Análisis y solución recomendada](entregables/02-diseno/analisis-y-solucion-recomendada.docx) | Comparación de opciones, fuentes, alcance, métricas, presupuesto y cronograma. |
| [Matriz de evaluación SMART](entregables/01-evaluacion/matriz-evaluacion-smart.xlsx) | Tres alternativas, puntuaciones ponderadas y 15 justificaciones. |
| [Canvas SMART](entregables/02-diseno/canvas-smart-glf.docx) | Objetivo, recursos, riesgos y planificación. |
| [Checklist SMART](entregables/01-evaluacion/checklist-smart-glf.docx) | Validación documental y condiciones pendientes. |
| [Guion del pitch](entregables/03-presentacion/guion-pitch-glf.docx) | Texto para ensayar una presentación de aproximadamente tres minutos. |
| [Formulario para el especialista](entregables/04-validacion/formulario-especialista-sostenibilidad.docx) | Entrevista con Ulf, referencia experta, medición y acuerdos. |

Descargar los archivos para editarlos en Word y Excel o herramientas compatibles. GitHub conserva los archivos, pero la revisión de diferencias de estos formatos binarios es limitada.

## Resultado de la selección

| Alternativa | Puntuación sobre 5 |
|---|---:|
| GLF | 4,40 |
| PreClass AI | 4,00 |
| PoliScope AI | 3,40 |

Las puntuaciones son una valoración técnica argumentada. No representan el rendimiento medido de modelos.

El checklist obtiene **24/31, amarillo**. Quedan pendientes la línea base de tiempos, la verificación del corpus, la dedicación semanal del equipo y la capacidad de cómputo.

## Restricciones y calendario

- Seis semanas totales, con cinco semanas restantes en la planificación preparada.
- Hasta 30 expedientes declarados, pendientes de inventario y anonimización.
- Presupuesto directo estimado por el equipo: USD 100.
- Ulf disponible como especialista; agenda y criterios específicos por acordar.
- Calendario propuesto: 19 de septiembre a 23 de octubre de 2026.
- Entrega del workshop prevista para el domingo 20 de septiembre a las 21:00; zona horaria de la plataforma pendiente de comprobar.

Las metas de recuperación, alertas, trazabilidad y ahorro de tiempo son propuestas para el piloto. No se presentan como resultados logrados.

## Manejo de documentos

Este paquete contiene únicamente los seis entregables preparados y los archivos de organización del repositorio. Los expedientes, documentos fuente institucionales, datos personales, archivos de trabajo y resultados temporales permanecen fuera del paquete.

Antes de habilitar acceso público, revisar que la difusión de los nombres y del contenido institucional incluido en los entregables esté autorizada. Un repositorio privado permite coordinar la revisión inicial.

El archivo .gitignore previene incorporaciones accidentales en las rutas habituales; no anonimiza documentos ni elimina información del historial de Git.

## Actualización

1. Editar el documento correspondiente sin cambiar su ruta.
2. Mantener coherencia entre matriz, análisis, Canvas, checklist y guion.
3. Registrar en el mensaje del commit el cambio y su motivo.
4. Actualizar los hashes de manifest.json si se modifica algún entregable.

manifest.json permite comprobar la integridad de esta copia inicial y relacionar sus nombres con los originales.

## Subir a GitHub

Crear un repositorio vacío y subir **el contenido de esta carpeta**, conservando su estructura. Si se usa Git, ejecutar desde esta carpeta:

~~~bash
git init
git add .
git commit -m "Añadir entregables del workshop SMART"
git branch -M main
git remote add origin https://github.com/USUARIO/NOMBRE-REPOSITORIO.git
git push -u origin main
~~~

Sustituir USUARIO y NOMBRE-REPOSITORIO por los datos reales. No se ha creado ni publicado un repositorio remoto como parte de esta preparación.

## Alcance de uso

Documentación académica de trabajo. No constituye aprobación institucional, certificación de cumplimiento ni autorización para reutilizar documentos de terceros. No se incorpora una licencia de redistribución porque sus condiciones todavía no han sido definidas.
