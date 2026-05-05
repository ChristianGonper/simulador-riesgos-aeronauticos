# Especificacion v0.2: obtencion cientifica de datos desde WRF

## 1. Proposito de esta fase

Esta primera fase define como debe entenderse, validar y transformar una salida del modelo WRF (`wrfout*.nc`) antes de cualquier visualizacion o calculo aeronautico avanzado. El objetivo no es dibujar mapas directamente ni construir todavia el simulador de rutas, sino producir una base de datos meteorologica coherente, trazable y fisicamente interpretable.

El producto de esta fase debe ser un conjunto normalizado de campos meteorologicos derivados de la salida cruda del modelo. Ese conjunto debe poder alimentar despues:

- mapas de analisis meteorologico general;
- diagnosticos sinopticos y mesoescalares;
- calculos posteriores de riesgos aeronauticos;
- consultas espaciales o temporales sobre el dominio del modelo.

La salida debe funcionar con el archivo de prueba disponible en el proyecto (`wrfout_d01_2009-12-16.nc`) y con otras salidas WRF equivalentes, aunque cambien el dominio horizontal, el numero de tiempos o la resolucion.

## 2. Criterio cientifico

WRF no debe tratarse como una tabla de datos meteorologicos finales. Es una salida de un modelo numerico, con variables nativas en coordenadas propias del modelo, una coordenada vertical seguidora del terreno de tipo eta/sigma y parte de la informacion expresada como perturbaciones o en mallas escalonadas. En particular, WRF-ARW usa una rejilla Arakawa-C, donde las componentes del viento y las variables de masa no siempre estan situadas en los mismos puntos de la celda. Por tanto, la obtencion de datos debe incorporar una fase de interpretacion fisica.

Los principios cientificos de esta fase son:

- La presion atmosferica util se obtiene como presion total, combinando presion perturbada y presion base.
- La temperatura debe derivarse desde la temperatura potencial perturbada cuando se trabaje con niveles del modelo.
- La altura debe obtenerse desde el geopotencial total, no desde indices verticales.
- Los vientos tridimensionales deben desescalonarse antes de combinar componentes o interpolar a niveles de presion.
- Los vientos deben expresarse, cuando sea necesario para analisis meteorologico, como componentes relativas a la Tierra y no solo relativas a la rejilla del modelo.
- Los campos en 850, 500 y 300 hPa deben obtenerse mediante interpolacion vertical sobre presion, porque WRF no usa directamente niveles isobaricos como coordenada vertical nativa.
- La precipitacion debe distinguir entre acumulado total e incremento entre tiempos consecutivos.
- Todas las variables derivadas deben conservar unidades y metadatos suficientes para evitar ambiguedad fisica.

Esta fase debe priorizar magnitudes meteorologicas estandar, no indices complejos. Los riesgos aeronauticos como engelamiento, turbulencia, cizalladura, visibilidad o conveccion quedan fuera del alcance de esta especificacion inicial, aunque se deben conservar campos auxiliares que permitan calcularlos despues.

## 2.1 Decisiones cerradas para la primera implementacion

Para que la primera fase sea implementable sin decisiones ambiguas, se fijan estas convenciones:

- La salida principal sera un `xarray.Dataset` normalizado y, por defecto, un NetCDF en `data/processed/wrf_normalizado.nc`.
- La implementacion debe aceptar un archivo unico o una lista/patron de archivos `wrfout*.nc` compatibles y concatenarlos temporalmente en orden cronologico.
- Los tiempos deben convertirse desde `Times` a una coordenada `time` interpretable por `xarray`; si la conversion temporal falla, el sistema debe conservar el texto original y registrar la limitacion.
- Las dimensiones nativas WRF se mapearan a nombres normalizados:
  - `Time` -> `time`;
  - `south_north` -> `y`;
  - `west_east` -> `x`;
  - `bottom_top` -> `model_level`;
  - dimensiones escalonadas `*_stag` -> dimensiones auxiliares solo durante el diagnostico.
- Las unidades canonicas internas seran:
  - presion en hPa para productos de analisis y niveles isobaricos;
  - temperatura en grados Celsius para campos operativos de superficie e isobaricos;
  - altura geopotencial en metros;
  - viento en m s-1, con opcion documentada de exportar diagnosticos auxiliares en kt cuando sean utiles para jet stream;
  - precipitacion en mm.
- El primer valor de `precip_increment_mm` sera `0.0` y el atributo del campo debe indicar que se trata de una convencion tecnica, no de una observacion real.
- Si se detectan incrementos negativos de precipitacion acumulada, por reinicios o discontinuidades de archivo, no deben corregirse silenciosamente. Deben marcarse como no disponibles o separarse por tramo temporal, registrando la decision en atributos.
- El umbral inicial para la mascara exploratoria de jet stream sera configurable y tendra como valor por defecto 60 kt, convertido internamente a m s-1 si el campo base esta en unidades SI.

## 3. Entrada esperada

La entrada principal sera uno o varios archivos NetCDF de salida WRF-ARW con patron `wrfout*.nc`. Deben admitirse tanto archivos individuales como series temporales formadas por varios archivos compatibles.

El sistema debe validar que existen, como minimo, las siguientes variables:

- Coordenadas y dominio: `XLAT`, `XLONG`, `Times`, y preferiblemente `ZNU` y `ZNW` para documentar la coordenada vertical nativa.
- Superficie: `T2`, `PSFC`, `U10`, `V10`, `HGT`.
- Precipitacion: `RAINC`, `RAINNC`.
- Atmosfera 3D: `U`, `V`, `PH`, `PHB`, `T`, `P`, `PB`, `QVAPOR`.

Variables adicionales como `W`, `QCLOUD`, `QRAIN`, `QICE`, `QSNOW`, `QGRAUP`, `PBLH` o `CLDFRA`, si estan disponibles, deben conservarse o quedar accesibles para fases posteriores, pero no son obligatorias para el nucleo de esta primera entrega.

La especificacion asume una salida WRF estandar. Si un archivo no cumple esa estructura, el sistema no debe intentar corregirlo silenciosamente: debe informar que faltan variables esenciales o que la estructura no es compatible.

La gestion temporal debe permitir seleccionar un instante concreto y tambien conservar series temporales completas. Esta capacidad sera necesaria en fases posteriores para estudiar la evolucion meteorologica y para muestrear trayectorias de vuelo.

Cuando la entrada sea multifichero, la validacion debe comprobar que los archivos pertenecen al mismo dominio fisico antes de combinarlos. Como minimo deben coincidir dimensiones horizontales, proyeccion, resolucion `DX`/`DY` y coordenadas `XLAT`/`XLONG` dentro de una tolerancia numerica razonable. Si hay tiempos duplicados, la implementacion debe ordenar cronologicamente y resolver duplicados de forma explicita, preferiblemente fallando con un mensaje claro salvo que se active una politica documentada.

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

Para el archivo de prueba local `wrfout_d01_2009-12-16.nc`, la validacion documental observada con `xarray`/`netCDF4` es:

- `Time`: 17 tiempos;
- `south_north`: 120 puntos;
- `west_east`: 99 puntos;
- `bottom_top`: 44 niveles de masa;
- `bottom_top_stag`: 45 niveles escalonados;
- `DX = DY = 27000.0 m`;
- `MAP_PROJ = 1`, compatible con proyeccion Lambert conforme en WRF;
- `START_DATE = 2009-12-16_00:00:00`.

Estos valores no deben codificarse como constantes del programa, pero sirven como prueba de integracion para comprobar que la extraccion reconoce correctamente una salida WRF real.

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
  - primer incremento definido como `0.0`, documentando en los atributos que es una convencion tecnica de la extraccion.

La presion a nivel del mar puede obtenerse mediante diagnosticos de `wrf-python` cuando este disponible. Si no lo esta, se debe usar una alternativa cientificamente documentada con `xarray`, `xWRF` o `MetPy`, evitando formulas ad hoc sin trazabilidad.

En el caso del viento, debe quedar documentado si las componentes usadas son relativas a la rejilla del modelo o relativas a la Tierra. Para representaciones meteorologicas y navegacion posterior se preferiran componentes rotadas a coordenadas terrestres, por ejemplo mediante diagnosticos equivalentes a `uvmet` o `uvmet10`.

La convencion de direccion de viento debe ser meteorologica: grados desde donde sopla el viento, con 0/360 grados para viento del norte y giro horario. Debe quedar indicado si la direccion procede de componentes terrestres rotadas o de componentes de rejilla.

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

Para reforzar el analisis sinoptico pedido en clase, se recomienda que el dataset incluya tambien, cuando sea viable con las mismas variables ya procesadas:

- presion a nivel del mar en superficie, util para localizar borrascas y anticiclones;
- altura geopotencial en 850 y 500 hPa, util para identificar vaguadas, dorsales y estructura baroclina;
- temperatura en 850 y 500 hPa, util para interpretar masas de aire e inestabilidad basica;
- precipitacion acumulada e incremental, util para relacionar la situacion sinoptica con tiempo sensible.

La deteccion automatica de frentes queda fuera de alcance, pero la extraccion debe producir los campos necesarios para que puedan interpretarse manualmente o calcularse en fases posteriores.

Para 300 hPa se debe obtener:

- componentes del viento;
- modulo del viento;
- un diagnostico basico para localizar el jet stream, entendido inicialmente como zonas de viento fuerte en ese nivel.

Como referencia operativa inicial, la localizacion del jet stream puede apoyarse en umbrales de viento fuerte del orden de 60-70 kt en 300 hPa. Ese umbral debe entenderse como criterio exploratorio para analisis, no como definicion fisica unica.

La interpolacion debe realizarse desde campos 3D usando presion total como coordenada vertical. El metodo recomendado es interpolacion vertical lineal o logaritmica en presion, siempre documentando la opcion elegida. La salida de cada nivel debe mantener la misma malla horizontal que el dominio WRF.

Debe contemplarse que, sobre zonas de relieve alto, algunos niveles de presion puedan quedar por debajo de la superficie del modelo. En esos puntos la salida debe usar valores no disponibles o mascaras fisicamente justificadas, no extrapolaciones silenciosas.

La interpolacion debe aplicarse solo tras desescalonar las variables que lo requieran y tras convertir la presion a unidades coherentes con los niveles solicitados. Si se usa `wrf-python`, `interplevel` realiza interpolacion lineal a un plano horizontal de presion o altura; si se usa `xWRF`/`xarray`, la implementacion debe documentar el metodo equivalente y verificar que las dimensiones finales son `time`, `level`, `y`, `x`.

### 4.4 Campos auxiliares para fases posteriores

Aunque esta fase no calcule riesgos aeronauticos, debe dejar preparados o accesibles los campos:

- presion 3D;
- temperatura 3D;
- altura geopotencial 3D;
- humedad especifica o razon de mezcla de vapor de agua;
- humedad relativa si puede obtenerse de forma fiable;
- componentes tridimensionales del viento ya desescalonadas;
- variables de condensado si estan disponibles (`QCLOUD`, `QRAIN`, `QICE`, `QSNOW`, `QGRAUP`);
- diagnosticos convectivos disponibles en el archivo o calculables mas adelante, como CAPE/CIN;
- variables diagnosticas especificas de WRF si existen, por ejemplo `AFWA_VIS` para visibilidad.

Estos campos seran la base para diagnosticos posteriores de cizalladura, turbulencia, engelamiento, nubosidad, conveccion y visibilidad.

Para orientar esas fases posteriores, la extraccion debe conservar la informacion necesaria para:

- visibilidad: usar variables diagnosticas como `AFWA_VIS` si el WRF fue configurado con esquemas AFWA, o preparar humedad y condensados de bajo nivel para estimaciones alternativas;
- engelamiento: identificar capas con temperatura entre 0 y -20 grados Celsius combinadas con humedad elevada o agua liquida subenfriada;
- turbulencia en aire claro: calcular mas adelante indices cinematicos como Ellrod-Knapp a partir de deformacion, convergencia y cizalladura vertical del viento;
- cizalladura: comparar vectorialmente el viento horizontal entre niveles, por ejemplo superficie-850 hPa o 850-500 hPa;
- conveccion: preparar los campos necesarios para CAPE, CIN y niveles caracteristicos como LCL cuando se incorporen diagnosticos convectivos.

## 5. Producto normalizado

El resultado esperado es un dataset etiquetado, no una coleccion informal de arrays. La estructura recomendada es compatible con `xarray.Dataset`.

### 5.1 Variables canonicas minimas

La primera implementacion debe intentar producir, como minimo, estas variables con nombres estables:

- `slp_hpa`: presion reducida al nivel del mar.
- `t2_c`: temperatura a 2 m.
- `u10_ms`, `v10_ms`: componentes del viento a 10 m.
- `wind10_speed_ms`, `wind10_dir_deg`: modulo y direccion meteorologica del viento a 10 m.
- `precip_total_mm`, `precip_increment_mm`: precipitacion total acumulada e incremento temporal.
- `geopotential_height_m`: altura geopotencial en niveles isobaricos.
- `temperature_c`: temperatura en niveles isobaricos.
- `u_ms`, `v_ms`: componentes de viento en niveles isobaricos.
- `wind_speed_ms`: modulo del viento en niveles isobaricos.
- `jet_stream_mask`: mascara booleana en 300 hPa basada en umbral configurable de viento.
- `pressure_3d_hpa`, `temperature_3d_c`, `geopotential_height_3d_m`: campos auxiliares 3D basicos cuando el coste de almacenamiento lo permita.

Si una variable no puede calcularse por ausencia de dependencia o variable fuente, el sistema debe fallar en las variables obligatorias y registrar como no disponible solo las variables auxiliares no esenciales.

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
- convencion usada en variables ambiguas, por ejemplo direccion del viento o precipitacion incremental;
- metodo de interpolacion vertical cuando proceda;
- indicacion de si el viento esta rotado a coordenadas terrestres o conserva la orientacion de la rejilla.

El dataset completo debe incluir atributos globales con:

- archivo fuente;
- modelo de origen;
- fecha de inicio de la simulacion;
- dominio;
- resolucion;
- proyeccion;
- convenciones cartograficas necesarias para representar despues los campos con herramientas como Cartopy;
- librerias o metodologia usada para los diagnosticos.

## 6. Librerias recomendadas

La estrategia recomendada es hibrida:

- `wrf-python` debe considerarse la referencia principal para diagnosticos WRF porque proporciona rutinas especificas como `getvar`, `interplevel`, `latlon_coords`, `destagger` y diagnosticos meteorologicos ya implementados.
- Tambien se consideran relevantes diagnosticos de `wrf-python` como `uvmet`, `uvmet10`, `uvmet10_wspd_wdir` o equivalentes, porque reducen el riesgo de confundir viento relativo a la rejilla con viento relativo a la Tierra.
- En fases posteriores tambien seran relevantes diagnosticos como `cape_2d`, `cape_3d` o variables AFWA si estan presentes en la salida WRF, pero no deben desplazar el objetivo de esta primera fase.
- `xarray` debe ser la estructura central para representar el producto final, por su manejo de dimensiones etiquetadas, coordenadas, atributos y NetCDF.
- `xWRF` es una opcion practica para postprocesar salidas WRF dentro del ecosistema `xarray`, especialmente cuando `wrf-python` sea dificil de instalar en Windows con `uv`.
- `MetPy` puede apoyar calculos meteorologicos con unidades cuando algun diagnostico no este disponible directamente.
- `netCDF4` o motores compatibles deben usarse para leer los archivos WRF originales.

La implementacion posterior debe usar `uv` para gestionar dependencias y entornos Python, siguiendo las normas del proyecto.

La especificacion no obliga a que todas las librerias se usen simultaneamente. Obliga a que el resultado cientifico sea equivalente y a que las decisiones de calculo queden documentadas.

La arquitectura de implementacion debe ocultar las diferencias entre librerias detras de una capa pequena de diagnosticos. En la practica:

- Ruta preferente: `wrf-python` para `getvar`, `interplevel`, `destagger`, `latlon_coords`, `uvmet` y `uvmet10` cuando instale correctamente.
- Ruta alternativa: `xarray` + `xWRF` para postprocesado CF, diagnosticos basicos y vientos relativos a la Tierra cuando `wrf-python` no sea viable.
- Ruta auxiliar: `MetPy` solo para calculos meteorologicos puntuales con unidades, evitando duplicar funciones que WRF o xWRF ya resuelven.

La documentacion consultada indica que `xarray.open_mfdataset` es la opcion natural para abrir multiples NetCDF y que `to_netcdf` permite controlar codificacion, compresion y valores de relleno. Tambien indica que `xWRF` proporciona `.xwrf.postprocess()` para renombrar dimensiones/variables hacia convenciones CF, convertir unidades, decodificar tiempos, incluir coordenadas de proyeccion y calcular variables diagnosticas esenciales cuando los campos fuente estan disponibles.

## 7. Validaciones cientificas minimas

Antes de aceptar una extraccion como valida, deben comprobarse los siguientes puntos:

- El archivo contiene las variables minimas necesarias.
- Las dimensiones horizontales de los campos finales coinciden entre si.
- Las coordenadas `lat` y `lon` corresponden a la misma malla que los campos extraidos.
- La presion total se calcula como `P + PB`.
- La altura se calcula desde `PH + PHB`.
- Los vientos escalonados se transforman a la malla no escalonada antes de derivar modulo, direccion o interpolaciones.
- Las componentes de viento usadas para analisis final estan correctamente rotadas o, si no lo estan, queda indicado de forma explicita.
- Los niveles 850, 500 y 300 hPa se obtienen mediante interpolacion vertical sobre presion.
- Los puntos donde un nivel isobarico queda por debajo del terreno se enmascaran o se identifican como no disponibles.
- La precipitacion incremental se obtiene por diferencia temporal del acumulado, no tomando directamente el acumulado bruto como lluvia horaria.
- Las unidades finales son explicitas y coherentes.
- Los campos derivados no contienen valores absurdos evidentes, como temperaturas fisicamente imposibles, presiones negativas o vientos no numericos.

Tambien deben comprobarse aspectos de integridad practica:

- La seleccion de un unico `time_index` produce el mismo resultado que seleccionar ese tiempo desde la serie completa, salvo diferencias de metadatos esperables.
- La salida NetCDF se puede reabrir con `xarray.open_dataset`.
- Las coordenadas `lat` y `lon` tienen dimensiones compatibles con `y`, `x`.
- Las variables booleanas, como `jet_stream_mask`, conservan un atributo con el umbral usado y las unidades del viento base.
- Las variables exportadas usan valores no disponibles compatibles con NetCDF y no mezclan `NaN` con codificaciones enteras sin `_FillValue`.

Estas comprobaciones no sustituyen al analisis meteorologico, pero reducen el riesgo de representar campos matematicamente mal interpretados.

## 8. Criterios de aceptacion

La fase de obtencion de datos se considerara correctamente especificada e implementable cuando permita:

- abrir una salida WRF estandar;
- trabajar con un tiempo individual o con una serie temporal completa;
- identificar el dominio, los tiempos y la malla geografica;
- producir campos de superficie listos para analisis;
- producir campos en 850, 500 y 300 hPa;
- conservar campos auxiliares 3D para fases posteriores;
- exportar o mantener el resultado como dataset con metadatos;
- fallar de forma explicita si el archivo no contiene las variables necesarias.

Para esta primera fase, la aceptacion no exige:

- calcular automaticamente riesgos aeronauticos;
- decidir rutas entre aeropuertos;
- detectar frentes de forma automatica;
- construir mapas finales interactivos.

Si se generan graficos durante el desarrollo, deben considerarse herramientas de verificacion, no producto obligatorio de esta fase.

## 9. Flujo conceptual de procesado

La futura implementacion deberia seguir, a nivel conceptual, esta secuencia:

1. Abrir el archivo o serie de archivos WRF conservando metadatos.
2. Validar variables, dimensiones, tiempos y coordenadas.
3. Preparar la geometria comun de trabajo: coordenadas geograficas, topografia, proyeccion y tratamiento de la rejilla escalonada.
4. Calcular magnitudes 3D basicas: presion total, temperatura, altura geopotencial y viento desescalonado/rotado.
5. Calcular diagnosticos de superficie: presion a nivel del mar, temperatura a 2 m, viento a 10 m y precipitacion.
6. Interpolar los campos necesarios a 850, 500 y 300 hPa.
7. Aplicar mascaras fisicamente justificadas en puntos no validos, especialmente sobre relieve.
8. Empaquetar el resultado como dataset normalizado con unidades, coordenadas y metadatos.

Para el archivo de prueba del proyecto, el resultado esperado debe reconocer una simulacion WRF con 17 tiempos, dominio horizontal de 120 x 99 puntos, 44 niveles verticales y resolucion aproximada de 27 km, segun los metadatos del NetCDF.

## 10. Fuera de alcance en esta version

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

## 11. Referencias tecnicas

- `wrf-python`: documentacion de `getvar`, diagnosticos WRF e interpolacion vertical con `interplevel` (`https://wrf-python.readthedocs.io/en/main/basic_usage.html` y `https://wrf-python.readthedocs.io/en/main/user_api/generated/wrf.interplevel.html`).
- `xarray`: modelo de datos basado en `Dataset`, dimensiones etiquetadas, apertura multifichero con `open_mfdataset`, coordenadas y exportacion NetCDF con `to_netcdf` (`https://docs.xarray.dev/`).
- `xWRF`: postprocesado de salidas WRF integrado con `xarray`, especialmente `.xwrf.postprocess()` (`https://xwrf.readthedocs.io/en/latest/reference/generated/xarray.Dataset.xwrf.postprocess.html`).
- `MetPy`: calculos meteorologicos con unidades y compatibilidad con `xarray`.
- Documentacion docente del proyecto en `docs/Presentacion_tarea`, especialmente la transcripcion de clase sobre campos a representar y objetivo del simulador.
