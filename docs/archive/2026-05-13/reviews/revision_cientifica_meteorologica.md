# Revision cientifica-meteorologica del simulador WRF

Fecha de revision: 2026-05-05.

## Alcance

Esta revision evalua el proyecto desde el punto de vista cientifico-meteorologico WRF y de coherencia docente. Se han leido:

- `docs/Presentacion_tarea/transcripcion_clase.txt`;
- `docs/instrucciones_programacion_wrf.md`;
- `src/simulador_wrf/diagnostics.py`;
- `src/simulador_wrf/io.py`;
- `src/simulador_wrf/normalization.py`;
- `src/simulador_wrf/backends.py`, por ser necesario para interpretar los diagnosticos WRF;
- tests relacionados en `tests/`;
- especificaciones, planes, guia y reportes en `docs/specs/`, `docs/plans/`, `docs/guide/` y `docs/reports/`.

Tambien se ha comprobado el archivo WRF de referencia `wrfout_d01_2009-12-16.nc` solo para verificar metadatos y variables fuente. El caso local corresponde a una salida WRF V3.1.1 con 17 tiempos, dominio de 120 x 99 puntos horizontales, 44 niveles verticales de masa, 45 niveles escalonados, `DX = DY = 27000 m`, proyeccion Lambert conforme (`MAP_PROJ = 1`) y fecha inicial `2009-12-16_00:00:00`.

## Veredicto resumido

El proyecto esta bien orientado para la practica docente: reconoce que WRF no entrega directamente campos meteorologicos finales, separa acumulado e incremento de precipitacion, usa las variables nativas correctas para presion, temperatura, altura geopotencial y viento, e incorpora explicitamente la naturaleza exploratoria de los riesgos aeronauticos.

Sin embargo, el nivel cientifico actual es todavia desigual. La base de normalizacion es razonable, pero hay huecos importantes de trazabilidad, validacion fisica y coherencia entre especificacion, documentacion y codigo. Los puntos que mas afectan al analisis meteorologico pedido en clase son: viento no rotado a coordenadas terrestres, SLP aproximada, diagnosticos aeronauticos demasiado simples, falta de control de precipitacion acumulada reiniciada, ausencia de humedad relativa derivada pese a disponer de `QVAPOR`, y tests sinteticos que no verifican suficientemente las hipotesis fisicas.

## Coherencia con el encargo docente

La transcripcion de clase pide dos resultados conectados:

1. Analisis meteorologico general de una salida WRF: superficie, 850 hPa, 500 hPa y 300 hPa, con interpretacion de borrascas, anticiclones, baroclinicidad, frentes, jet stream, precipitacion y tiempo sensible.
2. Aplicacion posterior a seguridad aeronautica: visibilidad, engelamiento, turbulencia, cizalladura y conveccion sobre rutas entre aeropuertos.

El proyecto cubre la estructura basica: `slp_hpa`, `t2_c`, viento 10 m, precipitacion, `gh_isobaric_m`, `t_isobaric_c`, `wind_speed_isobaric_ms`, `jet_stream_mask` y productos de riesgo. Tambien mantiene el aviso de que los riesgos son docentes y exploratorios.

La principal brecha docente es que algunos mapas pueden parecer mas concluyentes de lo que son. Para una exposicion en clase, el simulador puede servir si el grupo explica claramente que:

- la presion a nivel del mar es una reduccion barometrica simplificada, no el diagnostico SLP completo de WRF;
- los vientos son relativos a la rejilla, no necesariamente componentes este/norte reales;
- los riesgos aeronauticos identifican condiciones favorables, no peligros operacionales certificados;
- el modelo tiene resolucion de 27 km en el caso local, por lo que conveccion, visibilidad, cizalladura local y fenomenos de aeropuerto no quedan resueltos a escala fina.

## Hallazgos principales

### 1. Variables WRF fuente: seleccion correcta pero validacion incompleta

El codigo usa las variables WRF adecuadas para varios diagnosticos esenciales:

- presion 3D: `P + PB`, en Pa convertido a hPa;
- temperatura 3D: `T + 300` como temperatura potencial, convertida a temperatura con Exner;
- altura geopotencial: `(PH + PHB) / g`, desescalonada a niveles de masa;
- precipitacion acumulada: `RAINC + RAINNC`;
- viento 10 m: `U10`, `V10`;
- viento 3D: `U`, `V`, con desescalonado.

El problema es que `io.MANDATORY_VARIABLES` no incluye `T`, aunque `backends.get_temperature_c()` la necesita y la especificacion la declara esencial. Si falta `T`, la validacion inicial puede pasar y el fallo cientifico aparece mas tarde como diagnostico ausente.

Tambien se valida poco la estructura escalonada necesaria para `U`, `V`, `PH` y `PHB`: las dimensiones `bottom_top_stag`, `west_east_stag` y `south_north_stag` no estan en las dimensiones obligatorias. Para WRF real esto normalmente existe, pero una validacion cientifica deberia comprobar que cada variable escalonada tiene la dimension esperada.

### 2. Unidades: mayoritariamente coherentes, pero faltan atributos obligatorios

Las conversiones principales son coherentes:

- `T2` de K a `degC`;
- `P + PB` de Pa a hPa;
- `PSFC` de Pa a hPa para SLP;
- precipitacion en mm;
- viento en `m s-1`;
- altura geopotencial en m.

La debilidad esta en metadatos. Las instrucciones del proyecto exigen, cuando aplique, `units`, `long_name`, `method`, `source_variables`, `scientific_interpretation` y `limitations`. Muchos campos basicos no cumplen esto:

- `t2_c` no indica `method`, `source_variables` ni limitaciones;
- `u10_ms`, `v10_ms` se copian sin atributos propios;
- `wind10_speed_ms` y `wind10_dir_deg` tienen atributos minimos, pero no indican si el viento es grid-relative;
- `pressure_hpa`, `temperature_c`, `geopotential_height_m`, `u_ms`, `v_ms`, `wind_speed_ms` tienen trazabilidad parcial o nula;
- `slp_hpa` usa `limitation` singular en vez de `limitations`, y no declara `source_variables`.

Esto afecta directamente a la trazabilidad cientifica: el usuario puede ver un campo meteorologico correcto en unidades, pero no siempre puede reconstruir su procedencia.

### 3. Viento: el mayor riesgo de interpretacion meteorologica

El proyecto documenta que el viento se mantiene relativo a la rejilla del modelo. Esta decision es aceptable como fase inicial, pero tiene impacto fuerte:

- el viento a 10 m se trata como `u10_ms` y `v10_ms` sin rotacion a coordenadas terrestres;
- el modulo del viento es invariante ante rotacion, pero direccion, barbas, componentes y cizalladura vectorial no lo son;
- la ruta de vuelo y los productos de cizalladura/turbulencia pueden interpretarse mal si se leen como viento geografico este/norte;
- la direccion `wind10_dir_deg` usa una formula meteorologica correcta para componentes este/norte, pero las componentes fuente no estan garantizadas como terrestres.

La especificacion menciona diagnosticos equivalentes a `uvmet` y `uvmet10`. La documentacion de `wrf-python` tambien considera `uvmet`, `uvmet10` y `wspd_wdir_uvmet10` como vias directas para componentes rotadas. Mientras no se implementen, todos los mapas y perfiles con direccion o componentes deben etiquetarse de forma visible como viento de rejilla.

### 4. Presion a nivel del mar: util como proxy, debil para analisis sinoptico fino

`slp_hpa` se calcula con una formula barometrica usando `PSFC`, `T2`, `HGT` y un gradiente termico constante ISA (`0.0065 K m-1`). Es una aproximacion documentada, pero no equivale al diagnostico SLP completo de WRF o `wrf-python`, que usa informacion vertical mas apropiada.

Para clase, `slp_hpa` puede localizar aproximadamente bajas y altas, pero no deberia usarse para discutir con precision gradientes baricos, centros cerrados, frentes o estructura mesoescalar. La guia y los titulos de mapas deberian reflejar que es "SLP aproximada" si se mantiene esta ruta.

### 5. Niveles de presion: planteamiento correcto, validacion mejorable

La interpolacion a 850, 500 y 300 hPa responde exactamente al encargo docente. Es correcto derivarla desde `pressure_hpa`, porque WRF usa coordenada vertical eta/sigma y no niveles isobaricos nativos.

El metodo log-lineal en presion esta documentado en el codigo y en reportes. Es una decision defendible para algunas magnitudes, pero deberia quedar como atributo en cada campo interpolado. Ahora `interpolate_to_pressure()` devuelve campos con poca trazabilidad y no conserva explicitamente:

- metodo de interpolacion;
- variable fuente;
- politica bajo terreno;
- unidades heredadas;
- advertencia de extrapolacion evitada mediante mascara.

La mascara por rango de presion evita extrapolar cuando el nivel queda fuera de la columna, lo cual es fisicamente correcto. Falta test que verifique especificamente el caso de 850 hPa bajo terreno y el caso de 300 hPa por encima del techo del modelo.

### 6. Precipitacion: acumulado correcto, incremento incompleto

`precip_total_mm = RAINC + RAINNC` es correcto para precipitacion acumulada total convectiva y no convectiva. `precip_increment_mm` por diferencia temporal tambien es la transformacion adecuada para representar precipitacion por intervalo.

Faltan tres controles cientificos importantes:

- no se detectan incrementos negativos por reinicios del modelo o concatenacion de archivos;
- el primer incremento se fija a `0.0`, pero el atributo no explica que es una convencion tecnica y no una observacion;
- el proxy convectivo usa un umbral de 5 mm por paso de salida sin normalizar por duracion del intervalo. Si los `wrfout` tienen salidas cada 1 h, 3 h o intervalos irregulares, el significado fisico cambia.

Para exposicion docente, conviene decir "precipitacion acumulada durante el intervalo entre salidas" y no "intensidad" salvo que se convierta a `mm h-1`.

### 7. Riesgos aeronauticos: adecuados como demostracion, no como diagnostico robusto

Los riesgos actuales son coherentes con una primera version docente, pero deben presentarse con cautela:

- cizalladura: calcula diferencia vectorial 10 m-850 hPa. Es simple y util, pero depende de viento de rejilla y no considera capas criticas de aproximacion ni perfil vertical continuo;
- engelamiento: usa 850 hPa o T2 entre 0 y -20 degC, con RH opcional si existiera `rh_isobaric`. El problema es que `rh_isobaric` no se calcula, aunque el dataset exige `QVAPOR`. Sin humedad, condensado o nubosidad, el producto deberia llamarse "zona termica favorable", no `icing_mask` como riesgo;
- turbulencia: `wind_shear_10m_850_ms / 10` es un indice de escala docente. No incluye estabilidad estatica, deformacion, convergencia ni Ellrod-Knapp, por lo que no representa CAT ni turbulencia de niveles altos;
- conveccion: precipitacion incremental intensa es un proxy muy indirecto. Puede capturar precipitacion estratiforme intensa y perder conveccion sin precipitacion acumulada significativa en el intervalo;
- visibilidad: la decision de no inventarla si falta `AFWA_VIS` es cientificamente correcta.

La implementacion cumple la idea de "productos exploratorios", pero algunas denominaciones y mapas deberian reforzar esa limitacion para no inducir una interpretacion operacional.

### 8. Trazabilidad documental: buena intencion, inconsistencias de rutas y alcance

Los documentos del proyecto son mas rigurosos que parte de la implementacion. Las especificaciones reconocen correctamente:

- WRF como salida en rejilla Arakawa-C;
- necesidad de desescalonar viento;
- necesidad de interpolar a niveles isobaricos;
- limitacion del viento grid-relative;
- tratamiento de visibilidad solo si hay diagnostico fiable;
- caracter docente y exploratorio de los riesgos.

Hay inconsistencias menores pero importantes:

- algunos documentos internos enlazan rutas antiguas como `docs/especificacion_obtencion_datos_wrf.md` o `docs/decisiones_finales_implementacion_wrf.md`, mientras los archivos reales estan bajo `docs/specs/` y `docs/reports/`;
- el reporte de rutas termina con una frase de "implementacion certificada" que no encaja con el aviso de producto docente y exploratorio;
- la guia dice que turbulencia se basa en cizalladura y gradientes horizontales, pero el codigo actual solo usa cizalladura 10 m-850 hPa.

Estas incoherencias no rompen el codigo, pero si afectan a la defensa oral del trabajo.

### 9. Tests: pasan, pero no prueban suficientemente la ciencia

Se ejecuto `uv run pytest`: 14 tests pasan. La bateria actual cubre CLI, apertura, normalizacion basica, precipitacion, mapas y rutas. Esto da confianza tecnica minima.

La cobertura cientifica es limitada:

- el dataset sintetico usa valores aleatorios y presiones no necesariamente monotonicamente decrecientes con altura;
- no hay test de temperatura potencial a temperatura real con valores esperados;
- no hay test de altura geopotencial desescalonada con una columna simple;
- no hay test de direccion meteorologica de viento con casos conocidos;
- no hay test de viento grid-relative vs earth-relative;
- no hay test de interpolacion a presion con columna monotona controlada;
- no hay test de niveles bajo terreno;
- no hay test de precipitacion acumulada que se reinicia;
- no hay test de metadatos obligatorios completos.

En su estado actual, los tests verifican que el flujo no se rompe, pero no garantizan que los campos sean meteorologicamente interpretables.

## Recomendaciones prioritarias

### Prioridad alta

1. Anadir `T` como variable obligatoria y validar dimensiones escalonadas de `U`, `V`, `PH`, `PHB`.
2. Implementar o exponer una ruta de viento rotado a coordenadas terrestres (`uvmet`, `uvmet10` o equivalente). Si no se implementa, anadir `wind_reference = grid_relative` en todos los campos de viento y en los mapas/perfiles.
3. Completar atributos cientificos obligatorios en todos los campos derivados, no solo en riesgos.
4. Marcar `slp_hpa` como aproximada en nombre largo, atributos y mapas, o sustituirla por diagnostico WRF mas fiel cuando la dependencia lo permita.
5. Detectar incrementos negativos de precipitacion y documentar la politica aplicada.

### Prioridad media

1. Calcular humedad relativa 3D o isobarica desde `QVAPOR`, presion y temperatura si se quiere sostener mejor el engelamiento.
2. Convertir `precip_increment_mm` a tasa `mm h-1` o incluir explicitamente la duracion del intervalo usado.
3. Anadir `wind_shear_850_500_ms` si se quieren riesgos de capas medias y altas, no solo capa baja.
4. Ajustar nombres de riesgos: por ejemplo `icing_thermal_mask` cuando no hay humedad/condensado.
5. Sincronizar documentacion y codigo sobre turbulencia: o se implementan gradientes horizontales, o se corrige la guia.

### Prioridad baja

1. Corregir enlaces internos de documentos movidos a `docs/specs/` y `docs/reports/`.
2. Incorporar atributos globales del NetCDF normalizado con archivo fuente, backend, proyeccion, resolucion, fecha inicial y convenciones.
3. Anadir tests con un subconjunto real o con columnas sinteticas fisicamente plausibles.
4. Revisar warnings de `xarray` para hacer explicitas opciones de `concat`.

## Evaluacion final

El simulador ya tiene una estructura adecuada para una practica de meteorologia aplicada con WRF: lee una salida realista, normaliza dimensiones, calcula campos basicos y conecta mapas con rutas. Cientificamente, el proyecto es defendible si se presenta como prototipo docente y si se explican las limitaciones.

Para elevarlo a un producto meteorologico mas solido, la mejora mas importante no es anadir mas mapas, sino asegurar que cada campo representado pueda responder tres preguntas: de que variable WRF procede, en que coordenadas/unidades esta, y que conclusiones meteorologicas permite o no permite extraer.
