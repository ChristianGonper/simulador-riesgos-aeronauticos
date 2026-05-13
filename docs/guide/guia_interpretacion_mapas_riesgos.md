# Guia de interpretacion de mapas y riesgos aeronauticos

## 1. Como leer los mapas

Cada mapa representa un tiempo valido del modelo WRF normalizado. El titulo indica la variable, el instante y las unidades. La barra de color permite interpretar la magnitud y la distribucion espacial. La costa, fronteras y rejilla geografica ayudan a ubicar los maximos, minimos y gradientes.

Los mapas son herramientas de analisis meteorologico. No sustituyen una prediccion operacional ni certifican que una ruta de vuelo sea segura.

Un mapa entregable debe permitir explicar que campo se representa, de que variables WRF procede, que unidad tiene, que metodo se ha usado y que limitaciones fisicas conserva.

## 2. Analisis meteorologico general

La presion reducida al nivel del mar ayuda a localizar borrascas, anticiclones y gradientes baricos. Un gradiente intenso suele relacionarse con viento fuerte en superficie.

La temperatura a 2 m muestra masas de aire frias o calidas cerca de superficie. Debe interpretarse junto con viento y geopotencial para entender advecciones.

La precipitacion incremental muestra lluvia o nieve acumulada entre dos salidas consecutivas del modelo. No debe confundirse con precipitacion total acumulada desde el inicio de la simulacion.

En 850 hPa se interpretan masas de aire de baja troposfera y advecciones. En 500 hPa se localizan vaguadas, dorsales y aire frio en altura. En 300 hPa se analiza el jet stream mediante viento fuerte.

Las vaguadas y dorsales se interpretan principalmente en el geopotencial de 500 hPa. Los ciclones y borrascas se identifican con minimos de presion reducida al nivel del mar, pero conviene contrastarlos con viento, precipitacion y estructura vertical.

Las zonas baroclinas se infieren a partir de gradientes de temperatura, especialmente en 850 hPa o superficie. Un gradiente intenso ayuda a localizar posibles frentes, aunque no equivale por si solo a una deteccion frontal operacional.

## 3. Riesgos aeronauticos exploratorios

La cizalladura representa cambios vectoriales de viento entre niveles. Valores altos indican cambios bruscos con la altura, relevantes especialmente en ascensos, descensos y aproximaciones. En esta fase debe recordarse que el viento puede seguir siendo relativo a la rejilla del modelo.

El engelamiento combina una ventana termica favorable, entre `0` y `-20 degC`, con humedad o condensado cuando estan disponibles. Si falta humedad o condensado, el mapa solo identifica zonas termodinamicamente favorables.

La turbulencia se estima con un indice cinematico basado en cizalladura y gradientes horizontales de viento. Es util para localizar zonas dinamicamente activas, pero no equivale a un diagnostico completo de turbulencia.

La conveccion se aproxima inicialmente con precipitacion incremental intensa. Es una senal indirecta: puede indicar actividad convectiva, pero tambien precipitacion estratiforme intensa.

La visibilidad solo se representa si el WRF contiene un diagnostico especifico como `AFWA_VIS`. Si no existe, no se estima artificialmente para evitar conclusiones poco defendibles.

El jet stream se interpreta mejor con viento a 300 hPa. La mascara por umbral senala zonas de viento intenso, pero el eje del jet y su continuidad deben interpretarse con el mapa completo de viento.

Un hodografo puede ayudar a explicar cambios de viento con la altura en un aeropuerto o punto de ruta. Si se implementa, debe indicar niveles, unidades y si el viento esta rotado a coordenadas terrestres o es relativo a la rejilla.

## 4. Limitaciones importantes

Los mapas de riesgo son exploratorios. Los umbrales usados son criterios de analisis docente, no limites operacionales universales.

La deteccion automatica de frentes, vaguadas, dorsales, borrascas y zonas de viento es un objetivo de mejora. Mientras los diagnosticos sean exploratorios, deben presentarse como ayuda al analisis y no como clasificacion operacional cerrada.

Las rutas entre aeropuertos resumen condiciones a lo largo de una trayectoria. No sustituyen el analisis general de la situacion: primero se interpreta el dominio completo y despues se estudia el vuelo concreto.
