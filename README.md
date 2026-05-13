# Simulador WRF

Herramienta docente para analizar salidas del modelo WRF, representar la situacion meteorologica general y evaluar riesgos meteorologicos/aeronauticos de forma exploratoria.

El proyecto se organiza en dos fases:

1. **Representación Meteorológica Completa**: Mapas de superficie (SLP, T2, Viento, Precipitación) y niveles aeronáuticos (850, 500, 300 hPa) con geopotencial, temperatura y viento.
2. **Diagnósticos Estructurales**: Detección programática de centros de presión (A/B), ejes de vaguada/dorsal en 500hPa y gradientes térmicos (zonas baroclínicas) en 850hPa.
3. **Riesgos Aeronáuticos**: Proxies mejorados de engelamiento (Icing), turbulencia multinivel, cizalladura vertical, convección y visibilidad.
4. **Análisis de Rutas**: Muestreo meteorológico y de riesgos a lo largo de rutas de gran círculo entre cualquier aeropuerto ICAO/IATA.

La documentacion viva esta en [`docs/README.md`](docs/README.md).

## Instalación

Este proyecto utiliza `uv` para la gestión de dependencias.

```bash
uv sync
```

## Uso

Procesar archivos WRF:

```bash
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc
```

Generar mapas:

```bash
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps
```

Analizar una ruta:

```bash
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300
```

### Opciones `normalizar`

- `--input`, `-i`: Archivo(s) de entrada.
- `--output`, `-o`: Archivo de salida.
- `--jet-threshold`: Umbral de velocidad para detectar el jet stream (m/s).
- `--backend`: Backend de cálculo (`auto`, `xwrf`, `xarray`).
- `--levels`: Niveles de presión para interpolación.
- `--time-index`: Índice de tiempo específico.

### Opciones `mapas`

- `--input`, `-i`: Dataset NetCDF normalizado.
- `--output-dir`, `-o`: Directorio de salida para los mapas.
- `--time-index`: Índice de tiempo a representar.
- `--all-times`: Generar mapas para todos los tiempos.
- `--fields/--no-fields`: Generar mapas meteorológicos generales.
- `--risks/--no-risks`: Generar mapas de riesgos aeronáuticos.

### Opciones `ruta`

- `--input`, `-i`: Dataset NetCDF normalizado.
- `--origin`, `-src`: Código ICAO/IATA del aeropuerto de origen.
- `--dest`, `-dst`: Código ICAO/IATA del aeropuerto de destino.
- `--level`, `-l`: Nivel de presión para la ruta (hPa). Por defecto 300.
- `--n-points`, `-n`: Número de puntos en la ruta. Por defecto 50.
- `--output-dir`, `-o`: Directorio de salida para los resultados de la ruta.

## Desarrollo

Ejecutar pruebas:

```bash
uv run pytest
```

Linting:

```bash
uv run ruff check .
```

## Documentacion

- Estado actual: [`docs/estado_actual.md`](docs/estado_actual.md)
- Pendientes de correccion: [`docs/pendientes_correccion.md`](docs/pendientes_correccion.md)
- Plan tecnico activo: [`docs/plans/plan_codigo_deteccion_visualizacion.md`](docs/plans/plan_codigo_deteccion_visualizacion.md)
- Guia de interpretacion: [`docs/guide/guia_interpretacion_mapas_riesgos.md`](docs/guide/guia_interpretacion_mapas_riesgos.md)

Los productos de riesgo son docentes y exploratorios. No deben usarse para navegacion real.
