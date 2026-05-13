import numpy as np
from click.testing import CliRunner
from simulador_wrf.visualization import plot_hodograph
from simulador_wrf.normalization import process_wrf_dataset
from simulador_wrf.io import normalize_dataset
from simulador_wrf.cli import main

def test_plot_hodograph_missing_data(synthetic_wrf_dataset, tmp_path):
    ds = normalize_dataset(synthetic_wrf_dataset)
    # Sin niveles isobaricos
    output_path = tmp_path / "test_hodo_fail.png"
    res = plot_hodograph(ds, lat=40.5, lon=-3.5, time_index=0, output_path=output_path)
    assert res is None

def test_plot_hodograph_structure(synthetic_wrf_dataset, tmp_path):
    # Verificamos al menos que la lógica de selección no rompa
    ds = normalize_dataset(synthetic_wrf_dataset)
    # Solo normalizado, sin isobaricas
    res = plot_hodograph(ds, lat=40.5, lon=-3.5, time_index=0, output_path=tmp_path/"h.png")
    assert res is None

def test_cli_perfil_integration(synthetic_wrf_dataset, tmp_path):
    """Prueba de integración real del comando perfil en la CLI."""
    # Forzar coordenadas y niveles isobaricos para que el hodógrafo funcione
    lats = np.linspace(40, 41, 10)
    lons = np.linspace(-4, -3, 10)
    lon2d, lat2d = np.meshgrid(lons, lats)
    synthetic_wrf_dataset["XLAT"].values = lat2d
    synthetic_wrf_dataset["XLONG"].values = lon2d
    
    ds = normalize_dataset(synthetic_wrf_dataset)
    ds = process_wrf_dataset(ds, levels=[1000, 850, 500])
    
    input_path = tmp_path / "input.nc"
    ds.to_netcdf(input_path)
    output_path = tmp_path / "hodo.png"
    
    runner = CliRunner()
    # 1. Probar con lat/lon
    result = runner.invoke(main, [
        "perfil", 
        "-i", str(input_path), 
        "--lat", "40.5", 
        "--lon", "-3.5", 
        "-o", str(output_path)
    ])
    assert result.exit_code == 0
    assert output_path.exists()
    
    # 2. Probar con aeropuerto (MAD)
    output_path_mad = tmp_path / "hodo_mad.png"
    result = runner.invoke(main, [
        "perfil", 
        "-i", str(input_path), 
        "--airport", "MAD", 
        "-o", str(output_path_mad)
    ])
    assert result.exit_code == 0
    assert output_path_mad.exists()
