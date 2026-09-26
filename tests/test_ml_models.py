"""
tests/test_ml_models.py
-----------------------
Unit and integration tests for Stage 9 (Baseline ML) and Stage 10 (Ablation).
"""

import os
import pytest
import numpy as np
import pandas as pd
import xgboost as xgb

from src.models.cv_splitters import temporal_train_test_split, spatial_group_kfold
from src.domain.aqi import pm25_to_naqi
from src.features.feature_engineer import FeatureEngineer


@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "timestamp_utc": pd.date_range("2024-01-01", periods=n, freq="h"),
        "station_id": np.random.choice(["station_A", "station_B", "station_C", "station_D"], size=n),
        "latitude": np.random.uniform(18.4, 18.6, size=n),
        "longitude": np.random.uniform(73.7, 74.0, size=n),
        "temperature_2m": np.random.uniform(20.0, 35.0, size=n),
        "relative_humidity_2m": np.random.uniform(30.0, 90.0, size=n),
        "wind_speed_10m": np.random.uniform(0.5, 10.0, size=n),
        "wind_direction_10m": np.random.uniform(0.0, 360.0, size=n),
        "boundary_layer_height": np.random.uniform(200.0, 2500.0, size=n),
        "surface_pressure": np.random.uniform(950.0, 1015.0, size=n),
        "precipitation_1h": np.random.uniform(0.0, 5.0, size=n),
        "aod_550nm": np.random.uniform(0.1, 1.5, size=n),
        "satellite_no2": np.random.uniform(1e-5, 5e-4, size=n),
        "satellite_so2": np.random.uniform(1e-5, 5e-4, size=n),
        "satellite_co": np.random.uniform(0.01, 0.05, size=n),
        "satellite_o3": np.random.uniform(0.1, 0.3, size=n),
        "road_density": np.random.uniform(1.0, 25.0, size=n),
        "building_density": np.random.uniform(5.0, 70.0, size=n),
        "elevation_m": np.random.uniform(500.0, 650.0, size=n),
        "population_density": np.random.uniform(100.0, 15000.0, size=n),
        "distance_to_road_km": np.random.uniform(0.01, 5.0, size=n),
        "distance_to_industry_km": np.random.uniform(0.1, 20.0, size=n),
        "pm25_ground": np.random.uniform(15.0, 250.0, size=n),
    })
    return df


def test_temporal_train_test_split(sample_data):
    train_df, test_df = temporal_train_test_split(sample_data, timestamp_col="timestamp_utc", test_ratio=0.2)
    assert len(train_df) == 80
    assert len(test_df) == 20
    # Strict temporal separation
    assert train_df["timestamp_utc"].max() < test_df["timestamp_utc"].min()


def test_spatial_group_kfold_no_leakage(sample_data):
    folds = list(spatial_group_kfold(sample_data, group_col="station_id", n_splits=3))
    assert len(folds) >= 2
    for tr_idx, val_idx in folds:
        tr_stations = set(sample_data.iloc[tr_idx]["station_id"])
        val_stations = set(sample_data.iloc[val_idx]["station_id"])
        # Crucial: No station present in both train and validation folds
        assert len(tr_stations.intersection(val_stations)) == 0


def test_feature_engineering_transforms(sample_data):
    fe = FeatureEngineer(feature_group="full")
    transformed = fe.fit_transform(sample_data)
    assert "hour_sin" in transformed.columns
    assert "hour_cos" in transformed.columns
    assert "wind_u" in transformed.columns
    assert "aod_pblh_ratio" in transformed.columns
    assert len(transformed) == len(sample_data)


def test_xgboost_model_save_and_load(tmp_path, sample_data):
    fe = FeatureEngineer(feature_group="full")
    X = fe.fit_transform(sample_data)
    y = sample_data["pm25_ground"]

    model = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)

    model_path = str(tmp_path / "model.json")
    model.save_model(model_path)
    assert os.path.exists(model_path)

    loaded_model = xgb.XGBRegressor()
    loaded_model.load_model(model_path)
    preds = loaded_model.predict(X)
    assert len(preds) == len(X)
    assert not np.isnan(preds).any()
