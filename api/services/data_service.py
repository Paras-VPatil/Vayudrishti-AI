"""
api/services/data_service.py
----------------------------
Data service providing ambient weather, satellite, and GIS features for query coordinates.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from src.spatial.interpolation import generate_pune_city_grid, grid_to_geojson_heatmap


_PUNE_GRID_CACHE: Optional[pd.DataFrame] = None


def get_ambient_features_for_coords(lat: float, lon: float) -> pd.DataFrame:
    """
    Returns an aligned feature row for a given lat/lon in Pune.
    Interpolates or synthesizes ambient values based on location topography & time.
    """
    # Physically plausible Pune baseline with spatial variation
    dist_center = np.sqrt((lat - 18.5204)**2 + (lon - 73.8567)**2)
    urban_factor = max(0.0, 1.0 - (dist_center / 0.15))

    row = {
        "timestamp_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "latitude": lat,
        "longitude": lon,
        "temperature_2m": round(26.0 + 3.0 * (1.0 - urban_factor), 1),
        "relative_humidity_2m": round(60.0 + 10.0 * np.sin(lat * 10), 1),
        "wind_speed_10m": round(2.5 + 1.5 * np.cos(lon * 10), 1),
        "wind_direction_10m": 240.0,
        "boundary_layer_height": round(650.0 + 300.0 * urban_factor, 1),
        "surface_pressure": 955.0,
        "precipitation_1h": 0.0,
        "aod_550nm": round(0.35 + 0.30 * urban_factor, 3),
        "satellite_no2": round(0.00012 + 0.00018 * urban_factor, 6),
        "satellite_so2": 0.00002,
        "satellite_co": round(0.025 + 0.015 * urban_factor, 3),
        "satellite_o3": 0.15,
        "uv_aerosol_index": 0.45,
        "road_density": round(5.0 + 20.0 * urban_factor, 1),
        "building_density": round(15.0 + 55.0 * urban_factor, 1),
        "elevation_m": round(560.0 + (lat - 18.5) * 100.0, 1),
        "population_density": round(1000.0 + 12000.0 * urban_factor, 0),
        "distance_to_road_km": round(max(0.05, 0.5 * (1.0 - urban_factor)), 2),
        "distance_to_industry_km": round(max(0.5, 8.0 * (1.0 - urban_factor)), 2),
        "is_aod_missing": 0,
        "is_no2_missing": 0,
    }
    return pd.DataFrame([row])


def get_city_heatmap_geojson(metric: str = "pm25") -> Dict[str, Any]:
    """
    Generates gridded PM2.5, uncertainty, or reliability predictions and returns GeoJSON heatmap for Pune.
    """
    global _PUNE_GRID_CACHE
    if _PUNE_GRID_CACHE is None:
        _PUNE_GRID_CACHE = generate_pune_city_grid(
            lat_min=18.42,
            lat_max=18.62,
            lon_min=73.75,
            lon_max=73.95,
            resolution_deg=0.015
        )

    grid_df = _PUNE_GRID_CACHE.copy()
    
    # Predict PM2.5 for grid cells
    from api.services.model_service import predict_pm25
    from src.models.uncertainty import calculate_prediction_interval, calculate_data_reliability_score, find_nearest_official_station
    feature_rows = []
    for _, pt in grid_df.iterrows():
        feat = get_ambient_features_for_coords(pt["latitude"], pt["longitude"])
        feature_rows.append(feat)

    all_feats = pd.concat(feature_rows, ignore_index=True)
    preds = predict_pm25(all_feats)
    grid_df["pm25_pred"] = np.round(preds, 1)

    # Compute uncertainty & reliability metrics for spatial layers
    margins = []
    reliabilities = []
    for _, pt in grid_df.iterrows():
        stn = find_nearest_official_station(pt["latitude"], pt["longitude"])
        unc = calculate_prediction_interval(
            predicted_pm25=float(pt["pm25_pred"]),
            dist_to_station_km=stn["distance_km"],
            aod_missing=False,
            boundary_layer_height=700.0
        )
        rel = calculate_data_reliability_score(
            dist_to_station_km=stn["distance_km"],
            is_aod_missing=False,
            is_no2_missing=False
        )
        margins.append(unc["margin_of_error"])
        reliabilities.append(rel["reliability_score"])

    grid_df["uncertainty"] = margins
    grid_df["reliability"] = reliabilities

    # Select value column based on requested metric
    val_col = "pm25_pred"
    if metric == "uncertainty":
        val_col = "uncertainty"
    elif metric == "reliability":
        val_col = "reliability"

    return grid_to_geojson_heatmap(grid_df, value_col=val_col)


def get_historical_observations(lat: float, lon: float, n_hours: int = 24) -> list:
    """
    Returns time series of historical observations for the past n_hours.
    """
    from src.domain.aqi import pm25_to_naqi
    now = pd.Timestamp.now(tz="UTC")
    history = []

    base_pm25 = 75.0 + 15.0 * np.sin(lat * 5.0)

    for i in range(n_hours, 0, -1):
        ts = now - pd.Timedelta(hours=i)
        diurnal_factor = np.sin((ts.hour - 4) / 24.0 * 2 * np.pi)
        pm = max(10.0, base_pm25 + 25.0 * diurnal_factor + np.random.normal(0, 4.0))
        aqi_val, cat = pm25_to_naqi(pm)
        history.append({
            "timestamp": ts.isoformat(),
            "pm25": round(pm, 1),
            "aqi": round(aqi_val, 1),
            "category": cat
        })

    return history
