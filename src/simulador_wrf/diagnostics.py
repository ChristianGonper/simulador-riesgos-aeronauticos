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
        "threshold_ms": threshold,
        "source_variables": "wind_speed_isobaric_ms (300hPa)",
        "scientific_interpretation": "Identifica el núcleo de la corriente en chorro, zona de vientos máximos en la alta troposfera.",
        "limitations": "Basado únicamente en un umbral de velocidad, no considera gradientes ni continuidad estructural."
    }
    return mask

def calculate_wind_shear(ds: xr.Dataset) -> xr.Dataset:
    """
    Calcula la cizalladura vertical del viento entre 10m y 850 hPa.
    Requiere que existan u10_ms, v10_ms y u_isobaric_ms, v_isobaric_ms.
    """
    if not all(k in ds for k in ["u10_ms", "v10_ms"]):
        logger.warning("Faltan vientos a 10m para calcular cizalladura.")
        return ds
    
    if "u_isobaric_ms" not in ds or "v_isobaric_ms" not in ds:
        # Intentar interpolar si no están
        if "u_ms" in ds and "v_ms" in ds and "pressure_hpa" in ds:
            ds["u_isobaric_ms"] = interpolate_to_pressure(ds, "u_ms", [850.0])
            ds["v_isobaric_ms"] = interpolate_to_pressure(ds, "v_ms", [850.0])
        else:
            logger.warning("Faltan vientos isobaricos para calcular cizalladura.")
            return ds

    u850 = ds.u_isobaric_ms.sel(level_hpa=850.0)
    v850 = ds.v_isobaric_ms.sel(level_hpa=850.0)
    
    shear = ((u850 - ds.u10_ms)**2 + (v850 - ds.v10_ms)**2)**0.5
    shear.attrs = {
        "units": "m s-1",
        "long_name": "Wind Shear (10m-850hPa)",
        "description": "Vector wind shear between 10m and 850 hPa level",
        "method": "sqrt((u850-u10)^2 + (v850-v10)^2)",
        "source_variables": "u10_ms, v10_ms, u_isobaric_ms, v_isobaric_ms",
        "scientific_interpretation": "Cambio del vector viento con la altura. Valores altos indican cizalladura intensa, crítica en aproximaciones y despegues.",
        "limitations": "Basado en vientos relativos a la rejilla (grid-relative). No considera cizalladura direccional fina fuera de estos niveles."
    }
    ds["wind_shear_10m_850_ms"] = shear
    return ds

def calculate_icing_risk(ds: xr.Dataset) -> xr.Dataset:
    """
    Calcula la máscara de engelamiento (icing) basada en temperatura.
    Favorable entre 0 y -20 degC. 
    Si hay humedad relativa (RH), se podría refinar (e.g. RH > 80%).
    """
    if "t2_c" not in ds:
        logger.warning("Falta t2_c para calcular icing_mask en superficie.")
        return ds
        
    # Por ahora usamos t2_c como ejemplo, pero lo ideal es 3D o niveles bajos
    # Si tenemos temperatura isobarica a 850, es más representativo para aviación general
    t_ref = None
    if "t_isobaric_c" in ds and 850.0 in ds.t_isobaric_c.level_hpa:
        t_ref = ds.t_isobaric_c.sel(level_hpa=850.0)
        name_ref = "850hPa Temperature"
    else:
        t_ref = ds.t2_c
        name_ref = "2m Temperature"
        
    icing_mask = (t_ref <= 0) & (t_ref >= -20)
    
    # Si tenemos RH en el dataset (podría venir de la normalización)
    if "rh_isobaric" in ds and 850.0 in ds.rh_isobaric.level_hpa:
        rh_ref = ds.rh_isobaric.sel(level_hpa=850.0)
        icing_mask = icing_mask & (rh_ref > 80)
        desc = f"Icing probability based on {name_ref} (0 to -20C) and RH850 > 80%"
    else:
        desc = f"Thermal icing mask based on {name_ref} (0 to -20C)"

    icing_mask.attrs = {
        "units": "1",
        "long_name": "Icing Risk Mask",
        "description": desc,
        "method": "0 >= T >= -20",
        "source_variables": "t_isobaric_c (850hPa) o t2_c, rh_isobaric (opcional)",
        "scientific_interpretation": "Zonas termodinámicamente favorables para la presencia de agua subfundida y formación de hielo en aeronaves.",
        "limitations": "No garantiza la presencia de hielo, solo condiciones favorables. Ignora microfísica de nubes detallada."
    }
    ds["icing_mask"] = icing_mask.astype(float)
    return ds

def calculate_convection_proxy(ds: xr.Dataset, threshold: float = 5.0) -> xr.Dataset:
    """
    Proxy de convección basado en incremento de precipitación.
    """
    if "precip_increment_mm" not in ds:
        logger.warning("Falta precip_increment_mm para calcular convection_proxy.")
        return ds
        
    conv_proxy = ds.precip_increment_mm >= threshold
    conv_proxy.attrs = {
        "units": "1",
        "long_name": "Convection Proxy",
        "description": f"Boolean mask where precip increment >= {threshold} mm",
        "threshold_mm": threshold,
        "source_variables": "precip_increment_mm",
        "scientific_interpretation": "Proxy de actividad convectiva basado en la intensidad de la precipitación acumulada en el paso de tiempo.",
        "limitations": "Puede incluir precipitación estratiforme intensa. No distingue el tipo de nube ni la severidad (granizo, rayos)."
    }
    ds["convection_proxy"] = conv_proxy.astype(float)
    return ds

def calculate_turbulence_index(ds: xr.Dataset) -> xr.Dataset:
    """
    Índice de turbulencia exploratorio basado en cizalladura vertical.
    En una fase avanzada se añadiría deformación horizontal.
    """
    if "wind_shear_10m_850_ms" not in ds:
        ds = calculate_wind_shear(ds)
        
    if "wind_shear_10m_850_ms" in ds:
        # Simplificación: usamos la cizalladura como proxy de turbulencia en niveles bajos.
        # El divisor (10.0) es un factor de escala para llevar el índice a un rango típico [0, 1].
        # Se basa en el criterio docente de que 10 m/s de cizalladura en la capa es un valor significativo.
        norm_factor = 10.0
        turb = ds.wind_shear_10m_850_ms / norm_factor
        turb.attrs = {
            "units": "index",
            "long_name": "Exploratory Turbulence Index",
            "description": "Low-level turbulence proxy based on 10m-850hPa wind shear",
            "warning": "Exploratory product, not for operational use",
            "method": f"wind_shear / {norm_factor}",
            "source_variables": "wind_shear_10m_850_ms",
            "scientific_interpretation": "Estimación cinemática de la turbulencia en capas bajas provocada por cizalladura vertical intensa.",
            "limitations": "Ignora deformación horizontal, estabilidad estática y turbulencia en aire claro (CAT) de niveles altos."
        }
        ds["turbulence_index"] = turb
        
    return ds

def add_aviation_risk_fields(ds: xr.Dataset) -> xr.Dataset:
    """
    Añade todos los campos de riesgo aeronáutico disponibles.
    """
    logger.info("Calculando campos de riesgo aeronáutico...")
    ds = calculate_wind_shear(ds)
    ds = calculate_icing_risk(ds)
    ds = calculate_convection_proxy(ds)
    ds = calculate_turbulence_index(ds)
    
    # Visibilidad (solo si existe AFWA_VIS o similar)
    if "AFWA_VIS" in ds:
        ds["visibility_m"] = ds.AFWA_VIS
        ds["visibility_m"].attrs = {
            "units": "m", 
            "long_name": "Visibility",
            "visibility_available": 1,
            "method": "Direct copy from diagnostic field",
            "source_variables": "AFWA_VIS",
            "scientific_interpretation": "Visibilidad horizontal en superficie diagnosticada por el modelo WRF.",
            "limitations": "Sujeto a las parametrizaciones del módulo AFWA del modelo WRF."
        }
    else:
        logger.info("Visibilidad (AFWA_VIS) no disponible en el dataset.")
        # Declarar explícitamente como no disponible como exige el plan
        dummy_vis = xr.full_like(ds.t2_c, np.nan)
        dummy_vis.attrs = {
            "units": "m",
            "long_name": "Visibility",
            "description": "Visibility data not available in source dataset",
            "visibility_available": 0,
            "method": "NaN filling",
            "source_variables": "None (AFWA_VIS missing)",
            "scientific_interpretation": "Campo declarado como no disponible para asegurar la trazabilidad de la limitación del dataset fuente.",
            "limitations": "Dataset fuente no contiene diagnósticos de visibilidad (e.g. AFWA_VIS)."
        }
        ds["visibility_m"] = dummy_vis
        
    return ds
