# Especificacion v0.1: obtencion cientifica de datos desde WRF

## 1. Proposito de esta fase

Esta primera fase define como debe entenderse, validar y transformar una salida del modelo WRF (`wrfout*.nc`) antes de cualquier visualizacion o calculo aeronautico avanzado. El objetivo no es dibujar mapas directamente ni construir todavia el simulador de rutas, sino producir una base de datos meteorologica coherente, trazable y fisicamente interpretable.

El producto de esta fase debe ser un conjunto normalizado de campos meteorologicos derivados de la salida cruda del modelo. Ese conjunto debe poder alimentar despues:

- mapas de analisis meteorologico general;
- diagnosticos sinopticos y mesoescalares;
- calculos posteriores de riesgos aeronauticos;
- consultas espaciales o temporales sobre el dominio del modelo.

La salida debe funcionar con el archivo de prueba disponible en el proyecto (`wrfout_d01_2009-12-16.nc`) y con otras salidas WRF equivalentes, aunque cambien el dominio horizontal, el numero de tiempos o la resolucion.

## 2. Criterio cientifico

WRF no debe tratarse como una tabla de datos meteorologicos finales. Es una salida de un modelo numerico, con variables nativas en coordenadas propias del modelo y con parte de la informacion expresada como perturbaciones o en mallas escalonadas. Por tanto, la obtencion de datos debe incorporar una fase de interpretacion fisica.

Los principios cientificos de esta fase son:

- La presion atmosferica util se obtiene como presion total, combinando presion perturbada y presion base.
- La temperatura debe derivarse desde la temperatura potencial perturbada cuando se trabaje con niveles del modelo.
- La altura debe obtenerse desde el geopotencial total, no desde indices verticales.
- Los vientos tridimensionales deben desescalonarse antes de combinar componentes o interpolar a niveles de presion.
- Los campos en 850, 500 y 300 hPa deben obtenerse mediante interpolacion vertical sobre presion, porque WRF no usa directamente niveles isobaricos como coordenada vertical nativa.
- La precipitacion debe distinguir entre acumulado total e incremento entre tiempos consecutivos.
- Todas las variables derivadas deben conservar unidades y metadatos suficientes para evitar ambiguedad fisica.

Esta fase debe priorizar magnitudes meteorologicas estandar, no indices complejos. Los riesgos aeronauticos como engelamiento, turbulencia, cizalladura, visibilidad o conveccion quedan fuera del alcance de esta especificacion inicial, aunque se deben conservar campos auxiliares que permitan calcularlos despues.

## 3. Entrada esperada

La entrada principal sera uno o varios archivos NetCDF de salida WRF-ARW con patron `wrfout*.nc`.

El sistema debe validar que existen, como minimo, las siguientes variables:

- Coordenadas y dominio: `XLAT`, `XLONG`, `Times`.
- Superficie: `T2`, `PSFC`, `U10`, `V10`, `HGT`.
- Precipitacion: `RAINC`, `RAINNC`.
- Atmosfera 3D: `U`, `V`, `PH`, `PHB`, `T`, `P`, `PB`, `QVAPOR`.

Variables adicionales como `W`, `QCLOUD`, `QRAIN`, `QICE`, `QSNOW`, `QGRAUP`, `PBLH` o `CLDFRA`, si estan disponibles, deben conservarse o quedar accesibles para fases posteriores, pero no son obligatorias para el nucleo de esta primera entrega.

La especificacion asume una salida WRF estandar. Si un archivo no cumple esa estructura, el sistema no debe intentar corregirlo silenciosamente: debe informar que faltan variables esenciales o que la estructura no es compatible.

## 4. Campos que debe producir la extraccion

### 4.1 Metadatos del dominio

El dataset normalizado debe incluir:

- fecha inicial de la simulacion;
- tiempos validos disponibles;
- resolucion horizontal (`DX`, `DY`) si esta presente;
- proyeccion del modelo y parametros asociados si estan presentes;
- dimensiones horizontales del dominio;
- numero de niveles verticales;
- latitud y longitud de cada punto de malla;
- topografia del modelo.

Estos metadatos son necesarios para interpretar la escala espacial, ubicar los campos en un mapa y comparar el archivo de prueba con futuras simulaciones.

### 4.2 Campos de superficie

Para cada tiempo disponible se deben obtener:

- Presion reducida al nivel del mar, en hPa.
- Temperatura a 2 m, preferiblemente en grados Celsius para analisis operativo.
- Viento a 10 m:
  - componente zonal o este-oeste;
  - componente meridional o norte-sur;
  - modulo del viento;
  - direccion meteorologica, expresada como direccion desde la que sopla el viento.
- Precipitacion:
  - acumulado total `RAINC + RAINNC`;
  - incremento entre tiempos consecutivos;
  - primer incremento definido como cero o como dato no disponible, pero esta decision debe quedar documentada en los atributos del campo.

La presion a nivel del mar puede obtenerse mediante diagnosticos de `wrf-python` cuando este disponible. Si no lo esta, se debe usar una alternativa cientificamente documentada con `xarray`, `xWRF` o `MetPy`, evitando formulas ad hoc sin trazabilidad.

### 4.3 Campos en niveles isobaricos

La extraccion debe producir campos horizontales en los niveles:

- 850 hPa;
- 500 hPa;
- 300 hPa.

Para 850 hPa y 500 hPa se deben obtener:

- altura geopotencial o geopotential height;
- temperatura;
- componentes del viento;
- modulo del viento.

Para 300 hPa se debe obtener:

- componentes del viento;
- modulo del viento;
- un diagnostico basico para localizar el jet stream, entendido inicialmente como zonas de viento fuerte en ese nivel.

La interpolacion debe realizarse desde campos 3D usando presion total como coordenada vertical. La salida de cada nivel debe mantener la misma malla horizontal que el dominio WRF.

### 4.4 Campos auxiliares para fases posteriores

Aunque esta fase no calcule riesgos aeronauticos, debe dejar preparados o accesibles los campos:

- presion 3D;
- temperatura 3D;
- altura geopotencial 3D;
- humedad especifica o razon de mezcla de vapor de agua;
- humedad relativa si puede obtenerse de forma fiable;
- componentes tridimensionales del viento ya desescalonadas.

Estos campos seran la base para diagnosticos posteriores de cizalladura, turbulencia, engelamiento, nubosidad, conveccion y visibilidad.

## 5. Producto normalizado

El resultado esperado es un dataset etiquetado, no una coleccion informal de arrays. La estructura recomendada es compatible con `xarray.Dataset`.

Las dimensiones logicas deben ser:

- `time` para los tiempos validos;
- `level` para niveles isobaricos normalizados;
- `y` y `x` para la malla horizontal;
- una dimension vertical propia para campos 3D del modelo si se conservan sin interpolar.

Las coordenadas minimas deben ser:

- `time`;
- `level`, cuando aplique;
- `lat`;
- `lon`;
- `y`;
- `x`.

Cada variable debe incluir atributos con:

- nombre largo o descripcion fisica;
- unidades;
- procedencia o metodo de calculo;
- nivel vertical si aplica;
- convencion usada en variables ambiguas, por ejemplo direccion del viento o precipitacion incremental.

El dataset completo debe incluir atributos globales con:

- archivo fuente;
- modelo de origen;
- fecha de inicio de la simulacion;
- dominio;
- resolucion;
- proyeccion;
- librerias o metodologia usada para los diagnosticos.

## 6. Librerias recomendadas

La estrategia recomendada es hibrida:

- `wrf-python` debe considerarse la referencia principal para diagnosticos WRF porque proporciona rutinas especificas como `getvar`, `interplevel`, `latlon_coords`, `destagger` y diagnosticos meteorologicos ya implementados.
- `xarray` debe ser la estructura central para representar el producto final, por su manejo de dimensiones etiquetadas, coordenadas, atributos y NetCDF.
- `xWRF` es una opcion practica para postprocesar salidas WRF dentro del ecosistema `xarray`, especialmente cuando `wrf-python` sea dificil de instalar en Windows con `uv`.
- `MetPy` puede apoyar calculos meteorologicos con unidades cuando algun diagnostico no este disponible directamente.
- `netCDF4` o motores compatibles deben usarse para leer los archivos WRF originales.

La implementacion posterior debe usar `uv` para gestionar dependencias y entornos Python, siguiendo las normas del proyecto.

La especificacion no obliga a que todas las librerias se usen simultaneamente. Obliga a que el resultado cientifico sea equivalente y a que las decisiones de calculo queden documentadas.

## 7. Validaciones cientificas minimas

Antes de aceptar una extraccion como valida, deben comprobarse los siguientes puntos:

- El archivo contiene las variables minimas necesarias.
- Las dimensiones horizontales de los campos finales coinciden entre si.
- Las coordenadas `lat` y `lon` corresponden a la misma malla que los campos extraidos.
- La presion total se calcula como `P + PB`.
- La altura se calcula desde `PH + PHB`.
- Los vientos escalonados se transforman a la malla no escalonada antes de derivar modulo, direccion o interpolaciones.
- Los niveles 850, 500 y 300 hPa se obtienen mediante interpolacion vertical sobre presion.
- La precipitacion incremental se obtiene por diferencia temporal del acumulado, no tomando directamente el acumulado bruto como lluvia horaria.
- Las unidades finales son explicitas y coherentes.
- Los campos derivados no contienen valores absurdos evidentes, como temperaturas fisicamente imposibles, presiones negativas o vientos no numericos.

Estas comprobaciones no sustituyen al analisis meteorologico, pero reducen el riesgo de representar campos matematicamente mal interpretados.

## 8. Criterios de aceptacion

La fase de obtencion de datos se considerara correctamente especificada e implementable cuando permita:

- abrir una salida WRF estandar;
- identificar el dominio, los tiempos y la malla geografica;
- producir campos de superficie listos para analisis;
- producir campos en 850, 500 y 300 hPa;
- conservar campos auxiliares 3D para fases posteriores;
- exportar o mantener el resultado como dataset con metadatos;
- fallar de forma explicita si el archivo no contiene las variables necesarias.

Para el archivo de prueba del proyecto, el resultado esperado debe reconocer una simulacion WRF con 17 tiempos, dominio horizontal de 120 x 99 puntos, 44 niveles verticales y resolucion aproximada de 27 km, segun los metadatos del NetCDF.

## 9. Fuera de alcance en esta version

No forman parte de esta primera especificacion:

- interfaz grafica del simulador;
- seleccion de aeropuertos;
- muestreo de rutas de vuelo;
- calculo final de riesgo de engelamiento;
- calculo final de turbulencia;
- calculo final de cizalladura;
- estimacion operacional de visibilidad;
- deteccion automatica completa de frentes;
- generacion de mapas finales para presentacion.

Estos elementos dependen de una extraccion fiable y deberan especificarse en fases posteriores.

## 10. Referencias tecnicas

- `wrf-python`: documentacion de `getvar`, diagnosticos WRF e interpolacion vertical con `interplevel`.
- `xarray`: modelo de datos basado en `Dataset`, dimensiones etiquetadas, coordenadas y exportacion NetCDF.
- `xWRF`: postprocesado de salidas WRF integrado con `xarray`.
- `MetPy`: calculos meteorologicos con unidades y compatibilidad con `xarray`.
- Documentacion docente del proyecto en `docs/Presentacion_tarea`, especialmente la transcripcion de clase sobre campos a representar y objetivo del simulador.
