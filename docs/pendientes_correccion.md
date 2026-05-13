# Pendientes de corrección del simulador WRF

Fecha: 2026-05-13

Este documento recoge los aspectos pendientes que deben corregirse o ampliarse antes de considerar el simulador como entregable final. El criterio rector es mantener programación científica.

## P0 - Correcciones Necesarias (Completadas)

- [x] **Completar mapas obligatorios**: La CLI genera SLP, T2, Precip, Viento 10m/300hPa y niveles 850/500hPa por defecto.
- [x] **Muestreo del Jet Stream en rutas**: Integrado en reportes con porcentaje de trayectoria.
- [x] **Referencia del viento**: Añadidos metadatos `wind_reference = grid_relative` y avisos en plots.
- [x] **Lenguaje de riesgos**: Actualizado a términos como "condiciones térmicas favorables" y "proxy".
- [x] **Detección estructural**: Implementada con metadatos científicos completos.
- [x] **Hodógrafo**: Comando `perfil` funcional con búsqueda 2D de coordenadas.

## P1 - Mejoras científicas y visuales recomendadas

- [ ] **Rotación de viento**: Implementar rotación a coordenadas terrestres (Earth-Relative) usando `SINALPHA/COSALPHA` del WRF.
- [ ] **Visibilidad**: Mejorar la estimación si falta `AFWA_VIS`.
- [ ] **Frentes**: Explorar la detección de frentes mediante el parámetro de frontogénesis de Miller.

## P2 - Reproducibilidad y mantenimiento

- [ ] **Tests con datos reales**: Añadir fixtures que imiten la estructura de un wrfout real (coords 2D).
- [ ] **Entorno reproducible**: Revisar el warning binario de NumPy en Windows y documentar o fijar versiones si aparece en otros equipos.
- [x] **Limpieza de warnings de xarray**: Resueltos los avisos de `concat`, `Dataset.dims` y selección 2D del hodógrafo.

---
*La documentación histórica, reviews y reportes antiguos se encuentran en `docs/archive/`.*
