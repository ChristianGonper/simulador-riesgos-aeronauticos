# Registro de decisiones técnicas finales - Fase WRF

Este documento resume las decisiones técnicas y científicas adoptadas durante la implementación de la fase de obtención y procesamiento de datos WRF.

## 1. Arquitectura y Backend
- **Capa de Abstracción:** Se ha implementado un sistema de backends en `backends.py` para desacoplar la lógica de diagnósticos de las librerías específicas.
- **Diferenciación de Rutas:** 
    - `auto`/`xwrf`: Utilizan `xWRF` para operaciones optimizadas como el desescalonamiento de mallas escalonadas (Arakawa C-grid).
    - `xarray`: Fuerza una ruta de cálculo nativa y manual, garantizando la reproducibilidad sin dependencias de terceros.
- **Limitaciones de Viento:** En esta fase, los vientos se desescalonan a la rejilla de masa pero se mantienen como grid-relative (viento de rejilla). La rotación a coordenadas terrestres queda para fases posteriores.

## 2. Rigor Científico y Diagnósticos
- **Interpolación Isobarica:** Se utiliza **interpolación log-lineal** (lineal en el logaritmo de la presión). Es el método estándar para variables meteorológicas que varían exponencialmente con la altura (como la presión).
- **Reducción a SLP:** Se aplica la fórmula barométrica con un gradiente térmico constante (gamma = 0.0065 K/m). Se documenta como una aproximación exploratoria al no considerar el perfil de humedad.
- **Precipitación:** Se calcula la precipitación total (`RAINC + RAINNC`) y el incremento temporal. El primer paso de tiempo se fija en `0.0` para mantener la continuidad de la serie.

## 3. Gestión de Datos y Validación
- **Normalización de Dimensiones:** Estandarización a `time`, `y`, `x`, `model_level` (nativa) y `model_level_stag` (escalonada).
- **Validación Estricta:** Se comprueban 17 variables obligatorias (incluyendo `PSFC`, `U10`, `V10`, `HGT`, `QVAPOR`) antes de iniciar el procesamiento.
- **Compatibilidad Multifichero:** Antes de concatenar archivos, se verifica la coherencia física de:
    - Dimensiones espaciales.
    - Resolución horizontal (`DX`, `DY`).
    - Atributos de proyección (`MAP_PROJ`, `TRUELAT`, etc.).
    - Coordenadas geográficas (`XLAT`, `XLONG`).

## 4. Implementación Técnica
- **Eficiencia:** Uso extensivo de `xarray` y `Dask` para el manejo eficiente de grandes volúmenes de datos NetCDF.
- **Exportación:** Salida en NetCDF4 con compresión `zlib` nivel 4 activa por defecto.
- **CLI:** Interfaz completa con soporte para selección de índices temporales, niveles de presión personalizados y elección de backend.
