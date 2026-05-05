"""
Cálculo de rutas, validación de dominio y muestreo de datos WRF.
"""

import numpy as np
import xarray as xr
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from simulador_wrf.airports import Airport
from simulador_wrf.visualization import get_coords

@dataclass
class RoutePoint:
    lat: float
    lon: float
    distance_km: float
    data: Dict[str, Any]

def calculate_great_circle_route(origin: Airport, destination: Airport, n_points: int = 50) -> List[Tuple[float, float, float]]:
    """
    Calcula puntos intermedios en una ruta de gran círculo.
    Devuelve lista de (lat, lon, distancia_desde_origen_km).
    """
    lat1, lon1 = np.radians(origin.latitude), np.radians(origin.longitude)
    lat2, lon2 = np.radians(destination.latitude), np.radians(destination.longitude)
    
    # Distancia angular entre puntos (fórmula de Haversine)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Radio de la Tierra en km
    R = 6371.0
    total_distance = c * R
    
    points = []
    for i in range(n_points):
        f = i / (n_points - 1)
        # Interpolación de gran círculo (Slerp)
        A = np.sin((1 - f) * c) / np.sin(c)
        B = np.sin(f * c) / np.sin(c)
        
        x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
        y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
        z = A * np.sin(lat1) + B * np.sin(lat2)
        
        lat = np.arctan2(z, np.sqrt(x**2 + y**2))
        lon = np.arctan2(y, x)
        
        points.append((np.degrees(lat), np.degrees(lon), f * total_distance))
        
    return points

def is_route_in_domain(ds: xr.Dataset, points: List[Tuple[float, float, float]], max_dist_deg: float = 0.5) -> bool:
    """
    Comprueba si la ruta cae dentro del dominio del WRF.
    Se valida por envolvente y por distancia al punto más cercano.
    """
    lons_grid, lats_grid = get_coords(ds)
    
    lat_min, lat_max = float(lats_grid.min()), float(lats_grid.max())
    lon_min, lon_max = float(lons_grid.min()), float(lons_grid.max())
    
    for lat, lon, _ in points:
        # 1. Validación rápida por envolvente
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            return False
            
        # 2. Validación por distancia al punto más cercano (P2)
        dist_sq = (lats_grid - lat)**2 + (lons_grid - lon)**2
        min_dist_deg = float(np.sqrt(np.min(dist_sq)))
        
        if min_dist_deg > max_dist_deg:
            return False
        
    return True

def sample_wrf_at_points(ds: xr.Dataset, points: List[Tuple[float, float, float]], level_hpa: Optional[float] = 300.0, time_index: int = 0) -> List[RoutePoint]:
    """
    Muestrea variables WRF en los puntos de la ruta usando vecino más cercano.
    """
    # Pre-calcular coordenadas de malla (P1)
    lon_grid_da, lat_grid_da = get_coords(ds)
    lats_grid = lat_grid_da.values
    lons_grid = lon_grid_da.values
    
    route_data = []
    
    # Variables de superficie/2D
    vars_2d = [
        "t2_c", "wind10_speed_ms", "wind10_dir_deg", 
        "precip_increment_mm", "slp_hpa", "visibility_m",
        "wind_shear_10m_850_ms", "icing_mask", "convection_proxy", "turbulence_index"
    ]
    
    # Variables isobaricas
    vars_iso = [
        "t_isobaric_c", "gh_isobaric_m", "wind_speed_isobaric_ms",
        "u_isobaric_ms", "v_isobaric_ms"
    ]
    
    # Seleccionar tiempo
    ds_t = ds.isel(time=time_index)
    
    for lat, lon, dist in points:
        # Encontrar índice del vecino más cercano en la malla 2D
        # (lat - XLAT)^2 + (lon - XLONG)^2
        dist_sq = (lats_grid - lat)**2 + (lons_grid - lon)**2
        idx = np.unravel_index(np.argmin(dist_sq), dist_sq.shape)
        
        point_dict = {}
        
        # Muestrear 2D
        for var in vars_2d:
            if var in ds_t:
                val = ds_t[var].values[idx]
                point_dict[var] = float(val) if not np.isnan(val) else None
        
        # Muestrear Isobaricas
        if level_hpa is not None:
            for var in vars_iso:
                if var in ds_t:
                    # Comprobar si el nivel existe
                    if level_hpa in ds_t[var].level_hpa.values:
                        val = ds_t[var].sel(level_hpa=level_hpa).values[idx]
                        point_dict[var] = float(val) if not np.isnan(val) else None
        
        route_data.append(RoutePoint(lat, lon, dist, point_dict))
        
    return route_data
