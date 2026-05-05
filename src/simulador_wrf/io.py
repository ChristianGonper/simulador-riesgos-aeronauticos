import xarray as xr
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

MANDATORY_VARIABLES = [
    "T2", "U", "V", "RAINC", "RAINNC", "P", "PB", "PH", "PHB", 
    "XLAT", "XLONG", "Times", "PSFC", "U10", "V10", "HGT", "QVAPOR"
]

MANDATORY_DIMENSIONS = [
    "Time", "south_north", "west_east", "bottom_top"
]

DIM_MAP = {
    "Time": "time",
    "south_north": "y",
    "west_east": "x",
    "bottom_top": "model_level",
    "bottom_top_stag": "model_level_stag",
    "south_north_stag": "y_stag",
    "west_east_stag": "x_stag"
}

def validate_dataset(ds: xr.Dataset) -> bool:
    """
    Valida que el dataset contenga las variables y dimensiones obligatorias de WRF.
    """
    for var in MANDATORY_VARIABLES:
        if var not in ds:
            raise ValueError(f"Variable obligatoria ausente: {var}")
            
    for dim in MANDATORY_DIMENSIONS:
        if dim not in ds.dims:
            raise ValueError(f"Dimensión esperada ausente: {dim}")
            
    return True

def decode_times(ds: xr.Dataset) -> xr.Dataset:
    """
    Decodifica la variable 'Times' de WRF a un índice de tiempo real.
    """
    if "Times" not in ds:
        return ds
        
    times_bytes = ds.Times.values
    # Times suele ser (Time, DateStrLen)
    if times_bytes.dtype.kind in ("S", "U"):
        times_str = [t.decode("utf-8").replace("_", " ") if isinstance(t, bytes) else t.replace("_", " ") for t in times_bytes]
        times_dt = pd.to_datetime(times_str)
        ds = ds.assign_coords(time=("Time", times_dt))
        if "Time" in ds.dims:
            ds = ds.swap_dims({"Time": "time"})
    
    return ds

def normalize_dataset(ds: xr.Dataset) -> xr.Dataset:
    """
    Normaliza dimensiones y coordenadas del dataset WRF.
    """
    # 1. Decodificar tiempos
    ds = decode_times(ds)
    
    # 2. Renombrar dimensiones
    current_dims = {d: DIM_MAP[d] for d in ds.dims if d in DIM_MAP}
    ds = ds.rename(current_dims)
    
    # 3. Asegurar coordenadas de lat/lon
    if "XLAT" in ds and "y" in ds.dims and "x" in ds.dims:
        # XLAT suele ser (time, y, x) o (y, x)
        if "time" in ds.XLAT.dims:
             ds = ds.assign_coords(lat=ds.XLAT.isel(time=0).drop_vars("time"))
        else:
             ds = ds.assign_coords(lat=ds.XLAT)
             
    if "XLONG" in ds and "y" in ds.dims and "x" in ds.dims:
        if "time" in ds.XLONG.dims:
            ds = ds.assign_coords(lon=ds.XLONG.isel(time=0).drop_vars("time"))
        else:
            ds = ds.assign_coords(lon=ds.XLONG)
            
    return ds

def validate_compatibility(datasets: list) -> bool:
    """
    Valida que una lista de datasets sean compatibles para su concatenación temporal.
    Comprueba dominio, DX, DY, proyección y coordenadas XLAT/XLONG.
    """
    if not datasets:
        return True
        
    base = datasets[0]
    # Atributos de proyección críticos para la compatibilidad física
    PROJ_ATTRS = ["MAP_PROJ", "TRUELAT1", "TRUELAT2", "STAND_LON", "CEN_LAT", "CEN_LON", "DX", "DY"]
    
    for i, ds in enumerate(datasets[1:], 1):
        # 1. Comprobar dimensiones espaciales
        for dim in ["south_north", "west_east", "bottom_top"]:
            if ds.dims.get(dim) != base.dims.get(dim):
                raise ValueError(f"Incompatibilidad de dimensiones en archivo {i}: {dim}")
        
        # 2. Comprobar atributos de dominio y proyección
        for attr in PROJ_ATTRS:
            if ds.attrs.get(attr) != base.attrs.get(attr):
                # Usamos una tolerancia pequeña para flotantes si es necesario, 
                # pero los atributos de WRF suelen ser exactos.
                val_ds = ds.attrs.get(attr)
                val_base = base.attrs.get(attr)
                if isinstance(val_ds, (float, int)) and isinstance(val_base, (float, int)):
                    if not np.isclose(val_ds, val_base):
                         raise ValueError(f"Incompatibilidad de {attr} en archivo {i}: {val_ds} != {val_base}")
                elif val_ds != val_base:
                    raise ValueError(f"Incompatibilidad de {attr} en archivo {i}")
        
        # 3. Comprobar coordenadas espaciales (primer punto para rapidez)
        for coord in ["XLAT", "XLONG"]:
            if not np.allclose(ds[coord].isel(Time=0), base[coord].isel(Time=0), atol=1e-3):
                raise ValueError(f"Incompatibilidad de coordenadas {coord} en archivo {i}")
                
    return True

def open_wrf_dataset(paths, combine="nested"):
    """
    Abre uno o más archivos WRF, valida su compatibilidad y los normaliza.
    """
    if isinstance(paths, str):
        ds = xr.open_dataset(paths)
        validate_dataset(ds)
        ds = normalize_dataset(ds)
    else:
        # Abrir individualmente para validar compatibilidad antes de concatenar
        datasets = [xr.open_dataset(p) for p in paths]
        validate_compatibility(datasets)
        for ds_item in datasets:
            validate_dataset(ds_item)
            
        ds = xr.concat(datasets, dim="Time")
        # Asegurar orden temporal y normalización
        ds = normalize_dataset(ds)
        if "time" in ds.dims:
            ds = ds.sortby("time")
            # Comprobar duplicados
            if len(np.unique(ds.time.values)) != len(ds.time):
                 logger.warning("Se han detectado pasos de tiempo duplicados en la entrada.")
        
    return ds
