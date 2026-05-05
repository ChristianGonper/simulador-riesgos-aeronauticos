# Especificacion v0.1: representacion de mapas y riesgos aeronauticos

## 1. Proposito de esta fase

Esta fase convierte el producto WRF normalizado en representaciones meteorologicas interpretables. La entrada principal es el `xarray.Dataset` generado en la fase de obtencion de datos WRF, normalmente exportado como `data/processed/wrf_normalizado.nc`.

El objetivo es producir mapas estaticos reproducibles que permitan:

- analizar la situacion meteorologica general;
- localizar estructuras relevantes para la seguridad aeronautica;
- generar diagnosticos exploratorios de riesgo;
- documentar que se esta representando, como se ha calculado y que limitaciones tiene.

Esta fase no construye todavia el simulador de rutas entre aeropuertos. Antes de muestrear una trayectoria de vuelo, el sistema debe ser capaz de representar y explicar los campos meteorologicos basicos y los indices de riesgo sobre el dominio WRF completo.

## 2. Entrada esperada

La entrada debe ser un dataset normalizado segun `docs/especificacion_obtencion_datos_wrf.md`, con coordenadas y dimensiones:

- `time`;
- `y`, `x`;
- `lat`, `lon`;
- `level_hpa` cuando existan campos isobaricos.

Los campos meteorologicos esperados para esta fase son:

- superficie: `slp_hpa`, `t2_c`, `u10_ms`, `v10_ms`, `wind10_speed_ms`, `wind10_dir_deg`, `precip_increment_mm`;
- niveles isobaricos: `gh_isobaric_m`, `t_isobaric_c`, `wind_speed_isobaric_ms`;
- jet stream: `jet_stream_mask`;
- auxiliares: viento, temperatura, humedad, precipitacion y topografia disponibles.

Si falta una variable necesaria para un mapa solicitado, el sistema debe fallar con un mensaje claro. Si falta una variable auxiliar para un riesgo opcional, el riesgo debe marcarse como no disponible o degradarse de forma documentada.

## 3. Salida esperada

La salida principal son figuras `PNG` en `outputs/maps/`. Cada figura debe incluir:

- variable representada;
- tiempo valido;
- unidades;
- barra de color;
- costa, fronteras o elementos cartograficos basicos cuando Cartopy pueda dibujarlos;
- indicacion textual si el producto es exploratorio.

Opcionalmente se puede crear un indice `HTML` sencillo con enlaces a las figuras generadas.

## 4. Campos meteorologicos a representar

### 4.1 Superficie

Los mapas de superficie deben permitir interpretar el tiempo sensible y la estructura basica de presion:

- presion reducida al nivel del mar para localizar borrascas y anticiclones;
- temperatura a 2 m para identificar masas de aire frias o calidas;
- viento a 10 m para analizar advecciones y zonas ventosas;
- precipitacion incremental para relacionar la dinamica con tiempo sensible.

### 4.2 Niveles isobaricos

Los niveles isobaricos se representan para conectar superficie y atmosfera libre:

- 850 hPa: temperatura, geopotencial y viento para masas de aire de baja troposfera;
- 500 hPa: geopotencial y temperatura para vaguadas, dorsales e inestabilidad basica;
- 300 hPa: viento y mascara de jet stream para localizar circulacion intensa en altura.

## 5. Riesgos aeronauticos iniciales

Los riesgos de esta fase son diagnosticos exploratorios. No deben presentarse como productos operacionales ni como certificacion de seguridad de vuelo.

### 5.1 Cizalladura

La cizalladura se calcula como diferencia vectorial entre dos niveles:

- `wind_shear_10m_850_ms`: diferencia entre viento a 10 m y viento en 850 hPa;
- `wind_shear_850_500_ms`: diferencia entre viento en 850 y 500 hPa, si estan disponibles las componentes en ambos niveles.

La interpretacion es detectar cambios fuertes de viento con la altura que puedan afectar ascensos, descensos o crucero bajo.

### 5.2 Engelamiento

El engelamiento se estima con una mascara simple:

- temperatura entre `0` y `-20 degC`;
- humedad relativa elevada, razon de mezcla de vapor disponible o presencia de condensado si existe.

Si solo existe temperatura isobarica y no hay humedad/condensado fiable, el producto debe llamarse zona termodinamicamente favorable, no riesgo completo de engelamiento.

### 5.3 Turbulencia

La turbulencia se representa mediante un indice cinematico simple basado en:

- cizalladura vertical;
- gradientes horizontales de viento.

Este indice identifica zonas dinamicamente favorables a turbulencia, especialmente cerca de chorros o cambios bruscos de viento.

### 5.4 Conveccion

La conveccion se representa inicialmente con precipitacion incremental intensa. Si se implementan CAPE/CIN de forma trazable en una fase posterior, podran sustituir o complementar este indicador.

### 5.5 Visibilidad

La visibilidad solo se representa directamente si existe un diagnostico WRF fiable, por ejemplo `AFWA_VIS`. Si no existe, el sistema debe crear una variable de disponibilidad o registrar que la visibilidad no puede estimarse de forma defendible con los campos actuales.

## 6. Trazabilidad y atributos

Cada variable derivada debe incluir:

- `long_name`;
- `units`;
- `method`;
- `source_variables`;
- `scientific_interpretation`;
- `limitations`.

Los mapas deben usar esos atributos para titulos, etiquetas y documentacion. La trazabilidad debe permitir responder que variable se muestra, de donde procede, en que unidades esta, como se calculo y que no permite concluir.

## 7. Estilo cientifico de codigo

La implementacion debe seguir programacion cientifica clara:

- nombres de variables ligados a magnitudes fisicas y unidades;
- funciones pequenas con una responsabilidad meteorologica;
- umbrales configurables o documentados;
- ausencia de abstracciones innecesarias;
- errores explicitos cuando falten campos;
- comentarios solo cuando aclaren una decision fisica o numerica.

La fase WRF previa documento que los vientos desescalonados siguen siendo relativos a la rejilla. Mientras no se implemente rotacion a coordenadas terrestres, los productos de viento, cizalladura, turbulencia y navegacion deben declararse exploratorios.

## 8. Criterios de aceptacion

La fase queda aceptada cuando:

- existe esta especificacion y una guia de interpretacion;
- se generan mapas meteorologicos generales en PNG;
- se generan mapas exploratorios de riesgos;
- cada figura incluye unidades y tiempo valido;
- cada riesgo conserva metodo, fuentes y limitaciones;
- los tests unitarios validan calculos basicos de riesgo;
- un test de integracion genera al menos un PNG no vacio desde datos sinteticos.

## 9. Referencias internas

- `docs/especificacion_obtencion_datos_wrf.md`: base cientifica y tecnica del dataset normalizado.
- `docs/decisiones_finales_implementacion_wrf.md`: decisiones ya tomadas, incluyendo la limitacion de viento relativo a la rejilla.
- `docs/Presentacion_tarea/transcripcion_clase.txt`: requisitos docentes de analisis meteorologico y riesgos aeronauticos.
