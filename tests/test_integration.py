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
    result = runner.invoke(main, ["--input", str(input_path), "--output", str(output_path)])
    
    assert result.exit_code == 0
    assert os.path.exists(output_path)
    
    # 3. Verificar contenido del archivo de salida
    ds_out = xr.open_dataset(output_path)
    assert "precip_total_mm" in ds_out
    assert "t2_c" in ds_out
    assert "pressure_hpa" in ds_out
    assert "jet_stream_mask" in ds_out
    assert ds_out.dims["time"] == 3
