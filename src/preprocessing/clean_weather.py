"""
clean_weather.py
----------------
Cleaning, unit conversions, and meteorological variable derivation for ECMWF ERA5-Land reanalysis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def compute_relative_humidity(temp_c: pd.Series, dewpoint_c: pd.Series) -> pd.Series:
    """
    Computes Relative Humidity (%) from 2m temperature and dewpoint (°C)
    using the August-Roche-Magnus approximation.
    """
    a = 17.625
    b = 243.04  # °C
    
    alpha_t = (a * temp_c) / (b + temp_c)
    alpha_td = (a * dewpoint_c) / (b + dewpoint_c)
    
    rh = 100.0 * np.exp(alpha_td - alpha_t)
    return rh.clip(lower=0.0, upper=100.0)


def compute_wind_vectors(u: pd.Series, v: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Converts 10m eastward (u) and northward (v) wind velocity components (m/s)
    into:
      1. Wind speed (m/s)
      2. Meteorological wind direction (degrees from North, 0–360, direction wind is coming FROM)
    """
    speed = np.sqrt(u**2 + v**2)
    # Meteorological direction: atan2(-u, -v) in degrees converted to 0..360
    direction = (np.degrees(np.arctan2(-u, -v)) + 360.0) % 360.0
    return speed, direction


def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs standard meteorological cleaning:
      - Kelvin to Celsius if values > 150
      - Computes wind speed / direction if u, v components present
      - Validates and clips boundary layer height (PBLH >= 50m)
      - Pa to hPa conversion for surface pressure if > 2000 hPa
      - Relative humidity bounded to [0, 100]%
    """
    df = df.copy()

    # Temperature checks
    for t_col in ["temperature", "temperature_2m", "2m_temperature"]:
        if t_col in df.columns:
            # If in Kelvin (> 150 K), convert to Celsius
            is_kelvin = df[t_col] > 150.0
            df.loc[is_kelvin, t_col] = df.loc[is_kelvin, t_col] - 273.15
            # Physical bounds [-50°C, 60°C]
            invalid_temp = (df[t_col] < -50.0) | (df[t_col] > 60.0)
            df.loc[invalid_temp, t_col] = np.nan

    # Relative humidity checks
    for rh_col in ["humidity", "relative_humidity_2m", "2m_relative_humidity"]:
        if rh_col in df.columns:
            df[rh_col] = df[rh_col].clip(lower=0.0, upper=100.0)

    # Wind components
    if "u_component_of_wind_10m" in df.columns and "v_component_of_wind_10m" in df.columns:
        ws, wd = compute_wind_vectors(df["u_component_of_wind_10m"], df["v_component_of_wind_10m"])
        if "wind_speed_10m" not in df.columns:
            df["wind_speed_10m"] = ws
        if "wind_direction_10m" not in df.columns:
            df["wind_direction_10m"] = wd

    # Boundary Layer Height
    if "boundary_layer_height" in df.columns:
        # PBLH should be non-negative; clip minimal shallow inversion at 50m
        df["boundary_layer_height"] = df["boundary_layer_height"].clip(lower=50.0, upper=6000.0)

    # Surface Pressure (convert Pa to hPa if > 2000)
    if "surface_pressure" in df.columns:
        is_pa = df["surface_pressure"] > 2000.0
        df.loc[is_pa, "surface_pressure"] = df.loc[is_pa, "surface_pressure"] / 100.0
        # Valid bounds [500 hPa, 1100 hPa]
        invalid_press = (df["surface_pressure"] < 500.0) | (df["surface_pressure"] > 1100.0)
        df.loc[invalid_press, "surface_pressure"] = np.nan

    # Precipitation
    if "precipitation_1h" in df.columns:
        df["precipitation_1h"] = df["precipitation_1h"].clip(lower=0.0)

    return df
