# Documentacion viva del simulador WRF

Esta carpeta contiene la documentacion activa del proyecto. Los documentos historicos, planes cerrados, revisiones antiguas y especificaciones previas se conservan en `docs/archive/`.

## Lectura recomendada

1. `estado_actual.md`: que funciona ahora, que productos existen y que limitaciones hay.
2. `pendientes_correccion.md`: aspectos pendientes antes de la entrega final.
3. `plans/plan_codigo_deteccion_visualizacion.md`: plan tecnico para mejorar codigo, deteccion meteorologica y plots.
4. `guide/guia_interpretacion_mapas_riesgos.md`: guia fisica para interpretar mapas y riesgos.
5. `instrucciones_programacion_wrf.md`: convenciones cientificas y tecnicas del repo.

## Enfoque del proyecto

El simulador debe tener dos fases:

1. Representar la situacion meteorologica general de una salida WRF.
2. Detectar y representar riesgos meteorologicos y aeronauticos.

El objetivo final es que el codigo ayude a identificar de forma programatica estructuras y riesgos: vaguadas, dorsales, ciclones, borrascas, zonas de viento intenso, jet stream, cizalladura, turbulencia, conveccion, engelamiento y visibilidad cuando los datos lo permitan.

La visualizacion es parte del entregable. Los mapas deben poder explicarse fisicamente y deben incluir unidades, tiempo valido, nivel, metodo y limitaciones.
