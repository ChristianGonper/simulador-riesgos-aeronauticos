# Simulador WRF

Herramienta para la obtención, validación, diagnóstico y normalización de datos procedentes del modelo meteorológico WRF.

## Instalación

Este proyecto utiliza `uv` para la gestión de dependencias.

```bash
uv sync
```

## Uso

Procesar archivos WRF:

```bash
uv run simulador-wrf --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc
```

### Opciones CLI

- `--input`, `-i`: Archivo(s) de entrada.
- `--output`, `-o`: Archivo de salida (por defecto: `data/processed/wrf_normalizado.nc`).
- `--jet-threshold`: Umbral de velocidad para detectar el jet stream (m/s).
- `--backend`: Backend de cálculo (`auto`, `xwrf`, `xarray`).
- `--levels`: Niveles de presión para interpolación (ej: `850 500 300`).
- `--time-index`: Índice de tiempo específico a procesar.

## Desarrollo

Ejecutar pruebas:

```bash
uv run pytest
```

Linting:

```bash
uv run ruff check .
```
