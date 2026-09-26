"""
api/routers/map.py
------------------
Spatial GeoJSON heatmap endpoint for mapping and frontend layers.
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from api.services.data_service import get_city_heatmap_geojson

router = APIRouter(tags=["Spatial Heatmap"])


@router.get("/map")
def get_map_layer(
    metric: str = Query("pm25", description="Layer metric: pm25, uncertainty, or reliability")
) -> Dict[str, Any]:
    """
    Returns GeoJSON FeatureCollection of interpolated PM2.5 or Uncertainty/Reliability grid cells across Pune.
    """
    return get_city_heatmap_geojson(metric=metric)
