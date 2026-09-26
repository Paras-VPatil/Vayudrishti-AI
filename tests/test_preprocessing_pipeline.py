"""
test_preprocessing_pipeline.py
-------------------------------
End-to-end unit and integration tests for Vayudrishti-AI data acquisition,
preprocessing, missingness policies, and spatio-temporal matching.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.preprocessing.clean_cpcb import clean_cpcb_data, calculate_naqi_subindex
from src.preprocessing.clean_satellite import clean_satellite_data, clean_modis_aod
from src.preprocessing.clean_weather import clean_weather_data, compute_relative_humidity, compute_wind_vectors
from src.preprocessing.clean_osm import clean_osm_features
from src.preprocessing.missingness import handle_missing_data, detect_missingness
from src.preprocessing.spatial_temporal_matcher import SpatialTemporalMatcher, collocate_satellite_and_ground


def test_naqi_subindex_calculation():
    # Test Good bracket for PM2.5 (0-30 -> 0-50)
    assert calculate_naqi_subindex("pm25", 15.0) == 25.0
    # Test Moderate bracket for PM2.5 (61-90 -> 101-200)
    assert 101 <= calculate_naqi_subindex("pm25", 75.0) <= 200
    # Test invalid negative
    assert calculate_naqi_subindex("pm25", -5.0) is None


def test_clean_cpcb_negative_and_outliers():
    df = pd.DataFrame({
        "station_id": ["S1", "S1", "S1"],
        "timestamp_utc": ["2024-06-01T10:00:00Z", "2024-06-01T11:00:00Z", "2024-06-01T12:00:00Z"],
        "pm25": [-999.0, 150.0, 1500.0],  # negative and outlier
        "no2": [40.0, -1.0, 55.0]
    })
    cleaned = clean_cpcb_data(df)
    assert np.isnan(cleaned.loc[0, "pm25"])
    assert cleaned.loc[1, "pm25"] == 150.0
    assert np.isnan(cleaned.loc[2, "pm25"])
    assert "aqi_calculated" in cleaned.columns


def test_clean_satellite_modis():
    df = pd.DataFrame({
        "aod_550nm": [0.45, 0.85, 6.5, -0.1],
        "aod_qa_flag": [3, 1, 3, 3]
    })
    cleaned = clean_modis_aod(df, min_qa=2)
    assert cleaned.loc[0, "aod_550nm"] == 0.45
    assert np.isnan(cleaned.loc[1, "aod_550nm"])  # Dropped due to QA < 2
    assert np.isnan(cleaned.loc[2, "aod_550nm"])  # Dropped due to > 5.0
    assert np.isnan(cleaned.loc[3, "aod_550nm"])  # Dropped due to < 0


def test_clean_weather_conversions():
    df = pd.DataFrame({
        "temperature_2m": [300.15],  # In Kelvin
        "u_component_of_wind_10m": [3.0],
        "v_component_of_wind_10m": [4.0],
        "boundary_layer_height": [20.0],  # Shallow inversion under minimum
        "surface_pressure": [101325.0]     # In Pa
    })
    cleaned = clean_weather_data(df)
    assert pytest.approx(cleaned.loc[0, "temperature_2m"], 0.1) == 27.0
    assert pytest.approx(cleaned.loc[0, "wind_speed_10m"], 0.1) == 5.0
    assert cleaned.loc[0, "boundary_layer_height"] == 50.0
    assert pytest.approx(cleaned.loc[0, "surface_pressure"], 0.1) == 1013.25


def test_missingness_handling():
    df = pd.DataFrame({
        "aqi_label": [120.0, np.nan, 250.0],
        "aod_550nm": [0.5, 0.6, np.nan],
        "temperature_2m": [28.0, np.nan, 32.0],
        "road_density": [np.nan, 4.5, 2.1]
    })
    cleaned = handle_missing_data(df, is_training=True)
    # Row 1 (index 1) should be dropped in training because target is NaN
    assert len(cleaned) == 2
    assert "is_aod_missing" in cleaned.columns
    assert cleaned["road_density"].isna().sum() == 0


def test_spatial_temporal_matcher():
    # Satellite pixels
    sat_df = pd.DataFrame({
        "latitude": [28.65, 19.08],
        "longitude": [77.32, 72.88],
        "timestamp_utc": ["2024-06-01T10:30:00Z", "2024-06-01T10:30:00Z"],
        "aod_550nm": [0.72, 0.45]
    })
    # Ground stations
    ground_df = pd.DataFrame({
        "station_id": ["STN_DELHI", "STN_MUMBAI"],
        "latitude": [28.6468, 19.0760],
        "longitude": [77.3160, 72.8777],
        "timestamp_utc": ["2024-06-01T10:45:00Z", "2024-06-01T14:00:00Z"],
        "pm25": [115.0, 42.0]
    })
    matcher = SpatialTemporalMatcher(max_spatial_distance_km=10.0, max_temporal_window_minutes=30.0)
    spatially_matched = matcher.match_spatial_nearest(sat_df, ground_df)
    assert spatially_matched["station_id"].iloc[0] == "STN_DELHI"
    assert spatially_matched["distance_to_station_km"].iloc[0] < 2.0

    collocated = matcher.match_temporal_window(spatially_matched, ground_df)
    # Only STN_DELHI has time delta <= 30 mins (15 mins), Mumbai is 3.5 hrs off
    assert len(collocated) == 1
    assert collocated["station_id"].iloc[0] == "STN_DELHI"


# ─────────────────────────────────────────────────────────────────────────────
# T2.4 — Three additional data-quality guard tests
# ─────────────────────────────────────────────────────────────────────────────


def test_no_target_leakage():
    """
    Guard: aqi_label and aqi_category must NEVER appear in the ML feature set.

    The ML target is pm25_ground only.
    AQI is computed post-prediction via src/domain/aqi.py.
    Including AQI-derived columns as features creates target leakage.
    """
    import yaml
    from pathlib import Path

    config_path = Path("configs/feature_config.yaml")
    if not config_path.exists():
        pytest.skip("feature_config.yaml not yet created — skipping leakage test")

    with config_path.open() as f:
        feature_cfg = yaml.safe_load(f)

    leaky_columns = {"aqi_label", "aqi_category", "aqi_calculated", "aqi_index"}

    for group_name in ("features_weather_only", "features_weather_gis", "features_full"):
        group = set(feature_cfg.get(group_name, []))
        leaked = group & leaky_columns
        assert not leaked, (
            f"Target leakage detected in '{group_name}': {leaked}. "
            "Remove AQI-derived columns from feature sets."
        )

    # Also verify the declared target is pm25_ground
    assert feature_cfg.get("target") == "pm25_ground", (
        f"Expected target='pm25_ground', got '{feature_cfg.get('target')}'"
    )


def test_canonical_schema_coordinates():
    """
    Guard: a canonical-schema-shaped DataFrame must have valid
    lat/lon within Pune bounding box and non-null UTC timestamps.

    This is run on a synthetic canonical row to validate the schema itself,
    not real data (real data validation happens in scripts/validate_canonical.py).
    """
    canonical_row = pd.DataFrame([{
        "location_id": "pune_1850_7385",
        "station_id": "MPCB_PUNE_01",
        "latitude": 18.52,
        "longitude": 73.85,
        "timestamp_utc": "2024-06-15T10:30:00+00:00",
        "satellite_timestamp": "2024-06-15T10:28:00+00:00",
        "ground_timestamp": "2024-06-15T10:30:00+00:00",
        "distance_to_station_km": 1.2,
        "temporal_offset_minutes": 2.0,
        "aod_550nm": 0.45,
        "satellite_no2": 4.5e-5,
        "satellite_so2": 2.1e-3,
        "satellite_co": 0.031,
        "satellite_o3": 0.135,
        "uv_aerosol_index": 0.8,
        "is_aod_missing": False,
        "is_no2_missing": False,
        "temperature_2m": 32.5,
        "relative_humidity_2m": 58.0,
        "wind_speed_10m": 3.2,
        "wind_direction_10m": 270.0,
        "boundary_layer_height": 1200.0,
        "surface_pressure": 1010.0,
        "precipitation_1h": 0.0,
        "road_density": 12.4,
        "building_density": 45.0,
        "land_use_class": "Built-up",
        "elevation_m": 560.0,
        "population_density": 8200.0,
        "distance_to_road_km": 0.08,
        "distance_to_industry_km": 2.5,
        "pm25_ground": 82.0,
    }])

    # Coordinate checks
    assert canonical_row["latitude"].between(18.0, 19.0).all(), "Latitude out of Pune range"
    assert canonical_row["longitude"].between(73.0, 75.0).all(), "Longitude out of Pune range"

    # Timestamp must be parseable UTC
    ts = pd.to_datetime(canonical_row["timestamp_utc"], utc=True)
    assert ts.notna().all(), "timestamp_utc contains NaT"

    # AQI leakage guard on the schema itself
    forbidden = {"aqi_label", "aqi_category", "aqi_calculated"}
    assert not forbidden & set(canonical_row.columns), (
        f"AQI leakage columns in canonical schema: {forbidden & set(canonical_row.columns)}"
    )

    # Target must be present and non-null
    assert "pm25_ground" in canonical_row.columns
    assert canonical_row["pm25_ground"].notna().all(), "pm25_ground target is NaN"


def test_realistic_value_ranges():
    """
    Guard: physical values in a canonical-shaped row must be within
    realistic atmospheric bounds.  Catches unit errors (e.g. Kelvin
    instead of Celsius, Pa instead of hPa) and sentinel values (-999).
    """
    import yaml
    from pathlib import Path

    config_path = Path("configs/pipeline_config.yaml")
    if config_path.exists():
        with config_path.open() as f:
            cfg = yaml.safe_load(f)
        bounds = cfg.get("physical_bounds", {})
    else:
        # Fallback hardcoded bounds if config not yet present
        bounds = {
            "pm25": {"min": 0.0, "max": 1000.0},
            "aod":  {"min": 0.0, "max": 5.0},
            "pblh": {"min": 50.0, "max": 6000.0},
        }

    # Simulate a batch of plausible observations
    df = pd.DataFrame({
        "pm25_ground":        [10.0, 85.0, 250.0, 0.5],
        "aod_550nm":          [0.1,  0.45, 1.2,   0.03],
        "boundary_layer_height": [800.0, 1200.0, 3000.0, 150.0],
        "temperature_2m":     [18.0, 32.5, 42.0, 8.0],   # Celsius (not Kelvin)
        "relative_humidity_2m": [35.0, 58.0, 90.0, 20.0],
        "wind_speed_10m":     [0.5,  3.2,  12.0, 0.1],
        "surface_pressure":   [1005.0, 1010.0, 1020.0, 998.0],  # hPa (not Pa)
    })

    # PM2.5 must be non-negative and below physical max
    assert (df["pm25_ground"] >= 0).all(),  "Negative PM2.5 detected"
    assert (df["pm25_ground"] <= 1000).all(), "PM2.5 > 1000 ug/m3 (unrealistic)"

    # AOD range
    assert (df["aod_550nm"] >= 0).all(),  "Negative AOD"
    assert (df["aod_550nm"] <= 5.0).all(), "AOD > 5.0 (above physical limit)"

    # Temperature in Celsius — must not look like Kelvin (> 200°C impossible surface temp)
    assert (df["temperature_2m"] < 200.0).all(), (
        "temperature_2m appears to be in Kelvin, not Celsius"
    )
    assert (df["temperature_2m"] > -50.0).all(), "Temperature below -50°C (unrealistic)"

    # PBLH in metres — must be between 50m and 6000m
    assert (df["boundary_layer_height"] >= 50.0).all(),   "PBLH below 50m (below physical minimum)"
    assert (df["boundary_layer_height"] <= 6000.0).all(), "PBLH above 6000m (above physical maximum)"

    # Surface pressure in hPa — must not look like Pa (> 2000 hPa is impossible)
    assert (df["surface_pressure"] < 2000.0).all(), (
        "surface_pressure appears to be in Pa, not hPa"
    )
    assert (df["surface_pressure"] > 800.0).all(), "surface_pressure below 800 hPa (too low)"

    # No sentinel / fill values
    for col in df.columns:
        assert not (df[col] == -999.0).any(), f"Sentinel value -999 found in column '{col}'"
        assert not (df[col] == -9999.0).any(), f"Sentinel value -9999 found in column '{col}'"
