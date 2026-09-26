"""
clean_weather.py
----------------
Cleaning, unit conversions, and meteorological variable derivation for ECMWF ERA5-Land reanalysis.

Usage (CLI)
-----------
  python -m src.preprocessing.clean_weather \
      --input  "data/raw/weather/era5_*.parquet" \
      --output data/interim/weather_clean.parquet
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

    # Precipitation — rename ERA5 raw column and clip to >= 0
    if "total_precipitation" in df.columns and "precipitation_1h" not in df.columns:
        df["precipitation_1h"] = df["total_precipitation"].clip(lower=0.0)
    if "precipitation_1h" in df.columns:
        df["precipitation_1h"] = df["precipitation_1h"].clip(lower=0.0)

    # Derive relative humidity from dewpoint if not yet present
    if "relative_humidity_2m" not in df.columns:
        dew_col = next((c for c in ["dewpoint_temperature_2m", "2m_dewpoint_temperature"]
                        if c in df.columns), None)
        tmp_col = next((c for c in ["temperature_2m", "2m_temperature", "temperature"]
                        if c in df.columns), None)
        if dew_col and tmp_col:
            # Convert to Celsius first (clean_weather may already have done this)
            dew_c = df[dew_col].copy()
            if (dew_c > 150).any():       # still in Kelvin
                dew_c = dew_c - 273.15
            tmp_c = df[tmp_col].copy()
            df["relative_humidity_2m"] = compute_relative_humidity(tmp_c, dew_c)

    return df


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import logging
    from glob import glob
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Clean ERA5 weather data")
    parser.add_argument("--input",  required=True, help="Input parquet file or glob pattern")
    parser.add_argument("--output", required=True, help="Output parquet file path")
    args = parser.parse_args()

    import pandas as pd

    files = sorted(glob(args.input))
    if not files:
        raise FileNotFoundError(f"No files matched: {args.input}")

    frames = [pd.read_parquet(f) for f in files]
    raw_df = pd.concat(frames, ignore_index=True)
    log.info("Loaded %d rows from %d file(s)", len(raw_df), len(files))

    clean_df = clean_weather_data(raw_df)
    log.info("After cleaning: %d rows", len(clean_df))
    log.info("Columns: %s", list(clean_df.columns))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_parquet(out_path, index=False, engine="pyarrow")
    log.info("Saved → %s", out_path)

    from src.preprocessing.missingness import get_missingness_report
    print("\nMissingness report (interim/weather_clean):")
    print(get_missingness_report(clean_df))
