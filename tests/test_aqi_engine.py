"""
tests/test_aqi_engine.py
------------------------
Unit tests for India NAQI calculation engine according to official CPCB breakpoints.
"""

import pytest
import numpy as np
from src.domain.aqi import (
    calculate_sub_index,
    aqi_to_category,
    pm25_to_naqi,
    calculate_overall_aqi,
)


def test_pm25_reference_breakpoints():
    """Verify CPCB standard reference breakpoint checks."""
    val, cat = pm25_to_naqi(15.0)
    assert cat == "Good"
    assert 0 <= val <= 50

    val, cat = pm25_to_naqi(45.0)
    assert cat == "Satisfactory"
    assert 51 <= val <= 100

    val, cat = pm25_to_naqi(75.0)
    assert cat == "Moderate"
    assert 101 <= val <= 200

    val, cat = pm25_to_naqi(110.0)
    assert cat == "Poor"
    assert 201 <= val <= 300

    val, cat = pm25_to_naqi(200.0)
    assert cat == "Very Poor"
    assert 301 <= val <= 400

    val, cat = pm25_to_naqi(350.0)
    assert cat == "Severe"
    assert 401 <= val <= 500


def test_negative_and_nan_handling():
    """Negative or NaN values should return None / NaN gracefully."""
    assert calculate_sub_index("pm25", -5.0) is None
    assert calculate_sub_index("pm25", np.nan) is None

    val, cat = pm25_to_naqi(-10.0)
    assert np.isnan(val)
    assert cat == "Unknown"


def test_dominant_pollutant_identification():
    """Dominant pollutant must be the species with highest sub-index."""
    pollutants = {
        "pm25": 40.0,  # sub-index in 51-100 (Satisfactory)
        "no2": 250.0,  # sub-index in 201-300 (Poor)
        "so2": 20.0,   # sub-index in 0-50 (Good)
    }
    res = calculate_overall_aqi(pollutants)
    assert res["dominant_pollutant"] == "NO2"
    assert res["category"] == "Poor"
    assert 201 <= res["aqi"] <= 300
