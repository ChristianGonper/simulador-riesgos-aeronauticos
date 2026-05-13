# Revision de riesgos aeronauticos y rutas de vuelo

Fecha de revision: 2026-05-05

## Alcance

Esta revision contrasta los requisitos docentes de `docs/Presentacion_tarea/transcripcion_clase.txt`, las especificaciones de riesgos y rutas, la guia de interpretacion, los modulos `routes.py`, `route_outputs.py`, `airports.py`, `visualization.py`, `diagnostics.py` y los tests relacionados.

El foco es valorar si el proyecto permite explicar, con rigor docente, visibilidad, engelamiento, turbulencia, cizalladura, conveccion y trayectorias entre aeropuertos, incluyendo salidas y limitaciones. No se revisan aqui otros componentes del proyecto salvo cuando afectan directamente a estos productos.

## Resumen ejecutivo

El proyecto cubre razonablemente el objetivo docente inicial: genera campos meteorologicos, calcula riesgos exploratorios, permite elegir dos aeropuertos, muestrea una ruta de gran circulo sobre la malla WRF y exporta CSV, Markdown, mapa y perfiles. La advertencia de producto no operacional esta presente en la guia y en los resumenes de ruta.

El principal riesgo no es de ejecucion, sino de interpretacion: algunos productos se nombran como "riesgo" o "probabilidad" aunque el calculo es una mascara o proxy muy simplificado. Esto es especialmente importante para engelamiento, turbulencia, conveccion y visibilidad. Para una practica docente es aceptable si se presenta como diagnostico exploratorio, pero no deberia interpretarse como aptitud real de vuelo.

Los tests relacionados pasan, pero validan sobre todo que el flujo funciona y que se generan archivos. Falta cobertura cientifica sobre umbrales, disponibilidad de variables, niveles no presentes, distancia al vecino de malla y contenido interpretativo del Markdown.

## Adecuacion a la tarea docente

La transcripcion pide dos capas de trabajo: primero analisis meteorologico de situacion, y despues riesgos concretos para una trayectoria entre dos aeropuertos. El codigo refleja esa division mediante `simulador-wrf mapas` y `simulador-wrf ruta`.

Fortalezas:

- La documentacion insiste en que los mapas y rutas son docentes, exploratorios y no operacionales.
- Los campos generales permiten discutir presion, temperatura, precipitacion, viento y niveles isobaricos.
- Los riesgos tienen atributos de metodo, fuentes, interpretacion y limitaciones en `diagnostics.py`.
- La ruta usa gran circulo y vecino mas cercano, coherente con la especificacion de no interpolar directamente con `xarray.interp` sobre lat/lon curvilineas.
- La CLI de rutas valida que la trayectoria cae dentro del dominio antes de muestrear.

Limitaciones docentes relevantes:

- La salida de ruta no integra todavia un analisis meteorologico narrativo de situacion; resume estadisticas puntuales de ruta.
- El Markdown de ruta no explica con suficiente detalle que variables son proxies ni conserva todos los atributos cientificos de las variables muestreadas.
- La advertencia sobre viento relativo a la rejilla esta en especificaciones y atributos, pero el resumen de ruta solo usa una advertencia generica. Para rutas, esto afecta viento, cizalladura, turbulencia y cualquier lectura de navegacion.
- No hay representacion de ascenso, crucero y descenso; todos los puntos se muestrean en un nivel isobarico fijo mas campos 2D. Esto debe decirse explicitamente en cualquier exposicion.

## Evaluacion por riesgo aeronautico

### Visibilidad

Implementacion actual:

- `add_aviation_risk_fields` copia `AFWA_VIS` a `visibility_m` si existe.
- Si falta `AFWA_VIS`, crea `visibility_m` con `NaN` y atributos que declaran no disponibilidad.

Valoracion:

- Es una decision defendible. Evita inventar visibilidad con humedad/precipitacion sin una formulacion robusta.
- Cumple la especificacion y la guia: la visibilidad solo se representa si existe diagnostico WRF fiable.
- La ruta puede incluir la columna `visibility_m`, pero si todo es `NaN` queda como informacion no disponible en el Markdown.

Riesgo:

- Bajo desde el punto de vista cientifico, porque no sobreinterpreta. Medio desde el punto de vista de usuario, porque un CSV con una columna de `NaN` puede confundirse si no se lee el resumen.

Recomendacion:

- En el Markdown de ruta, separar "variable presente pero no disponible por fuente" de "variable no muestreada". Para visibilidad, indicar expresamente que no se ha estimado si falta `AFWA_VIS`.

### Engelamiento

Implementacion actual:

- `calculate_icing_risk` usa temperatura entre `0` y `-20 degC`.
- Prefiere `t_isobaric_c` a 850 hPa si existe; si no, usa `t2_c`.
- Solo incorpora humedad relativa si existe `rh_isobaric` a 850 hPa.
- El campo se llama `icing_mask` y se exporta como flotante.

Valoracion:

- La ventana termica es coherente como criterio inicial de zona favorable.
- La funcion documenta que no garantiza hielo y que ignora microfisica.
- El uso de 850 hPa es util para baja troposfera, pero no representa una capa vertical de engelamiento ni el perfil real atravesado por una aeronave.

Riesgo:

- Medio-alto de interpretacion. En `route_outputs.py`, el resumen calcula "Probabilidad de engelamiento en ruta" como porcentaje de puntos con mascara activa. Eso no es una probabilidad fisica, sino una fraccion espacial de puntos favorables segun un criterio termico.
- Si falta humedad, el producto deberia nombrarse mas claramente como "zona termodinamicamente favorable", tal como exige la especificacion.

Recomendaciones:

- Cambiar en futuros trabajos el texto del resumen a "fraccion de trayectoria con condiciones termicas favorables a engelamiento".
- Registrar en el Markdown si `icing_mask` uso humedad o solo temperatura.
- Evitar conclusiones de seguridad en rutas con `icing_mask` sin humedad/condensado.

### Turbulencia

Implementacion actual:

- `calculate_turbulence_index` deriva `turbulence_index` como `wind_shear_10m_850_ms / 10`.
- No incluye gradientes horizontales, deformacion, estabilidad estatica ni indices tipo Ellrod-Knapp.

Valoracion:

- Es util como proxy de turbulencia de baja cota asociada a cizalladura.
- Esta claramente marcado como exploratorio en atributos.

Riesgo:

- Alto si se interpreta como turbulencia general de vuelo. No detecta turbulencia en aire claro cerca del jet ni turbulencia asociada a estabilidad, montana, conveccion o deformacion horizontal.
- En rutas a 300 hPa, el resumen puede presentar "Turbulencia maxima (niveles bajos)" junto a viento de 300 hPa. Esa mezcla de niveles puede inducir una lectura equivocada.

Recomendaciones:

- En rutas, etiquetar el indice como "proxy de turbulencia en capa 10 m-850 hPa".
- No mezclarlo visualmente con perfiles de crucero sin aclarar que procede de niveles bajos.
- Si se amplia el proyecto, incorporar gradientes horizontales de viento o un indice cinematico separado para niveles altos.

### Cizalladura

Implementacion actual:

- `calculate_wind_shear` calcula diferencia vectorial entre viento a 10 m y 850 hPa.
- La especificacion tambien contempla `wind_shear_850_500_ms`, pero no aparece implementado.

Valoracion:

- El calculo 10 m-850 hPa es correcto como magnitud vectorial simple.
- Es especialmente util para discutir ascensos, descensos, aproximaciones y capas bajas.

Riesgo:

- Medio. La ausencia de cizalladura 850-500 limita la lectura de capas medias y trayectorias a niveles por encima de 850 hPa.
- La advertencia sobre vientos relativos a la rejilla es importante. Mientras no haya rotacion a coordenadas terrestres, la magnitud de diferencia vectorial puede seguir siendo util exploratoriamente, pero direccion y navegacion no deben tratarse como operacionales.

Recomendaciones:

- Implementar o documentar explicitamente como pendiente `wind_shear_850_500_ms`.
- En salidas de ruta, distinguir cizalladura de baja capa frente a cizalladura en atmosfera libre.

### Conveccion

Implementacion actual:

- `calculate_convection_proxy` usa `precip_increment_mm >= 5.0`.
- La guia ya advierte que puede incluir precipitacion estratiforme intensa.

Valoracion:

- Es un proxy docente sencillo y trazable.
- Sirve para senalar zonas de precipitacion intensa sobre la ruta.

Riesgo:

- Medio-alto de interpretacion. Precipitacion intensa no equivale siempre a conveccion, y conveccion seca o incipiente puede no aparecer.
- El umbral de 5 mm depende del intervalo temporal de salida; si cambia la frecuencia de WRF, el significado fisico cambia.

Recomendaciones:

- Incluir en atributos y resumen el intervalo temporal de `precip_increment_mm` cuando sea posible.
- Llamar al resultado "proxy convectivo por precipitacion intensa", no "riesgo convectivo" sin matiz.
- Considerar CAPE/CIN, reflectividad, graupel o campos convectivos si estan disponibles en futuras fases.

## Evaluacion de trayectorias entre aeropuertos

Fortalezas:

- `airports.py` resuelve por ICAO e IATA con un catalogo interno simple.
- `calculate_great_circle_route` genera puntos reproducibles de gran circulo.
- `is_route_in_domain` valida envolvente geografica y distancia al punto de malla mas cercano.
- `sample_wrf_at_points` usa vecino mas cercano sobre lat/lon 2D, adecuado para mallas WRF curvilineas en esta fase.

Riesgos y limitaciones:

- `calculate_great_circle_route` no maneja explicitamente `n_points < 2`; con `n_points=1` habria division por cero.
- La distancia maxima al punto de malla se expresa en grados (`max_dist_deg=0.5`), no en kilometros. A distintas latitudes no representa la misma distancia fisica.
- La ruta no incluye fraccion de avance ni indices `y`, `x` ni distancia al vecino de malla en el CSV, aunque la especificacion lo pide.
- No se conserva en la salida que punto WRF fue usado para cada punto de ruta. Esto reduce auditabilidad y dificulta explicar errores de muestreo.
- No hay interpolacion temporal ni vertical continua, lo cual esta fuera de alcance, pero debe mantenerse visible.
- El catalogo de aeropuertos es pequeno y estatico. Esto es aceptable para la primera version, pero limita rutas docentes si el dominio WRF no cubre esos aeropuertos.

Recomendaciones:

- Anadir en futuras iteraciones `fraction`, `y_index`, `x_index` y `nearest_grid_distance_km` a `RoutePoint`/CSV.
- Validar `n_points >= 2` desde CLI y funcion.
- Convertir el umbral de cercania a kilometros o documentar claramente que es una aproximacion angular.
- En el resumen, indicar si origen/destino y todos los puntos estan dentro del dominio y cual fue la maxima distancia al vecino.

## Evaluacion de outputs

Mapas:

- Los mapas incluyen variable, unidades, tiempo valido y barra de color.
- `plot_risk_map` aplica paletas diferenciadas para riesgos.
- `plot_scalar_map` muestra aviso exploratorio solo si encuentra "exploratorio" o "exploratory" en `description`; varios campos usan la limitacion en otros atributos, por lo que el aviso puede no aparecer.
- En `simulador-wrf mapas`, para niveles isobaricos se generan geopotenciales de 850 y 500 hPa, pero no temperatura isobarica ni viento/jet de 300 hPa como conjunto completo de analisis sinoptico.

Rutas:

- Se generan CSV, Markdown, mapa y perfiles de viento y temperatura.
- El nombre esperado por la especificacion para perfil unico (`..._profile.png`) no coincide con la implementacion, que produce `..._wind_profile.png` y `..._temp_profile.png`.
- El resumen Markdown lista variables no disponibles, pero no lista claramente variables disponibles ni sus metodos/limitaciones.
- El mapa de ruta no superpone ningun campo meteorologico o de riesgo; solo muestra la linea sobre el dominio.

Recomendaciones:

- Mejorar el Markdown de ruta con una tabla de variables disponibles, unidades, metodo y limitacion principal.
- Incorporar al menos un perfil o grafico de riesgos principales frente a distancia.
- Superponer en el mapa de ruta un campo base seleccionable, por ejemplo viento a nivel, precipitacion o proxy convectivo.
- Asegurar que productos exploratorios muestren aviso aunque la palabra este en `limitations`, `warning` o `scientific_interpretation`, no solo en `description`.

## Evaluacion de tests

Resultado ejecutado:

```text
uv run pytest tests/test_diagnostics.py tests/test_routes.py tests/test_integration.py
10 passed, 28 warnings
```

Cobertura positiva:

- Calculo de precipitacion total e incremental.
- Resolucion ICAO/IATA.
- Generacion basica de gran circulo.
- Validacion de dominio.
- Muestreo de ruta con coordenadas WRF y coordenadas normalizadas.
- Ejecucion CLI de mapas y rutas con datos sinteticos.

Huecos de cobertura:

- No hay tests unitarios directos para `calculate_wind_shear`, `calculate_icing_risk`, `calculate_convection_proxy`, `calculate_turbulence_index` ni disponibilidad de `visibility_m`.
- No se comprueba que los atributos cientificos sobrevivan y lleguen a salidas interpretables.
- No se valida el caso de nivel isobarico solicitado ausente.
- No se prueba `n_points < 2`.
- No se verifica que el CSV incluya indices de malla o distancia al vecino, requisito de la especificacion.
- Los tests no revisan el contenido semantico del Markdown, por ejemplo el uso de "probabilidad" para una mascara.

## Riesgos prioritarios

1. Interpretacion excesiva de proxies como riesgos operacionales. Afecta sobre todo a engelamiento, turbulencia y conveccion.
2. Mezcla de niveles en ruta: se muestrea viento/temperatura a 300 hPa junto a riesgos calculados en superficie o 850 hPa sin una explicacion suficientemente visible.
3. Falta de trazabilidad espacial en ruta: no se exportan indices de malla ni distancia al vecino.
4. Cobertura incompleta de analisis meteorologico general en mapas isobaricos.
5. Tests centrados en existencia de archivos mas que en validez fisica y semantica.

## Conclusiones

El proyecto es adecuado como simulador docente exploratorio si se presenta con cautela. La estructura cumple el objetivo principal de la clase: conectar campos meteorologicos WRF con riesgos aeronauticos y una trayectoria entre aeropuertos. Las decisiones conservadoras sobre visibilidad y las advertencias de no operacionalidad son puntos fuertes.

Para que el resultado sea mas robusto en una defensa oral o entrega final, conviene reforzar la comunicacion de limitaciones: llamar proxy a lo que es proxy, evitar "probabilidad" cuando se calcula una fraccion de puntos, separar niveles bajos de crucero, y exportar trazabilidad del muestreo de ruta. La prioridad tecnica no deberia ser complicar el modelo, sino hacer que cada mapa, CSV y resumen diga exactamente que permite concluir y que no.
