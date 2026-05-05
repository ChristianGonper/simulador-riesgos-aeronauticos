# Plan de implementacion: representacion de mapas y riesgos aeronauticos

## 1. Objetivo del plan

Este documento define los pasos tecnicos y cientificos para implementar, en una fase posterior, la representacion de mapas meteorologicos y los primeros riesgos aeronauticos a partir del dataset WRF normalizado.

La implementacion no debe empezar hasta que se valide la especificacion asociada en `docs/specs/especificacion_representacion_riesgos_aeronauticos.md`.

El objetivo de esta fase sera generar productos interpretables para la exposicion docente:

- mapas meteorologicos generales;
- mapas exploratorios de riesgos aeronauticos;
- trazabilidad de cada campo representado;
- documentacion de las limitaciones fisicas y numericas.

No se implementara todavia la seleccion de aeropuertos ni el muestreo de una ruta de vuelo.

## 2. Principios de implementacion

La implementacion debe mantener un estilo de programacion cientifica:

- usar nombres de variables que indiquen magnitud fisica y unidades;
- preferir funciones pequenas, explicitas y verificables;
- documentar cada diagnostico con atributos en el `xarray.Dataset`;
- evitar indices complejos si no se pueden justificar meteorologicamente;
- no ocultar umbrales sin explicacion;
- separar calculo, representacion y CLI;
- fallar de forma clara cuando falten variables necesarias.

La trazabilidad es obligatoria. Cada variable derivada debe indicar:

- variables fuente;
- metodo de calculo;
- unidades;
- interpretacion cientifica;
- limitaciones.

Mientras el viento siga siendo relativo a la rejilla del modelo, los productos de viento, cizalladura, turbulencia y navegacion deben etiquetarse como exploratorios.

## 3. Orden recomendado de trabajo

### Paso 1. Validar entradas y convenciones

Antes de escribir mapas o riesgos, revisar el dataset normalizado producido por la fase WRF:

- confirmar nombres de variables disponibles;
- confirmar dimensiones de campos isobaricos;
- confirmar existencia de `lat` y `lon`;
- confirmar como se codifica `level_hpa`;
- revisar atributos actuales de viento y su limitacion como viento relativo a la rejilla.

Resultado esperado: una tabla breve en la documentacion o en comentarios de desarrollo con campos disponibles y campos faltantes.

### Paso 2. Definir API interna de riesgos

Crear una capa de diagnosticos aeronauticos independiente de la visualizacion.

Interfaz conceptual:

```python
def add_aviation_risk_fields(ds: xr.Dataset) -> xr.Dataset:
    ...
```

Esta funcion debe devolver una copia o version enriquecida del dataset, sin modificar de forma opaca la entrada.

Variables previstas:

- `wind_shear_10m_850_ms`;
- `wind_shear_850_500_ms`, si hay componentes de viento isobaricas suficientes;
- `icing_mask`;
- `turbulence_index`;
- `convection_proxy`;
- `visibility_available` o campo equivalente si no existe `AFWA_VIS`.

Cada variable debe conservar atributos cientificos completos.

### Paso 3. Implementar calculos de riesgo simples

Implementar primero los diagnosticos mas defendibles:

- cizalladura vectorial entre viento a 10 m y 850 hPa;
- mascara termica de engelamiento entre `0` y `-20 degC`;
- proxy convectivo basado en precipitacion incremental intensa.

Despues implementar diagnosticos que requieren mas cautela:

- turbulencia exploratoria basada en cizalladura y gradientes horizontales;
- engelamiento combinado con humedad o condensado si esos campos estan disponibles;
- visibilidad solo si existe `AFWA_VIS`.

No se debe inventar una estimacion de visibilidad si el dataset no tiene informacion suficiente.

### Paso 4. Definir API interna de mapas

Crear una capa de representacion independiente de la CLI.

Interfaz conceptual:

```python
def plot_scalar_map(ds: xr.Dataset, variable: str, time_index: int, output_path: Path) -> Path:
    ...

def plot_wind_map(
    ds: xr.Dataset,
    u_variable: str,
    v_variable: str,
    speed_variable: str,
    time_index: int,
    output_path: Path,
) -> Path:
    ...

def plot_risk_map(ds: xr.Dataset, risk_variable: str, time_index: int, output_path: Path) -> Path:
    ...
```

Los mapas deben usar `lat` y `lon` bidimensionales y declarar la transformacion geografica correspondiente. El producto minimo sera `PNG`.

Cada figura debe incluir:

- titulo con variable y tiempo valido;
- unidades;
- barra de color;
- costa o referencia geografica;
- advertencia cuando el producto sea exploratorio.

### Paso 5. Integrar CLI de representacion

Anadir un modo o subcomando separado de la normalizacion WRF.

Comando previsto:

```powershell
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
```

Opciones previstas:

- `--time-index`;
- `--all-times`;
- `--fields`;
- `--risks`;
- `--format png`;
- `--output-dir`.

La CLI no debe recalcular la normalizacion WRF salvo que se disene explicitamente un flujo compuesto. La entrada de esta fase es el NetCDF ya normalizado.

### Paso 6. Generar productos meteorologicos minimos

Los primeros mapas obligatorios deben ser:

- `slp_hpa`;
- `t2_c`;
- `wind10_speed_ms`;
- `precip_increment_mm`;
- `gh_isobaric_m` en 850 y 500 hPa;
- `t_isobaric_c` en 850 y 500 hPa;
- `wind_speed_isobaric_ms` en 300 hPa;
- `jet_stream_mask`.

Despues se generaran mapas de riesgos:

- `wind_shear_10m_850_ms`;
- `icing_mask`;
- `turbulence_index`;
- `convection_proxy`;
- visibilidad solo si existe campo fuente fiable.

### Paso 7. Documentar interpretacion

Actualizar `docs/guide/guia_interpretacion_mapas_riesgos.md` cuando se concreten nombres finales, umbrales y limitaciones.

La guia debe permitir explicar en la presentacion:

- que significa cada mapa;
- que estructura meteorologica identifica;
- que riesgo aeronautico sugiere;
- que informacion no permite concluir.

## 4. Estrategia de pruebas

### Tests unitarios

Crear tests para:

- cizalladura con arrays sinteticos de viento;
- mascara de engelamiento con temperatura y humedad sinteticas;
- proxy convectivo con precipitacion incremental;
- caso sin `AFWA_VIS`, que debe declarar visibilidad no disponible;
- errores claros cuando faltan `lat`, `lon` o la variable pedida.

### Tests de integracion

Crear un test que:

- genere un dataset sintetico normalizado;
- calcule riesgos basicos;
- produzca al menos un mapa `PNG`;
- verifique que el archivo existe y no esta vacio;
- ejecute la CLI de mapas con codigo de salida correcto.

Comandos de verificacion previstos:

```powershell
uv run pytest
uv run ruff check .
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
```

## 5. Riesgos tecnicos y cientificos

- **Cartopy en Windows:** puede requerir dependencias geoespaciales. Si instala mal, considerar una ruta temporal con Matplotlib sobre `lon`/`lat` sin cartografia avanzada, documentando la limitacion.
- **Viento relativo a la rejilla:** afecta a interpretacion de viento, cizalladura y turbulencia. Mitigacion: rotar viento en una fase previa o marcar productos como exploratorios.
- **Falta de humedad/condensado:** limita engelamiento. Mitigacion: separar mascara termica de diagnostico completo.
- **Falta de visibilidad WRF:** no estimar artificialmente. Mitigacion: declarar no disponible.
- **Umbrales meteorologicos:** deben ser configurables o estar documentados como criterios docentes exploratorios.

## 6. Criterios de aceptacion de la implementacion futura

La implementacion futura se considerara aceptada cuando:

- lea un NetCDF normalizado sin repetir la fase WRF;
- genere mapas meteorologicos generales en `PNG`;
- genere mapas exploratorios de riesgos;
- incluya unidades, tiempo valido y trazabilidad;
- documente limitaciones en atributos y en Markdown;
- supere tests unitarios e integracion;
- mantenga separadas las capas de calculo, representacion y CLI.

## 7. Fuera de alcance

No forman parte de esta implementacion:

- dashboard interactivo avanzado;
- seleccion de aeropuertos;
- calculo de trayectoria Barcelona-Londres u otras rutas;
- interpolacion temporal o espacial sobre una ruta;
- diagnostico operacional certificado;
- deteccion automatica completa de frentes.
