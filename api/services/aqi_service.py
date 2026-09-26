"""
api/services/aqi_service.py
---------------------------
Air Quality Index (NAQI) conversion service wrapping domain calculation rules.
"""

from typing import Dict, Any, Tuple
from src.domain.aqi import pm25_to_naqi, aqi_to_category, calculate_overall_aqi


def compute_aqi_from_pm25(pm25_val: float) -> Tuple[float, str, str, str]:
    """
    Returns (aqi_value, category, hex_color, health_advisory).
    """
    aqi_val, cat = pm25_to_naqi(pm25_val)
    cat_name, color, adv = aqi_to_category(aqi_val)
    return aqi_val, cat_name, color, adv
