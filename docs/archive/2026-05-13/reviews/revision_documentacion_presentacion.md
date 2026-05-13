# Revision de documentacion para presentacion

Fecha de revision: 2026-05-05

## Alcance revisado

Se revisaron, desde el punto de vista de producto y uso en una exposicion docente:

- `docs/Presentacion_tarea/transcripcion_clase.txt`
- `README.md`
- `docs/guide/guia_interpretacion_mapas_riesgos.md`
- `docs/reports/*`
- `docs/specs/*`
- `docs/plans/*`
- CLI `simulador-wrf` en `src/simulador_wrf/cli.py`
- salidas generadas en `outputs/maps/` y `outputs/routes/`

No se han editado otros archivos del proyecto.

## Veredicto ejecutivo

El proyecto tiene una base tecnicamente demostrable: permite normalizar una salida WRF, generar mapas meteorologicos/riesgos y consultar una ruta Madrid-Barcelona con salidas CSV, Markdown y PNG. Para una exposicion, el grupo podria ensenar el simulador funcionando y defender varias decisiones cientificas si prepara bien el relato.

Sin embargo, la documentacion actual no guia todavia a un usuario externo de principio a fin ni ayuda lo suficiente a convertir las salidas en una defensa oral ante el profesor. Hay buena documentacion de implementacion, pero falta documentacion de producto: que abrir, en que orden, que decir mirando cada mapa, que limitaciones reconocer y que resultado concreto demuestra cada requisito de clase.

Riesgo principal para la exposicion: que el grupo muestre comandos y figuras, pero no tenga un hilo meteorologico claro para explicar borrascas, anticiclones, jet stream, riesgos y ruta. La transcripcion de clase exige primero analisis meteorologico de la situacion y despues analisis de un vuelo concreto; el README y las salidas actuales priorizan el flujo tecnico.

## Encaje con lo pedido en clase

La clase pide dos bloques claramente diferenciados:

1. Analisis meteorologico general de la prediccion WRF.
2. Analisis de riesgos para una ruta entre aeropuertos.

El proyecto cubre parcialmente ambos:

- Superficie: hay mapas de presion a nivel del mar, temperatura a 2 m, precipitacion y viento a 10 m.
- Niveles altos: hay geopotencial a 850 y 500 hPa, y diagnostico de jet stream.
- Riesgos: hay cizalladura, engelamiento, turbulencia, conveccion y declaracion de visibilidad no disponible.
- Ruta: hay comando `ruta` y salidas para `MAD -> BCN` a 300 hPa.

Brechas frente a la exposicion:

- La clase pide interpretar geopotencial y temperatura en 850 y 500 hPa; las salidas generadas visibles incluyen geopotencial, pero no mapas separados de temperatura en 850/500 hPa.
- El jet stream se representa como mascara de riesgo, pero falta un mapa claro de viento a 300 hPa que permita explicar intensidad y estructura del chorro.
- No hay una guia de exposicion que convierta los mapas en frases meteorologicas defendibles.
- No hay deteccion automatica de frentes, lo cual esta correctamente fuera de alcance, pero conviene indicar explicitamente como se inferirian manualmente con presion, temperatura, viento y precipitacion.

## README

Fortalezas:

- Es breve y permite descubrir los tres comandos principales.
- Usa `uv`, coherente con las normas del proyecto.
- Incluye ejemplos de normalizacion, mapas, ruta, tests y linting.

Problemas para uso en exposicion:

- No explica el objetivo docente: primero diagnosticar la situacion meteorologica y despues analizar una ruta.
- No lista requisitos previos practicos: donde debe estar el archivo `wrfout`, cuanto pesa, cuanto puede tardar la normalizacion, donde se genera `data/processed/wrf_normalizado.nc` y que carpetas se crean.
- No incluye un "camino feliz" completo con verificacion de salidas esperadas.
- No dice que archivos abrir durante la demo.
- No advierte de limitaciones importantes: viento relativo a la rejilla, riesgos exploratorios, visibilidad no disponible si falta `AFWA_VIS`, dominio WRF limitado.
- No menciona el catalogo disponible de aeropuertos ni ejemplos de rutas que probablemente funcionan con el dominio actual.

Recomendacion concreta:

Anadir una seccion "Demo para la exposicion" con este flujo:

```powershell
uv sync
uv run simulador-wrf normalizar --input wrfout_d01_2009-12-16.nc --output data/processed/wrf_normalizado.nc --time-index 0
uv run simulador-wrf mapas --input data/processed/wrf_normalizado.nc --output-dir outputs/maps --time-index 0
uv run simulador-wrf ruta --input data/processed/wrf_normalizado.nc --origin MAD --dest BCN --level 300 --time-index 0 --output-dir outputs/routes
```

Y despues listar los artefactos clave:

- `outputs/maps/slp_t0.png`
- `outputs/maps/wind10_t0.png`
- `outputs/maps/gh500_t0.png`
- `outputs/maps/risk_jet_stream_mask_t0.png`
- `outputs/routes/route_MAD_BCN_t0_300hpa.md`
- `outputs/routes/route_MAD_BCN_t0_300hpa_map.png`
- `outputs/routes/route_MAD_BCN_t0_300hpa_wind_profile.png`

## Guia de interpretacion

Fortalezas:

- Explica bien que los mapas son productos docentes y no operacionales.
- Reconoce limitaciones clave: visibilidad, umbrales exploratorios, viento relativo a rejilla.
- Ayuda a distinguir precipitacion incremental de acumulada.

Debilidades:

- Es generica: no esta conectada a los nombres reales de archivos generados.
- No contiene una secuencia de lectura para la exposicion.
- No ofrece frases tipo para defender lo observado.
- No incluye una tabla variable -> archivo -> pregunta meteorologica -> limitacion.
- Todavia dice que la seleccion de aeropuertos y rutas "se abordara despues", pero el proyecto ya tiene `simulador-wrf ruta`.

Recomendacion concreta:

Actualizar la guia con una tabla operativa:

| Archivo | Que demuestra | Como defenderlo |
| --- | --- | --- |
| `slp_t0.png` | borrascas, anticiclones y gradiente barico | localizar minimos/maximos y relacionarlos con viento |
| `t2_t0.png` | masas de aire en superficie | comparar zonas frias/calidas con adveccion |
| `wind10_t0.png` | viento en superficie | explicar direccion/intensidad y posible impacto en aproximacion |
| `gh850_t0.png` | baja troposfera | identificar advecciones y estructura termica si se anade temperatura |
| `gh500_t0.png` | vaguadas/dorsales | relacionar aire frio en altura e inestabilidad |
| `risk_jet_stream_mask_t0.png` | zonas de viento fuerte en 300 hPa | explicar que es umbral exploratorio |
| `route_*.md` | resumen de ruta | pasar del dominio completo al vuelo concreto |

## Specs, plans y reports

Fortalezas:

- Las especificaciones son bastante completas y alineadas con la transcripcion.
- Hay trazabilidad de decisiones tecnicas, especialmente sobre WRF, interpolacion isobarica, precipitacion y riesgos.
- Los planes muestran criterio cientifico y tecnico, no solo tareas de programacion.

Problemas:

- Hay rutas internas desactualizadas en algunos documentos. Por ejemplo, se referencia `docs/especificacion_obtencion_datos_wrf.md` o `docs/decisiones_finales_implementacion_wrf.md`, pero los archivos reales estan bajo `docs/specs/` y `docs/reports/`.
- Los reports son utiles para desarrollo, pero no estan escritos como defensa de producto. Un profesor no necesita ver "fase completada"; necesita oir que magnitud se calcula, con que limitacion y por que responde a la practica.
- `reporte_implementacion_rutas.md` termina con una frase de certificacion de herramienta externa ("Implementacion certificada por Antigravity") que no aporta a la defensa y puede sonar poco academica.
- Los planes todavia hablan de implementacion futura en partes que ya existen; eso puede confundir durante una revision.

Recomendacion concreta:

Crear un documento corto adicional, por ejemplo `docs/guide/guion_demo_exposicion.md`, que no sustituya specs/plans sino que los traduzca a exposicion:

1. Contexto WRF y dominio.
2. Campos generales que se muestran.
3. Diagnosticos de riesgo y limitaciones.
4. Ruta elegida y resultados.
5. Que preguntas puede hacer el profesor y respuestas preparadas.

## CLI y flujo de usuario

Fortalezas:

- El CLI esta bien dividido en tres verbos naturales: `normalizar`, `mapas`, `ruta`.
- La ayuda de Click es clara y suficiente para recordar opciones.
- Las rutas de salida por defecto son razonables: `data/processed`, `outputs/maps`, `outputs/routes`.

Problemas de producto:

- No hay comando unico de demo. Para exposicion, el grupo debe recordar tres comandos y el orden.
- `mapas` no genera todos los campos que el relato meteorologico necesita con la misma claridad: faltan mapas explicitos de temperatura en 850/500 hPa y viento en 300 hPa.
- `ruta` genera dos perfiles separados de viento y temperatura, pero la especificacion habla de un perfil de variables/riesgos. Falta un perfil o resumen visual de riesgos.
- El CLI no imprime al final una lista de archivos generados; eso obliga a buscar manualmente en carpetas.

Recomendacion concreta:

Sin cambiar necesariamente el codigo antes de la presentacion, documentar un "checklist post-comando":

- Tras `normalizar`, comprobar que existe `data/processed/wrf_normalizado.nc`.
- Tras `mapas`, comprobar que hay 11 PNG en `outputs/maps/`.
- Tras `ruta`, comprobar CSV, Markdown, mapa, perfil de viento y perfil de temperatura en `outputs/routes/`.

## Salidas generadas

Fortalezas:

- Los PNG existen y tienen tamano real; no son archivos vacios.
- Los mapas tienen titulo, tiempo valido y barra de color.
- El mapa de ruta es claro visualmente para ensenar origen, destino y trayectoria.
- El Markdown de ruta resume tiempo valido, nivel, distancia, temperatura media, viento maximo y riesgos principales.

Problemas para defender:

- Las etiquetas de mapas estan en ingles (`Sea Level Pressure`, `Valid`) mientras el resto de documentacion y exposicion esta en espanol.
- El mapa de ruta no superpone ningun campo meteorologico; muestra la trayectoria, pero no por si solo las condiciones atmosfericas de la ruta.
- El resumen de ruta dice "Probabilidad de engelamiento" aunque el diagnostico es una mascara exploratoria; seria mas defendible llamarlo "porcentaje de puntos con condiciones favorables a engelamiento".
- El resumen de ruta no incluye la advertencia especifica sobre viento relativo a la rejilla, aunque la especificacion indica que debe aparecer.
- El Markdown de ruta no explica por que `jet_stream_mask` no esta disponible si el viento maximo a 300 hPa si aparece en el CSV.
- Los perfiles grafican nombres internos de variables en el eje (`wind_speed_isobaric_ms`, `t_isobaric_c`), no nombres preparados para una audiencia.

Recomendacion concreta:

Para la exposicion, preparar una diapositiva o nota oral que traduzca cada salida:

- "Este no es un plan de vuelo real; es un muestreo docente de la malla WRF."
- "El 98% indica puntos de la ruta dentro de la mascara termica/humeda de engelamiento, no probabilidad operacional."
- "El viento y turbulencia son exploratorios porque el viento se mantiene relativo a la rejilla del modelo."
- "La visibilidad no se estima porque el WRF usado no contiene un diagnostico fiable `AFWA_VIS`."

## Claridad para demostrar el simulador

El grupo puede demostrar el simulador si prepara la exposicion con una secuencia muy concreta:

1. Mostrar el archivo WRF de entrada y explicar que es una salida de modelo mesoscalar.
2. Ejecutar o mostrar `normalizar` y explicar que convierte variables nativas WRF a magnitudes meteorologicas interpretables.
3. Abrir mapas generales y hacer analisis meteorologico de superficie y altura.
4. Abrir mapas de riesgo y explicar que son diagnosticos docentes exploratorios.
5. Ejecutar o mostrar `ruta MAD -> BCN`.
6. Abrir el Markdown y los perfiles de ruta.
7. Cerrar con limitaciones y mejoras futuras.

La parte mas debil es el paso 3: faltan ayudas concretas para interpretar una situacion meteorologica real. La documentacion dice que hay que localizar borrascas, anticiclones, vaguadas, dorsales y jet stream, pero no proporciona un analisis ya hecho del caso `2009-12-16 00`.

## Recomendaciones priorizadas

### Prioridad alta antes de la exposicion

1. Crear un guion de demo de una pagina con comandos, archivos a abrir y frase de interpretacion para cada figura.
2. Actualizar README con prerequisitos, flujo completo y salidas esperadas.
3. Corregir en la guia la frase que dice que rutas se abordaran despues.
4. Preparar interpretacion meteorologica del caso real `2009-12-16 00`: presion, viento, precipitacion, 500 hPa y jet.
5. Documentar que el resumen de ruta es exploratorio y que "probabilidad" debe interpretarse como porcentaje de puntos con mascara activa.

### Prioridad media

1. Generar mapas de temperatura a 850/500 hPa y viento a 300 hPa, o documentar explicitamente por que no estan en la demo.
2. Mejorar nombres y unidades en perfiles de ruta para que no aparezcan identificadores internos.
3. Anadir una tabla de aeropuertos soportados y ejemplos de rutas dentro/fuera del dominio.
4. Corregir referencias internas a rutas de documentos bajo `docs/specs/` y `docs/reports/`.
5. Eliminar o reformular frases poco academicas en reports.

### Prioridad baja

1. Crear indice HTML o Markdown de salidas generadas.
2. Anadir capturas pequenas en la documentacion para que el usuario sepa que esperar.
3. Crear un comando compuesto o script de demo si el equipo quiere reducir errores durante la exposicion.

## Preguntas probables del profesor y preparacion recomendada

- Que representa cada mapa y en que unidades esta.
- Como se paso de coordenada vertical WRF a 850/500/300 hPa.
- Si el viento esta en coordenadas terrestres o relativas a la rejilla.
- Como se calcula la precipitacion incremental.
- Por que la visibilidad no aparece.
- Por que el engelamiento no es una probabilidad operacional.
- Que ocurre si la ruta cae fuera del dominio WRF.
- Que limitaciones tiene usar un nivel fijo de 300 hPa para toda la ruta.

El grupo deberia preparar respuestas cortas y honestas. En este proyecto, reconocer bien las limitaciones aumenta la defendibilidad.

## Conclusion

El simulador es demostrable, pero la documentacion todavia esta mas orientada a desarrollo que a uso docente. Para defenderlo ante el profesor, falta empaquetar el flujo como producto: comandos reproducibles, salidas clave, interpretacion meteorologica del caso y limitaciones explicadas con lenguaje claro.

Con un README ampliado, una guia de demo y una interpretacion preparada del caso `2009-12-16 00`, el grupo podria usar y defender el proyecto razonablemente. Sin esos apoyos, la exposicion dependera demasiado de que quien presente conozca internamente el codigo y las decisiones tecnicas.
