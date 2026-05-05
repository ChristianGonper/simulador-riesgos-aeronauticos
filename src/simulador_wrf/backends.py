import xarray as xr
import logging

logger = logging.getLogger(__name__)

def get_wrf_backend(ds: xr.Dataset, backend_name: str = "auto"):
    """
    Detecta y devuelve el mejor backend disponible para diagnósticos WRF.
    """
    if backend_name == "auto" or backend_name == "xwrf":
        return XWrfBackend(ds, use_xwrf=True)
    elif backend_name == "xarray":
        return XWrfBackend(ds, use_xwrf=False)
    else:
        logger.warning(f"Backend {backend_name} no reconocido, usando auto.")
        return XWrfBackend(ds, use_xwrf=True)

class XWrfBackend:
    """
    Backend para diagnósticos meteorológicos.
    """
    def __init__(self, ds: xr.Dataset, use_xwrf: bool = True):
        self.ds = ds
        self.use_xwrf = use_xwrf
        
    def get_pressure(self):
        """Calcula presión 3D en hPa."""
        # P + PB es presión total en Pa
        if "P" in self.ds and "PB" in self.ds:
            p_hpa = (self.ds.P + self.ds.PB) / 100.0
            p_hpa.attrs = {"units": "hPa", "long_name": "Pressure"}
            return p_hpa
        return None

    def get_geopotential_height(self):
        """Calcula altura geopotencial en m en puntos de masa."""
        if "PH" in self.ds and "PHB" in self.ds:
            gh_staggered = (self.ds.PH + self.ds.PHB) / 9.81
            # Desescalonar de model_level_stag a model_level
            dim = "model_level_stag" if "model_level_stag" in gh_staggered.dims else "bottom_top_stag"
            gh_m = gh_staggered.rolling({dim: 2}).mean().dropna(dim)
            # Renombrar dimensión a la de masa
            target_dim = "model_level" if "model_level" in self.ds.dims else "bottom_top"
            gh_m = gh_m.rename({dim: target_dim})
            gh_m.attrs = {"units": "m", "long_name": "Geopotential Height"}
            return gh_m
        return None

    def get_slp(self):
        """Calcula la presión a nivel del mar (SLP) en hPa."""
        # Implementación de SLP siguiendo la fórmula barométrica estándar con lapse rate.
        # Limitación: No utiliza el perfil vertical de humedad ni correcciones de temperatura complejas
        # que implementa WRF o MetPy, por lo que es una aproximación exploratoria.
        if all(k in self.ds for k in ["T2", "PSFC", "HGT"]):
            R = 287.05
            g = 9.81
            gamma = 0.0065 # Lapse rate estándar K/m (ISA)
            
            psfc = self.ds.PSFC / 100.0 # Pa -> hPa
            t2 = self.ds.T2 # K
            hgt = self.ds.HGT # m
            
            # Reducción barométrica considerando el gradiente térmico (gamma):
            # P0 = Ps * (1 + gamma*H / T2)^(g / (R*gamma))
            slp = psfc * (1 + (gamma * hgt) / t2)**(g / (R * gamma))
            
            slp.attrs = {
                "units": "hPa", 
                "long_name": "Sea Level Pressure", 
                "method": "Barometric formula with constant lapse rate (gamma=0.0065 K/m)",
                "limitation": "Aproximación exploratoria, no considera perfil de humedad ni correcciones de mesoescala WRF."
            }
            return slp
        return None

    def get_temperature_c(self):
        """Calcula temperatura 3D en Celsius."""
        if "T" in self.ds and "P" in self.ds and "PB" in self.ds:
            p_total = self.ds.P + self.ds.PB
            # T es theta perturbada (theta - 300)
            theta = self.ds.T + 300.0
            t_k = theta * (p_total / 100000.0)**(287.05/1004.64)
            t_c = t_k - 273.15
            t_c.attrs = {"units": "degC", "long_name": "Temperature"}
            return t_c
        return None

    def get_destaggered_wind(self):
        """Desescalona U y V a la rejilla de masa."""
        # Usamos xWRF solo si el backend lo permite
        if self.use_xwrf:
            try:
                import xwrf  # noqa: F401
                ds_destag = self.ds.xwrf.destagger()
                return ds_destag.U, ds_destag.V
            except (ImportError, AttributeError, Exception) as e:
                logger.warning(f"Error al desescalonar con xWRF: {e}")
        
        # Fallback manual simple (promedio) o ruta xarray pura
        dim_u = "x_stag" if "x_stag" in self.ds.U.dims else "west_east_stag"
        dim_v = "y_stag" if "y_stag" in self.ds.V.dims else "south_north_stag"
        
        # Promedio entre puntos adyacentes
        u_mass = self.ds.U.rolling({dim_u: 2}).mean().dropna(dim_u)
        v_mass = self.ds.V.rolling({dim_v: 2}).mean().dropna(dim_v)
        
        # Reasignar nombres de dimensiones para que coincidan con la rejilla de masa
        target_u_dim = "x" if "x" in self.ds.dims else "west_east"
        target_v_dim = "y" if "y" in self.ds.dims else "south_north"
        
        u_mass = u_mass.rename({dim_u: target_u_dim})
        v_mass = v_mass.rename({dim_v: target_v_dim})
        
        return u_mass, v_mass
