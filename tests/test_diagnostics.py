import numpy as np
from simulador_wrf.io import normalize_dataset
from simulador_wrf.diagnostics import calculate_precipitation, calculate_precip_increment

def test_calculate_precipitation(synthetic_wrf_dataset):
    """Verifica el cálculo de precipitación total."""
    ds = normalize_dataset(synthetic_wrf_dataset)
    ds = calculate_precipitation(ds)
    
    expected = ds.RAINC + ds.RAINNC
    np.testing.assert_allclose(ds.precip_total_mm.values, expected.values)
    assert ds.precip_total_mm.attrs["units"] == "mm"

def test_calculate_precip_increment(synthetic_wrf_dataset):
    """Verifica el cálculo del incremento de precipitación."""
    ds = normalize_dataset(synthetic_wrf_dataset)
    ds = calculate_precipitation(ds)
    ds = calculate_precip_increment(ds)
    
    assert "precip_increment_mm" in ds
    assert ds.precip_increment_mm.isel(time=0).values.sum() == 0.0
    
    # El segundo incremento debe ser la diferencia
    expected_inc = ds.precip_total_mm.isel(time=1) - ds.precip_total_mm.isel(time=0)
    np.testing.assert_allclose(ds.precip_increment_mm.isel(time=1).values, expected_inc.values)
