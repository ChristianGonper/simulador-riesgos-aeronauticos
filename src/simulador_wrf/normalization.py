import xarray as xr
import os
from simulador_wrf.diagnostics import (
    calculate_precipitation, 
    calculate_precip_increment, 
    calculate_surface_diagnostics,
    interpolate_to_pressure,
    detect_jet_stream
)
from simulador_wrf.backends import get_wrf_backend

def process_wrf_dataset(ds: xr.Dataset, jet_threshold: float = 30.0, levels: list = None, backend_name: str = "auto") -> xr.Dataset:
    """
    Aplica todos los diagnósticos y normalizaciones para obtener el dataset final.
    """
    if levels is None:
        levels = [850, 500, 300]
        
    # 1. Backend para diagnósticos 3D
    backend = get_wrf_backend(ds, backend_name=backend_name)
    
    # 2. Diagnósticos de superficie
    ds = calculate_precipitation(ds)
    ds = calculate_precip_increment(ds)
    ds = calculate_surface_diagnostics(ds)
    
    # 3. Diagnósticos 3D básicos
    p_hpa = backend.get_pressure()
    if p_hpa is not None:
        ds["pressure_hpa"] = p_hpa
        
    gh_m = backend.get_geopotential_height()
    if gh_m is not None:
        ds["geopotential_height_m"] = gh_m
        
    slp = backend.get_slp()
    if slp is not None:
        ds["slp_hpa"] = slp
        
    t_c = backend.get_temperature_c()
    if t_c is not None:
        ds["temperature_c"] = t_c
    
    # Desescalonar vientos si están presentes
    if "U" in ds and "V" in ds:
        u_destag, v_destag = backend.get_destaggered_wind()
        if u_destag is not None and v_destag is not None:
            ds["u_ms"] = u_destag
            ds["v_ms"] = v_destag
            ds["wind_speed_ms"] = (ds.u_ms**2 + ds.v_ms**2)**0.5
    
    # 4. Interpolación a niveles isobaricos
    if "temperature_c" in ds and "pressure_hpa" in ds:
        ds["t_isobaric_c"] = interpolate_to_pressure(ds, "temperature_c", levels)
    
    if "geopotential_height_m" in ds and "pressure_hpa" in ds:
        ds["gh_isobaric_m"] = interpolate_to_pressure(ds, "geopotential_height_m", levels)

    if "wind_speed_ms" in ds and "pressure_hpa" in ds:
        ds["wind_speed_isobaric_ms"] = interpolate_to_pressure(ds, "wind_speed_ms", levels)
        
        # 5. Jet stream en 300 hPa
        if 300 in ds.wind_speed_isobaric_ms.level_hpa.values:
            wind_300 = ds.wind_speed_isobaric_ms.sel(level_hpa=300)
            ds["jet_stream_mask"] = detect_jet_stream(wind_300, threshold=jet_threshold)
    
    return ds

def export_dataset(ds: xr.Dataset, output_path: str):
    """
    Exporta el dataset a NetCDF con compresión.
    """
    # Asegurar directorio de salida
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Definir encoding para compresión
    encoding = {}
    for var in ds.data_vars:
        encoding[var] = {"zlib": True, "complevel": 4}
        
    ds.to_netcdf(output_path, encoding=encoding)
    print(f"Dataset exportado exitosamente a {output_path}")
