"""
src/domain/aqi.py
-----------------
Official India National Air Quality Index (NAQI) calculation engine.

Based on the Central Pollution Control Board (CPCB) Ministry of Environment,
Forest and Climate Change, Government of India guidelines.

NAQI Formula:
-------------
Sub-index formula for pollutant concentration C in breakpoint interval [B_lo, B_hi]:
    I = I_lo + ((I_hi - I_lo) / (B_hi - B_lo)) * (C - B_lo)

Overall AQI is the maximum of sub-indices provided at least 3 pollutants are measured,
one of which must be PM2.5 or PM10.
"""

from typing import Dict, Optional, Tuple, List, Union
import numpy as np
import pandas as pd


# Official CPCB Breakpoints (Concentration Range in ug/m3, CO in mg/m3)
# (B_low, B_high, I_low, I_high)
CPCB_BREAKPOINTS = {
    "pm25": [
        (0.0, 30.0, 0, 50),
        (30.1, 60.0, 51, 100),
        (60.1, 90.0, 101, 200),
        (90.1, 120.0, 201, 300),
        (120.1, 250.0, 301, 400),
        (250.1, 500.0, 401, 500),
    ],
    "pm10": [
        (0.0, 50.0, 0, 50),
        (50.1, 100.0, 51, 100),
        (100.1, 250.0, 101, 200),
        (250.1, 350.0, 201, 300),
        (350.1, 430.0, 301, 400),
        (430.1, 500.0, 401, 500),
    ],
    "no2": [
        (0.0, 40.0, 0, 50),
        (40.1, 80.0, 51, 100),
        (80.1, 180.0, 101, 200),
        (180.1, 280.0, 201, 300),
        (280.1, 400.0, 301, 400),
        (400.1, 800.0, 401, 500),
    ],
    "so2": [
        (0.0, 40.0, 0, 50),
        (40.1, 80.0, 51, 100),
        (80.1, 380.0, 101, 200),
        (380.1, 800.0, 201, 300),
        (800.1, 1600.0, 301, 400),
        (1600.1, 2000.0, 401, 500),
    ],
    "co": [
        (0.0, 1.0, 0, 50),
        (1.01, 2.0, 51, 100),
        (2.01, 10.0, 101, 200),
        (10.01, 17.0, 201, 300),
        (17.01, 34.0, 301, 400),
        (34.01, 50.0, 401, 500),
    ],
    "o3": [
        (0.0, 50.0, 0, 50),
        (50.1, 100.0, 51, 100),
        (100.1, 168.0, 101, 200),
        (168.1, 208.0, 201, 300),
        (208.1, 748.0, 301, 400),
        (748.1, 1000.0, 401, 500),
    ],
}

AQI_CATEGORIES = [
    (0, 50, "Good", "#00B050", "Minimal health impact. Air quality is considered satisfactory."),
    (51, 100, "Satisfactory", "#92D050", "Minor breathing discomfort to sensitive people."),
    (101, 200, "Moderate", "#FFFF00", "Breathing discomfort to people with lungs, asthma and heart diseases."),
    (201, 300, "Poor", "#FF9900", "Breathing discomfort to most people on prolonged exposure."),
    (301, 400, "Very Poor", "#FF0000", "Respiratory illness on prolonged exposure."),
    (401, 500, "Severe", "#C00000", "Affects healthy people and seriously impacts those with existing diseases."),
]


def calculate_sub_index(pollutant: str, concentration: float) -> Optional[float]:
    """
    Computes CPCB sub-index for a specific pollutant concentration.

    Parameters
    ----------
    pollutant : str
        One of 'pm25', 'pm10', 'no2', 'so2', 'co', 'o3'.
    concentration : float
        Measured or predicted concentration in ug/m3 (or mg/m3 for CO).

    Returns
    -------
    sub_index : Optional[float]
        Sub-index in [0, 500], or None if concentration is invalid/negative.
    """
    pollutant = pollutant.lower().replace(".", "").replace("-", "")
    if pollutant not in CPCB_BREAKPOINTS:
        return None
    if concentration is None or np.isnan(concentration) or concentration < 0:
        return None

    breakpoints = CPCB_BREAKPOINTS[pollutant]
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= concentration <= b_hi:
            sub_index = i_lo + ((i_hi - i_lo) / (b_hi - b_lo)) * (concentration - b_lo)
            return float(np.clip(sub_index, 0, 500))

    # If concentration exceeds highest breakpoint, cap at 500
    if concentration > breakpoints[-1][1]:
        return 500.0

    return 0.0


def aqi_to_category(aqi_value: float) -> Tuple[str, str, str]:
    """
    Returns category name, hex color code, and health advisory for an AQI value.

    Returns
    -------
    (category, color_hex, health_advisory) : Tuple[str, str, str]
    """
    if aqi_value is None or np.isnan(aqi_value):
        return "Unknown", "#808080", "No data available."

    aqi_round = round(aqi_value)
    for i_lo, i_hi, cat, color, adv in AQI_CATEGORIES:
        if i_lo <= aqi_round <= i_hi:
            return cat, color, adv

    if aqi_round > 500:
        return "Severe", "#C00000", "Affects healthy people and seriously impacts those with existing diseases."

    return "Good", "#00B050", "Minimal impact."


def pm25_to_naqi(pm25: float) -> Tuple[float, str]:
    """
    Convenience function: Convert PM2.5 (ug/m3) to India NAQI value and category string.

    Parameters
    ----------
    pm25 : float
        PM2.5 in ug/m3.

    Returns
    -------
    (aqi_value, category) : Tuple[float, str]
    """
    sub_idx = calculate_sub_index("pm25", pm25)
    if sub_idx is None:
        return np.nan, "Unknown"
    cat, _, _ = aqi_to_category(sub_idx)
    return round(sub_idx, 1), cat


def calculate_overall_aqi(pollutants: Dict[str, float]) -> Dict[str, Union[float, str, Dict[str, float]]]:
    """
    Calculates overall CPCB NAQI and dominant pollutant from available species.

    Parameters
    ----------
    pollutants : Dict[str, float]
        Dictionary with concentrations (e.g. {'pm25': 65.4, 'pm10': 120.0, 'no2': 35.0}).

    Returns
    -------
    result : dict
        {
            'aqi': float,
            'category': str,
            'color': str,
            'dominant_pollutant': str,
            'health_advisory': str,
            'sub_indices': Dict[str, float]
        }
    """
    sub_indices = {}
    for pol, conc in pollutants.items():
        val = calculate_sub_index(pol, conc)
        if val is not None:
            sub_indices[pol.lower()] = round(val, 1)

    if not sub_indices:
        return {
            "aqi": np.nan,
            "category": "Unknown",
            "color": "#808080",
            "dominant_pollutant": "None",
            "health_advisory": "No measurements provided.",
            "sub_indices": {}
        }

    # Dominant pollutant is the one with max sub-index
    dominant_pol = max(sub_indices, key=sub_indices.get)
    max_aqi = sub_indices[dominant_pol]
    cat, color, adv = aqi_to_category(max_aqi)

    return {
        "aqi": max_aqi,
        "category": cat,
        "color": color,
        "dominant_pollutant": dominant_pol.upper(),
        "health_advisory": adv,
        "sub_indices": sub_indices
    }
