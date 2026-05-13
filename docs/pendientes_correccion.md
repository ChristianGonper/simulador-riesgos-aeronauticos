# Pendientes de correccion del simulador WRF

Fecha: 2026-05-13

Este documento recoge los aspectos pendientes que deben corregirse o ampliarse antes de considerar el simulador como entregable final. El criterio rector es mantener programacion cientifica: variables con significado fisico claro, unidades explicitas, metodos trazables y visualizaciones que ayuden a interpretar la atmosfera.

## Objetivo funcional

El proyecto debe organizarse en dos fases conectadas:

1. Representacion meteorologica general de la salida WRF.
2. Deteccion y representacion de riesgos meteorologicos y aeronauticos.

La meta final es que el sistema pueda detectar de forma programatica aspectos relevantes para la interpretacion meteorologica y aeronautica: vaguadas, dorsales, ciclones, borrascas, zonas de viento intenso, jet stream, cizalladura, turbulencia, conveccion, engelamiento y visibilidad cuando la salida WRF lo permita.

Los plots deben poder funcionar como entregable: cada mapa debe ser legible, fisicamente interpretable, con unidades, tiempo valido, nivel, limitaciones y, cuando proceda, avisos de producto exploratorio.

## P0 - Correcciones necesarias antes de la entrega

### Completar mapas obligatorios del profesor

El subcomando `simulador-wrf mapas` debe generar por defecto todos los campos solicitados en clase:

- superficie: viento, direccion, presion a nivel del mar, temperatura y precipitacion;
- 850 hPa: geopotencial y temperatura;
- 500 hPa: geopotencial y temperatura;
- 300 hPa: viento en altura y jet stream.

Actualmente el dataset contiene `t_isobaric_c`, `gh_isobaric_m` y `wind_speed_isobaric_ms`, pero la CLI no produce todos esos PNG por defecto.

### Corregir muestreo del jet stream en rutas

`jet_stream_mask` existe en el NetCDF normalizado, pero no se muestrea en rutas. El resumen Markdown puede marcarlo como no disponible aunque el campo exista.

Accion:

- incluir `jet_stream_mask` en el muestreo de `sample_wrf_at_points`;
- reflejar el porcentaje de ruta afectada por jet stream a 300 hPa;
- mantener la advertencia de que es una mascara por umbral de viento, no una deteccion sinoptica completa.

### Hacer visible la referencia del viento

Los vientos estan desescalonados, pero no rotados a coordenadas terrestres. Esto afecta a:

- direccion de viento;
- barbas de viento;
- cizalladura;
- turbulencia;
- perfiles de ruta;
- interpretacion de zonas de viento.

Accion minima:

- anadir metadatos `wind_reference = grid_relative` o equivalente en todos los campos de viento;
- mostrar una advertencia visible en mapas y resumen de ruta.

Accion deseable:

- implementar viento rotado a coordenadas terrestres usando `SINALPHA` y `COSALPHA`, o una libreria meteorologica adecuada.

### Ajustar lenguaje de riesgos

Los riesgos actuales son proxies docentes. No deben presentarse como diagnosticos operacionales.

Accion:

- cambiar "probabilidad de engelamiento" por "porcentaje de ruta con condiciones termicas favorables a engelamiento";
- cambiar "riesgo convectivo" por "proxy convectivo por precipitacion";
- explicar que turbulencia y cizalladura son diagnosticos simplificados.

### Preparar guion meteorologico del caso real

Debe existir un documento breve para defender la situacion meteorologica:

- superficie: bajas, altas, gradiente barico, viento y precipitacion;
- 850 hPa: masas de aire y advecciones;
- 500 hPa: vaguadas, dorsales y aire frio en altura;
- 300 hPa: jet stream y zonas de viento intenso;
- riesgos aeronauticos;
- ruta de ejemplo.

## P1 - Mejoras cientificas y visuales recomendadas

### Deteccion programatica de estructuras meteorologicas

Implementar diagnosticos que ayuden a identificar:

- centros de baja y alta presion;
- vaguadas y dorsales mediante geopotencial en 500 hPa;
- zonas baroclinas mediante gradiente horizontal de temperatura;
- frentes aproximados como ayuda visual, no como analisis operacional;
- maximos de viento y ejes de jet stream;
- areas de precipitacion intensa.

Cada diagnostico debe indicar variables fuente, unidades, metodo, interpretacion y limitaciones.

### Mejorar visualizacion meteorologica

Se permite anadir librerias de meteorologia y representacion si mejoran el rigor o la claridad:

- MetPy para calculos meteorologicos y hodografos;
- Cartopy para mapas;
- xarray y Dask para datasets;
- librerias WRF especificas si resuelven viento rotado, interpolacion vertical o diagnosticos.

Productos visuales deseables:

- mapas combinados de SLP, viento y precipitacion;
- mapas de 850 hPa con temperatura, geopotencial y viento;
- mapas de 500 hPa con geopotencial, temperatura y zonas de vaguada/dorsal;
- mapas de 300 hPa con velocidad de viento, barbas y eje del jet;
- hodografo de viento para puntos o aeropuertos relevantes;
- perfiles de ruta con viento, temperatura y riesgos.

### Mejorar engelamiento, turbulencia y visibilidad

Engelamiento:

- calcular humedad relativa desde `QVAPOR`, presion y temperatura cuando sea posible;
- usar humedad o condensado para no depender solo de temperatura.

Turbulencia:

- incorporar cizalladura en capas adicionales;
- explorar deformacion horizontal y estabilidad estatica si los datos lo permiten.

Visibilidad:

- usar `AFWA_VIS` si existe;
- si no existe, mantenerla como no disponible salvo que se implemente una estimacion fisicamente justificada.

## P2 - Reproducibilidad y mantenimiento

### Tests mas representativos

Los tests sinteticos pasan, pero conviene anadir un fixture reducido mas parecido a un WRF real:

- dimensiones escalonadas reales;
- niveles verticales razonables;
- coordenadas 2D;
- variables de viento y presion con rangos fisicos;
- caso con y sin `AFWA_VIS`.

### Warnings conocidos

Durante la verificacion aparecieron warnings de `xarray` sobre cambios futuros en `concat` y un warning de dimension ilimitada `Time` al exportar un solo tiempo. No bloquean la ejecucion actual, pero deben limpiarse para evitar fragilidad futura.

### README y documentacion viva

El README debe explicar:

- flujo completo de uso;
- productos esperados por el profesor;
- limitaciones cientificas;
- como interpretar los mapas;
- donde se escriben las salidas.

La documentacion historica debe quedar archivada. La documentacion viva debe ser corta, actual y orientada al uso y a la fisica del simulador.
