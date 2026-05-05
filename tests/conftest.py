import pytest
import xarray as xr
import numpy as np
import pandas as pd

@pytest.fixture
def synthetic_wrf_dataset():
    """Crea un dataset xarray sintético con la estructura mínima de WRF."""
    times = pd.date_range("2009-12-16", periods=3, freq="h")
    y = np.arange(10)
    x = np.arange(10)
    level = np.arange(5)
    
    # Dimensiones escalonadas
    np.arange(11)
    np.arange(11)
    np.arange(6)
    
    ds = xr.Dataset(
        data_vars={
            "T2": (("Time", "south_north", "west_east"), np.random.rand(3, 10, 10).astype(np.float32) + 290),
            "T": (("Time", "bottom_top", "south_north", "west_east"), np.random.rand(3, 5, 10, 10).astype(np.float32) * 2),
            "U": (("Time", "bottom_top", "south_north", "west_east_stag"), np.random.rand(3, 5, 10, 11).astype(np.float32)),
            "V": (("Time", "bottom_top", "south_north_stag", "west_east"), np.random.rand(3, 5, 11, 10).astype(np.float32)),
            "W": (("Time", "bottom_top_stag", "south_north", "west_east"), np.random.rand(3, 6, 10, 10).astype(np.float32)),
            "PH": (("Time", "bottom_top_stag", "south_north", "west_east"), np.random.rand(3, 6, 10, 10).astype(np.float32) * 100),
            "PHB": (("Time", "bottom_top_stag", "south_north", "west_east"), np.random.rand(3, 6, 10, 10).astype(np.float32) * 1000),
            "P": (("Time", "bottom_top", "south_north", "west_east"), np.random.rand(3, 5, 10, 10).astype(np.float32) * 10),
            "PB": (("Time", "bottom_top", "south_north", "west_east"), np.random.rand(3, 5, 10, 10).astype(np.float32) * 100000),
            "RAINC": (("Time", "south_north", "west_east"), np.cumsum(np.random.rand(3, 10, 10).astype(np.float32), axis=0)),
            "RAINNC": (("Time", "south_north", "west_east"), np.cumsum(np.random.rand(3, 10, 10).astype(np.float32), axis=0)),
            "XLAT": (("south_north", "west_east"), np.random.rand(10, 10).astype(np.float32) + 40),
            "XLONG": (("south_north", "west_east"), np.random.rand(10, 10).astype(np.float32) - 3),
            "PSFC": (("Time", "south_north", "west_east"), np.random.rand(3, 10, 10).astype(np.float32) * 1000 + 100000),
            "U10": (("Time", "south_north", "west_east"), np.random.rand(3, 10, 10).astype(np.float32) * 5),
            "V10": (("Time", "south_north", "west_east"), np.random.rand(3, 10, 10).astype(np.float32) * 5),
            "HGT": (("south_north", "west_east"), np.random.rand(10, 10).astype(np.float32) * 500),
            "QVAPOR": (("Time", "bottom_top", "south_north", "west_east"), np.random.rand(3, 5, 10, 10).astype(np.float32) * 0.01),
            "Times": (("Time",), times.strftime("%Y-%m-%d_%H:%M:%S").values.astype("S19")),
        },
        coords={
            "bottom_top": level,
            "south_north": y,
            "west_east": x,
        },
        attrs={
            "TITLE": " OUTPUT FROM WRF V3.1.1 MODEL",
            "DX": 1000.0,
            "DY": 1000.0,
            "MAP_PROJ": 1,
            "TRUELAT1": 30.0,
            "TRUELAT2": 60.0,
            "STAND_LON": -3.0,
            "CEN_LAT": 40.0,
            "CEN_LON": -3.0,
            "WEST-EAST_GRID_DIMENSION": 11,
            "SOUTH-NORTH_GRID_DIMENSION": 11,
            "BOTTOM-TOP_GRID_DIMENSION": 6,
        }
    )
    return ds
