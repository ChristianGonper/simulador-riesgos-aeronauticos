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
    # En una fase futura se debería usar la proyección original del modelo
    ax = plt.axes(projection=ccrs.PlateCarree())
    setup_map_axes(ax)
    
    cmap = kwargs.get('cmap', 'viridis')
    levels = kwargs.get('levels', None)
    
    im = ax.contourf(lon, lat, data, levels=levels, cmap=cmap, transform=ccrs.PlateCarree())
    
    # Título y etiquetas
    units = data.attrs.get('units', 'n/a')
    long_name = data.attrs.get('long_name', variable)
    plt.title(f"{long_name} ({units})\nValid: {time_str}", fontsize=14)
    
    cbar = plt.colorbar(im, orientation='vertical', pad=0.02, aspect=40)
    cbar.set_label(f"{variable} [{units}]")
    
    # Añadir aviso si es exploratorio
    if "exploratorio" in data.attrs.get('description', '').lower() or "exploratory" in data.attrs.get('description', '').lower():
         plt.text(0.02, 0.02, "PRODUCTO EXPLORATORIO - NO OPERACIONAL", 
                  transform=ax.transAxes, color='red', fontsize=8, fontweight='bold',
                  bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

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
    plt.title(f"Wind Speed and Direction ({units})\nValid: {time_str}", fontsize=14)
    
    cbar = plt.colorbar(im, orientation='vertical', pad=0.02, aspect=40)
    cbar.set_label(f"Speed [{units}]")
    
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
        'jet_stream_mask': 'magma'
    }
    
    cmap = risk_cmaps.get(risk_variable, 'hot_r')
    
    # Para máscaras binarias, ajustar niveles
    if 'mask' in risk_variable or 'proxy' in risk_variable:
        kwargs = {'levels': [0, 0.5, 1], 'cmap': cmap}
    else:
        kwargs = {'cmap': cmap}
        
    return plot_scalar_map(ds, risk_variable, time_index, output_path, **kwargs)
