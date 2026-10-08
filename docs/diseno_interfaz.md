# Diseño inicial de la interfaz GLF

Estado: primera interfaz local implementada para búsqueda normativa BM25 y lectura de evidencia. El recorrido completo descrito a continuación sigue siendo el objetivo; carga de propuestas, matriz y recomendaciones están pendientes.

## Recorrido del especialista

1. Inicio: alcance Galápagos, objetivo de apoyo y ejemplo de uso.
2. Analizar propuesta: archivo y contexto del proyecto, validación de formato y tamaño, aviso sobre el tratamiento de documentos.
3. Revisión: riesgos y campos faltantes, medidas propuestas y evidencia asociada, con posibilidad de inspeccionar cada fuente.
4. Evidencia: fragmento, documento, sección o página verificable, idioma y naturaleza de la fuente.
5. Acerca del sistema: versión, metodología, métricas medidas y límites.

## Estados que deben diseñarse

Entrada vacía; formato incompatible; archivo sin texto extraíble; documento fuera de alcance; procesamiento; error recuperable; evidencia insuficiente; resultados disponibles. La ausencia de evidencia debe mostrarse como tal, sin una recomendación inventada.

## Dirección visual propuesta

Interfaz en español, fondo claro, tipografía legible y contraste suficiente. Verde oscuro y azul como acentos de conservación y contexto marino. No utilizar logotipos institucionales sin una fuente autorizada. Navegación simple y diseño adaptable a móvil y escritorio. Los resultados presentan primero la observación y después su evidencia, evitando una pantalla saturada de métricas técnicas.

Una puntuación de similitud no se mostrará como probabilidad de corrección. El requisito de confianza de la consigna debe resolverse mediante una medida justificable o una adaptación acordada. Toda recomendación queda sujeta al especialista.

## Tecnología

Primera implementación: servidor local Python y HTML/CSS/JavaScript; recuperador separado en src/retrieval.py. Esta decisión permite probar el corpus sin dependencias web adicionales. La plataforma de despliegue definitivo sigue pendiente.
