# Estado actual del simulador WRF

Fecha: 2026-05-13

El simulador ya ejecuta un flujo funcional sobre el archivo real `wrfout_d01_2009-12-16.nc`: normaliza datos WRF, genera mapas meteorologicos, calcula riesgos exploratorios y produce salidas de ruta entre aeropuertos.

## Flujo actual

```powershell
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --output-dir outputs/routes
```

## Capacidades implementadas

### Normalizacion WRF

- Validacion de variables WRF obligatorias.
- Normalizacion de dimensiones a `time`, `y`, `x`, `model_level`.
- Coordenadas `lat` y `lon`.
- Presion 3D desde `P + PB`.
- Temperatura 3D desde temperatura potencial perturbada.
- Altura geopotencial desde `PH + PHB`.
- Viento desescalonado a rejilla de masa.
- Precipitacion total e incremental.
- Exportacion NetCDF.

### Representacion meteorologica

- Presion a nivel del mar aproximada.
- Temperatura a 2 m.
- Precipitacion incremental.
- Viento a 10 m.
- Geopotencial en 850 y 500 hPa.
- Mascara de jet stream.
- Mapas de riesgos.

### Riesgos aeronauticos

- Cizalladura 10 m-850 hPa.
- Engelamiento como mascara termica, con humedad solo si existe.
- Proxy convectivo por precipitacion incremental.
- Indice exploratorio de turbulencia por cizalladura.
- Visibilidad solo si existe `AFWA_VIS`; si falta, se declara no disponible.

### Rutas

- Resolucion de aeropuertos por ICAO/IATA.
- Ruta de gran circulo.
- Validacion de dominio.
- Muestreo por vecino mas cercano.
- Exportacion CSV, Markdown, mapa y perfiles.

## Limitaciones actuales

- La CLI de mapas no genera aun todos los productos obligatorios por defecto: faltan temperatura en 850/500 hPa y viento de 300 hPa como mapa principal.
- El viento esta desescalonado, pero no rotado a coordenadas terrestres.
- La SLP es una aproximacion barometrica.
- Los riesgos son productos docentes exploratorios.
- La visibilidad no se estima si falta `AFWA_VIS`.
- El resumen de ruta no muestrea actualmente `jet_stream_mask`.

## Verificacion reciente

Comandos ejecutados:

```powershell
uv run pytest
uv run ruff check .
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output outputs/review/wrf_real_t0_normalizado.nc --time-index 0 --backend xarray
uv run simulador-wrf mapas --input outputs/review/wrf_real_t0_normalizado.nc --output-dir outputs/review/maps --time-index 0
uv run simulador-wrf ruta --input outputs/review/wrf_real_t0_normalizado.nc --origin MAD --dest BCN --output-dir outputs/review/routes --time-index 0 --level 300
```

Resultado:

- tests: `14 passed`;
- lint: sin errores;
- flujo real reducido: correcto.

Warnings a revisar:

- cambios futuros de `xarray` en defaults de concatenacion;
- aviso de dimension ilimitada `Time` al exportar datasets de un solo tiempo;
- posible warning binario de NumPy en el entorno local.
