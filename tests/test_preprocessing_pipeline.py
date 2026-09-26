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
