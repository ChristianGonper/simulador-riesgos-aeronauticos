import pytest
from simulador_wrf.io import validate_dataset, normalize_dataset

def test_normalize_dataset(synthetic_wrf_dataset):
    """Verifica que el dataset se normalice correctamente."""
    ds_norm = normalize_dataset(synthetic_wrf_dataset)
    
    assert "time" in ds_norm.dims
    assert "y" in ds_norm.dims
    assert "x" in ds_norm.dims
    assert "model_level" in ds_norm.dims
    assert "lat" in ds_norm.coords
    assert "lon" in ds_norm.coords
    
def test_validate_dataset_success(synthetic_wrf_dataset):
    """Verifica que un dataset válido pase la validación."""
    assert validate_dataset(synthetic_wrf_dataset) is True

def test_validate_dataset_missing_var(synthetic_wrf_dataset):
    """Verifica que falte una variable obligatoria falle la validación."""
    ds = synthetic_wrf_dataset.drop_vars("T2")
    with pytest.raises(ValueError, match="Variable obligatoria ausente: T2"):
        validate_dataset(ds)

def test_validate_dataset_dimensions(synthetic_wrf_dataset):
    """Verifica que las dimensiones sean correctas."""
    ds = synthetic_wrf_dataset.rename({"south_north": "y"})
    with pytest.raises(ValueError, match="Dimensión esperada ausente: south_north"):
        validate_dataset(ds)
