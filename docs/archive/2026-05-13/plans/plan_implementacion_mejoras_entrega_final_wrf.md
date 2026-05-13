# Plan de implementacion: mejoras para entrega final del simulador WRF

Estado: borrador listo para implementar.

Especificacion base: `docs/specs/especificacion_mejoras_entrega_final_wrf.md`.

## 1. Objetivo tecnico

Implementar las mejoras necesarias para que el simulador produzca una demo docente completa y defendible:

- viento rotado a coordenadas terrestres;
- mapas obligatorios de 850, 500 y 300 hPa;
- metadatos cientificos completos;
- salidas de ruta auditables;
- documentacion de exposicion;
- tests proporcionales al riesgo.

El plan evita una reestructuracion amplia del proyecto. Los cambios deben ser incrementales, revisables y compatibles con los comandos actuales.

## 2. Orden de implementacion

### Fase 1. Preparar fixtures y contrato de viento

Archivos principales:

- `tests/conftest.py`;
- `src/simulador_wrf/diagnostics.py`;
- `src/simulador_wrf/backends.py`;
- `src/simulador_wrf/normalization.py`;
- `src/simulador_wrf/cli.py`.

Tareas:

1. Hacer determinista `synthetic_wrf_dataset`.
2. Anadir `SINALPHA` y `COSALPHA` al fixture sintetico.
3. Definir una funcion testeable para rotacion:

   ```python
   rotate_wind_to_earth(u_grid, v_grid, sin_alpha, cos_alpha)
   ```

4. Anadir el parametro `wind_reference` a la cadena:

   ```text
   CLI -> process_wrf_dataset -> diagnosticos de superficie y viento 3D
   ```

5. Validar `wind_reference in {"earth", "grid"}` cerca de la entrada de la normalizacion.

Aceptacion:

- El fixture sintetico permite probar viento earth-relative.
- La rotacion se puede testear sin ejecutar la CLI.
- No cambia ningun nombre publico de variable.

Verificacion:

```powershell
uv run pytest tests/test_diagnostics.py tests/test_integration.py
```

### Fase 2. Rotar viento y completar metadatos

Archivos principales:

- `src/simulador_wrf/diagnostics.py`;
- `src/simulador_wrf/backends.py`;
- `src/simulador_wrf/normalization.py`.

Tareas:

1. Para viento 10 m:
   - si `wind_reference == "earth"`, crear `u10_ms` y `v10_ms` rotados con `SINALPHA/COSALPHA`;
   - si `wind_reference == "grid"`, copiar `U10/V10` como ahora;
   - calcular `wind10_speed_ms` y `wind10_dir_deg` desde `u10_ms/v10_ms`.

2. Para viento 3D:
   - desescalonar `U/V`;
   - si `earth`, rotar componentes desescalonadas;
   - guardar `u_ms`, `v_ms`, `wind_speed_ms`.

3. Propagar `wind_reference_frame` a:
   - componentes;
   - velocidades;
   - direccion;
   - campos isobaricos derivados;
   - cizalladura y turbulencia.

4. Completar atributos cientificos prioritarios:
   - `pressure_hpa`;
   - `temperature_c`;
   - `geopotential_height_m`;
   - `slp_hpa`;
   - `t_isobaric_c`;
   - `gh_isobaric_m`;
   - `wind_speed_isobaric_ms`.

5. Cambiar `slp_hpa` para que indique claramente "aproximada" en `long_name` y `limitations`.

Aceptacion:

- Con `earth`, los campos de viento declaran `wind_reference_frame = "earth_relative"`.
- Con `grid`, declaran `wind_reference_frame = "grid_relative"`.
- Si faltan `SINALPHA/COSALPHA` y se pide `earth`, se lanza un error claro.

Verificacion:

```powershell
uv run pytest tests/test_diagnostics.py tests/test_integration.py
```

### Fase 3. Precipitacion incremental y errores de CLI

Archivos principales:

- `src/simulador_wrf/diagnostics.py`;
- `src/simulador_wrf/cli.py`;
- `src/simulador_wrf/normalization.py`.

Tareas:

1. Detectar incrementos negativos en `precip_increment_mm`.
2. Aplicar politica por defecto:
   - valores negativos -> `0.0`;
   - atributo `negative_increment_count`;
   - `method` y `limitations` actualizados.
3. Anadir `--wind-reference earth|grid` a `normalizar`.
4. Sustituir abortos genericos de errores esperables por `click.ClickException`:
   - falta variable obligatoria;
   - falta `SINALPHA/COSALPHA`;
   - indice temporal fuera de rango;
   - `n_points < 2`.

Aceptacion:

- La CLI muestra mensajes accionables para errores de usuario.
- Los incrementos negativos quedan trazados en atributos.

Verificacion:

```powershell
uv run pytest tests/test_diagnostics.py tests/test_integration.py
```

### Fase 4. Completar mapas obligatorios

Archivos principales:

- `src/simulador_wrf/cli.py`;
- `src/simulador_wrf/visualization.py`;
- `tests/test_integration.py`.

Tareas:

1. En `simulador-wrf mapas`, generar:
   - `t850_t{idx}.png` desde `t_isobaric_c` en 850 hPa;
   - `t500_t{idx}.png` desde `t_isobaric_c` en 500 hPa;
   - `wind300_t{idx}.png` desde `u_isobaric_ms`, `v_isobaric_ms`, `wind_speed_isobaric_ms` en 300 hPa.

2. Asegurar que `plot_wind_map` puede funcionar sobre un dataset seleccionado por nivel.

3. Hacer que `plot_scalar_map` muestre aviso exploratorio si aparece en:
   - `description`;
   - `limitations`;
   - `warning`;
   - `scientific_interpretation`.

4. Mejorar titulos de SLP para indicar aproximacion cuando el atributo lo declare.

Aceptacion:

- Los tres PNG nuevos se generan por defecto.
- Los mapas nuevos no rompen los tests existentes de mapas.

Verificacion:

```powershell
uv run pytest tests/test_integration.py
```

### Fase 5. Mejorar rutas y salidas

Archivos principales:

- `src/simulador_wrf/routes.py`;
- `src/simulador_wrf/route_outputs.py`;
- `src/simulador_wrf/cli.py`;
- `tests/test_routes.py`.

Tareas:

1. Validar `n_points >= 2` en `calculate_great_circle_route` y en CLI.
2. Ampliar `RoutePoint` o `data` para incluir:
   - `fraction`;
   - `y_index`;
   - `x_index`;
   - `nearest_grid_distance_km`;
   - `wind_reference_frame`.
3. Calcular distancia al vecino con haversine aproximado.
4. Exportar esas columnas al CSV.
5. Reescribir frases del Markdown:
   - "Probabilidad de engelamiento" -> "Porcentaje de trayectoria con condiciones favorables a engelamiento";
   - "Riesgo convectivo" -> "Proxy convectivo por precipitacion intensa";
   - anadir aviso de viento `earth_relative` o `grid_relative`.
6. Mantener el aviso final de producto docente y exploratorio.

Aceptacion:

- CSV contiene columnas de trazabilidad espacial.
- Markdown no usa lenguaje operacional para mascaras/proxies.
- `n_points < 2` falla con mensaje claro.

Verificacion:

```powershell
uv run pytest tests/test_routes.py
```

### Fase 6. Documentacion de entrega

Archivos principales:

- `README.md`;
- `docs/guide/guion_demo_exposicion.md`;
- docs con referencias internas obsoletas.

Tareas:

1. Actualizar README con:
   - flujo completo de demo;
   - `--wind-reference`;
   - salidas esperadas de mapas y rutas;
   - aviso de riesgos exploratorios;
   - comandos de test y lint.

2. Crear `docs/guide/guion_demo_exposicion.md` con:
   - orden de ejecucion;
   - archivos que abrir;
   - lectura meteorologica de cada bloque;
   - limitaciones que reconocer;
   - preguntas previsibles del profesor.

3. Corregir referencias obsoletas evidentes:
   - rutas antiguas fuera de `docs/specs/`;
   - rutas antiguas fuera de `docs/reports/`;
   - frase poco academica en el reporte de rutas.

Aceptacion:

- Una persona puede preparar la demo siguiendo README + guion.
- No quedan referencias internas rotas en los documentos tocados.

Verificacion:

```powershell
rg -n "docs/especificacion_|docs/decisiones_finales|certificada" docs
```

### Fase 7. Verificacion final con tests y WRF real

Tareas:

1. Ejecutar tests completos:

   ```powershell
   uv run pytest
   ```

2. Ejecutar lint:

   ```powershell
   uv run ruff check .
   ```

3. Ejecutar flujo con WRF real:

   ```powershell
   uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc --time-index 0 --wind-reference earth
   uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
   uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --time-index 0 --output-dir outputs/routes
   ```

4. Comprobar salidas:
   - NetCDF normalizado existe;
   - mapas obligatorios existen y no estan vacios;
   - CSV/Markdown/mapa/perfiles de ruta existen;
   - Markdown contiene aviso no operacional;
   - atributos de viento indican `earth_relative`.

Aceptacion:

- Tests y lint pasan.
- El flujo real termina sin errores.
- Las salidas generadas son coherentes para la exposicion.

## 3. Riesgos y mitigaciones

Riesgo: algunos datasets sinteticos antiguos no contienen `SINALPHA/COSALPHA`.

Mitigacion: actualizar fixtures y anadir test explicito de error cuando falten esos campos.

Riesgo: rotar el viento 3D antes de alinear dimensiones puede producir desajustes `xarray`.

Mitigacion: desescalonar primero, comprobar dimensiones finales `time`, `model_level`, `y`, `x` y probar con arrays deterministas.

Riesgo: `wind300_t0.png` requiere seleccionar `level_hpa=300` antes de llamar a `plot_wind_map`.

Mitigacion: usar el mismo patron que los mapas de geopotencial por nivel y anadir test de existencia del PNG.

Riesgo: el flujo real con WRF grande puede tardar.

Mitigacion: para verificacion final usar `--time-index 0` y documentar que la demo trabaja sobre un unico instante.

Riesgo: completar todos los metadatos puede generar cambios extensos.

Mitigacion: priorizar campos usados en mapas, rutas y riesgos; dejar metadatos de variables auxiliares no representadas para una fase posterior.

## 4. Criterios de cierre

La implementacion puede considerarse terminada cuando:

- la especificacion nueva y este plan estan en `docs/`;
- la CLI soporta `--wind-reference earth|grid`;
- el viento earth-relative funciona con el WRF real local;
- los mapas `t850`, `t500` y `wind300` se generan por defecto;
- el CSV de ruta incluye trazabilidad espacial;
- el Markdown de ruta usa lenguaje exploratorio y no operacional;
- README y guia de demo estan actualizados;
- `uv run pytest` pasa;
- `uv run ruff check .` pasa;
- el flujo real con `wrfout_d01_2009-12-16.nc` queda verificado.

