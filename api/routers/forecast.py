"""
api/routers/forecast.py
-----------------------
Multi-horizon PM2.5 and AQI forecasting endpoint (+1h, +6h, +12h, +24h).
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone, timedelta

from api.schemas.response import ForecastResponse, ForecastHorizonPoint
from api.services.model_service import predict_forecast_horizons
from api.services.aqi_service import compute_aqi_from_pm25
from api.services.data_service import get_ambient_features_for_coords

router = APIRouter(tags=["Forecasting"])


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    lat: float = Query(18.5204, ge=18.0, le=19.5),
    lon: float = Query(73.8567, ge=73.0, le=75.0)
):
    """
    Returns multi-horizon (+1h, +6h, +12h, +24h) air quality forecast with AQI categories.
    """
    input_df = get_ambient_features_for_coords(lat, lon)
    horizons_preds = predict_forecast_horizons(input_df)

    now = datetime.now(timezone.utc)
    points = []

    for h, val in sorted(horizons_preds.items()):
        aqi_val, cat, color, _ = compute_aqi_from_pm25(val)
        target_time = (now + timedelta(hours=h)).isoformat()
        points.append(
            ForecastHorizonPoint(
                horizon_hours=h,
                predicted_pm25=round(val, 1),
                predicted_aqi=round(aqi_val, 1),
                category=cat,
                color=color,
                target_time=target_time
            )
        )

    return ForecastResponse(
        latitude=lat,
        longitude=lon,
        horizons=points,
        forecast_generated_at=now.isoformat()
    )
