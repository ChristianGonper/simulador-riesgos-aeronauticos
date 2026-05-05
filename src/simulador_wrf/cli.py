import click
import logging
from simulador_wrf.io import open_wrf_dataset
from simulador_wrf.normalization import process_wrf_dataset, export_dataset

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--input", "-i", 
    multiple=True, 
    required=True, 
    help="Archivo(s) wrfout de entrada. Puede usarse varias veces."
)
@click.option(
    "--output", "-o", 
    default="data/processed/wrf_normalizado.nc", 
    help="Archivo de salida NetCDF."
)
@click.option(
    "--jet-threshold", 
    default=30.0, 
    help="Umbral de velocidad de viento para jet stream (m/s)."
)
@click.option(
    "--backend", 
    type=click.Choice(["auto", "xwrf", "xarray"]), 
    default="auto", 
    help="Backend de cálculo meteorológico."
)
@click.option(
    "--levels", 
    multiple=True, 
    type=float,
    default=[850.0, 500.0, 300.0], 
    help="Niveles de presión para interpolación (hPa)."
)
@click.option(
    "--time-index", 
    type=int, 
    help="Índice de tiempo específico a procesar (base 0)."
)
def main(input, output, jet_threshold, backend, levels, time_index):
    """
    Simulador WRF: Herramienta de procesamiento y normalización de datos WRF.
    """
    try:
        logger.info(f"Abriendo archivos: {input}")
        
        # Delegamos en open_wrf_dataset para validación y normalización completa
        ds = open_wrf_dataset(input)
        
        if time_index is not None:
            logger.info(f"Seleccionando índice de tiempo: {time_index}")
            if "time" in ds.dims:
                 ds = ds.isel(time=[time_index])
            elif "Time" in ds.dims:
                 ds = ds.isel(Time=[time_index])

        logger.info(f"Procesando con backend: {backend}")
        ds_processed = process_wrf_dataset(ds, jet_threshold=jet_threshold, levels=list(levels), backend_name=backend)
        
        logger.info(f"Exportando resultados a: {output}")
        export_dataset(ds_processed, output)
        
        logger.info("Proceso completado exitosamente.")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        raise click.Abort()

if __name__ == "__main__":
    main()
