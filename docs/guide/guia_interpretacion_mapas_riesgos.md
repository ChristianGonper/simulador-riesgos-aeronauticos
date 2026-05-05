# Guia de interpretacion de mapas y riesgos aeronauticos

## 1. Como leer los mapas

Cada mapa representa un tiempo valido del modelo WRF normalizado. El titulo indica la variable, el instante y las unidades. La barra de color permite interpretar la magnitud y la distribucion espacial. La costa, fronteras y rejilla geografica ayudan a ubicar los maximos, minimos y gradientes.

Los mapas son herramientas de analisis meteorologico. No sustituyen una prediccion operacional ni certifican que una ruta de vuelo sea segura.

## 2. Analisis meteorologico general

La presion reducida al nivel del mar ayuda a localizar borrascas, anticiclones y gradientes baricos. Un gradiente intenso suele relacionarse con viento fuerte en superficie.

La temperatura a 2 m muestra masas de aire frias o calidas cerca de superficie. Debe interpretarse junto con viento y geopotencial para entender advecciones.

La precipitacion incremental muestra lluvia o nieve acumulada entre dos salidas consecutivas del modelo. No debe confundirse con precipitacion total acumulada desde el inicio de la simulacion.

En 850 hPa se interpretan masas de aire de baja troposfera y advecciones. En 500 hPa se localizan vaguadas, dorsales y aire frio en altura. En 300 hPa se analiza el jet stream mediante viento fuerte.

## 3. Riesgos aeronauticos exploratorios

La cizalladura representa cambios vectoriales de viento entre niveles. Valores altos indican cambios bruscos con la altura, relevantes especialmente en ascensos, descensos y aproximaciones. En esta fase debe recordarse que el viento puede seguir siendo relativo a la rejilla del modelo.

El engelamiento combina una ventana termica favorable, entre `0` y `-20 degC`, con humedad o condensado cuando estan disponibles. Si falta humedad o condensado, el mapa solo identifica zonas termodinamicamente favorables.

La turbulencia se estima con un indice cinematico basado en cizalladura y gradientes horizontales de viento. Es util para localizar zonas dinamicamente activas, pero no equivale a un diagnostico completo de turbulencia.

La conveccion se aproxima inicialmente con precipitacion incremental intensa. Es una senal indirecta: puede indicar actividad convectiva, pero tambien precipitacion estratiforme intensa.

La visibilidad solo se representa si el WRF contiene un diagnostico especifico como `AFWA_VIS`. Si no existe, no se estima artificialmente para evitar conclusiones poco defendibles.

## 4. Limitaciones importantes

Los mapas de riesgo son exploratorios. Los umbrales usados son criterios de analisis docente, no limites operacionales universales.

La deteccion automatica de frentes queda fuera de esta fase. Los mapas de presion, temperatura, viento y precipitacion proporcionan contexto para interpretarlos manualmente.

La seleccion de aeropuertos y rutas se abordara despues, cuando los campos y riesgos ya puedan representarse y explicarse sobre el dominio completo.
