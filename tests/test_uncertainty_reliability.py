"""
tests/test_uncertainty_reliability.py
-------------------------------------
Unit tests for uncertainty quantification, data reliability scoring,
station comparison (blind spot disruption), and provenance tracking.
"""

import pytest
from src.models.uncertainty import (
    calculate_prediction_interval,
    calculate_data_reliability_score,
    find_nearest_official_station,
    compare_nearest_vs_hyperlocal,
    compute_optimal_outdoor_window,
    generate_prediction_provenance
)


def test_prediction_interval_bounds():
    interval = calculate_prediction_interval(
        predicted_pm25=85.0,
        dist_to_station_km=4.5,
        aod_missing=False,
        boundary_layer_height=900.0
    )
    assert interval["pm25_lower_bound"] < 85.0 < interval["pm25_upper_bound"]
    assert interval["margin_of_error"] > 0
    assert interval["confidence_level"] == 0.90
    assert interval["uncertainty_level"] in ["LOW", "MEDIUM", "HIGH"]


def test_prediction_interval_missing_satellite_penalty():
    # When satellite AOD is missing, uncertainty margin must expand
    nominal = calculate_prediction_interval(predicted_pm25=85.0, dist_to_station_km=5.0, aod_missing=False)
    degraded = calculate_prediction_interval(predicted_pm25=85.0, dist_to_station_km=5.0, aod_missing=True)
    assert degraded["margin_of_error"] > nominal["margin_of_error"]


def test_data_reliability_scoring():
    rel = calculate_data_reliability_score(
        dist_to_station_km=2.0,
        is_aod_missing=False,
        is_no2_missing=False
    )
    assert 80 <= rel["reliability_score"] <= 100
    assert rel["reliability_level"] == "HIGH"

    # Degraded score when distant and missing AOD
    rel_degraded = calculate_data_reliability_score(
        dist_to_station_km=25.0,
        is_aod_missing=True,
        is_no2_missing=True
    )
    assert rel_degraded["reliability_score"] < rel["reliability_score"]
    assert rel_degraded["reliability_level"] in ["MEDIUM", "LOW"]


def test_nearest_station_comparison():
    comp = compare_nearest_vs_hyperlocal(
        predicted_pm25=110.0,
        lat=18.5314,  # Exactly at Shivajinagar
        lon=73.8446
    )
    assert comp["nearest_station_name"] == "Shivajinagar (IMD)"
    assert comp["distance_to_station_km"] < 1.0
    assert "blind_spot_insight" in comp


def test_optimal_outdoor_window():
    horizons = [
        {"horizon_hours": 1, "predicted_pm25": 95.0, "category": "Moderate"},
        {"horizon_hours": 6, "predicted_pm25": 42.0, "category": "Satisfactory"},
        {"horizon_hours": 12, "predicted_pm25": 110.0, "category": "Poor"},
        {"horizon_hours": 24, "predicted_pm25": 88.0, "category": "Moderate"},
    ]
    advisor = compute_optimal_outdoor_window(horizons)
    assert advisor["lowest_predicted_pm25"] == 42.0
    assert "+6" in advisor["recommended_window"]
    assert advisor["peak_hazard_pm25"] == 110.0


def test_prediction_provenance():
    prov = generate_prediction_provenance(18.5204, 73.8567)
    assert prov["prediction_id"].startswith("VAYU-")
    assert prov["model_version"] == "v1.0.0-xgb-fusion"
    assert "Terra MODIS (MCD19A2 MAIAC)" in prov["satellite_sensors"]
    assert prov["target_leakage_guaranteed"] is True
