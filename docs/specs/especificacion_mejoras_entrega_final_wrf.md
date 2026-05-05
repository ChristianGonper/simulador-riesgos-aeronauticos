# Especificacion: mejoras para entrega final del simulador WRF

Estado: borrador listo para revision.

Fecha: 2026-05-05.

Revisiones base:

- `docs/reviews/revision_cumplimiento_profesor.md`
- `docs/reviews/revision_cientifica_meteorologica.md`
- `docs/reviews/revision_codigo_tests_cli.md`
- `docs/reviews/revision_riesgos_rutas.md`
- `docs/reviews/revision_documentacion_presentacion.md`

## 1. Objetivo

Esta fase consolida el simulador para una entrega docente defendible. El objetivo no es ampliar el proyecto con muchos diagnosticos nuevos ni hacer una refactorizacion arquitectonica amplia, sino cerrar los huecos que impiden mostrar, explicar y justificar el resultado ante el profesor.

El simulador debe permitir:

- normalizar una salida WRF real;
- generar mapas meteorologicos generales que cubran los campos pedidos en clase;
- usar viento en coordenadas terrestres cuando el WRF contenga los campos necesarios;
- analizar una ruta entre aeropuertos con salidas auditables;
- documentar claramente que los riesgos aeronauticos son productos docentes y exploratorios;
- ejecutar un flujo de demo reproducible con `uv`.

La entrega se considera correcta cuando una persona externa puede ejecutar los comandos principales, abrir las salidas esperadas y explicar que representa cada campo sin tener que leer el codigo fuente.

## 2. Alcance funcional

### 2.1 Normalizacion WRF

El subcomando `simulador-wrf normalizar` debe seguir aceptando los argumentos actuales y anadir una opcion explicita:

```powershell
--wind-reference earth|grid
```

El valor por defecto sera `earth`.

Con `--wind-reference earth`, el sistema debe calcular componentes de viento relativas a la Tierra usando `SINALPHA` y `COSALPHA`, equivalentes conceptualmente a los diagnosticos `uvmet` y `uvmet10` de `wrf-python`:

```text
u_east = u_grid * COSALPHA - v_grid * SINALPHA
v_north = v_grid * COSALPHA + u_grid * SINALPHA
```

Esta regla aplica a:

- viento de 10 m: `U10`, `V10` -> `u10_ms`, `v10_ms`;
- viento 3D tras desescalonado: `U`, `V` -> `u_ms`, `v_ms`.

Con `--wind-reference grid`, el sistema puede mantener el comportamiento actual, pero todos los campos de viento derivados deben quedar marcados como relativos a la rejilla.

Si el usuario solicita `earth` y faltan `SINALPHA` o `COSALPHA`, el sistema debe fallar con un error de usuario claro. No debe degradar silenciosamente a viento relativo a la rejilla.

### 2.2 Metadatos cientificos

Todo campo derivado relevante debe incluir, cuando aplique:

- `units`;
- `long_name`;
- `method`;
- `source_variables`;
- `scientific_interpretation`;
- `limitations`.

Los productos derivados de viento deben incluir ademas:

```text
wind_reference_frame = "earth_relative" | "grid_relative"
```

Campos prioritarios para completar metadatos:

- `t2_c`;
- `u10_ms`, `v10_ms`, `wind10_speed_ms`, `wind10_dir_deg`;
- `pressure_hpa`, `temperature_c`, `geopotential_height_m`;
- `u_ms`, `v_ms`, `wind_speed_ms`;
- `t_isobaric_c`, `gh_isobaric_m`, `wind_speed_isobaric_ms`, `u_isobaric_ms`, `v_isobaric_ms`;
- `slp_hpa`;
- `precip_total_mm`, `precip_increment_mm`;
- riesgos aeronauticos existentes.

`slp_hpa` debe mantenerse como campo valido para la demo, pero su `long_name`, titulo de mapa y `limitations` deben indicar que es una presion a nivel del mar aproximada por formula barometrica, no el diagnostico SLP completo de WRF.

### 2.3 Precipitacion acumulada e incremental

`precip_total_mm` debe seguir calculandose como:

```text
RAINC + RAINNC
```

`precip_increment_mm` debe representar el incremento entre salidas consecutivas. El primer tiempo queda en `0.0` por convencion tecnica, y el atributo del campo debe decirlo expresamente.

Si aparecen incrementos negativos, la implementacion debe:

- detectarlos;
- no ocultarlos silenciosamente;
- aplicar una politica documentada.

Politica por defecto de esta fase: fijar incrementos negativos a `0.0`, registrar el numero de celdas afectadas en atributos y documentar que pueden indicar reinicio del modelo o concatenacion discontinua.

### 2.4 Mapas obligatorios de la entrega

`simulador-wrf mapas` debe generar por defecto, ademas de los mapas actuales, estos archivos:

```text
t850_t{idx}.png
t500_t{idx}.png
wind300_t{idx}.png
```

El conjunto minimo de mapas para la demo sera:

- superficie:
  - `slp_t0.png`;
  - `t2_t0.png`;
  - `precip_t0.png`;
  - `wind10_t0.png`;
- niveles medios:
  - `gh850_t0.png`;
  - `t850_t0.png`;
  - `gh500_t0.png`;
  - `t500_t0.png`;
- niveles altos:
  - `wind300_t0.png`;
  - `risk_jet_stream_mask_t0.png`;
- riesgos:
  - `risk_wind_shear_10m_850_ms_t0.png`;
  - `risk_icing_mask_t0.png`;
  - `risk_turbulence_index_t0.png`;
  - `risk_convection_proxy_t0.png`.

Los mapas deben incluir titulo, unidades, tiempo valido y, cuando proceda, aviso visible de producto exploratorio o limitacion cientifica relevante.

### 2.5 Rutas entre aeropuertos

`simulador-wrf ruta` mantiene la interfaz actual, pero sus salidas deben ser mas auditables.

El CSV debe incluir, por punto:

- `lat`;
- `lon`;
- `fraction`;
- `distance_km`;
- `y_index`;
- `x_index`;
- `nearest_grid_distance_km`;
- variables meteorologicas y de riesgo muestreadas.

`fraction` representa el avance normalizado desde origen a destino, en el rango `[0, 1]`.

`nearest_grid_distance_km` representa la distancia aproximada entre el punto de ruta y el punto WRF usado para muestreo.

La funcion de gran circulo y la CLI deben rechazar `n_points < 2` con mensaje claro.

El Markdown de ruta debe evitar lenguaje operacional. En particular:

- no debe decir "probabilidad de engelamiento" si se calcula una mascara;
- debe decir "porcentaje de trayectoria con condiciones favorables a engelamiento";
- debe llamar a `convection_proxy` proxy convectivo por precipitacion intensa;
- debe indicar si el viento usado es `earth_relative` o `grid_relative`;
- debe repetir que el producto es docente, exploratorio y no apto para navegacion real.

### 2.6 Documentacion de entrega

Debe crearse una guia corta:

```text
docs/guide/guion_demo_exposicion.md
```

La guia debe incluir:

- comandos de demo;
- archivos que abrir en orden;
- una frase defendible para cada mapa clave;
- limitaciones que conviene reconocer ante el profesor;
- respuestas breves a preguntas previsibles.

El README debe actualizarse con:

- instalacion con `uv`;
- flujo completo de demo;
- lista de salidas esperadas;
- explicacion breve de `--wind-reference`;
- aviso de riesgos exploratorios;
- politica de outputs generados.

Tambien deben corregirse referencias internas desactualizadas detectadas en las revisiones, sin reescribir toda la documentacion historica.

## 3. Interfaces publicas

### 3.1 CLI

Comando de normalizacion:

```powershell
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc --time-index 0 --wind-reference earth
```

Reglas:

- `--wind-reference earth` es el valor por defecto.
- `--wind-reference grid` es fallback explicito.
- Si se pide `earth` y faltan coeficientes de rotacion, se debe usar `click.ClickException`, no `click.Abort` generico.

Comando de mapas:

```powershell
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
```

Debe generar los mapas obligatorios definidos en esta especificacion siempre que las variables existan.

Comando de ruta:

```powershell
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --time-index 0 --output-dir outputs/routes
```

Debe generar CSV, Markdown, mapa y perfiles con nombres estables. Si alguna variable esperada no esta disponible, el Markdown debe declararlo de forma explicita.

### 3.2 Dataset normalizado

El dataset normalizado debe conservar nombres canonicos ya usados por el proyecto. No se deben renombrar campos publicos existentes salvo que haya una razon cientifica fuerte.

La rotacion de viento cambia el significado de `u10_ms`, `v10_ms`, `u_ms` y `v_ms` cuando `wind_reference_frame = earth_relative`, pero no cambia sus nombres. La interpretacion correcta debe estar en atributos y documentacion.

## 4. Comandos de desarrollo y verificacion

Instalacion:

```powershell
uv sync
```

Tests:

```powershell
uv run pytest
```

Lint:

```powershell
uv run ruff check .
```

Flujo completo de demo:

```powershell
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc --time-index 0 --wind-reference earth
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --time-index 0 --output-dir outputs/routes
```

## 5. Estilo de codigo esperado

La implementacion debe mantener estilo cientifico simple, con nombres explicitos y sin abstracciones innecesarias.

Ejemplo de estilo aceptado para la rotacion:

```python
def rotate_wind_to_earth(u_grid, v_grid, sin_alpha, cos_alpha):
    """Rota viento WRF de rejilla a componentes este/norte."""
    u_east = u_grid * cos_alpha - v_grid * sin_alpha
    v_north = v_grid * cos_alpha + u_grid * sin_alpha
    return u_east, v_north
```

La funcion debe ser testeable con arrays sinteticos. No debe quedar escondida dentro de la CLI.

## 6. Estrategia de pruebas

### 6.1 Tests unitarios

Se deben anadir tests deterministas para:

- rotacion 10 m con `SINALPHA = 0`, `COSALPHA = 1`;
- rotacion 10 m con un angulo controlado de 90 grados;
- rotacion 3D tras desescalonado;
- direccion meteorologica de viento con componentes conocidas;
- metadatos obligatorios en campos derivados prioritarios;
- incremento negativo de precipitacion;
- `calculate_great_circle_route(..., n_points=1)`.

### 6.2 Tests de integracion CLI

Se deben anadir o ajustar tests para:

- `normalizar --wind-reference earth` con dataset sintetico que incluya `SINALPHA` y `COSALPHA`;
- error claro si faltan `SINALPHA` o `COSALPHA` y se pide `earth`;
- generacion de `t850_t0.png`, `t500_t0.png` y `wind300_t0.png`;
- Markdown de ruta sin la palabra "probabilidad" aplicada a engelamiento;
- CSV de ruta con `fraction`, `y_index`, `x_index` y `nearest_grid_distance_km`.

### 6.3 Verificacion con WRF real

Antes de cerrar la fase debe ejecutarse el flujo completo con:

```text
wrfout_d01_2009-12-16.nc
```

Debe comprobarse que:

- la normalizacion termina sin error;
- los mapas obligatorios se generan y no estan vacios;
- la ruta demo genera CSV, Markdown, mapa y perfiles;
- el Markdown conserva avisos no operacionales;
- los atributos de viento indican `earth_relative`.

## 7. Limites de esta fase

No se implementa visibilidad si falta `AFWA_VIS`. El campo puede seguir declarandose como no disponible con `NaN` y metadatos explicativos.

No se exige implementar diagnosticos operacionales de engelamiento, turbulencia, conveccion o CAT. Los riesgos actuales se mantienen como proxies docentes, pero deben nombrarse y documentarse mejor.

No se exige una refactorizacion completa de `cli.py`, `diagnostics.py` o `routes.py`. Solo se permiten extracciones pequenas si hacen el cambio mas testeable.

No se anade `wrf-python` como dependencia obligatoria en esta fase. La rotacion se implementa explicitamente con `SINALPHA` y `COSALPHA`, ya presentes en el WRF real local.

## 8. Criterios de exito

La fase queda cerrada cuando:

- existe esta especificacion y el plan de implementacion asociado;
- `normalizar` soporta `--wind-reference earth|grid`;
- los campos de viento del dataset normalizado declaran su marco de referencia;
- `mapas` genera los mapas obligatorios adicionales;
- `ruta` produce CSV y Markdown auditables y no operacionales;
- README y guia de demo permiten preparar la exposicion;
- `uv run pytest` pasa;
- `uv run ruff check .` pasa;
- el flujo completo funciona con el WRF real local.

