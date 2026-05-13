import xarray as xr
import numpy as np
import logging
from scipy.ndimage import minimum_filter, maximum_filter

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
        ds["wind10_speed_ms"].attrs = {
            "units": "m s-1", 
            "long_name": "10m Wind Speed",
            "wind_reference": "grid_relative"
        }
        
        # Dirección del viento (de dónde viene)
        ds["wind10_dir_deg"] = (np.arctan2(ds.U10, ds.V10) * 180 / np.pi + 180) % 360
        ds["wind10_dir_deg"].attrs = {
            "units": "degree", 
            "long_name": "10m Wind Direction",
            "wind_reference": "grid_relative"
        }

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
        
    return xr.concat(interpolated_levels, dim="level_hpa", coords="minimal", compat="override")

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

    if 850.0 not in ds.u_isobaric_ms.level_hpa.values:
        logger.warning("Nivel 850 hPa no disponible para cizalladura.")
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
    Calcula la máscara de condiciones favorables para engelamiento (icing).
    Favorable entre 0 y -20 degC. 
    Se ajusta el lenguaje a "proxy de condiciones favorables" para evitar falsas expectativas operacionales.
    """
    if "t2_c" not in ds and "t_isobaric_c" not in ds:
        logger.warning("Faltan datos de temperatura para calcular icing_mask.")
        return ds
        
    # Preferimos 850 hPa para aviación, si no 2m
    if "t_isobaric_c" in ds and 850.0 in ds.t_isobaric_c.level_hpa:
        t_ref = ds.t_isobaric_c.sel(level_hpa=850.0)
        name_ref = "850hPa Temperature"
    else:
        t_ref = ds.t2_c
        name_ref = "2m Temperature"
        
    # Máscara térmica base
    icing_mask = (t_ref <= 0) & (t_ref >= -20)
    
    # Intentar refinar con Humedad Relativa si está disponible
    rh_info = ""
    if "rh_isobaric" in ds and 850.0 in ds.rh_isobaric.level_hpa:
        rh_ref = ds.rh_isobaric.sel(level_hpa=850.0)
        icing_mask = icing_mask & (rh_ref > 80)
        rh_info = " and RH850 > 80%"
    elif "QVAPOR" in ds and "pressure_hpa" in ds and "temperature_c" in ds:
        # Cálculo simplificado de RH si tenemos QVAPOR
        try:
            # Aproximación rápida para RH
            pres_pa = ds.pressure_hpa * 100.0
            qv = ds.QVAPOR
            
            # Presión de vapor de saturación (Tetens)
            # Asegurar rango térmico para evitar overflow en np.exp
            t_clipped = ds.temperature_c.clip(-100, 50)
            es = 611.2 * np.exp(17.67 * t_clipped / (t_clipped + 243.5))
            # Razón de mezcla de saturación
            ws = 0.622 * es / (pres_pa - es)
            rh = (qv / ws) * 100.0
            
            # Interpolar RH a 850 si es posible
            if "level_hpa" in ds:
                rh_850 = interpolate_to_pressure(ds.assign(rh_calc=rh), "rh_calc", [850.0]).sel(level_hpa=850.0)
                icing_mask = icing_mask & (rh_850 > 80)
                rh_info = " and calculated RH850 > 80%"
        except Exception as e:
            logger.debug(f"No se pudo refinar icing con RH: {e}")

    icing_mask.attrs = {
        "units": "1",
        "long_name": "Icing Favorable Conditions Proxy",
        "description": f"Thermal icing proxy based on {name_ref} (0 to -20C){rh_info}",
        "method": "0 >= T >= -20 (plus RH > 80% if available)",
        "source_variables": "t_isobaric_c (850hPa) o t2_c, QVAPOR (opcional)",
        "scientific_interpretation": "Zonas termodinámicamente favorables para la formación de hielo en aeronaves. Producto docente, no operacional.",
        "limitations": "No garantiza la presencia de hielo. No considera microfísica de nubes."
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
    Índice de turbulencia exploratorio basado en cizalladura vertical en varias capas.
    """
    if "u_isobaric_ms" not in ds or "v_isobaric_ms" not in ds:
        logger.warning("Faltan vientos isobaricos para calcular turbulencia multinivel.")
        return ds
    
    # 1. Cizalladura capas bajas (10m - 850hPa)
    if "wind_shear_10m_850_ms" not in ds:
        ds = calculate_wind_shear(ds)
    
    shear_low = ds.get("wind_shear_10m_850_ms", 0.0)
    
    # 2. Cizalladura capas medias (850 - 500 hPa)
    shear_mid = 0.0
    if all(lev in ds.level_hpa for lev in [850, 500]):
        u850, v850 = ds.u_isobaric_ms.sel(level_hpa=850), ds.v_isobaric_ms.sel(level_hpa=850)
        u500, v500 = ds.u_isobaric_ms.sel(level_hpa=500), ds.v_isobaric_ms.sel(level_hpa=500)
        shear_mid = ((u500 - u850)**2 + (v500 - v850)**2)**0.5
        
    # 3. Cizalladura capas altas (500 - 300 hPa)
    shear_high = 0.0
    if all(lev in ds.level_hpa for lev in [500, 300]):
        u500, v500 = ds.u_isobaric_ms.sel(level_hpa=500), ds.v_isobaric_ms.sel(level_hpa=500)
        u300, v300 = ds.u_isobaric_ms.sel(level_hpa=300), ds.v_isobaric_ms.sel(level_hpa=300)
        shear_high = ((u300 - u500)**2 + (v300 - v500)**2)**0.5

    # Índice combinado ponderado (priorizando capas bajas y altas)
    turb = (shear_low * 0.5 + shear_mid * 0.2 + shear_high * 0.3) / 10.0
    
    turb.attrs = {
        "units": "index",
        "long_name": "Multi-level Exploratory Turbulence Proxy",
        "description": "Turbulence proxy based on vertical wind shear at 10-850, 850-500 and 500-300 hPa",
        "warning": "EXPLORATORY PRODUCT - NOT FOR OPERATIONAL USE",
        "method": "Weighted average of vertical shears / 10",
        "source_variables": "u/v_isobaric_ms, u10/v10_ms",
        "scientific_interpretation": "Estimación de turbulencia por cizalladura vertical. Valores > 1.0 indican condiciones severas potenciales.",
        "limitations": "No considera turbulencia térmica, de montaña ni deformación horizontal."
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

# --- NUEVOS DIAGNÓSTICOS ESTRUCTURALES ---

def detect_pressure_centers(ds: xr.Dataset, neighborhood_size: int = 20) -> xr.Dataset:
    """
    Detecta centros de baja (B) y alta (A) presión en SLP.
    neighborhood_size controla la escala de los centros detectados.
    """
    if "slp_hpa" not in ds:
        return ds
        
    slp = ds.slp_hpa
    
    def find_extrema(data_2d, size, mode="min"):
        if mode == "min":
            filtered = minimum_filter(data_2d, size=size)
            extrema = (data_2d == filtered)
        else:
            filtered = maximum_filter(data_2d, size=size)
            extrema = (data_2d == filtered)
        return extrema

    lows_mask = xr.apply_ufunc(
        find_extrema, slp, 
        input_core_dims=[["y", "x"]], output_core_dims=[["y", "x"]],
        kwargs={"size": neighborhood_size, "mode": "min"},
        vectorize=True, dask="parallelized"
    )
    
    highs_mask = xr.apply_ufunc(
        find_extrema, slp, 
        input_core_dims=[["y", "x"]], output_core_dims=[["y", "x"]],
        kwargs={"size": neighborhood_size, "mode": "max"},
        vectorize=True, dask="parallelized"
    )
    
    ds["low_centers_mask"] = lows_mask.astype(float)
    ds["high_centers_mask"] = highs_mask.astype(float)
    
    ds["low_centers_mask"].attrs = {
        "long_name": "Low Pressure Centers (B)", 
        "units": "mask (0 or 1)",
        "description": "Exploratory detection of local SLP minima",
        "method": f"Local minimum filter with neighborhood_size={neighborhood_size}",
        "source_variables": "slp_hpa",
        "scientific_interpretation": "Identifica núcleos de baja presión (borrascas o bajas térmicas) basados en mínimos locales de SLP.",
        "limitations": "La detección depende del neighborhood_size. Puede detectar bajas insignificantes si el umbral no es estricto.",
        "warning": "EXPLORATORY PRODUCT"
    }
    ds["high_centers_mask"].attrs = {
        "long_name": "High Pressure Centers (A)", 
        "units": "mask (0 or 1)",
        "description": "Exploratory detection of local SLP maxima",
        "method": f"Local maximum filter with neighborhood_size={neighborhood_size}",
        "source_variables": "slp_hpa",
        "scientific_interpretation": "Identifica centros de alta presión (anticiclones) basados en máximos locales de SLP.",
        "limitations": "La detección depende del neighborhood_size. Sensible a ruido en el campo de presión.",
        "warning": "EXPLORATORY PRODUCT"
    }
    
    return ds

def detect_troughs_ridges(ds: xr.Dataset, level: float = 500.0) -> xr.Dataset:
    """
    Identifica áreas potenciales de vaguadas y dorsales basadas en la curvatura del geopotencial.
    """
    if "gh_isobaric_m" not in ds or level not in ds.level_hpa:
        return ds
        
    gh = ds.gh_isobaric_m.sel(level_hpa=level)
    
    # Calcular Laplaciano (curvatura) como proxy simple
    # En una rejilla regular, esto es d2z/dx2 + d2z/dy2
    # Usamos np.gradient dos veces
    
    def calculate_curvature(data_2d):
        gy, gx = np.gradient(data_2d)
        gyy, gxy = np.gradient(gy)
        gyx, gxx = np.gradient(gx)
        return gxx + gyy

    curvature = xr.apply_ufunc(
        calculate_curvature, gh,
        input_core_dims=[["y", "x"]], output_core_dims=[["y", "x"]],
        vectorize=True, dask="parallelized"
    )
    
    # Vaguadas (Troughs): Curvatura positiva (ciclónica en NH)
    # Dorsales (Ridges): Curvatura negativa (anticiclónica en NH)
    # Nota: esto es una simplificación extrema
    
    ds[f"trough_ridge_index_{int(level)}"] = curvature
    ds[f"trough_ridge_index_{int(level)}"].attrs = {
        "long_name": f"Trough/Ridge Curvature Index ({level}hPa)",
        "units": "m / grid_cell^2",
        "description": "Laplacian of geopotential height. Positive values indicate cyclonic curvature (troughs).",
        "method": "Discrete Laplacian (d2z/dx2 + d2z/dy2) using np.gradient",
        "source_variables": "gh_isobaric_m",
        "scientific_interpretation": "Mide la curvatura del campo de geopotencial. Valores positivos (NH) indican vaguadas o depresiones en altura; negativos indican dorsales.",
        "limitations": "Calculado en espacio de rejilla (no físico). No considera la convergencia de meridianos ni la deformación por latitud.",
        "warning": "EXPLORATORY PRODUCT"
    }
    
    return ds

def calculate_temperature_gradient(ds: xr.Dataset, level: float = 850.0) -> xr.Dataset:
    """
    Calcula el gradiente horizontal de temperatura para identificar zonas baroclínicas.
    """
    if "t_isobaric_c" not in ds or level not in ds.level_hpa:
        return ds
        
    t = ds.t_isobaric_c.sel(level_hpa=level)
    
    def horizontal_gradient(data_2d):
        gy, gx = np.gradient(data_2d)
        return np.sqrt(gx**2 + gy**2)

    grad = xr.apply_ufunc(
        horizontal_gradient, t,
        input_core_dims=[["y", "x"]], output_core_dims=[["y", "x"]],
        vectorize=True, dask="parallelized"
    )
    
    ds[f"t_gradient_{int(level)}_index"] = grad
    ds[f"t_gradient_{int(level)}_index"].attrs = {
        "long_name": f"Temperature Horizontal Gradient ({level}hPa)",
        "units": "degC / grid_cell",
        "description": "Magnitude of horizontal temperature gradient. Higher values indicate baroclinic zones.",
        "method": "Magnitude of 2D gradient using np.gradient",
        "source_variables": "t_isobaric_c",
        "scientific_interpretation": "Identifica zonas de transición entre masas de aire (frentes), fundamentales para la ciclogénesis y frontogénesis.",
        "limitations": "Dependiente de la resolución de rejilla (DX, DY). El valor absoluto varía según la distancia entre puntos de malla.",
        "warning": "EXPLORATORY PRODUCT"
    }
    
    return ds
