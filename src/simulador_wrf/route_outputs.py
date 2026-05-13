"""
Exportación de resultados de ruta: CSV, Markdown y gráficos.
"""

import pandas as pd
from typing import List
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from simulador_wrf.routes import RoutePoint
from simulador_wrf.visualization import setup_map_axes, get_coords
import xarray as xr

def export_route_csv(route_points: List[RoutePoint], output_path: Path):
    """
    Exporta los puntos de la ruta a un archivo CSV.
    """
    data = []
    for p in route_points:
        row = {
            "lat": p.lat,
            "lon": p.lon,
            "distance_km": p.distance_km,
        }
        row.update(p.data)
        data.append(row)
        
    df = pd.DataFrame(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Ruta exportada a CSV: {output_path}")

def generate_route_markdown(route_points: List[RoutePoint], origin_name: str, dest_name: str, level_hpa: float, output_path: Path, valid_time: str = "N/A"):
    """
    Genera un resumen de la ruta en formato Markdown.
    """
    df = pd.DataFrame([p.data for p in route_points])
    
    # Calcular estadísticas básicas
    summary = []
    summary.append(f"# Resumen de Ruta: {origin_name} -> {dest_name}")
    summary.append(f"**Tiempo válido:** {valid_time}")
    summary.append(f"**Nivel de vuelo solicitado:** {level_hpa} hPa")
    summary.append(f"**Distancia total:** {route_points[-1].distance_km:.1f} km\n")
    
    summary.append("## Estadísticas Meteorológicas en Ruta")
    
    if "t_isobaric_c" in df.columns and not df.t_isobaric_c.isnull().all():
        summary.append(f"- **Temperatura media ({level_hpa} hPa):** {df.t_isobaric_c.mean():.1f} °C")
    if "wind_speed_isobaric_ms" in df.columns and not df.wind_speed_isobaric_ms.isnull().all():
        summary.append(f"- **Viento máximo ({level_hpa} hPa):** {df.wind_speed_isobaric_ms.max():.1f} m/s")
    
    summary.append("\n## Condicionantes y Riesgos Aeronáuticos")
    summary.append("> [!NOTE]")
    summary.append("> Estos campos son diagnósticos exploratorios basados en proxies meteorológicos. No son diagnósticos operacionales.")
    
    if "icing_mask" in df.columns and not df.icing_mask.isnull().all():
        icing_pct = (df.icing_mask > 0.5).mean() * 100
        summary.append(f"- **Trayectoria con condiciones térmicas favorables a engelamiento:** {icing_pct:.1f}%")
    
    if "jet_stream_mask" in df.columns and not df.jet_stream_mask.isnull().all():
        jet_pct = (df.jet_stream_mask > 0.5).mean() * 100
        summary.append(f"- **Trayectoria dentro del núcleo del Jet Stream (300hPa):** {jet_pct:.1f}%")

    if "convection_proxy" in df.columns and not df.convection_proxy.isnull().all():
        conv_pct = (df.convection_proxy > 0.5).mean() * 100
        summary.append(f"- **Proxy convectivo por intensidad de precipitación:** {conv_pct:.1f}% de la trayectoria")
    
    if "turbulence_index" in df.columns and not df.turbulence_index.isnull().all():
        summary.append(f"- **Índice de turbulencia máximo (basado en cizalladura vertical):** {df.turbulence_index.max():.2f}")

    summary.append("\n## Avisos Técnicos")
    summary.append("- **Referencia de viento:** Vientos relativos a la rejilla (Grid-Relative). No están rotados a coordenadas terrestres.")
    summary.append("- **Visibilidad:** Si no está disponible en la tabla inferior, el dataset fuente no incluye el diagnóstico AFWA_VIS.")
        
    # Variables no disponibles (P2, P3)
    expected_vars = [
        ("t_isobaric_c", f"Temperatura a {level_hpa} hPa"),
        ("wind_speed_isobaric_ms", f"Viento a {level_hpa} hPa"),
        ("gh_isobaric_m", f"Geopotencial a {level_hpa} hPa"),
        ("jet_stream_mask", "Máscara de Jet Stream (300 hPa)"),
        ("icing_mask", "Riesgo de engelamiento"),
        ("convection_proxy", "Riesgo convectivo (proxy)"),
        ("turbulence_index", "Índice de turbulencia"),
        ("wind_shear_10m_850_ms", "Cizalladura vertical"),
        ("visibility_m", "Visibilidad"),
        ("t2_c", "Temperatura a 2m"),
        ("slp_hpa", "Presión a nivel del mar"),
        ("wind10_speed_ms", "Viento a 10m"),
        ("precip_increment_mm", "Incremento de precipitación")
    ]
    
    missing = []
    for var_id, var_name in expected_vars:
        if var_id not in df.columns or df[var_id].isnull().all():
            missing.append(var_name)
            
    if missing:
        summary.append("\n## Información No Disponible")
        for m in missing:
            summary.append(f"- {m}")

    summary.append("\n---")
    summary.append("*Producto docente y exploratorio. No usar para navegación real.*")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))
    print(f"Resumen Markdown generado: {output_path}")

def plot_route_map(ds: xr.Dataset, route_points: List[RoutePoint], output_path: Path):
    """
    Genera un mapa de la ruta sobre el dominio WRF.
    """
    lon_grid, lat_grid = get_coords(ds)
    
    plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    setup_map_axes(ax)
    
    # Dibujar extensión del dominio WRF
    ax.set_extent([lon_grid.min(), lon_grid.max(), lat_grid.min(), lat_grid.max()], crs=ccrs.PlateCarree())
    
    # Dibujar ruta
    route_lats = [p.lat for p in route_points]
    route_lons = [p.lon for p in route_points]
    ax.plot(route_lons, route_lats, 'r-', linewidth=2, transform=ccrs.PlateCarree(), label='Ruta')
    ax.plot(route_lons[0], route_lats[0], 'go', transform=ccrs.PlateCarree(), label='Origen')
    ax.plot(route_lons[-1], route_lats[-1], 'bo', transform=ccrs.PlateCarree(), label='Destino')
    
    plt.title("Mapa de Ruta sobre Dominio WRF")
    plt.legend()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Mapa de ruta guardado: {output_path}")

def plot_route_profile(route_points: List[RoutePoint], variable: str, level_hpa: float, output_path: Path):
    """
    Genera un gráfico de perfil (distancia vs variable).
    """
    distances = [p.distance_km for p in route_points]
    values = [p.data.get(variable) for p in route_points]
    
    # Filtrar Nones
    valid_dist = [d for d, v in zip(distances, values) if v is not None]
    valid_val = [v for v in values if v is not None]
    
    if not valid_val:
        return
        
    plt.figure(figsize=(10, 5))
    plt.plot(valid_dist, valid_val, 'b-', linewidth=2)
    plt.grid(True, alpha=0.3)
    plt.xlabel("Distancia desde origen (km)")
    plt.ylabel(f"{variable}")
    plt.title(f"Perfil de {variable} en ruta (Nivel: {level_hpa} hPa)")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Perfil de ruta guardado: {output_path}")
