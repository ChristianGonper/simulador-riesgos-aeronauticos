# Instrucciones breves de programacion WRF

Estas instrucciones deben seguirse durante la implementacion de la fase de obtencion de datos WRF.

## 1. Trazabilidad cientifica

- Documentar cada decision fisica o de ingenieria que afecte al resultado: unidades, interpolacion, mascaras, rotacion de viento, tratamiento de precipitacion y valores no disponibles.
- Indicar siempre de que variables WRF procede cada diagnostico derivado.
- No usar formulas meteorologicas ad hoc sin justificar. Si se aplica una aproximacion, explicar por que es aceptable y donde queda limitada.
- Mantener separados los diagnosticos meteorologicos basicos de los calculos de riesgos aeronauticos, que quedan fuera de esta fase.

## 2. Estilo de codigo

- Usar nombres claros y cientificos: `pressure_hpa`, `geopotential_height_m`, `wind_speed_ms`, `precip_increment_mm`.
- Preferir funciones pequenas, con una responsabilidad meteorologica o tecnica concreta.
- Evitar abstracciones innecesarias. Primero claridad, despues reutilizacion.
- Documentar con docstrings breves las funciones publicas y las funciones cuyo significado fisico no sea evidente.
- Anadir comentarios solo cuando ayuden a entender una decision fisica, una convencion de unidades o una limitacion del modelo.
- Mantener unidades explicitas en nombres, atributos o ambos.

## 3. Documentacion del proyecto

- Registrar en Markdown las decisiones relevantes encontradas durante la implementacion.
- Si una libreria impone una convencion concreta, documentarla junto al enlace o referencia usada.
- Actualizar la especificacion o el plan cuando la implementacion obligue a cambiar una decision.

## 4. Librerias y dudas tecnicas

- Usar `uv` para dependencias, entornos y ejecucion de comandos Python.
- Usar Context7 para consultar documentacion actualizada de librerias cuando haya dudas entre `wrf-python`, `xWRF`, `xarray`, `MetPy` u otras dependencias.
- Priorizar documentacion oficial o de los proyectos antes que soluciones copiadas de foros.

## 5. Commits

- Hacer commits pequenos y revisables.
- Cada commit debe corresponder a un avance verificable: estructura, validacion, diagnostico, exportacion, CLI o documentacion.
- No mezclar refactorizaciones, cambios cientificos y cambios de formato en el mismo commit.
- Ejecutar las comprobaciones aplicables antes de cada commit.
- No incluir archivos NetCDF grandes generados localmente en los commits.
