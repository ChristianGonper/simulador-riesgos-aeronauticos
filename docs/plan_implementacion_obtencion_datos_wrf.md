# Plan de implementacion: obtencion de datos WRF

Estado: borrador v0.2 revisado para primera fase.

Especificacion base: `docs/especificacion_obtencion_datos_wrf.md`.

## Objetivo del plan

Definir el orden tecnico para implementar la fase de obtencion, validacion, diagnostico, normalizacion y exportacion de datos WRF. El plan respeta las decisiones ya cerradas en la especificacion:

- `precip_increment_mm` empieza con valor `0.0`.
- El dataset normalizado se guarda por defecto en `data/processed/wrf_normalizado.nc`.
- `xWRF` queda aceptado como alternativa si `wrf-python` no instala correctamente con `uv` en Windows.
- El diagnostico de jet stream en 300 hPa incluye velocidad del viento y mascara booleana por umbral configurable.
- El sistema de identificacion de riesgos aeronauticos queda excluido de esta fase. Solo se conservan campos auxiliares para poder calcularlos despues.
- La salida por defecto debe ser reabrible con `xarray.open_dataset` y conservar metadatos cientificos suficientes para explicar que se esta representando.

## Componentes principales

1. Configuracion del paquete Python:
   - Crear `pyproject.toml`, estructura `src/simulador_wrf/` y `tests/`.
   - Configurar dependencias base (`xarray`, `netCDF4`, `numpy`) y herramientas (`pytest`, `ruff`) con `uv`.
   - Incluir `dask` si se usa `xarray.open_mfdataset(..., parallel=True)` o chunking para archivos grandes.
   - Tratar `wrf-python`, `xWRF` y `MetPy` como dependencias meteorologicas condicionadas por viabilidad local.
   - Documentar en `README` o en `docs/` los comandos reales usados con `uv`, evitando instrucciones con `pip`.

2. Capa de entrada y validacion (`io.py`):
   - Resolver rutas de archivo unico y patrones `wrfout*.nc`.
   - Abrir datasets con `xarray`/`netCDF4`.
   - Para multiples archivos, usar una combinacion temporal explicita: lista ordenada o `xarray.open_mfdataset(..., combine="nested", concat_dim="Time")` cuando sea compatible.
   - Validar variables obligatorias, dimensiones y coordenadas.
   - Validar compatibilidad de dominio en entradas multifichero: `DX`, `DY`, proyeccion, dimensiones horizontales, `XLAT` y `XLONG`.
   - Decodificar `Times` hacia `time`; conservar texto original en atributos si la conversion no es perfecta.
   - Normalizar nombres de dimensiones hacia `time`, `model_level`, `y`, `x` sin perder metadatos originales.
   - Detectar tiempos duplicados o desordenados y fallar con mensaje claro en la primera version.

3. Diagnosticos meteorologicos (`diagnostics.py`):
   - Calcular precipitacion total e incremental.
   - Detectar incrementos negativos de precipitacion acumulada y marcarlos como no disponibles o fallar segun politica configurable.
   - Calcular o extraer presion 3D, altura geopotencial, temperatura y humedad.
   - Calcular viento de superficie y viento 3D desescalonado/rotado cuando la libreria lo permita.
   - Preparar interpolacion a 850, 500 y 300 hPa.
   - Calcular velocidad en 300 hPa y mascara booleana de jet stream.
   - Centralizar conversiones de unidades para evitar mezclar Pa/hPa, K/C, m s-1/kt.
   - Anadir atributos `method`, `units`, `source_variables` y `wind_reference` donde corresponda.

4. Capa de backends meteorologicos (`backends.py`):
   - Definir una interfaz pequena para diagnosticos WRF: `pressure`, `geopotential_height`, `temperature`, `earth_relative_wind`, `slp` e `interpolate_to_pressure_levels`.
   - Implementar primero el backend disponible localmente mas simple.
   - Mantener una ruta preferente `wrf-python` cuando instale correctamente y una ruta alternativa `xWRF`/`xarray`.
   - Evitar que la CLI o la normalizacion dependan directamente de detalles de `wrf-python` o `xWRF`.

5. Normalizacion y exportacion (`normalization.py`):
   - Construir el `xarray.Dataset` final con coordenadas, variables, atributos y convenciones.
   - Usar nombres canonicos definidos en la especificacion: `slp_hpa`, `t2_c`, `u10_ms`, `v10_ms`, `wind10_speed_ms`, `wind10_dir_deg`, `precip_total_mm`, `precip_increment_mm`, `geopotential_height_m`, `temperature_c`, `u_ms`, `v_ms`, `wind_speed_ms`, `jet_stream_mask`.
   - Aplicar politica de valores no disponibles bajo terreno.
   - Crear `data/processed/` si no existe.
   - Guardar por defecto en `data/processed/wrf_normalizado.nc` y permitir devolver el dataset en memoria.
   - Definir encoding NetCDF basico: compresion para variables grandes, `_FillValue` coherente para flotantes y atributos globales con librerias/metodos.

6. Interfaz de linea de comandos (`cli.py`):
   - Implementar `--input`, `--output`, `--time-index` o equivalente.
   - Anadir parametro configurable para el umbral de jet stream.
   - Anadir `--backend auto|wrf-python|xwrf|xarray` para hacer reproducible la ruta usada.
   - Anadir `--levels 850 500 300` con esos valores por defecto, aunque en esta fase se prueben esos tres niveles.
   - Usar `data/processed/wrf_normalizado.nc` como salida por defecto.
   - Mostrar errores claros ante variables ausentes o archivos incompatibles.

7. Documentacion tecnica y cientifica:
   - Mantener docstrings de modulos en espanol.
   - Documentar decisiones sobre `wrf-python` frente a `xWRF`.
   - Registrar limitaciones cientificas de interpolacion, rotacion de viento y mascara de jet stream.
   - Incluir un ejemplo minimo de uso de la CLI con el archivo de prueba local.
   - Explicar que los mapas y el calculo de riesgos quedan para fases posteriores.

## Orden de implementacion

1. Preparar estructura del paquete, `pyproject.toml`, `ruff` y `pytest`.
2. Crear datasets sinteticos minimos que representen dimensiones WRF reales, incluidas variables escalonadas `U`, `V`, `PH` y `PHB`.
3. Crear tests de validacion de variables obligatorias, dimensiones, tiempos y compatibilidad de dominio.
4. Implementar apertura, orden temporal y validacion de entradas.
5. Implementar normalizacion de coordenadas y dimensiones sin calcular todavia diagnosticos complejos.
6. Implementar diagnosticos simples y verificables: precipitacion total, incremento con primer valor `0.0`, conversiones basicas y atributos.
7. Implementar construccion del dataset normalizado y exportacion NetCDF por defecto.
8. Implementar capa de backend meteorologico y diagnosticos 3D.
9. Implementar interpolacion isobarica a 850, 500 y 300 hPa, incluyendo mascara bajo terreno.
10. Implementar mascara de jet stream en 300 hPa con umbral configurable.
11. Integrar CLI.
12. Ejecutar pruebas con dataset sintetico y con `wrfout_d01_2009-12-16.nc` si las dependencias meteorologicas estan disponibles.
13. Actualizar documentacion de decisiones reales encontradas durante la implementacion.

## Dependencias entre componentes

- La validacion de entradas debe existir antes de cualquier diagnostico.
- Los diagnosticos de precipitacion y superficie pueden implementarse antes que la interpolacion 3D.
- La exportacion NetCDF depende de que el dataset normalizado tenga coordenadas y atributos estables.
- La CLI depende de `io.py`, `diagnostics.py` y `normalization.py`.
- La mascara de jet stream depende de interpolar o diagnosticar correctamente el viento a 300 hPa.
- El backend meteorologico debe estabilizarse antes de conectar la CLI final, para que los errores por dependencia ausente sean comprensibles.
- Las pruebas con archivo real deben ejecutarse despues de las sinteticas, porque son mas lentas y dependen de librerias instaladas localmente.

## Trabajo paralelizable

- Tests de validacion de entradas y tests de precipitacion pueden escribirse en paralelo.
- Documentacion de decisiones cientificas puede avanzar mientras se implementan diagnosticos.
- CLI puede bosquejarse despues de fijar la firma de la funcion principal, sin esperar a todos los diagnosticos 3D.
- La preparacion de ejemplos Markdown puede avanzar en paralelo con pruebas de integracion, siempre que no fije resultados numericos no verificados.
- Tests de encoding NetCDF y reapertura con `xarray.open_dataset` pueden desarrollarse en paralelo con la normalizacion.

## Riesgos y mitigaciones

- Riesgo: `wrf-python` puede ser dificil de instalar en Windows con `uv`.
  Mitigacion: aceptar ruta `xWRF`/`xarray`, documentar diferencias y encapsular diagnosticos para que el resto del codigo no dependa de una unica libreria.

- Riesgo: los archivos WRF reales pueden tener dimensiones o nombres ligeramente distintos.
  Mitigacion: validar estructura al inicio, conservar metadatos originales y probar con dataset sintetico mas archivo real.

- Riesgo: combinar varios `wrfout` sin ordenar o con dominios distintos puede producir una serie temporal falsa.
  Mitigacion: ordenar por `Times`, validar dominio antes de concatenar y fallar ante duplicados en la primera version.

- Riesgo: interpolar bajo terreno puede producir valores fisicamente invalidos.
  Mitigacion: enmascarar puntos no validos y documentar `missing_policy`.

- Riesgo: confundir viento de rejilla con viento terrestre.
  Mitigacion: incluir `wind_reference` en cada variable de viento y preferir `uvmet`/`uvmet10` o equivalente.

- Riesgo: el NetCDF de salida puede ser grande.
  Mitigacion: permitir seleccionar tiempos, documentar coste de guardar campos auxiliares 3D y no versionar `data/processed/`.

- Riesgo: diferencias de unidades entre librerias pueden contaminar los diagnosticos.
  Mitigacion: centralizar conversiones, validar rangos fisicos y guardar unidades canonicas en atributos.

- Riesgo: la precipitacion acumulada puede reiniciarse entre archivos o por reinicio del modelo.
  Mitigacion: detectar incrementos negativos y no convertirlos automaticamente en cero sin documentarlo.

## Checkpoints de verificacion

1. Checkpoint de estructura:
   - `uv sync`
   - `uv run ruff check .`
   - `uv run pytest`

2. Checkpoint de entrada:
   - Tests de variables obligatorias pasan.
   - Un archivo inexistente o incompatible falla con mensaje claro.
   - Un conjunto multifichero incompatible falla antes de calcular diagnosticos.
   - `Times` queda convertido o preservado de forma trazable.

3. Checkpoint de superficie:
   - `precip_total_mm` y `precip_increment_mm` pasan tests.
   - El primer incremento es `0.0`.
   - Variables derivadas tienen unidades y metodo de calculo.

4. Checkpoint de dataset:
   - El resultado tiene dimensiones `time`, `level`, `y`, `x` cuando aplica.
   - Se guarda por defecto en `data/processed/wrf_normalizado.nc`.
   - El NetCDF reabre con `xarray.open_dataset`.
   - Las variables canonicas minimas existen o el error explica por que no se pueden calcular.
   - Los atributos globales incluyen archivo fuente, backend, librerias principales y convenciones.

5. Checkpoint de niveles isobaricos:
   - 850/500/300 hPa existen en `level`.
   - Los puntos bajo terreno estan enmascarados o marcados como no disponibles.
   - La mascara de jet stream existe y usa el umbral configurado.
   - El viento usado para jet stream esta documentado como terrestre o de rejilla.

6. Checkpoint final:
   - `uv run pytest -vv`
   - `uv run ruff check .`
   - Ejecucion CLI con el archivo de prueba local, si las dependencias disponibles lo permiten.
   - Reapertura del NetCDF generado y comprobacion rapida de dimensiones esperadas para el archivo local: 17 tiempos, 120 x 99 puntos horizontales y 44 niveles nativos.

## Politica de commits pequenos

Durante la implementacion se deben realizar commits pequenos y revisables. Cada commit debe corresponder a un avance verificable y no debe mezclar cambios de naturaleza distinta.

Secuencia sugerida:

1. `docs: cerrar decisiones y anadir plan wrf`
2. `build: crear paquete python y configurar uv`
3. `test: cubrir validacion inicial de wrf`
4. `feat: abrir y validar salidas wrf`
5. `feat: normalizar coordenadas y tiempos wrf`
6. `feat: calcular precipitacion y campos de superficie`
7. `feat: normalizar y exportar dataset wrf`
8. `feat: anadir backend meteorologico wrf`
9. `feat: interpolar niveles isobaricos`
10. `feat: detectar mascara de jet stream`
11. `feat: anadir cli de extraccion wrf`
12. `docs: registrar decisiones cientificas finales`

Antes de cada commit se debe ejecutar la verificacion aplicable al alcance del commit. No se deben incluir archivos NetCDF grandes generados localmente en los commits.

## Criterio para pasar a tareas

Se puede pasar a la fase de tareas cuando este plan sea aprobado y se confirme que el primer bloque de implementacion puede crear la estructura Python del proyecto.

Antes de empezar a programar conviene dejar fijadas estas decisiones operativas:

- Backend inicial a intentar en el equipo de desarrollo: `auto`, con prioridad para `wrf-python` y fallback a `xWRF`/`xarray`.
- Politica ante incrementos negativos de precipitacion: fallar en modo estricto y permitir mascara en modo tolerante.
- Politica de almacenamiento de campos 3D: conservarlos por defecto solo si se procesa un unico tiempo o si el usuario activa una opcion explicita para serie completa.
- Formato de salida principal: NetCDF normalizado; Zarr queda como posible mejora futura si el tamano crece.

## Referencias usadas en la revision

- Transcripcion docente: `docs/Presentacion_tarea/transcripcion_clase.txt`.
- Especificacion revisada: `docs/especificacion_obtencion_datos_wrf.md`.
- `wrf-python`: `getvar` e `interplevel` para diagnosticos WRF e interpolacion vertical.
- `xarray`: `open_mfdataset` para multiples NetCDF y `to_netcdf` con encoding.
- `xWRF`: `.xwrf.postprocess()` para postprocesar salidas WRF hacia convenciones mas compatibles con `xarray`.
