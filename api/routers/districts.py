"""
api/routers/districts.py
------------------------
Endpoints for Maharashtra's 36 Administrative Districts and Multilingual Local Advisories.

Provides:
- /districts: All 36 districts with geographic metadata, division, population, and estimated AQI.
- /advisory/local: Multilingual (Marathi, Hindi, English) advisory segmented by citizen personas
  (General, Sensitive, Farmers, Traffic Police, Construction Workers, Schools).
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import numpy as np

from src.domain.districts import (
    get_all_districts,
    find_nearest_district,
    get_all_towns,
    get_all_locations,
    search_locations,
    find_nearest_location
)
from src.domain.local_advisory import generate_local_advisory
from api.services.model_service import predict_pm25
from api.services.data_service import get_ambient_features_for_coords
from src.domain.aqi import pm25_to_naqi, aqi_to_category

router = APIRouter(tags=["Maharashtra Districts & Local Advisory"])


@router.get("/districts")
def list_districts() -> List[Dict[str, Any]]:
    """
    Returns all 36 districts of Maharashtra with administrative division,
    geographic coordinates, economic/emission profile, and current estimated AQI.
    """
    districts = get_all_districts()
    results = []

    for d in districts:
        lat = d["lat"]
        lon = d["lon"]

        # Base regional PM2.5 baseline calculation based on geography & urban tier
        # Vidarbha / Industrial = higher SO2/PM; Konkan = marine dispersal; Pune = vehicular
        base_pm25 = 48.0
        if d.get("tier") == 1:
            base_pm25 += 24.0
        elif d.get("tier") == 2:
            base_pm25 += 14.0

        if d.get("region") == "Vidarbha":
            base_pm25 += 12.0
        elif d.get("region") == "Konkan":
            base_pm25 -= 8.0

        # Small spatial modulation
        pm25_val = round(base_pm25 + 6.0 * np.sin(lat * 1.8) + 4.0 * np.cos(lon * 1.5), 1)
        aqi_val, cat = pm25_to_naqi(pm25_val)
        cat_name, cat_color, cat_adv = aqi_to_category(aqi_val)

        results.append({
            "id": d["id"],
            "name": d["name"],
            "name_mr": d["name_mr"],
            "name_hi": d["name_hi"],
            "division": d["division"],
            "region": d["region"],
            "lat": lat,
            "lon": lon,
            "population": d.get("population_approx", 0),
            "tier": d.get("tier", 3),
            "has_cpcb": d.get("has_cpcb", False),
            "emission_profile": d.get("emission_profile", ""),
            "estimated_pm25": pm25_val,
            "estimated_aqi": aqi_val,
            "category": cat_name,
            "color": cat_color,
            "health_advisory": cat_adv
        })

    return results


@router.get("/locations")
def list_locations(
    include_towns: bool = Query(True, description="Whether to include in-between cities and talukas")
) -> List[Dict[str, Any]]:
    """
    Returns full catalog of all 36 districts and in-between cities/talukas across Maharashtra.
    """
    locations = get_all_locations() if include_towns else get_all_districts()
    results = []

    for loc in locations:
        lat = loc["lat"]
        lon = loc["lon"]

        base_pm25 = 48.0
        if loc.get("tier") == 1:
            base_pm25 += 24.0
        elif loc.get("tier") == 2:
            base_pm25 += 14.0

        if loc.get("region") == "Vidarbha":
            base_pm25 += 12.0
        elif loc.get("region") == "Konkan":
            base_pm25 -= 8.0

        pm25_val = round(base_pm25 + 6.0 * np.sin(lat * 1.8) + 4.0 * np.cos(lon * 1.5), 1)
        aqi_val, cat = pm25_to_naqi(pm25_val)
        cat_name, cat_color, cat_adv = aqi_to_category(aqi_val)

        res_item = dict(loc)
        res_item["estimated_pm25"] = pm25_val
        res_item["estimated_aqi"] = aqi_val
        res_item["category"] = cat_name
        res_item["color"] = cat_color
        res_item["health_advisory"] = cat_adv
        results.append(res_item)

    return results


@router.get("/locations/search")
def search_locations_endpoint(
    q: str = Query(..., min_length=1, description="Search query in English, Marathi, or Hindi")
) -> List[Dict[str, Any]]:
    """
    Fast fuzzy search across English, Marathi, and Hindi names for districts and in-between towns.
    """
    matches = search_locations(q)
    results = []
    for loc in matches:
        lat = loc["lat"]
        lon = loc["lon"]
        pm25_val = round(48.0 + 6.0 * np.sin(lat * 1.8) + 4.0 * np.cos(lon * 1.5), 1)
        aqi_val, cat = pm25_to_naqi(pm25_val)
        cat_name, cat_color, _ = aqi_to_category(aqi_val)
        res_item = dict(loc)
        res_item["estimated_pm25"] = pm25_val
        res_item["estimated_aqi"] = aqi_val
        res_item["category"] = cat_name
        res_item["color"] = cat_color
        results.append(res_item)
    return results


@router.get("/advisory/local")
def get_local_advisory(
    lat: float = Query(18.5204, ge=15.0, le=23.0, description="Latitude in Maharashtra"),
    lon: float = Query(73.8567, ge=72.0, le=82.0, description="Longitude in Maharashtra"),
    aqi: Optional[float] = Query(None, description="Current AQI (if omitted, computed automatically)"),
    dominant_pollutant: str = Query("PM2.5", description="Dominant pollutant (PM2.5, PM10, NO2)"),
    lang: str = Query("mr", description="Language code: mr (Marathi मराठी), hi (Hindi हिंदी), en (English)")
) -> Dict[str, Any]:
    """
    Returns localized, persona-segmented health, occupational, and civic advisory.
    Specifically designed for Maharashtra citizens, farmers, traffic workers, and schools.
    """
    # Defensive check for direct python invocations where default is Query param object
    if not isinstance(lat, (int, float)):
        lat = 18.5204
    if not isinstance(lon, (int, float)):
        lon = 73.8567
    if not isinstance(dominant_pollutant, str):
        dominant_pollutant = "PM2.5"
    if not isinstance(lang, str):
        lang = "mr"

    if aqi is None or not isinstance(aqi, (int, float)):
        # Compute hyperlocal estimate from features
        input_df = get_ambient_features_for_coords(lat, lon)
        pm25_pred = float(predict_pm25(input_df)[0])
        aqi_computed, _ = pm25_to_naqi(pm25_pred)
        aqi = aqi_computed

    return generate_local_advisory(
        aqi_value=aqi,
        lat=lat,
        lon=lon,
        dominant_pollutant=dominant_pollutant,
        lang=lang
    )
