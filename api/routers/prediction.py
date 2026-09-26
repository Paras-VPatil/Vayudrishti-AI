"""
api/routers/prediction.py
-------------------------
Real-time hyperlocal PM2.5 and India NAQI estimation endpoints with
uncertainty bounds, data reliability scoring, station comparison, and provenance.
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone
import pandas as pd

from api.schemas.response import CurrentAQIResponse, CurrentPM25Response, HistoricalResponse
from api.services.model_service import predict_pm25, predict_forecast_horizons
from api.services.aqi_service import compute_aqi_from_pm25
from api.services.data_service import get_ambient_features_for_coords, get_historical_observations
from src.models.uncertainty import (
    calculate_prediction_interval,
    calculate_data_reliability_score,
    compare_nearest_vs_hyperlocal,
    compute_optimal_outdoor_window,
    generate_prediction_provenance,
    find_nearest_official_station
)

router = APIRouter(tags=["Air Quality & Predictions"])


@router.get("/aqi/current", response_model=CurrentAQIResponse)
def get_current_aqi(
    lat: float = Query(18.5204, ge=18.0, le=19.5, description="Latitude (Pune region)"),
    lon: float = Query(73.8567, ge=73.0, le=75.0, description="Longitude (Pune region)")
):
    """
    Computes real-time fused PM2.5 concentration, India NAQI index,
    prediction uncertainty bounds (90% CI), data reliability score,
    nearest official station microclimate delta, and provenance.
    """
    input_df = get_ambient_features_for_coords(lat, lon)
    pm25_pred = float(predict_pm25(input_df)[0])
    aqi_val, cat, color, adv = compute_aqi_from_pm25(pm25_pred)

    # 1. Station proximity
    nearest_stn = find_nearest_official_station(lat, lon)
    dist_km = nearest_stn["distance_km"]

    # 2. Uncertainty bounds
    uncertainty_dict = calculate_prediction_interval(
        predicted_pm25=pm25_pred,
        dist_to_station_km=dist_km,
        aod_missing=bool(input_df.get("is_aod_missing", [0])[0]),
        boundary_layer_height=float(input_df.get("boundary_layer_height", [800.0])[0])
    )

    # 3. Data reliability score
    reliability_dict = calculate_data_reliability_score(
        dist_to_station_km=dist_km,
        is_aod_missing=bool(input_df.get("is_aod_missing", [0])[0]),
        is_no2_missing=bool(input_df.get("is_no2_missing", [0])[0])
    )

    # 4. Nearest station blind-spot comparison
    comparison_dict = compare_nearest_vs_hyperlocal(
        predicted_pm25=pm25_pred,
        lat=lat,
        lon=lon
    )

    # 5. Outdoor advisor
    forecast_horizons = predict_forecast_horizons(input_df)
    fc_list = []
    for h, val in forecast_horizons.items():
        _, h_cat, _, _ = compute_aqi_from_pm25(val)
        fc_list.append({"horizon_hours": h, "predicted_pm25": val, "category": h_cat})
    advisor_dict = compute_optimal_outdoor_window(fc_list)

    # 6. Provenance
    provenance_dict = generate_prediction_provenance(lat, lon)

    return CurrentAQIResponse(
        latitude=lat,
        longitude=lon,
        predicted_pm25=round(pm25_pred, 1),
        predicted_aqi=round(aqi_val, 1),
        category=cat,
        color=color,
        dominant_pollutant="PM2.5",
        health_advisory=adv,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uncertainty=uncertainty_dict,
        data_reliability=reliability_dict,
        station_comparison=comparison_dict,
        outdoor_advisor=advisor_dict,
        provenance=provenance_dict
    )


@router.get("/pm25/current", response_model=CurrentPM25Response)
def get_current_pm25(
    lat: float = Query(18.5204, ge=18.0, le=19.5),
    lon: float = Query(73.8567, ge=73.0, le=75.0)
):
    """
    Returns standalone surface PM2.5 prediction value with uncertainty intervals.
    """
    input_df = get_ambient_features_for_coords(lat, lon)
    pm25_pred = float(predict_pm25(input_df)[0])
    nearest_stn = find_nearest_official_station(lat, lon)
    uncertainty_dict = calculate_prediction_interval(
        predicted_pm25=pm25_pred,
        dist_to_station_km=nearest_stn["distance_km"]
    )

    return CurrentPM25Response(
        latitude=lat,
        longitude=lon,
        pm25=round(pm25_pred, 1),
        unit="ug/m3",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uncertainty=uncertainty_dict
    )


@router.get("/historical", response_model=HistoricalResponse)
def get_historical(
    lat: float = Query(18.5204, ge=18.0, le=19.5),
    lon: float = Query(73.8567, ge=73.0, le=75.0),
    hours: int = Query(24, ge=6, le=168)
):
    """
    Returns historical 24-hour time series of PM2.5 and AQI observations.
    """
    history = get_historical_observations(lat, lon, n_hours=hours)
    return HistoricalResponse(
        latitude=lat,
        longitude=lon,
        station_id="PUNE_HYPERLOCAL_GRID",
        history=history
    )
