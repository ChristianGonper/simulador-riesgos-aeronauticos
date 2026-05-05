import os
import xarray as xr
from click.testing import CliRunner
from simulador_wrf.cli import main

def test_cli_execution(synthetic_wrf_dataset, tmp_path):
    """Prueba la ejecución completa de la CLI con datos sintéticos."""
    # 1. Guardar dataset sintético en un archivo temporal
    input_path = tmp_path / "wrfout_test.nc"
    synthetic_wrf_dataset.to_netcdf(input_path)
    
    output_path = tmp_path / "output.nc"
    
    # 2. Ejecutar CLI
    runner = CliRunner()
    result = runner.invoke(main, ["normalizar", "--input", str(input_path), "--output", str(output_path)])
    
    assert result.exit_code == 0
    assert os.path.exists(output_path)
    
    # 3. Verificar contenido del archivo de salida
    ds_out = xr.open_dataset(output_path)
    assert "precip_total_mm" in ds_out
    assert "t2_c" in ds_out
    assert "pressure_hpa" in ds_out
    assert "jet_stream_mask" in ds_out
    assert ds_out.dims["time"] == 3

def test_map_generation(synthetic_wrf_dataset, tmp_path):
    """Prueba la generación de mapas desde la CLI."""
    # 1. Preparar dataset normalizado
    from simulador_wrf.io import normalize_dataset
    from simulador_wrf.normalization import process_wrf_dataset
    
    ds_norm = normalize_dataset(synthetic_wrf_dataset)
    ds_norm = process_wrf_dataset(ds_norm)
    
    input_path = tmp_path / "normalized.nc"
    ds_norm.to_netcdf(input_path)
    
    output_dir = tmp_path / "maps"
    
    # 2. Ejecutar CLI mapas
    runner = CliRunner()
    result = runner.invoke(main, ["mapas", "--input", str(input_path), "--output-dir", str(output_dir), "--time-index", "0"])
    
    assert result.exit_code == 0
    assert os.path.exists(output_dir)
    
    # 3. Verificar existencia de archivos PNG (al menos uno representativo)
    slp_map = output_dir / "slp_t0.png"
    assert os.path.exists(slp_map)
    assert os.path.getsize(slp_map) > 0
    
    # Verificar un riesgo
    risk_map = output_dir / "risk_icing_mask_t0.png"
    assert os.path.exists(risk_map)
    assert os.path.getsize(risk_map) > 0
