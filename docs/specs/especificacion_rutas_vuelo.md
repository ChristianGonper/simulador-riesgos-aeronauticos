# Especificacion v0.1: consulta de rutas de vuelo

## 1. Proposito

Esta fase conecta los mapas meteorologicos y los riesgos aeronauticos ya calculados con el objetivo final de la practica: seleccionar dos aeropuertos y resumir las condiciones atmosfericas que encontraria un vuelo entre ellos.

El producto sigue siendo docente y exploratorio. No pretende planificar un vuelo real ni sustituir informacion operacional aeronautica.

## 2. Entrada

La entrada principal es un NetCDF normalizado producido por `simulador-wrf normalizar`, con:

- coordenadas `time`, `lat`, `lon`, `y`, `x`;
- campos meteorologicos generales;
- campos de riesgo aeronautico cuando esten disponibles;
- niveles isobaricos en la coordenada `level_hpa` para variables de altura.

El usuario selecciona:

- aeropuerto origen mediante codigo ICAO o IATA;
- aeropuerto destino mediante codigo ICAO o IATA;
- indice temporal;
- nivel isobarico fijo, por defecto `300 hPa`;
- numero de puntos de muestreo sobre la ruta.

## 3. Aeropuertos

La primera version usara un catalogo interno de aeropuertos principales. El catalogo debe incluir, al menos:

- codigo ICAO;
- codigo IATA;
- nombre;
- pais;
- latitud;
- longitud.

El sistema no debe asumir que todos los aeropuertos del catalogo caen dentro de cualquier dominio WRF. En cada ejecucion debe validar que origen, destino y puntos de ruta estan dentro del dominio geografico del dataset.

## 4. Ruta

La ruta se calcula como una aproximacion de gran circulo entre origen y destino. La salida de la ruta es una secuencia ordenada de puntos con:

- fraccion de avance;
- distancia acumulada aproximada en kilometros;
- latitud;
- longitud;
- indices `y`, `x` del punto de malla WRF mas cercano;
- distancia al punto de malla mas cercano.

La version inicial usa vecino mas cercano sobre la malla `lat/lon` bidimensional. No debe usar `xarray.interp` directo en latitud/longitud porque la malla WRF puede ser curvilinea.

## 5. Variables muestreadas

La consulta de ruta debe muestrear, cuando existan:

- `wind_speed_isobaric_ms` en el nivel seleccionado;
- `t_isobaric_c` en el nivel seleccionado;
- `gh_isobaric_m` en el nivel seleccionado;
- `jet_stream_mask` cuando el nivel sea compatible, especialmente 300 hPa;
- `wind_shear_10m_850_ms`;
- `icing_mask`;
- `turbulence_index`;
- `convection_proxy`;
- `visibility_m`;
- `precip_increment_mm`;
- `t2_c`;
- `slp_hpa`;
- `wind10_speed_ms`.

Si una variable no existe, se omite del CSV y queda indicada como no disponible en el resumen.

## 6. Salidas

La fase debe producir en `outputs/routes/`:

- `route_<ORIGIN>_<DESTINATION>_t<TIME>_<LEVEL>hpa.csv`: tabla de puntos y valores muestreados;
- `route_<ORIGIN>_<DESTINATION>_t<TIME>_<LEVEL>hpa.md`: resumen interpretable;
- `route_<ORIGIN>_<DESTINATION>_t<TIME>_<LEVEL>hpa_map.png`: mapa de la ruta sobre el dominio WRF;
- `route_<ORIGIN>_<DESTINATION>_t<TIME>_<LEVEL>hpa_profile.png`: grafico de variables/riesgos frente a distancia.

El resumen debe incluir:

- aeropuertos de origen y destino;
- tiempo valido;
- nivel usado;
- distancia total aproximada;
- variables disponibles y no disponibles;
- maximos o medias relevantes;
- advertencia de que viento, cizalladura y turbulencia son exploratorios si el viento sigue siendo relativo a la rejilla.

## 7. Criterios de aceptacion

La fase se acepta cuando:

- resuelve aeropuertos por ICAO o IATA;
- filtra aeropuertos por dominio WRF;
- detecta rutas fuera del dominio;
- genera puntos de ruta reproducibles;
- muestrea variables sobre la malla WRF por vecino mas cercano;
- genera CSV, Markdown, mapa y perfil;
- expone una CLI `simulador-wrf ruta`;
- tiene tests unitarios e integracion;
- mantiene la trazabilidad cientifica y las limitaciones en el resumen.

## 8. Fuera de alcance

No forman parte de esta version:

- ascenso, crucero y descenso realistas;
- seleccion automatica de nivel de vuelo;
- interpolacion temporal;
- interpolacion vertical continua;
- restricciones de espacio aereo;
- meteorologia operacional certificada;
- deteccion automatica de frentes.
