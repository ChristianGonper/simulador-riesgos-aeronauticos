# Simulador WRF

Herramienta para la obtención, validación, diagnóstico y normalización de datos procedentes del modelo meteorológico WRF.

## Instalación

Este proyecto utiliza `uv` para la gestión de dependencias.

```bash
uv sync
```

## Uso

Procesar archivos WRF (Normalización):

```bash
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc
```

Generar Mapas:

```bash
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps
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

## Desarrollo

Ejecutar pruebas:

```bash
uv run pytest
```

Linting:

```bash
uv run ruff check .
```
