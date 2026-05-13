# Estado actual del simulador WRF

Fecha: 2026-05-13

El simulador es funcional y permite el procesamiento completo de salidas WRF para análisis meteorológico y aeronáutico.

## Flujo de Trabajo Recomendado

```powershell
# 1. Normalizar y calcular diagnósticos
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output outputs/processed.nc

# 2. Generar suite completa de mapas (Meteorología + Riesgos + Estructuras)
uv run simulador-wrf mapas --input outputs/processed.nc --output-dir outputs/maps

# 3. Analizar perfil vertical (Hodógrafo) en un punto o aeropuerto
uv run simulador-wrf perfil --airport MAD --input outputs/processed.nc --output outputs/hodografo_mad.png

# 4. Analizar ruta aérea
uv run simulador-wrf ruta --input outputs/processed.nc --origin MAD --dest BCN --level 300
```

## Capacidades Implementadas

### Representación Meteorológica e Isobarica
- **Mapas de superficie**: SLP, T2, Viento 10m, Precipitación incremental.
- **Niveles aeronáuticos**: Interpolación log-lineal a 850, 500 y 300 hPa.
- **Diagnósticos estructurales**: Detección de centros de presión (A/B), ejes de vaguada/dorsal (500hPa) y gradientes térmicos (850hPa).

### Riesgos Aeronáuticos
- **Engelamiento (Icing)**: Basado en temperatura y humedad relativa (estimada si falta).
- **Turbulencia**: Índice multinivel basado en cizalladura vertical ponderada.
- **Jet Stream**: Detección por umbral de velocidad y muestreo en rutas.
- **Cizalladura y Convección**: Proxies basados en viento y precipitación.

### Rutas y Perfiles
- **Ruta de gran círculo**: Muestreo robusto en rejillas 2D (XLAT/XLONG).
- **Hodógrafos**: Representación de perfiles de viento mediante MetPy.

## Limitaciones Conocidas
- **Referencia de viento**: Vientos desescalonados pero relativos a la rejilla (Grid-Relative).
- **Interpretación**: Los productos de riesgo son docentes y exploratorios.
- **Visibilidad**: Dependiente del diagnóstico AFWA_VIS original.

## Verificación
- `uv run pytest`: 20 passed.
- `uv run ruff check .`: Sin errores.
- Generación de suite de 18+ mapas: Verificada.
- Flujo CLI real con `wrfout_d01_2009-12-16.nc`: normalización, mapas, hodógrafo y ruta verificados.
- **Nota sobre warnings**: La suite mantiene un único warning de compatibilidad binaria de NumPy en el entorno Windows local. No procede de la lógica meteorológica del proyecto.
