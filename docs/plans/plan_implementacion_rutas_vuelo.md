# Plan de implementacion: consulta de rutas de vuelo

## 1. Objetivo

Implementar una primera version de consulta de ruta entre dos aeropuertos usando el NetCDF WRF normalizado. La fase debe producir un resumen meteorologico y aeronautico simple, reproducible y defendible en la practica.

## 2. Componentes

- Catalogo interno de aeropuertos principales, con ICAO/IATA, nombre, pais y coordenadas.
- Utilidades de dominio para comprobar si un aeropuerto o una ruta cae dentro del `lat/lon` del WRF.
- Generacion de ruta por gran circulo con un numero configurable de puntos.
- Muestreo por vecino mas cercano sobre malla WRF 2D.
- Salidas de ruta: CSV, Markdown, mapa y perfil.
- CLI `simulador-wrf ruta`.

## 3. Orden de implementacion

1. Crear modulo `airports.py` con catalogo y resolucion por codigo.
2. Crear modulo `routes.py` con calculo de gran circulo, validacion de dominio y muestreo.
3. Crear modulo `route_outputs.py` con escritura de CSV, resumen Markdown y graficos.
4. Integrar subcomando `ruta` en `cli.py`.
5. Actualizar `README.md`.
6. Añadir tests unitarios e integracion.

## 4. Decisiones tecnicas

- Usar vecino mas cercano con `numpy`, sin depender de `scipy`.
- Validar dominio por envolvente geografica y por distancia maxima al punto WRF mas cercano.
- Usar nivel fijo `--level`, por defecto `300`.
- Si una variable isobarica no contiene el nivel solicitado, se omite y se registra como no disponible.
- Las variables de superficie se muestrean sin seleccion vertical.
- Las salidas se nombran con origen, destino, tiempo y nivel.

## 5. Tests previstos

- Resolver aeropuertos por ICAO/IATA.
- Filtrar aeropuertos dentro de un dominio sintetico.
- Generar ruta con distancia creciente.
- Detectar ruta fuera del dominio.
- Muestrear variables sinteticas sobre `lat/lon`.
- Ejecutar `simulador-wrf ruta` y verificar CSV, Markdown, mapa y perfil no vacios.

## 6. Limitaciones documentadas

- Producto docente y exploratorio.
- Viento, cizalladura y turbulencia dependen de que el viento siga siendo relativo a la rejilla.
- No hay perfil vertical realista de vuelo.
- No hay interpolacion temporal.
- La ruta Barcelona-Londres solo es valida si el dominio WRF la cubre.
