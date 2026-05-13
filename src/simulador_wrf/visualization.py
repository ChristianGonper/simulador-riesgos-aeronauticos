import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)

def setup_map_axes(ax):
    """
    Configura el mapa con costas, fronteras y rejilla.
    """
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='#f9f9f9', alpha=0.5)
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.3)
    gl.top_labels = False
    gl.right_labels = False
    return ax

def get_coords(ds):
    """
    Extrae lat/lon 2D para el plot.
    Prioriza nombres normalizados, luego nombres WRF originales.
    """
    if 'lon' in ds.coords and 'lat' in ds.coords:
        return ds.lon, ds.lat
    elif 'XLONG' in ds and 'XLAT' in ds:
        # Seleccionar primer tiempo si es 3D
        lon = ds.XLONG.isel(time=0) if 'time' in ds.XLONG.dims else ds.XLONG
        lat = ds.XLAT.isel(time=0) if 'time' in ds.XLAT.dims else ds.XLAT
        return lon, lat
    else:
        # Búsqueda desesperada
        for lon_name in ['longitude', 'lon', 'XLONG']:
            for lat_name in ['latitude', 'lat', 'XLAT']:
                if lon_name in ds and lat_name in ds:
                    return ds[lon_name], ds[lat_name]
    
    raise ValueError("No se encontraron coordenadas lat/lon (lon/lat o XLONG/XLAT) en el dataset.")

def get_time_str(ds, time_index):
    """
    Devuelve un string con el tiempo válido.
    """
    try:
        t = ds.time.isel(time=time_index).values
        return np.datetime_as_string(t, unit='h').replace('T', ' ')
    except Exception as e:
        logger.warning(f"Error al obtener string de tiempo: {e}")
        return f"Index {time_index}"

def plot_scalar_map(ds: xr.Dataset, variable: str, time_index: int, output_path: Path, **kwargs) -> Path:
    """
    Representa una variable escalar en un mapa.
    """
    if variable not in ds:
        logger.error(f"Variable {variable} no encontrada en el dataset.")
        return None

    data = ds[variable].isel(time=time_index)
    lon, lat = get_coords(ds)
    time_str = get_time_str(ds, time_index)
    
    plt.figure(figsize=(12, 8))
    # Usar PlateCarree como aproximación si no conocemos la proyección WRF exacta
    ax = plt.axes(projection=ccrs.PlateCarree())
    setup_map_axes(ax)
    
    cmap = kwargs.get('cmap', 'viridis')
    levels = kwargs.get('levels', None)
    
    im = ax.contourf(lon, lat, data, levels=levels, cmap=cmap, transform=ccrs.PlateCarree())
    
    # Título y etiquetas
    units = data.attrs.get('units', 'n/a')
    long_name = data.attrs.get('long_name', variable)
    level = ds.coords.get('level_hpa', None)
    level_str = ""
    if level is not None:
        try:
            # Manejar tanto escalares como arrays de un elemento
            lev_val = int(level.item()) if hasattr(level, 'item') else int(level)
            level_str = f" at {lev_val} hPa"
        except (ValueError, AttributeError, TypeError):
            level_str = ""
    
    plt.title(f"{long_name}{level_str} ({units})\nValid: {time_str}", fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, orientation='vertical', pad=0.02, aspect=40)
    cbar.set_label(f"{long_name} [{units}]")
    
    # Añadir avisos (Referencia de viento, exploratorio, etc.)
    warning_text = []
    
    # 1. Aviso de viento relativo si aplica
    if data.attrs.get('wind_reference') == 'grid_relative':
        warning_text.append("⚠ VIENTO RELATIVO A REJILLA (GRID-RELATIVE)")

    # 2. Aviso si es exploratorio
    is_exploratory = (
        "exploratorio" in data.attrs.get('description', '').lower() or 
        "exploratory" in data.attrs.get('description', '').lower() or
        "exploratory" in data.attrs.get('warning', '').lower()
    )
    if is_exploratory:
        warning_text.append("⚠ PRODUCTO EXPLORATORIO - NO PARA USO OPERACIONAL")

    if warning_text:
        full_warning = "\n".join(warning_text)
        plt.text(0.02, 0.02, full_warning, 
                 transform=ax.transAxes, color='darkred', fontsize=9, fontweight='bold',
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.5'))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Mapa guardado en: {output_path}")
    return output_path

def plot_wind_map(
    ds: xr.Dataset,
    u_variable: str,
    v_variable: str,
    speed_variable: str,
    time_index: int,
    output_path: Path,
    **kwargs
) -> Path:
    """
    Representa un mapa de viento con barbas o flechas y fondo de velocidad.
    """
    if speed_variable not in ds:
        logger.error(f"Variable {speed_variable} no encontrada.")
        return None

    speed = ds[speed_variable].isel(time=time_index)
    u = ds[u_variable].isel(time=time_index)
    v = ds[v_variable].isel(time=time_index)
    lon, lat = get_coords(ds)
    time_str = get_time_str(ds, time_index)
    
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    setup_map_axes(ax)
    
    # Fondo de velocidad
    im = ax.contourf(lon, lat, speed, cmap='YlGnBu', transform=ccrs.PlateCarree(), alpha=0.8)
    
    # Barbas de viento (diezmadas para claridad)
    skip = kwargs.get('skip', 10)
    ax.barbs(lon.values[::skip, ::skip], lat.values[::skip, ::skip], 
             u.values[::skip, ::skip], v.values[::skip, ::skip], 
             transform=ccrs.PlateCarree(), length=5, linewidth=0.5)
    
    units = speed.attrs.get('units', 'm/s')
    level = ds.coords.get('level_hpa', None)
    level_str = " (Surface)"
    if level is not None:
        try:
            lev_val = int(level.item()) if hasattr(level, 'item') else int(level)
            level_str = f" at {lev_val} hPa"
        except (ValueError, AttributeError, TypeError):
            pass
    
    plt.title(f"Wind Speed and Direction{level_str} ({units})\nValid: {time_str}", fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, orientation='vertical', pad=0.02, aspect=40)
    cbar.set_label(f"Speed [{units}]")
    
    # Aviso de viento relativo
    if speed.attrs.get('wind_reference') == 'grid_relative':
        plt.text(0.02, 0.02, "⚠ VIENTO RELATIVO A REJILLA (GRID-RELATIVE)", 
                 transform=ax.transAxes, color='darkred', fontsize=9, fontweight='bold',
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.5'))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def plot_risk_map(ds: xr.Dataset, risk_variable: str, time_index: int, output_path: Path) -> Path:
    """
    Representa un mapa de riesgo con una paleta de colores de advertencia.
    """
    # Usamos plot_scalar_map con una paleta específica para riesgos
    risk_cmaps = {
        'wind_shear_10m_850_ms': 'YlOrRd',
        'icing_mask': 'Blues',
        'turbulence_index': 'PuRd',
        'convection_proxy': 'Reds',
        'jet_stream_mask': 'magma',
        'low_centers_mask': 'Blues',
        'high_centers_mask': 'Reds',
        'trough_ridge_index_500': 'RdBu_r',
        't_gradient_850_index': 'YlOrBr'
    }
    
    cmap = risk_cmaps.get(risk_variable, 'hot_r')
    
    # Para máscaras binarias, ajustar niveles
    if 'mask' in risk_variable or 'proxy' in risk_variable:
        kwargs = {'levels': [0, 0.5, 1], 'cmap': cmap}
    else:
        kwargs = {'cmap': cmap}
        
    return plot_scalar_map(ds, risk_variable, time_index, output_path, **kwargs)

def plot_hodograph(ds: xr.Dataset, lat: float, lon: float, time_index: int, output_path: Path) -> Path:
    """
    Crea un hodógrafo de viento para una ubicación específica.
    Usa MetPy para la representación si está disponible.
    """
    try:
        from metpy.plots import Hodograph
        from metpy.units import units as metpy_units
        
        # Encontrar punto más cercano en rejilla 2D
        dist_sq = (ds.lat - lat)**2 + (ds.lon - lon)**2
        
        # argmin() sobre el array aplanado y luego unravel
        flat_idx = int(dist_sq.values.argmin())
        y_idx, x_idx = np.unravel_index(flat_idx, dist_sq.shape)
        
        ds_point = ds.isel(y=y_idx, x=x_idx, time=time_index)
        
        # Obtener coordenadas reales del punto seleccionado
        actual_lat = ds_point.lat.item()
        actual_lon = ds_point.lon.item()
        
        if 'u_isobaric_ms' not in ds_point or 'v_isobaric_ms' not in ds_point:
            logger.error("Variables de viento isobarico no encontradas para la ubicación seleccionada.")
            return None
            
        u = ds_point.u_isobaric_ms.values * metpy_units('m/s')
        v = ds_point.v_isobaric_ms.values * metpy_units('m/s')
        
        u_vals = u.m
        v_vals = v.m
        
        # Filtrar NaNs para evitar errores en MetPy
        mask = ~np.isnan(u_vals) & ~np.isnan(v_vals)
        if not np.any(mask):
            logger.error("Todos los valores de viento para el hodógrafo son NaN.")
            return None
            
        u_plot = u[mask]
        v_plot = v[mask]
        
        max_speed = np.nanmax(np.sqrt(u_vals**2 + v_vals**2))
        if np.isnan(max_speed):
            max_speed = 20.0
            
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1)
        h = Hodograph(ax, component_range=max_speed + 5)
        h.add_grid(increment=10)
        h.plot(u_plot, v_plot, color='blue', linewidth=2)
        
        plt.title(f"Wind Hodograph\nTarget: {lat:.2f}, {lon:.2f} | Selected: {actual_lat:.2f}, {actual_lon:.2f}\nValid: {get_time_str(ds, time_index)}", fontsize=12)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=120, bbox_inches='tight')
        plt.close()
        return output_path
    except Exception as e:
        logger.error(f"Error creando hodógrafo: {e}")
        return None
