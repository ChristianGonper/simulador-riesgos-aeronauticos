# Revision de cumplimiento respecto a lo pedido por el profesor

Fecha de revision: 2026-05-05

## Alcance revisado

Se revisaron:

- `docs/Presentacion_tarea/transcripcion_clase.txt`
- `README.md`
- `docs/specs/`
- `docs/plans/`
- `docs/reports/`
- `docs/guide/guia_interpretacion_mapas_riesgos.md`
- codigo necesario en `src/simulador_wrf/`
- tests principales en `tests/`

Tambien se ejecuto:

```powershell
uv run pytest
uv run ruff check .
```

Resultado: `14 passed`, `ruff` sin errores. Hay warnings de compatibilidad/futuro de `xarray` y un warning de runtime de NumPy, pero no bloquean la ejecucion actual.

## Requisitos del profesor extraidos

De la transcripcion se extraen estos requisitos docentes:

1. Construir un simulador basado en salidas del modelo WRF, no solo graficos aislados.
2. El simulador debe servir para la salida de prueba y para otras salidas WRF equivalentes, aunque cambie el dominio.
3. Antes del analisis de vuelo debe poder hacerse un analisis meteorologico general de la situacion.
4. En superficie hay que representar:
   - velocidad y direccion del viento;
   - presion a nivel del mar;
   - temperatura;
   - precipitacion.
5. En 850 hPa hay que representar geopotencial y temperatura.
6. En 500 hPa hay que representar geopotencial y temperatura.
7. En 300 hPa hay que representar el jet stream.
8. El sistema debe resolver el problema de que WRF no usa niveles verticales de presion nativos, interpolando o calculando esos campos.
9. Deben calcularse variables que afecten a la seguridad aeronautica:
   - visibilidad;
   - engelamiento;
   - turbulencia;
   - cizalladura;
   - conveccion o corrientes convectivas.
10. El objetivo integrado es introducir dos aeropuertos y obtener informacion de las caracteristicas atmosfericas en la trayectoria.
11. En la presentacion/prueba no bastara con mostrar graficas: el grupo debe explicar fisica y meteorologicamente que se representa.
12. El analisis debe permitir describir borrascas, anticiclones, baroclinicidad, frentes si es posible, jet stream y riesgos destacados como olas de calor/frio o precipitaciones intensas.

## Que esta cubierto

### Base WRF y normalizacion

El proyecto tiene una fase de normalizacion real mediante `simulador-wrf normalizar`. La lectura y validacion estan en `src/simulador_wrf/io.py`, y la construccion del dataset procesado en `src/simulador_wrf/normalization.py`.

Puntos cubiertos:

- valida variables WRF obligatorias;
- normaliza dimensiones principales a `time`, `y`, `x`, `model_level`;
- crea coordenadas `lat` y `lon`;
- calcula presion 3D como `P + PB`;
- calcula temperatura 3D desde temperatura potencial perturbada;
- calcula altura geopotencial desde `PH + PHB`;
- calcula precipitacion total e incremental;
- calcula campos de superficie: `t2_c`, `u10_ms`, `v10_ms`, `wind10_speed_ms`, `wind10_dir_deg`;
- interpola campos a niveles de presion mediante log-presion;
- genera `slp_hpa` con formula barometrica aproximada;
- exporta NetCDF normalizado.

Esto cubre una parte importante de lo pedido por el profesor: no se trata el WRF como tabla simple, sino que se derivan campos meteorologicos necesarios para el analisis.

### Campos meteorologicos generales

El subcomando `simulador-wrf mapas` genera mapas PNG desde el NetCDF normalizado. Estan implementados:

- presion a nivel del mar;
- temperatura a 2 m;
- precipitacion incremental;
- viento a 10 m;
- geopotencial en 850 y 500 hPa;
- mapas de riesgos;
- mascara de jet stream.

La guia `docs/guide/guia_interpretacion_mapas_riesgos.md` ayuda a explicar presion, temperatura, precipitacion, 850/500/300 hPa y riesgos.

### Riesgos aeronauticos

En `src/simulador_wrf/diagnostics.py` se implementan diagnosticos exploratorios:

- `wind_shear_10m_850_ms`;
- `icing_mask`;
- `convection_proxy`;
- `turbulence_index`;
- `visibility_m` como disponible si existe `AFWA_VIS`, o como campo NaN trazable si no existe;
- `jet_stream_mask`.

Los atributos documentan fuentes, metodo, interpretacion y limitaciones en varias variables. Esto es positivo para defender la parte cientifica, siempre que se presente como exploratoria.

### Rutas entre aeropuertos

El subcomando `simulador-wrf ruta` cumple la idea general de introducir origen y destino:

- resuelve aeropuertos por ICAO/IATA;
- calcula una ruta de gran circulo;
- valida que la ruta cae dentro del dominio WRF;
- muestrea variables por vecino mas cercano;
- genera CSV, resumen Markdown, mapa y perfiles.

Esto cubre el objetivo integrado mencionado por el profesor: consultar condiciones atmosfericas a lo largo de una trayectoria.

### Documentacion interna y trazabilidad

Existen specs, planes y reportes para las tres fases principales:

- obtencion de datos WRF;
- mapas y riesgos aeronauticos;
- rutas de vuelo.

La documentacion reconoce limitaciones relevantes, especialmente que los vientos siguen siendo relativos a la rejilla y que los riesgos no son productos operacionales.

## Que falta o queda debil

### Mapas obligatorios incompletos en la CLI

La CLI de mapas no genera todos los campos que el profesor pidio explicitamente:

- en 850 hPa genera geopotencial, pero no temperatura;
- en 500 hPa genera geopotencial, pero no temperatura;
- para 300 hPa genera `jet_stream_mask` como riesgo, pero no un mapa claro de velocidad de viento a 300 hPa como campo meteorologico principal.

El dataset puede contener `t_isobaric_c` y `wind_speed_isobaric_ms`, pero la salida grafica estandar no los produce todos. Para la presentacion esto es importante: el profesor pidio esos campos concretos como base del analisis.

### Analisis meteorologico no esta automatizado ni preparado como guion final

El proyecto genera mapas y una guia de interpretacion, pero no hay un informe de situacion meteorologica para un caso concreto. Falta una pieza tipo:

- resumen sinoptico por tiempo valido;
- localizacion de bajas y altas;
- interpretacion de vaguadas/dorsales;
- relacion entre 850/500/300 hPa;
- identificacion manual de frentes o zonas baroclinas;
- riesgos meteorologicos destacados para explicar en clase.

El profesor insistio en que no basta con programar; hay que saber explicar la meteorologia.

### Frentes y baroclinicidad quedan solo como interpretacion manual

La transcripcion dice "si sois capaces tambien de dibujar los frentes" y menciona baroclinicidad. El proyecto produce campos utiles para interpretarlos, pero no detecta ni dibuja frentes. Esto no parece obligatorio estricto, pero si el profesor pregunta por frentes, el grupo tendra que defenderlos manualmente sobre mapas de presion, temperatura y viento.

### Viento relativo a la rejilla

La documentacion reconoce que los vientos se desescalonan pero no se rotan a coordenadas terrestres. Esto afecta:

- direccion de viento;
- cizalladura;
- turbulencia;
- interpretacion de ruta.

Para una practica docente puede ser aceptable si se declara, pero es uno de los puntos cientificos mas delicados si el profesor espera viento meteorologico real sobre mapa.

### Visibilidad no se calcula salvo diagnostico WRF externo

El sistema no estima visibilidad si falta `AFWA_VIS`; crea `visibility_m` con NaNs y lo documenta. Esta decision es cientificamente prudente, pero desde el punto de vista del encargo del profesor queda parcialmente sin cubrir: "calcular visibilidad" no esta resuelto para salidas WRF que no traigan ese diagnostico.

### Riesgos aeronauticos son proxies simples

Los riesgos estan implementados, pero son diagnosticos exploratorios:

- engelamiento usa principalmente ventana termica, con humedad solo si existe;
- conveccion usa precipitacion incremental;
- turbulencia usa cizalladura baja escalada, no un indice completo de CAT;
- cizalladura se limita principalmente a 10 m-850 hPa.

Esto puede servir para la practica, pero debe explicarse con cuidado para no venderlo como producto operacional.

### Robustez con WRF real no verificada en esta revision

Los tests pasan con datos sinteticos. No se ha verificado en esta revision una ejecucion completa con el archivo real `wrfout_d01_2009-12-16.nc`, porque no aparece en el arbol de archivos revisado. El riesgo principal es que el caso real tenga dimensiones, metadatos o verticales que expongan problemas no cubiertos por el dataset sintetico.

### README demasiado operativo y poco docente

El README explica instalacion y comandos, pero no recoge:

- lista de mapas que requiere el profesor;
- flujo recomendado para preparar la presentacion;
- limitaciones cientificas clave;
- que productos mirar para hacer el analisis meteorologico;
- ejemplo completo de normalizar + mapas + ruta + interpretacion.

Como puerta de entrada del proyecto, queda corto para una entrega defendible.

## Riesgos para la presentacion o prueba final

1. Riesgo alto: que el profesor pida temperatura en 850/500 hPa o viento a 300 hPa y la CLI no los haya generado como PNG por defecto.
2. Riesgo alto: que la prueba use otro WRF real y aparezcan problemas no detectados por los tests sinteticos.
3. Riesgo alto: que el grupo muestre mapas sin una interpretacion meteorologica clara de borrascas, anticiclones, vaguadas, jet y precipitacion.
4. Riesgo medio-alto: que se pregunte por direccion del viento o cizalladura y haya que explicar que el viento no esta rotado a coordenadas terrestres.
5. Riesgo medio: que "visibilidad" se considere incumplida si el archivo WRF no trae `AFWA_VIS`.
6. Riesgo medio: que los riesgos aeronauticos parezcan demasiado simples si no se presentan como aproximaciones docentes.
7. Riesgo medio: dependencia de Cartopy/xWRF en Windows; los tests pasan ahora, pero puede complicar reproducibilidad en otro equipo.
8. Riesgo bajo-medio: warnings de `xarray` anticipan cambios futuros en defaults de concatenacion, aunque no afectan a la entrega inmediata.

## Prioridades concretas

### P0 - Antes de la prueba final

1. Asegurar que `simulador-wrf mapas` genera tambien:
   - temperatura en 850 hPa;
   - temperatura en 500 hPa;
   - viento en 300 hPa;
   - jet stream superpuesto o claramente asociado al viento de 300 hPa.
2. Ejecutar el flujo completo con el WRF real de prueba cuando este disponible:
   - normalizar;
   - generar mapas;
   - generar una ruta dentro del dominio;
   - abrir salidas PNG/CSV/MD y comprobar que no estan vacias ni incoherentes.
3. Preparar un guion meteorologico del caso de prueba con capturas/mapas concretos:
   - superficie;
   - 850 hPa;
   - 500 hPa;
   - 300 hPa;
   - riesgos aeronauticos;
   - ruta.

### P1 - Muy recomendable

4. Documentar en README un flujo de entrega completo y la lista de productos esperados por el profesor.
5. Anadir una advertencia visible en el resumen de ruta cuando el viento sea grid-relative.
6. Mejorar la salida de mapas para incluir titulos mas orientados a la defensa: nivel, variable, tiempo valido, unidades y aviso exploratorio.
7. Crear una tabla de variables disponibles/no disponibles tras normalizar, especialmente para visibilidad y humedad.

### P2 - Si queda tiempo

8. Rotar viento a coordenadas terrestres usando una herramienta WRF adecuada, o dejar una comparacion/documentacion muy clara de por que no se hace.
9. Mejorar engelamiento usando humedad/condensados cuando existan.
10. Implementar un diagnostico de cizalladura adicional 850-500 hPa.
11. Facilitar dibujo manual de frentes o zonas baroclinas mediante gradientes de temperatura/presion.
12. Anadir tests con un NetCDF WRF real reducido o fixture mas parecido a WRF real.

## Conclusion

El proyecto cubre la arquitectura principal solicitada: procesa WRF, genera campos meteorologicos, calcula riesgos exploratorios y consulta rutas entre aeropuertos. La base tecnica es suficiente para una demo funcional.

El mayor hueco no es de estructura, sino de cumplimiento visible en la presentacion: faltan algunos mapas obligatorios por defecto y falta preparar una interpretacion meteorologica concreta. Para maximizar la nota, la prioridad debe ser cerrar esos productos visibles y ensayar la explicacion fisica de cada mapa y riesgo.
