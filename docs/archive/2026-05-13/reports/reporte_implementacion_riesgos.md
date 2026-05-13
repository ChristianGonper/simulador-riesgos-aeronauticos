# Reporte de Implementación: Riesgos Aeronáuticos y Mapas

Se ha completado la implementación del sistema de diagnóstico y visualización de riesgos aeronáuticos basado en datos WRF normalizados, siguiendo el plan definido en `docs/plans/plan_implementacion_representacion_riesgos_aeronauticos.md`.

## 1. Diagnósticos de Riesgo Implementados

Se han añadido los siguientes campos al módulo `diagnostics.py`:

- **Cizalladura del viento (10m-850hPa):** Diferencia vectorial entre el viento en superficie y el nivel de 850 hPa.
- **Máscara de Engelamiento (Icing):** Identifica zonas favorables (0 a -20 °C), con filtro opcional de humedad.
- **Proxy de Convección:** Basado en intensidad de precipitación incremental.
- **Índice de Turbulencia:** Estimación cinemática escalada por un factor docente de 10.0.
- **Jet Stream:** Máscara de vientos máximos en 300 hPa.

Cada variable incluye ahora atributos de **trazabilidad científica** (`source_variables`, `scientific_interpretation`, `limitations`).

## 2. Sistema de Visualización

Se ha creado el módulo `visualization.py` utilizando `matplotlib` y `cartopy`.

- **Mapas Escalares:** Con paletas de colores meteorológicas estándar (RdBu_r para presión, coolwarm para temperatura, YlGnBu para precipitación).
- **Mapas de Viento:** Combinación de contornos de velocidad y barbas de viento para dirección e intensidad.
- **Mapas de Riesgo:** Uso de paletas de advertencia (YlOrRd, Reds, Blues) y gestión de máscaras binarias.
- **Georeferenciación:** Inclusión de líneas de costa y fronteras para facilitar la interpretación geográfica.

## 3. Interfaz de Línea de Comandos (CLI)

La herramienta `simulador-wrf` ahora soporta dos subcomandos:

1.  `normalizar`: Procesa los archivos `wrfout` originales y genera el NetCDF normalizado con todos los diagnósticos.
2.  `mapas`: Lee el NetCDF normalizado y genera los archivos PNG en el directorio de salida.

### Ejemplo de uso:

```powershell
# Fase 1: Normalización y Diagnóstico
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc

# Fase 2: Generación de Mapas
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps
```

## 4. Resultados Obtenidos

Se han generado satisfactoriamente 11 mapas para el caso de estudio (2009-12-16):
- Mapas generales: SLP, T2, Precipitación, Viento 10m, Geopotencial (850, 500 hPa).
- Mapas de riesgo: Cizalladura, Engelamiento, Turbulencia, Convección, Jet Stream.

## 5. Limitaciones Científicas

- El viento se mantiene relativo a la rejilla del modelo (grid-relative).
- La visibilidad se declara explícitamente en el dataset: si no existe `AFWA_VIS`, se genera la variable `visibility_m` con NaNs y un flag `visibility_available: 0` para asegurar la trazabilidad de la limitación.
- Los umbrales de riesgo son de carácter docente y exploratorio.
