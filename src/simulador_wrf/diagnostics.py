import xarray as xr
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_precipitation(ds: xr.Dataset) -> xr.Dataset:
    """
    Calcula la precipitación total acumulada (RAINC + RAINNC).
    """
    precip_total = ds.RAINC + ds.RAINNC
    precip_total.attrs = {
        "units": "mm",
        "standard_name": "precipitation_amount",
        "long_name": "Total Accumulated Precipitation",
        "description": "Sum of convective and non-convective precipitation",
        "method": "RAINC + RAINNC"
    }
    ds["precip_total_mm"] = precip_total
    return ds

def calculate_precip_increment(ds: xr.Dataset) -> xr.Dataset:
    """
    Calcula el incremento de precipitación entre pasos de tiempo.
    El primer paso de tiempo tiene un incremento de 0.0.
    """
    if "precip_total_mm" not in ds:
        ds = calculate_precipitation(ds)
        
    precip = ds.precip_total_mm
    
    # Calcular diferencia entre tiempos
    precip_inc = precip.diff(dim="time", label="upper")
    
    # Crear un array de ceros para el primer tiempo
    first_time_inc = xr.zeros_like(precip.isel(time=0))
    
    # Concatenar
    precip_inc = xr.concat([first_time_inc, precip_inc], dim="time")
    
    # Restaurar coordenadas de tiempo y asegurar orden de dimensiones (time, y, x)
    precip_inc = precip_inc.assign_coords(time=ds.time)
    if all(d in precip_inc.dims for d in ["time", "y", "x"]):
        precip_inc = precip_inc.transpose("time", "y", "x")
    
    precip_inc.attrs = {
        "units": "mm",
        "standard_name": "precipitation_increment",
        "long_name": "Precipitation Increment",
        "description": "Precipitation increment between time steps",
        "method": "diff(precip_total_mm)"
    }
    
    ds["precip_increment_mm"] = precip_inc
    return ds

def calculate_surface_diagnostics(ds: xr.Dataset) -> xr.Dataset:
    """
    Calcula diagnósticos básicos de superficie: T2 en Celsius, vientos a 10m, etc.
    """
    if "T2" in ds:
        ds["t2_c"] = ds.T2 - 273.15
        ds["t2_c"].attrs = {
            "units": "degC",
            "standard_name": "air_temperature",
            "long_name": "2m Air Temperature",
            "description": "Temperature at 2 meters above ground"
        }
        
    if "U10" in ds and "V10" in ds:
        ds["u10_ms"] = ds.U10
        ds["v10_ms"] = ds.V10
        ds["wind10_speed_ms"] = (ds.U10**2 + ds.V10**2)**0.5
        ds["wind10_speed_ms"].attrs = {"units": "m s-1", "long_name": "10m Wind Speed"}
        
        # Dirección del viento (de dónde viene)
        ds["wind10_dir_deg"] = (np.arctan2(ds.U10, ds.V10) * 180 / np.pi + 180) % 360
        ds["wind10_dir_deg"].attrs = {"units": "degree", "long_name": "10m Wind Direction"}

    return ds

def interpolate_to_pressure(ds: xr.Dataset, var_name: str, levels_hpa: list) -> xr.DataArray:
    """
    Interpola una variable 3D a los niveles de presión indicados usando interpolación lineal.
    """
    if "pressure_hpa" not in ds:
        from simulador_wrf.backends import get_wrf_backend
        backend = get_wrf_backend(ds)
        ds["pressure_hpa"] = backend.get_pressure()
        
    var_3d = ds[var_name]
    pressure = ds.pressure_hpa
    
    # Usar metpy para interpolación vertical si es posible, 
    # de lo contrario implementar una interpolación lineal manual vectorizada.
    
    # Implementación manual vectorizada de interpolación lineal en log(P):
    def log_linear_interp(target_lev, pressure_3d, data_3d):
        log_target = np.log(target_lev)
        
        # Implementación manual de interpolación lineal 1D en espacio logarítmico:
        logger.info(f"Interpolando log-linealmente {var_name} a {target_lev} hPa")
        
        # Encontrar índice del nivel justo debajo (presión mayor)
        idx_below = (pressure > target_lev).sum(dim="model_level") - 1
        idx_below = idx_below.clip(0, pressure.model_level.size - 2).compute()
        
        idx_above = idx_below + 1
        
        p_below = pressure.isel(model_level=idx_below)
        p_above = pressure.isel(model_level=idx_above)
        v_below = var_3d.isel(model_level=idx_below)
        v_above = var_3d.isel(model_level=idx_above)
        
        # Peso en espacio logarítmico para mayor precisión física (espesores geopotenciales)
        log_p_below = np.log(p_below)
        log_p_above = np.log(p_above)
        
        weight = (log_target - log_p_below) / (log_p_above - log_p_below)
        interp_val = v_below + weight * (v_above - v_below)
        
        # Enmascarar puntos fuera del rango de presión del modelo
        mask = (target_lev <= pressure.max(dim="model_level")) & (target_lev >= pressure.min(dim="model_level"))
        interp_val = interp_val.where(mask)
        
        return interp_val

    interpolated_levels = []
    for level in levels_hpa:
        interp_val = log_linear_interp(level, pressure, var_3d)
        interp_val = interp_val.assign_coords(level_hpa=level)
        interpolated_levels.append(interp_val)
        
    return xr.concat(interpolated_levels, dim="level_hpa")

def detect_jet_stream(wind_speed: xr.DataArray, threshold: float = 30.0) -> xr.DataArray:
    """
    Crea una máscara booleana para el jet stream basado en un umbral de velocidad (m/s).
    """
    mask = wind_speed >= threshold
    mask.attrs = {
        "units": "1",
        "long_name": "Jet Stream Mask",
        "description": f"Boolean mask where wind speed >= {threshold} m/s",
        "threshold_ms": threshold
    }
    return mask
