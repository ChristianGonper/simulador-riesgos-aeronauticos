from simulador_wrf.diagnostics import (
    detect_pressure_centers, 
    detect_troughs_ridges, 
    calculate_temperature_gradient
)
from simulador_wrf.normalization import process_wrf_dataset

def test_structural_diagnostics(synthetic_wrf_dataset):
    from simulador_wrf.io import normalize_dataset
    ds = normalize_dataset(synthetic_wrf_dataset)
    ds = process_wrf_dataset(ds)
    
    # 1. Centros de presión
    ds = detect_pressure_centers(ds, neighborhood_size=2)
    assert "low_centers_mask" in ds
    assert "high_centers_mask" in ds
    assert ds.low_centers_mask.attrs["warning"] == "EXPLORATORY PRODUCT"
    assert "method" in ds.low_centers_mask.attrs
    
    # 2. Vaguadas/Dorsales
    # Necesitamos niveles isobaricos
    ds = process_wrf_dataset(ds, levels=[500.0])
    ds = detect_troughs_ridges(ds, level=500.0)
    assert "trough_ridge_index_500" in ds
    assert ds.trough_ridge_index_500.attrs["units"] == "m / grid_cell^2"
    
    # 3. Gradiente térmico
    ds = calculate_temperature_gradient(ds, level=850.0)
    # Si 850 no estaba en levels, process_wrf_dataset no lo interpoló. 
    # Pero el fixture por defecto usa [850, 500, 300] si no se especifica.
    # Re-procesamos con 850
    ds = process_wrf_dataset(ds, levels=[850.0, 500.0])
    ds = calculate_temperature_gradient(ds, level=850.0)
    assert "t_gradient_850_index" in ds
    assert "degC / grid_cell" in ds.t_gradient_850_index.attrs["units"]

def test_aviation_risks_improved(synthetic_wrf_dataset):
    from simulador_wrf.io import normalize_dataset
    ds = normalize_dataset(synthetic_wrf_dataset)
    ds = process_wrf_dataset(ds)
    
    assert "icing_mask" in ds
    assert "turbulence_index" in ds
    assert "convection_proxy" in ds
    
    # Verificar que tienen metadatos de viento si son de viento
    assert ds.turbulence_index.attrs["scientific_interpretation"] != ""
    
    # Verificar trazabilidad de viento
    assert ds.wind_speed_isobaric_ms.attrs["wind_reference"] == "grid_relative"
    assert ds.u_ms.attrs["wind_reference"] == "grid_relative"

def test_icing_with_qvapor(synthetic_wrf_dataset):
    from simulador_wrf.io import normalize_dataset
    ds = normalize_dataset(synthetic_wrf_dataset)
    # Asegurar que tiene QVAPOR (el fixture ya lo tiene)
    assert "QVAPOR" in ds
    
    from simulador_wrf.diagnostics import calculate_icing_risk
    ds = process_wrf_dataset(ds)
    ds = calculate_icing_risk(ds)
    
    assert "icing_mask" in ds
    # Debería haber usado la estimación de RH si rh_isobaric no existía
