# Instrucciones de programacion y trazabilidad del simulador WRF

Estas instrucciones deben seguirse durante cualquier fase de implementacion.

El objetivo no es solo que el codigo funcione. El proyecto debe poder ser entendido, usado y continuado por otra persona sin reconstruir mentalmente las decisiones tomadas.

## 1. Trazabilidad cientifica

- Documentar cada decision fisica o de ingenieria que afecte al resultado: unidades, interpolacion, mascaras, rotacion de viento, tratamiento de precipitacion y valores no disponibles.
- Indicar siempre de que variables WRF procede cada diagnostico derivado.
- No usar formulas meteorologicas ad hoc sin justificar. Si se aplica una aproximacion, explicar por que es aceptable y donde queda limitada.
- Mantener separados los diagnosticos meteorologicos basicos, los riesgos aeronauticos, la visualizacion y las rutas de vuelo.
- Todo campo derivado que quede en un `xarray.Dataset` debe incluir, cuando aplique:
  - `units`;
  - `long_name`;
  - `method`;
  - `source_variables`;
  - `scientific_interpretation`;
  - `limitations`.
- Si un campo no puede calcularse, no debe ocultarse. Debe fallar con mensaje claro o declararse explicitamente como no disponible, con atributos que expliquen la razon.
- Los productos basados en viento deben indicar si el viento esta rotado a coordenadas terrestres o sigue siendo relativo a la rejilla del modelo.
- Los riesgos aeronauticos actuales son productos docentes y exploratorios. No deben describirse como diagnosticos operacionales.

## 2. Estilo de codigo

- Usar nombres claros y cientificos: `pressure_hpa`, `geopotential_height_m`, `wind_speed_ms`, `precip_increment_mm`.
- Preferir funciones pequenas, con una responsabilidad meteorologica o tecnica concreta.
- Evitar abstracciones innecesarias. Primero claridad, despues reutilizacion.
- Documentar con docstrings breves las funciones publicas y las funciones cuyo significado fisico no sea evidente.
- Anadir comentarios solo cuando ayuden a entender una decision fisica, una convencion de unidades o una limitacion del modelo.
- Mantener unidades explicitas en nombres, atributos o ambos.
- No mezclar en una misma funcion lectura de datos, calculo cientifico, visualizacion y escritura de salidas.
- Las funciones publicas deben tener una entrada y salida facilmente comprobables con tests.
- Evitar cambios globales o silenciosos sobre datasets de entrada si no estan documentados.

## 3. Documentacion del proyecto

- Registrar en Markdown las decisiones relevantes encontradas durante la implementacion.
- Si una libreria impone una convencion concreta, documentarla junto al enlace o referencia usada.
- Actualizar la especificacion o el plan cuando la implementacion obligue a cambiar una decision.
- Cada fase nueva debe tener, antes o junto a su implementacion:
  - una especificacion en `docs/specs/`;
  - un plan de implementacion en `docs/plans/`;
  - si procede, una guia de interpretacion o uso en `docs/guide/`;
  - un reporte final de implementacion o decisiones cuando la fase se cierre.
- Las referencias internas entre documentos deben apuntar a la ruta real del archivo. Si se mueve un documento, hay que actualizar todos los enlaces relacionados.
- El README debe mantenerse como puerta de entrada para el usuario:
  - instalacion con `uv`;
  - comandos principales;
  - ejemplos copiables;
  - descripcion de subcomandos y flags;
  - ubicacion de salidas generadas.
- Si se anade, elimina o cambia un comando CLI, el README y los tests de integracion deben actualizarse en el mismo cambio.
- Si se generan nuevos productos (`outputs/maps`, `outputs/routes`, NetCDF procesados, PNG, CSV, Markdown), documentar:
  - donde se escriben;
  - que significan;
  - si deben versionarse o quedar ignorados por git.
- No dejar documentacion que afirme que algo esta implementado si solo esta planificado.

## 4. Librerias y dudas tecnicas

- Usar `uv` para dependencias, entornos y ejecucion de comandos Python.
- Usar Context7 para consultar documentacion actualizada de librerias cuando haya dudas entre `wrf-python`, `xWRF`, `xarray`, `MetPy` u otras dependencias.
- Priorizar documentacion oficial o de los proyectos antes que soluciones copiadas de foros.
- Si se anade una dependencia, actualizar `pyproject.toml`, `uv.lock`, README si afecta al uso, y explicar brevemente para que se usa.
- Evitar nuevas dependencias si la funcionalidad se puede resolver de forma clara con la pila ya existente.
- Las rutas alternativas o degradadas deben documentarse. Ejemplo: visualizacion sin Cartopy, visibilidad no disponible, viento sin rotar.

## 5. Uso de la herramienta

- La CLI debe ser reproducible y facil de usar. Cada subcomando debe tener un ejemplo en el README.
- Los comandos deben aceptar rutas explicitas de entrada y salida.
- Los errores deben ayudar al usuario a corregir el problema: variable ausente, nivel no disponible, aeropuerto fuera del dominio, archivo no encontrado, etc.
- Los nombres de archivos de salida deben ser estables y descriptivos, incluyendo cuando proceda variable, tiempo, nivel, origen y destino.
- Las salidas generadas para uso local deben ir preferentemente a `outputs/` o `data/processed/`, no mezcladas con el codigo fuente.
- Los productos generados grandes o reproducibles no deben versionarse salvo que se decida explicitamente que son ejemplos de referencia.

## 6. Pruebas y verificacion

- Cada fase implementada debe incluir tests proporcionales al riesgo del cambio.
- Como minimo, antes de cerrar una fase deben ejecutarse:
  - `uv run pytest`;
  - `uv run ruff check .`.
- Si se anade un subcomando CLI, debe existir al menos un test de integracion que lo ejecute.
- Si se genera un archivo de salida, los tests deben comprobar que existe y que no esta vacio.
- Si se anade un diagnostico cientifico, debe existir un test unitario con datos sinteticos simples.
- Los warnings conocidos pueden aceptarse temporalmente, pero no deben ocultar fallos reales.

## 7. Commits

- Hacer commits pequenos y revisables.
- Cada commit debe corresponder a un avance verificable: estructura, validacion, diagnostico, exportacion, CLI o documentacion.
- No mezclar refactorizaciones, cambios cientificos y cambios de formato en el mismo commit.
- Ejecutar las comprobaciones aplicables antes de cada commit.
- No incluir archivos NetCDF grandes generados localmente en los commits.
- Antes de un commit, revisar `git status --short` y confirmar que no entran artefactos generados por accidente.
- Si se modifica una fase ya revisada, explicar en el mensaje o reporte que problema corrige.
- Un commit de cierre de fase debe dejar coherentes codigo, tests, README, specs, planes y reportes.
