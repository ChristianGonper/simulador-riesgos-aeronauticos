import click
import logging
from simulador_wrf.io import open_wrf_dataset
from simulador_wrf.normalization import process_wrf_dataset, export_dataset
from simulador_wrf.airports import resolve_airport
from simulador_wrf.routes import calculate_great_circle_route, is_route_in_domain, sample_wrf_at_points
from simulador_wrf.route_outputs import export_route_csv, generate_route_markdown, plot_route_map, plot_route_profile

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@click.group()
def main():
    """
    Simulador WRF: Herramienta de procesamiento y representación de datos WRF.
    """
    pass

@main.command()
@click.option("--input", "-i", multiple=True, required=True, help="Archivo(s) wrfout de entrada.")
@click.option("--output", "-o", default="data/processed/wrf_normalizado.nc", help="Archivo de salida NetCDF.")
@click.option("--jet-threshold", default=30.0, help="Umbral para jet stream (m/s).")
@click.option("--backend", type=click.Choice(["auto", "xwrf", "xarray"]), default="auto", help="Backend de cálculo.")
@click.option("--levels", multiple=True, type=float, default=[850.0, 500.0, 300.0], help="Niveles de presión (hPa).")
@click.option("--time-index", type=int, help="Índice de tiempo específico.")
def normalizar(input, output, jet_threshold, backend, levels, time_index):
    """Procesa y normaliza archivos wrfout."""
    try:
        logger.info(f"Abriendo archivos: {input}")
        ds = open_wrf_dataset(input)
        
        if time_index is not None:
            logger.info(f"Seleccionando índice de tiempo: {time_index}")
            ds = ds.isel(time=[time_index])

        logger.info(f"Procesando con backend: {backend}")
        ds_processed = process_wrf_dataset(ds, jet_threshold=jet_threshold, levels=list(levels), backend_name=backend)
        
        logger.info(f"Exportando resultados a: {output}")
        export_dataset(ds_processed, output)
        logger.info("Normalización completada.")
    except Exception as e:
        logger.error(f"Error en normalización: {e}")
        raise click.Abort()

@main.command()
@click.option("--input", "-i", required=True, help="Dataset NetCDF normalizado.")
@click.option("--output-dir", "-o", default="outputs/maps", help="Directorio de salida para los mapas.")
@click.option("--time-index", type=int, default=0, help="Índice de tiempo a representar.")
@click.option("--all-times", is_flag=True, help="Generar mapas para todos los tiempos disponibles.")
@click.option("--fields/--no-fields", default=True, help="Generar mapas meteorológicos generales.")
@click.option("--risks/--no-risks", default=True, help="Generar mapas de riesgos aeronáuticos.")
def mapas(input, output_dir, time_index, all_times, fields, risks):
    """Genera representaciones gráficas de campos y riesgos."""
    from simulador_wrf.visualization import plot_scalar_map, plot_wind_map, plot_risk_map
    import xarray as xr
    from pathlib import Path

    try:
        logger.info(f"Cargando dataset: {input}")
        ds = xr.open_dataset(input)
        
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        times = range(len(ds.time)) if all_times else [time_index]
        
        for t_idx in times:
            logger.info(f"Generando mapas para el paso de tiempo {t_idx}...")
            
            if fields:
                # Mapas generales
                if "slp_hpa" in ds:
                    plot_scalar_map(ds, "slp_hpa", t_idx, out_path / f"slp_t{t_idx}.png", cmap="RdBu_r")
                if "t2_c" in ds:
                    plot_scalar_map(ds, "t2_c", t_idx, out_path / f"t2_t{t_idx}.png", cmap="coolwarm")
                if "precip_increment_mm" in ds:
                    plot_scalar_map(ds, "precip_increment_mm", t_idx, out_path / f"precip_t{t_idx}.png", cmap="YlGnBu")
                
                # Vientos
                if "wind10_speed_ms" in ds:
                    plot_wind_map(ds, "u10_ms", "v10_ms", "wind10_speed_ms", t_idx, out_path / f"wind10_t{t_idx}.png")
                
                # Niveles isobaricos (850, 500)
                if "gh_isobaric_m" in ds:
                    for lev in [850, 500]:
                        if lev in ds.level_hpa:
                            ds_lev = ds.sel(level_hpa=lev)
                            plot_scalar_map(ds_lev, "gh_isobaric_m", t_idx, out_path / f"gh{lev}_t{t_idx}.png", cmap="terrain")

            if risks:
                # Riesgos
                risk_vars = [
                    "wind_shear_10m_850_ms", "icing_mask", "turbulence_index", 
                    "convection_proxy", "jet_stream_mask"
                ]
                for rv in risk_vars:
                    if rv in ds:
                        plot_risk_map(ds, rv, t_idx, out_path / f"risk_{rv}_t{t_idx}.png")
                    else:
                        logger.debug(f"Variable de riesgo {rv} no disponible.")

        logger.info(f"Mapas generados exitosamente en {output_dir}")
        
    except Exception as e:
        logger.error(f"Error generando mapas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise click.Abort()

@main.command()
@click.option("--input", "-i", required=True, help="Dataset NetCDF normalizado.")
@click.option("--origin", "-src", required=True, help="Código ICAO/IATA del aeropuerto de origen.")
@click.option("--dest", "-dst", required=True, help="Código ICAO/IATA del aeropuerto de destino.")
@click.option("--level", "-l", type=float, default=300.0, help="Nivel de presión para la ruta (hPa).")
@click.option("--n-points", "-n", type=int, default=50, help="Número de puntos en la ruta.")
@click.option("--time-index", "-t", type=int, default=0, help="Índice de tiempo a muestrear.")
@click.option("--output-dir", "-o", default="outputs/routes", help="Directorio de salida.")
def ruta(input, origin, dest, level, n_points, time_index, output_dir):
    """Genera un análisis meteorológico de una ruta aérea entre dos aeropuertos."""
    import xarray as xr
    from pathlib import Path
    
    try:
        # 1. Resolver aeropuertos
        ap_src = resolve_airport(origin)
        ap_dst = resolve_airport(dest)
        
        if not ap_src:
            logger.error(f"Aeropuerto de origen no encontrado: {origin}")
            raise click.Abort()
        if not ap_dst:
            logger.error(f"Aeropuerto de destino no encontrado: {dest}")
            raise click.Abort()
            
        logger.info(f"Ruta solicitada: {ap_src.name} ({ap_src.icao}) -> {ap_dst.name} ({ap_dst.icao})")
        
        # 2. Cargar dataset
        logger.info(f"Cargando dataset: {input}")
        ds = xr.open_dataset(input)
        
        # 3. Calcular puntos de la ruta
        points = calculate_great_circle_route(ap_src, ap_dst, n_points=n_points)
        
        # 4. Validar dominio
        if not is_route_in_domain(ds, points):
            logger.error("La ruta solicitada (o parte de ella) cae fuera del dominio WRF disponible.")
            raise click.Abort()
            
        # 5. Muestrear datos
        logger.info(f"Muestreando datos (tiempo={time_index}) en {n_points} puntos a {level} hPa...")
        route_data = sample_wrf_at_points(ds, points, level_hpa=level, time_index=time_index)
        
        # 6. Generar salidas
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        from simulador_wrf.visualization import get_time_str
        valid_time = get_time_str(ds, time_index)
        
        prefix = f"route_{origin}_{dest}_t{time_index}_{int(level)}hpa"
        
        export_route_csv(route_data, out_path / f"{prefix}.csv")
        generate_route_markdown(route_data, ap_src.name, ap_dst.name, level, out_path / f"{prefix}.md", valid_time=valid_time)
        plot_route_map(ds, route_data, out_path / f"{prefix}_map.png")
        plot_route_profile(route_data, "wind_speed_isobaric_ms", level, out_path / f"{prefix}_wind_profile.png")
        plot_route_profile(route_data, "t_isobaric_c", level, out_path / f"{prefix}_temp_profile.png")
        
        logger.info(f"Análisis de ruta completado exitosamente en {output_dir}")
        
    except Exception as e:
        logger.error(f"Error procesando ruta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise click.Abort()

if __name__ == "__main__":
    main()
