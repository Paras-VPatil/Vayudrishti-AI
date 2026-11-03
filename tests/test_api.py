"""
tests/test_api.py
-----------------
API Integration & Router Contract Tests.
Directly exercises route handlers and schema validations.
"""

import pytest
from api.routers.health import get_health
from api.routers.prediction import get_current_aqi, get_current_pm25, get_historical
from api.routers.forecast import get_forecast
from api.routers.explain import explain_prediction
from api.routers.map import get_map_layer, get_stations, get_layers, get_map_overlay_png
from api.routers.districts import list_districts, get_local_advisory, list_locations, search_locations_endpoint
from api.routers.research import get_research_metrics
from api.services.model_service import load_artifacts


@pytest.fixture(scope="session", autouse=True)
def init_models():
    load_artifacts()


def test_health_endpoint():
    res = get_health()
    data = res.model_dump()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["model_loaded"] is True
    assert data["forecaster_loaded"] is True
    assert "Maharashtra" in data["city"]


def test_prediction_aqi_current():
    res = get_current_aqi(lat=18.5204, lon=73.8567)
    data = res.model_dump()
    assert "predicted_pm25" in data
    assert "predicted_aqi" in data
    assert 0 <= data["predicted_aqi"] <= 500
    assert data["category"] in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    assert data["color"].startswith("#")
    assert data["dominant_pollutant"] == "PM2.5"
    assert "uncertainty" in data
    assert "data_reliability" in data


def test_prediction_pm25_current():
    res = get_current_pm25(lat=18.5204, lon=73.8567)
    data = res.model_dump()
    assert "pm25" in data
    assert data["unit"] == "ug/m3"
    assert data["pm25"] >= 0


def test_forecast_endpoint():
    res = get_forecast(lat=18.5204, lon=73.8567)
    data = res.model_dump()
    assert "horizons" in data
    assert len(data["horizons"]) >= 4
    horizons = [pt["horizon_hours"] for pt in data["horizons"]]
    assert 1 in horizons
    assert 24 in horizons


def test_explain_endpoint():
    res = explain_prediction(lat=18.5204, lon=73.8567)
    data = res.model_dump()
    assert "top_drivers" in data
    assert len(data["top_drivers"]) > 0
    assert "narrative_explanation" in data
    assert len(data["narrative_explanation"]) > 10


def test_map_layer_endpoint():
    data = get_map_layer(metric="pm25")
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    first_feat = data["features"][0]
    assert first_feat["geometry"]["type"] == "Point"
    assert "value" in first_feat["properties"]


def test_historical_endpoint():
    res = get_historical(lat=18.5204, lon=73.8567, hours=24)
    data = res.model_dump()
    assert "history" in data
    assert len(data["history"]) == 24


def test_stations_endpoint():
    stations = get_stations()
    assert len(stations) >= 20
    cities = {s["city"] for s in stations}
    assert "Pune" in cities
    assert "Mumbai" in cities
    assert "Nagpur" in cities
    assert "Nashik" in cities


def test_layers_endpoint():
    layers_meta = get_layers()
    assert layers_meta["region"] == "Maharashtra"
    assert "bounds" in layers_meta
    assert layers_meta["bounds"]["south"] == 15.60
    assert len(layers_meta["layers"]) >= 1


def test_map_overlay_png_endpoint():
    response = get_map_overlay_png(metric="aqi", lead=0)
    assert response.status_code == 200
    assert response.media_type == "image/png"
    assert len(response.body) > 1000  # Valid PNG byte array


def test_mumbai_prediction():
    # Verify non-Pune coordinate query (Mumbai BKC)
    res = get_current_aqi(lat=19.0662, lon=72.8687)
    data = res.model_dump()
    assert data["predicted_aqi"] >= 0
    assert "BKC" in data["station_comparison"]["nearest_station_name"] or "Mumbai" in data["station_comparison"]["nearest_station_name"]


def test_districts_catalog_endpoint():
    districts = list_districts()
    assert len(districts) == 36
    d_names = {d["name"] for d in districts}
    assert "Pune" in d_names
    assert "Mumbai City" in d_names
    assert "Nagpur" in d_names
    assert "Gadchiroli" in d_names
    assert "Nanded" in d_names
    for d in districts:
        assert "name_mr" in d
        assert "name_hi" in d
        assert "division" in d
        assert 0 <= d["estimated_aqi"] <= 500


def test_local_advisory_multilingual():
    # Marathi advisory
    adv_mr = get_local_advisory(lat=18.5204, lon=73.8567, aqi=140.0, lang="mr")
    assert adv_mr["language"] == "mr"
    assert "district" in adv_mr
    assert adv_mr["district"]["name"] == "Pune"
    assert "personas" in adv_mr
    assert "farmer" in adv_mr["personas"]
    assert "traffic_worker" in adv_mr["personas"]

    # Hindi advisory
    adv_hi = get_local_advisory(lat=21.1458, lon=79.0882, aqi=180.0, lang="hi")
    assert adv_hi["language"] == "hi"
    assert adv_hi["district"]["name"] == "Nagpur"
    assert "किसान" in adv_hi["personas"]["farmer"]["title"]

    # English advisory
    adv_en = get_local_advisory(lat=19.0760, lon=72.8777, aqi=85.0, lang="en")
    assert adv_en["language"] == "en"
    assert "mask_recommendation" in adv_en


def test_research_metrics_endpoint():
    metrics = get_research_metrics()
    assert "framework_version" in metrics
    assert "cross_validation_matrix" in metrics
    assert len(metrics["cross_validation_matrix"]) == 4
    strategies = [m["strategy"] for m in metrics["cross_validation_matrix"]]
    assert any("Temporal" in s for s in strategies)
    assert any("Spatial" in s for s in strategies)
    assert any("Regional" in s for s in strategies)
    assert "feature_ablation_study" in metrics
    assert "conformal_calibration" in metrics
    assert "atmospheric_physics" in metrics


def test_locations_catalog_and_search():
    # 1. Full catalog of 36 districts + in-between towns
    all_locs = list_locations(include_towns=True)
    assert len(all_locs) >= 80
    names = {l["name"] for l in all_locs}
    assert "Lonavala" in names
    assert "Baramati" in names
    assert "Shirdi" in names
    assert "Karad" in names
    assert "Ichalkaranji" in names
    assert "Malegaon" in names
    assert "Bhusawal" in names
    assert "Chiplun" in names

    # 2. Search endpoint
    search_lon = search_locations_endpoint(q="Lonavala")
    assert len(search_lon) >= 1
    assert search_lon[0]["name"] == "Lonavala"

    # Search in Marathi
    search_mr = search_locations_endpoint(q="बारामती")
    assert len(search_mr) >= 1
    assert search_mr[0]["name"] == "Baramati"

