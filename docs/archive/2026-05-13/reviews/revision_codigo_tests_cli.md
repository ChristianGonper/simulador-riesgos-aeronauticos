# Revision de arquitectura, mantenibilidad, CLI y pruebas

Fecha de revision: 2026-05-05

Archivos revisados:

- `pyproject.toml`
- `README.md`
- `src/simulador_wrf/*.py`
- `tests/*.py`
- `docs/instrucciones_programacion_wrf.md`

Comprobaciones ejecutadas:

- `uv run pytest`: 14 tests correctos, 28 warnings.
- `uv run ruff check .`: correcto, sin incidencias.

Tambien se consulto Context7 para contrastar practicas actuales de `pytest`: el uso de `tmp_path` y fixtures es adecuado para aislar salidas temporales; los warnings conocidos conviene verificarlos explicitamente con mecanismos como `recwarn` o filtrarlos de forma documentada cuando sean aceptados.

## Resumen ejecutivo

El proyecto tiene una base razonablemente clara para una herramienta cientifica pequena: separa entrada/salida WRF, normalizacion, diagnosticos, rutas, visualizacion, salidas de ruta y CLI. El README ya ofrece comandos reproducibles con `uv`, el entrypoint esta declarado en `pyproject.toml`, y existen tests unitarios e integracion que cubren el flujo principal `normalizar`, generacion de mapas y analisis de ruta.

Los riesgos principales no estan en el estilo superficial, sino en contratos cientificos y de arquitectura que todavia son fragiles:

- La CLI contiene demasiada orquestacion, imports internos y detalles de productos de salida.
- Algunos modulos cientificos mutan datasets en cadena sin contrato claro de entrada/salida.
- Hay inconsistencias de metadatos respecto a las instrucciones del proyecto, especialmente `limitations` vs `limitation` y campos derivados sin `source_variables`, `method` o interpretacion cientifica.
- Los errores de CLI se simplifican con `click.Abort`, perdiendo mensajes estructurados y codigos de fallo mas utiles.
- Las pruebas pasan, pero usan datos aleatorios, no fijan semilla y apenas validan valores cientificos de diagnosticos complejos.
- Hay warnings de compatibilidad futura de `xarray` y un warning de posible incompatibilidad binaria de `numpy` que no deberian quedar como ruido permanente.

## Arquitectura y separacion de responsabilidades

### Fortalezas

- `src/simulador_wrf/io.py` concentra validacion, decodificacion temporal y normalizacion de dimensiones.
- `src/simulador_wrf/backends.py` encapsula calculos WRF basicos y el fallback entre `xwrf` y `xarray`.
- `src/simulador_wrf/diagnostics.py` agrupa diagnosticos meteorologicos y riesgos aeronauticos.
- `src/simulador_wrf/routes.py` mantiene calculo de ruta, validacion de dominio y muestreo.
- `src/simulador_wrf/route_outputs.py` agrupa CSV, Markdown y graficos de ruta.
- `src/simulador_wrf/visualization.py` centraliza mapas y utilidades de coordenadas.

La estructura modular esta alineada con `docs/instrucciones_programacion_wrf.md`, que pide separar diagnosticos, riesgos, visualizacion y rutas.

### Problemas

1. La CLI mezcla demasiadas responsabilidades.

`src/simulador_wrf/cli.py` no solo define opciones: tambien abre datasets, selecciona tiempos, decide nombres de archivos, resuelve aeropuertos, valida dominio, muestrea, exporta CSV/Markdown/PNG y maneja errores. Esto hace mas dificil probar la logica de aplicacion sin pasar por `CliRunner` y aumenta el coste de cambiar la CLI.

Prioridad: alta.

Recomendacion: extraer servicios de aplicacion, por ejemplo:

- `run_normalization(input_paths, output_path, options)`
- `run_map_generation(input_path, output_dir, options)`
- `run_route_analysis(input_path, origin, dest, options)`

La CLI deberia convertir strings de usuario a parametros tipados y delegar.

2. Hay acoplamiento inverso entre rutas y visualizacion.

`src/simulador_wrf/routes.py` importa `get_coords` desde `visualization.py`. Esa funcion no es realmente de visualizacion: es una utilidad de coordenadas del dataset. Esto fuerza a la logica de rutas a depender indirectamente de `matplotlib`/`cartopy` por el modulo de visualizacion.

Prioridad: media.

Recomendacion: mover `get_coords` a un modulo neutral, por ejemplo `coordinates.py` o `grid.py`, y usarlo desde rutas y visualizacion.

3. `diagnostics.py` mezcla diagnosticos basicos, riesgos y utilidades de interpolacion.

El modulo es funcional, pero ya acumula precipitacion, superficie, interpolacion vertical, jet stream, cizalladura, icing, conveccion, turbulencia y visibilidad. La separacion conceptual existe en funciones, pero no en modulos. Para un proyecto cientifico, convendria distinguir:

- diagnosticos basicos (`surface.py`, `vertical.py`, `precipitation.py`);
- riesgos aeronauticos exploratorios (`aviation_risks.py`);
- interpolacion o utilidades numericas (`interpolation.py`).

Prioridad: media. No es urgente mientras el proyecto sea pequeno, pero reducira deuda si se anaden mas diagnosticos.

4. `normalization.py` es un orquestador correcto, pero su contrato es implicito.

`process_wrf_dataset` aplica una cadena larga de mutaciones sobre `ds`. La funcion es facil de leer, pero no define claramente cuales variables espera ya normalizadas, cuales crea siempre, cuales son opcionales y bajo que condiciones se omiten.

Prioridad: media.

Recomendacion: documentar el contrato en docstring y/o en un reporte de variables esperadas/generadas. Para tests, convendria verificar un conjunto minimo de campos obligatorios y atributos.

## Mantenibilidad y estilo cientifico

### Aspectos positivos

- Los nombres principales son explicitos: `pressure_hpa`, `geopotential_height_m`, `wind_speed_ms`, `precip_increment_mm`, `level_hpa`.
- Se evita, en general, una abstraccion excesiva.
- Varias funciones incorporan docstrings breves.
- Los riesgos aeronauticos incluyen metadatos utiles como `source_variables`, `scientific_interpretation` y `limitations`.
- El resumen Markdown de rutas incluye aviso de producto docente y exploratorio.

### Problemas de trazabilidad cientifica

1. Metadatos incompletos o inconsistentes.

Las instrucciones piden que los campos derivados incluyan, cuando aplique, `units`, `long_name`, `method`, `source_variables`, `scientific_interpretation` y `limitations`.

Hay campos que no cumplen completamente:

- `src/simulador_wrf/backends.py`: `pressure_hpa`, `geopotential_height_m` y `temperature_c` solo incluyen `units` y `long_name`.
- `src/simulador_wrf/backends.py`: `slp_hpa` usa `limitation` en singular, mientras el documento pide `limitations`.
- `src/simulador_wrf/diagnostics.py`: `t2_c`, `wind10_speed_ms` y `wind10_dir_deg` tienen metadatos basicos, pero no trazabilidad completa.
- `src/simulador_wrf/normalization.py`: `wind_speed_ms` se calcula sin atributos.
- Los campos interpolados como `t_isobaric_c`, `gh_isobaric_m`, `wind_speed_isobaric_ms`, `u_isobaric_ms` y `v_isobaric_ms` no reciben atributos especificos tras `interpolate_to_pressure`.

Prioridad: alta.

Recomendacion: crear helpers pequenos para asignar atributos cientificos por variable derivada, sin construir una abstraccion pesada. Esto reduciria duplicacion y haria testeable la trazabilidad.

2. Viento no rotado: la limitacion aparece tarde y de forma parcial.

`calculate_wind_shear` declara que se basa en viento relativo a la rejilla, pero `u_ms`, `v_ms`, `wind_speed_ms`, `u_isobaric_ms` y `v_isobaric_ms` no arrastran claramente esa advertencia. Las instrucciones exigen indicar si el viento esta rotado a coordenadas terrestres o sigue siendo relativo a la rejilla.

Prioridad: alta.

Recomendacion: marcar todos los productos derivados de viento con un atributo comun, por ejemplo `wind_reference_frame = "grid_relative"` y `limitations`.

3. Fallbacks silenciosos o demasiado permisivos.

`get_wrf_backend` acepta backend desconocido, emite warning y usa auto. Para un CLI reproducible, un backend invalido ya queda prevenido por `click.Choice`, pero como API interna seria mejor fallar con `ValueError` o documentar explicitamente el fallback.

Prioridad: baja-media.

4. Uso de datos aleatorios en tests.

`tests/conftest.py` crea datasets con `np.random.rand` sin semilla. Aunque los tests actuales no parecen flakies, los valores fisicos sinteticos no son controlados y dificultan comprobar formulas.

Prioridad: media.

Recomendacion: usar un generador con semilla (`np.random.default_rng(0)`) o, mejor, campos deterministas simples para presion, temperatura y viento.

## CLI y reproducibilidad

### Fortalezas

- `pyproject.toml` define el script `simulador-wrf = "simulador_wrf.cli:main"`.
- El README documenta instalacion con `uv sync`.
- Los comandos principales son copiables:
  - `uv run simulador-wrf normalizar ...`
  - `uv run simulador-wrf mapas ...`
  - `uv run simulador-wrf ruta ...`
- Los subcomandos aceptan rutas explicitas de entrada y salida.
- Existen tests de integracion para `normalizar`, `mapas` y `ruta`.

### Problemas

1. Manejo de errores poco informativo para automatizacion.

La CLI captura `Exception`, registra el error y lanza `click.Abort`. Esto produce fallo, pero no distingue errores de usuario esperables: archivo no encontrado, variable ausente, nivel no disponible, aeropuerto fuera del dominio, indice temporal invalido.

Prioridad: alta.

Recomendacion: usar `click.ClickException` para errores corregibles por el usuario y dejar que errores inesperados fallen con traceback en modo desarrollo o con una opcion `--debug`.

2. Faltan tests de mensajes de error.

Hay tests de camino feliz, pero no se cubren:

- aeropuerto desconocido en `ruta`;
- ruta fuera del dominio;
- dataset sin variable obligatoria en `normalizar`;
- `time-index` fuera de rango;
- nivel isobarico solicitado no disponible;
- entrada inexistente.

Prioridad: alta.

3. README incompleto respecto a salidas.

El README dice donde se pasan `--output` y `--output-dir`, pero no lista nombres estables de productos generados. Las instrucciones del repo piden documentar donde se escriben, que significan y si deben versionarse o ignorarse por git.

Prioridad: media.

4. `export_dataset` falla con salidas sin directorio.

`src/simulador_wrf/normalization.py` usa `os.makedirs(os.path.dirname(output_path), exist_ok=True)`. Si el usuario pasa `--output wrf_normalizado.nc`, `os.path.dirname` devuelve cadena vacia y puede fallar. El README usa `data/processed/...`, pero la CLI deberia aceptar tambien una ruta de archivo en el directorio actual.

Prioridad: media.

## Pruebas

### Cobertura actual

Los tests cubren:

- validacion y normalizacion basica de datasets WRF;
- precipitacion acumulada e incremento;
- ejecucion CLI de `normalizar`;
- generacion CLI de mapas;
- resolucion de aeropuertos;
- calculo de ruta de gran circulo;
- validacion de dominio;
- muestreo en ruta;
- ejecucion CLI de `ruta` y existencia/no vacio de salidas CSV, Markdown y PNG.

Esto es una buena base para el tamano actual del proyecto.

### Debilidades

1. Falta validacion cientifica de diagnosticos complejos.

No hay tests directos para:

- presion `P + PB`;
- temperatura potencial a Celsius;
- altura geopotencial desescalonada;
- desescalonado manual de U/V;
- SLP aproximada;
- interpolacion log-lineal a presion;
- jet stream threshold;
- cizalladura, icing, conveccion y turbulencia con casos sinteticos deterministas.

Prioridad: alta.

2. Los tests de integracion validan existencia, no calidad de contenido.

Para mapas y rutas se comprueba que los archivos existan y no esten vacios, lo cual es correcto como smoke test. Falta comprobar contenido minimo del CSV/Markdown: columnas esperadas, origen/destino, distancia creciente, ausencia/presencia de variables y aviso no operacional.

Prioridad: media.

3. Warnings no gestionados.

`uv run pytest` genera 28 warnings:

- warning de posible incompatibilidad binaria de `numpy`;
- warnings futuros de `xarray` por `xr.concat`;
- warning futuro por `Dataset.dims` en tests.

Prioridad: media.

Recomendacion:

- Cambiar tests a `Dataset.sizes`.
- Pasar argumentos explicitos a `xr.concat` para `data_vars` y `coords` si procede.
- Investigar el warning binario de `numpy`; si proviene de una dependencia conocida y no es accionable, documentarlo y filtrarlo de forma especifica.

4. Tests dependientes de Cartopy pueden ser costosos.

Los tests de mapas y ruta ejecutan generacion real de PNG con `cartopy`. Esto da confianza, pero puede ser lento o fragil en CI si faltan datos/proyecciones. Mantener uno o dos smoke tests esta bien; para logica de nombres y seleccion de variables conviene tests sin render pesado.

Prioridad: baja-media.

## Dependencias y pyproject

### Observaciones

- `requires-python = ">=3.13"` es moderno y puede limitar instalacion en entornos cientificos donde aun se use Python 3.11/3.12. Si el proyecto depende realmente de 3.13, esta bien; si no, conviene evaluar bajar el minimo para facilitar reproducibilidad.
- Las dependencias principales estan declaradas en `pyproject.toml`.
- El grupo `dev` incluye `pytest` y `ruff`, suficiente para las comprobaciones actuales.
- Se respeta la gestion con `uv`.

### Riesgos

- Versiones minimas futuras o muy recientes (`numpy>=2.4.4`, `pandas>=3.0.2`, `xarray>=2026.4.0`, `dask>=2026.3.0`) pueden reducir reproducibilidad si el ecosistema binario local no esta estabilizado. El warning de `numpy.ndarray size changed` refuerza esta preocupacion.
- No se reviso `uv.lock` porque no estaba en la lista solicitada, pero para reproducibilidad real el lockfile es clave.

Prioridad: media.

## Deuda tecnica priorizada

### P1 - Alta prioridad

1. Completar metadatos cientificos de todos los campos derivados.

Debe incluir unidades, metodo, variables fuente, interpretacion y limitaciones cuando aplique. Especialmente viento, interpolacion, temperatura, presion, geopotencial y SLP.

2. Mejorar errores de CLI.

Sustituir abortos genericos por errores de usuario con mensajes accionables y tests negativos.

3. Anadir tests deterministas para diagnosticos cientificos.

Priorizar formulas fisicas y transformaciones de dimensiones: presion, temperatura, geopotencial, viento desescalonado, interpolacion y riesgos principales.

### P2 - Prioridad media

4. Extraer logica de aplicacion fuera de `cli.py`.

Permite probar flujos completos sin depender de Click y reduce acoplamiento.

5. Separar utilidades de coordenadas de `visualization.py`.

Evita que rutas dependan de stack grafico.

6. Gestionar warnings.

Eliminar warnings futuros de `xarray` y `Dataset.dims`; documentar o resolver el warning binario.

7. Hacer determinista `synthetic_wrf_dataset`.

Usar semilla o campos analiticos simples.

### P3 - Prioridad baja

8. Sustituir `print` por logging o devoluciones estructuradas en funciones de exportacion.

La CLI puede decidir como informar al usuario; las funciones de libreria deberian evitar imprimir directamente.

9. Dividir `diagnostics.py` cuando crezca.

No es imprescindible ahora, pero ayudara cuando haya mas productos.

10. Ampliar README con tabla de salidas generadas.

Incluir nombres de archivos, significado y politica de versionado/ignorado.

## Comandos reproducibles recomendados

Para desarrollo local:

```bash
uv sync
uv run pytest
uv run ruff check .
```

Para probar la CLI:

```bash
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --output-dir outputs/routes
```

## Conclusion

El proyecto esta en buen punto para consolidarse: la estructura existe, los comandos principales funcionan bajo tests y el README permite reproducir el uso basico con `uv`. La siguiente mejora de mayor impacto es convertir la trazabilidad cientifica en un contrato comprobable por tests, y endurecer la CLI ante errores reales de usuario. Despues conviene reducir acoplamientos pequenos pero relevantes, especialmente `cli.py` como orquestador excesivo y `routes.py` dependiendo de `visualization.py`.
