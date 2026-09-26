"""
tests/test_forecasting_spatial.py
---------------------------------
Unit tests for Stage 12 (Forecasting), Stage 13 (SHAP Explainability), and Stage 14 (Spatial Interpolation).
"""

import pytest
import numpy as np
import pandas as pd
import xgboost as xgb

from src.features.sliding_window import create_sliding_window_dataset, compute_persistence_baseline
from src.spatial.interpolation import idw_interpolate, generate_pune_city_grid, grid_to_geojson_heatmap
from src.explainability.explain import ModelExplainer, generate_human_explanation


@pytest.fixture
def time_series_df():
    np.random.seed(42)
    n = 60
    df = pd.DataFrame({
        "timestamp_utc": pd.date_range("2024-01-01", periods=n, freq="h"),
        "station_id": ["station_01"] * 30 + ["station_02"] * 30,
        "pm25_ground": np.random.uniform(20.0, 150.0, size=n),
    })
    return df


def test_sliding_window_lags(time_series_df):
    windowed = create_sliding_window_dataset(
        time_series_df,
        target_col="pm25_ground",
        station_col="station_id",
        timestamp_col="timestamp_utc",
        lags=[1, 2, 3],
        horizons=[1, 6]
    )
    assert "pm25_ground_lag_1h" in windowed.columns
    assert "pm25_ground_lag_2h" in windowed.columns
    assert "target_lead_1h" in windowed.columns
    assert "target_lead_6h" in windowed.columns
    assert len(windowed) > 0


def test_persistence_baseline(time_series_df):
    windowed = create_sliding_window_dataset(
        time_series_df,
        lags=[1],
        horizons=[1]
    )
    mae, rmse = compute_persistence_baseline(windowed, target_col="pm25_ground", horizon=1)
    assert mae > 0
    assert rmse >= mae


def test_idw_interpolation():
    known_coords = np.array([[18.5, 73.8], [18.6, 73.9]])
    known_values = np.array([50.0, 100.0])
    query_coords = np.array([[18.5, 73.8], [18.55, 73.85]])

    interp = idw_interpolate(known_coords, known_values, query_coords)
    assert len(interp) == 2
    # Exact collocation should yield value very close to known point
    assert np.isclose(interp[0], 50.0, atol=1.0)
    # Midpoint should be between the two values
    assert 50.0 < interp[1] < 100.0


def test_pune_city_grid():
    grid = generate_pune_city_grid(lat_min=18.40, lat_max=18.60, lon_min=73.70, lon_max=73.90, resolution_deg=0.1)
    assert len(grid) > 0
    assert "latitude" in grid.columns
    assert "longitude" in grid.columns

    geojson = grid_to_geojson_heatmap(grid)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == len(grid)


def test_explainability_human_narrative():
    narrative = generate_human_explanation(
        predicted_pm25=125.4,
        base_value=60.0,
        top_drivers=[
            {"driver": "optical aerosol density", "shap_value": 35.2},
            {"driver": "inversion layer trapping", "shap_value": 18.1}
        ]
    )
    assert "125.4 ug/m3" in narrative
    assert "POOR" in narrative or "VERY POOR" in narrative
    assert "Optical aerosol density" in narrative
