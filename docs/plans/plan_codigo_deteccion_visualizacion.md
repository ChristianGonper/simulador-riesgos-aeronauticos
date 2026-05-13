# Plan de codigo: deteccion meteorologica y visualizacion entregable

Fecha: 2026-05-13

Este plan traduce los pendientes del proyecto en tareas de implementacion. Debe ejecutarse con programacion cientifica: funciones pequenas, nombres fisicos, unidades explicitas, tests con datos controlados y metadatos completos en cada campo derivado.

## Principios de implementacion

- Separar lectura WRF, diagnosticos meteorologicos, riesgos aeronauticos, rutas y visualizacion.
- No mezclar calculo fisico y plot en una misma funcion salvo wrappers de alto nivel.
- Preferir `xarray.DataArray` y `xarray.Dataset` para conservar dimensiones, coordenadas y atributos.
- Usar librerias meteorologicas cuando aporten rigor o eviten formulas ad hoc.
- Documentar siempre `units`, `long_name`, `method`, `source_variables`, `scientific_interpretation` y `limitations`.
- Si un diagnostico es exploratorio, nombrarlo y rotularlo como tal.

## Fase 1 - Representacion meteorologica general

### 1.1 Completar productos de mapa

Modificar `simulador_wrf.cli.mapas` para generar:

- `slp_t<T>.png`;
- `t2_t<T>.png`;
- `precip_t<T>.png`;
- `wind10_t<T>.png`;
- `t850_t<T>.png`;
- `gh850_t<T>.png`;
- `t500_t<T>.png`;
- `gh500_t<T>.png`;
- `wind300_t<T>.png`;
- `jet300_t<T>.png` o una version superpuesta sobre `wind300`.

Tests:

- test de integracion que compruebe que esos archivos existen y no estan vacios.

### 1.2 Mejorar titulos y rotulos

Cada mapa debe mostrar:

- variable;
- nivel si aplica;
- unidades;
- tiempo valido;
- aviso de producto exploratorio si aplica;
- advertencia de viento relativo a rejilla cuando corresponda.

Tests:

- test unitario de una funcion generadora de titulos o metadatos, sin depender de imagenes.

### 1.3 Viento rotado o trazabilidad explicita

Ruta minima:

- anadir `wind_reference = grid_relative` a `u10_ms`, `v10_ms`, `wind10_speed_ms`, `wind10_dir_deg`, `u_ms`, `v_ms`, `wind_speed_ms`, `u_isobaric_ms`, `v_isobaric_ms` y `wind_speed_isobaric_ms`;
- propagar ese aviso a mapas y rutas.

Ruta deseable:

- si existen `SINALPHA` y `COSALPHA`, crear componentes terrestres;
- definir nombres claros, por ejemplo `u10_earth_ms`, `v10_earth_ms`, `wind10_earth_speed_ms`, `wind10_earth_dir_deg`;
- permitir seleccionar referencia de viento en CLI.

Tests:

- caso sintetico con `SINALPHA=0`, `COSALPHA=1`, donde viento de rejilla y terrestre coinciden;
- caso con rotacion conocida para verificar signos y convencion meteorologica.

## Fase 2 - Riesgos y estructuras meteorologicas

### 2.1 Corregir jet stream en rutas

Incluir `jet_stream_mask` en `sample_wrf_at_points` y mostrarlo en el Markdown de ruta.

Tests:

- ruta sintetica con algunos puntos en jet;
- resumen Markdown con porcentaje correcto.

### 2.2 Centros de presion

Implementar deteccion exploratoria de minimos y maximos locales de `slp_hpa`.

Campos/salidas:

- tabla CSV o DataFrame con latitud, longitud, valor y tipo (`low`, `high`);
- capa opcional para plots con simbolos `B` y `A` o etiquetas equivalentes.

Limitacion:

- en dominios pequenos o baja resolucion puede detectar centros parciales o espurios.

### 2.3 Vaguadas y dorsales

Implementar ayuda diagnostica en 500 hPa:

- gradiente o curvatura de `gh_isobaric_m` a 500 hPa;
- identificacion exploratoria de ejes de vaguada/dorsal;
- no venderlo como analisis frontal automatico.

Tests:

- campo sintetico con una vaguada idealizada.

### 2.4 Zonas baroclinas y frentes aproximados

Calcular gradiente horizontal de temperatura en 850 hPa o superficie.

Salida:

- `temperature_gradient_850_km` o nombre equivalente con unidades claras;
- mapa de zonas baroclinas;
- opcion futura para dibujar lineas frontales manuales o semiautomaticas.

Limitacion:

- un gradiente termico intenso no equivale por si solo a un frente.

### 2.5 Riesgos aeronauticos mejorados

Engelamiento:

- calcular humedad relativa isobarica si hay variables suficientes;
- combinar temperatura y humedad.

Turbulencia:

- anadir cizalladura 850-500 hPa y 500-300 hPa;
- explorar deformacion horizontal si se puede calcular con la rejilla.

Conveccion:

- mantener proxy por precipitacion;
- si existen CAPE, reflectividad o variables convectivas, usarlas preferentemente.

Visibilidad:

- usar `AFWA_VIS` cuando exista;
- no estimar con formulas debiles sin documentar.

### 2.6 Hodografo y perfiles verticales

Crear productos para aeropuertos o puntos de ruta:

- hodografo de viento;
- perfil vertical de temperatura y viento;
- resumen de niveles relevantes.

Se puede usar MetPy si simplifica el calculo o la representacion.

## Fase 3 - Documentacion y entregable

### 3.1 README como puerta de entrada

Actualizar README con:

- instalacion;
- flujo completo;
- productos generados;
- limitaciones;
- ejemplo con el WRF real de prueba;
- enlace a guia de interpretacion y pendientes.

### 3.2 Informe meteorologico de caso

Crear un documento de caso de estudio para `wrfout_d01_2009-12-16.nc`:

- situacion de superficie;
- 850 hPa;
- 500 hPa;
- 300 hPa;
- riesgos;
- ruta de ejemplo.

### 3.3 Limpieza documental continua

Mantener vivos solo:

- `docs/README.md`;
- `docs/estado_actual.md`;
- `docs/pendientes_correccion.md`;
- `docs/guide/guia_interpretacion_mapas_riesgos.md`;
- planes activos en `docs/plans/`.

Los specs, reports y reviews historicos deben permanecer en `docs/archive/`.

## Verificacion minima antes de cerrar cada bloque

Ejecutar:

```powershell
uv run pytest
uv run ruff check .
```

Si se cambia visualizacion, ejecutar tambien un flujo real reducido:

```powershell
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output outputs/review/wrf_real_t0_normalizado.nc --time-index 0 --backend xarray
uv run simulador-wrf mapas --input outputs/review/wrf_real_t0_normalizado.nc --output-dir outputs/review/maps --time-index 0
uv run simulador-wrf ruta --input outputs/review/wrf_real_t0_normalizado.nc --origin MAD --dest BCN --output-dir outputs/review/routes --time-index 0 --level 300
```
