"""
tests/test_api.py
-----------------
API Integration Tests using FastAPI TestClient (Stage 15).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["model_loaded"] is True


def test_prediction_aqi_current():
    response = client.get("/aqi/current?lat=18.5204&lon=73.8567")
    assert response.status_code == 200
    data = response.json()
    assert "predicted_pm25" in data
    assert "predicted_aqi" in data
    assert 0 <= data["predicted_aqi"] <= 500
    assert data["category"] in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    assert data["color"].startswith("#")
    assert data["dominant_pollutant"] == "PM2.5"


def test_prediction_pm25_current():
    response = client.get("/pm25/current?lat=18.5204&lon=73.8567")
    assert response.status_code == 200
    data = response.json()
    assert "pm25" in data
    assert data["unit"] == "ug/m3"
    assert data["pm25"] >= 0


def test_forecast_endpoint():
    response = client.get("/forecast?lat=18.5204&lon=73.8567")
    assert response.status_code == 200
    data = response.json()
    assert "horizons" in data
    assert len(data["horizons"]) >= 4
    horizons = [pt["horizon_hours"] for pt in data["horizons"]]
    assert 1 in horizons
    assert 24 in horizons


def test_explain_endpoint():
    response = client.get("/explain?lat=18.5204&lon=73.8567")
    assert response.status_code == 200
    data = response.json()
    assert "top_drivers" in data
    assert len(data["top_drivers"]) > 0
    assert "narrative_explanation" in data
    assert len(data["narrative_explanation"]) > 10


def test_map_layer_endpoint():
    response = client.get("/map")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    first_feat = data["features"][0]
    assert first_feat["geometry"]["type"] == "Point"
    assert "value" in first_feat["properties"]


def test_historical_endpoint():
    response = client.get("/historical?lat=18.5204&lon=73.8567&hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) == 24
