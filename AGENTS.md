
Usar programacion cientifica: nombres fisicos claros, unidades explicitas, funciones pequenas y metadatos trazables en cada campo derivado.

El simulador tiene dos fases: primero representar la situacion meteorologica WRF y despues detectar/representar riesgos meteorologicos y aeronauticos. Los plots son parte del entregable y deben ser interpretables por si mismos.

Priorizar codigo que permita detectar de forma programatica estructuras meteorologicas: vaguadas, dorsales, ciclones, borrascas, zonas de viento intenso, jet stream, cizalladura, turbulencia, conveccion, engelamiento y visibilidad cuando los datos lo permitan.

Se pueden anadir librerias de meteorologia y visualizacion si mejoran el rigor o la claridad, por ejemplo MetPy, Cartopy o herramientas especificas WRF. Usar `uv` para dependencias y ejecucion.

Usar Context7 para documentacion actualizada de librerias y busqueda web directa para fuentes externas cuando haga falta.

Documentacion viva:
- Estado actual: docs/estado_actual.md
- Pendientes: docs/pendientes_correccion.md
- Plan tecnico activo: docs/plans/plan_codigo_deteccion_visualizacion.md
- Convenciones: docs/instrucciones_programacion_wrf.md

Mantener la documentacion limpia: archivar planes, specs, reports y reviews historicos en `docs/archive/`; no duplicar informacion viva en documentos antiguos.
