import os
import numpy as np
from click.testing import CliRunner
from simulador_wrf.cli import main
from simulador_wrf.airports import resolve_airport
from simulador_wrf.routes import calculate_great_circle_route, is_route_in_domain, sample_wrf_at_points

def test_resolve_airport():
    mad = resolve_airport("MAD")
    assert mad is not None
    assert mad.icao == "LEMD"
    
    lebl = resolve_airport("lebl")
    assert lebl is not None
    assert lebl.iata == "BCN"
    
    none = resolve_airport("NONEXISTENT")
    assert none is None

def test_great_circle():
    mad = resolve_airport("MAD")
    bcn = resolve_airport("BCN")
    
    points = calculate_great_circle_route(mad, bcn, n_points=10)
    assert len(points) == 10
    # Primer punto debe ser el origen
    assert np.allclose(points[0][0], mad.latitude)
    assert np.allclose(points[0][1], mad.longitude)
    # Último punto debe ser el destino
    assert np.allclose(points[-1][0], bcn.latitude)
    assert np.allclose(points[-1][1], bcn.longitude)
    # Distancia debe ser creciente
    distances = [p[2] for p in points]
    assert all(x < y for x, y in zip(distances, distances[1:]))

def test_route_sampling(synthetic_wrf_dataset):
    # Ajustar coordenadas del dataset sintético para que incluyan puntos de prueba
    # Usaremos puntos arbitrarios dentro del rango (40-41, -3 a -2)
    synthetic_wrf_dataset["XLAT"].values = np.linspace(40, 41, 100).reshape(10, 10)
    synthetic_wrf_dataset["XLONG"].values = np.linspace(-3, -2, 100).reshape(10, 10)
    
    # Crear un dataset normalizado mínimo
    from simulador_wrf.normalization import process_wrf_dataset
    from simulador_wrf.io import normalize_dataset
    ds_norm = normalize_dataset(synthetic_wrf_dataset)
    ds_norm = process_wrf_dataset(ds_norm)
    
    # Puntos de prueba dentro del dominio
    p1 = (40.2, -2.8, 0.0)
    p2 = (40.8, -2.2, 100.0)
    points = [p1, p2]
    
    assert is_route_in_domain(ds_norm, points)
    
    route_data = sample_wrf_at_points(ds_norm, points, level_hpa=300.0)
    assert len(route_data) == 2
    assert "t2_c" in route_data[0].data
    assert "t_isobaric_c" in route_data[0].data

def test_route_sampling_normalized_coords(synthetic_wrf_dataset):
    """Prueba que el muestreo funcione con coordenadas lat/lon normalizadas (P1)."""
    # Eliminar XLAT/XLONG y poner lat/lon
    lats = np.linspace(40, 41, 10).astype(np.float32)
    lons = np.linspace(-3, -2, 10).astype(np.float32)
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    ds = synthetic_wrf_dataset.drop_vars(["XLAT", "XLONG"])
    # Normalizar primero para tener dimensiones y nombres correctos
    from simulador_wrf.io import normalize_dataset
    from simulador_wrf.normalization import process_wrf_dataset
    ds = normalize_dataset(ds)
    
    # Asignar lat/lon (nombres normalizados)
    ds = ds.assign_coords(lat=(("y", "x"), lat2d), 
                          lon=(("y", "x"), lon2d))
    
    # Calcular diagnósticos
    ds = process_wrf_dataset(ds)
    
    p = [(40.5, -2.5, 0.0)]
    route_data = sample_wrf_at_points(ds, p, level_hpa=None)
    assert len(route_data) == 1
    assert "t2_c" in route_data[0].data

def test_domain_validation_distance():
    """Prueba la validación de dominio por distancia máxima (P2)."""
    import xarray as xr
    lats = np.linspace(40, 41, 10)
    lons = np.linspace(-3, -2, 10)
    lon2d, lat2d = np.meshgrid(lons, lats)
    ds = xr.Dataset(coords={"lat": (("y", "x"), lat2d), "lon": (("y", "x"), lon2d)})
    
    # Punto dentro de la envolvente pero lejos de cualquier celda (si la malla fuera muy gruesa)
    # Aquí simularemos un punto que está a 0.6 grados de distancia
    points = [(40.5, -1.4, 0.0)] # Lon -1.4 está fuera de [-3, -2]
    assert not is_route_in_domain(ds, points, max_dist_deg=0.5)
    
    # Punto cerca
    points_near = [(40.5, -2.5, 0.0)]
    assert is_route_in_domain(ds, points_near, max_dist_deg=0.5)

def test_cli_ruta(synthetic_wrf_dataset, tmp_path):
    # 1. Preparar dataset normalizado que cubra MAD y una zona cercana para que pase la validación
    # MAD: 40.47, -3.56
    # Vamos a forzar el dominio sintético a cubrir MAD y VLC
    # MAD (40.47, -3.56), VLC (39.48, -0.48)
    # Rango: Lat [39, 41], Lon [-4, 0]
    lats = np.linspace(39, 41, 10).astype(np.float32)
    lons = np.linspace(-4, 0, 10).astype(np.float32)
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    synthetic_wrf_dataset["XLAT"].values = lat2d
    synthetic_wrf_dataset["XLONG"].values = lon2d
    
    from simulador_wrf.normalization import process_wrf_dataset
    from simulador_wrf.io import normalize_dataset
    ds_norm = normalize_dataset(synthetic_wrf_dataset)
    ds_norm = process_wrf_dataset(ds_norm)
    
    input_path = tmp_path / "normalized_route.nc"
    ds_norm.to_netcdf(input_path)
    
    output_dir = tmp_path / "route_output"
    
    # 2. Ejecutar CLI ruta
    runner = CliRunner()
    # Usamos MAD y VLC (LEVC)
    result = runner.invoke(main, ["ruta", "--input", str(input_path), "--origin", "MAD", "--dest", "VLC", "--output-dir", str(output_dir)])
    
    assert result.exit_code == 0
    assert os.path.exists(output_dir)
    
    # 3. Verificar archivos generados
    prefix = "route_MAD_VLC_t0_300hpa"
    expected_files = [
        f"{prefix}.csv",
        f"{prefix}.md",
        f"{prefix}_map.png",
        f"{prefix}_wind_profile.png",
        f"{prefix}_temp_profile.png"
    ]
    
    for f in expected_files:
        path = output_dir / f
        assert path.exists(), f"El archivo {f} no fue generado."
        assert path.stat().st_size > 0, f"El archivo {f} está vacío."
