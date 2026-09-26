"""
missingness.py
--------------
Structured detection, flagging, and principled handling of missing data across satellite, ground, weather, and geospatial streams.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def detect_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scans the DataFrame and returns a comprehensive summary table
    with null counts, percentage missing, and recommended handling strategy.
    """
    records = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        pct = (null_count / len(df)) * 100 if len(df) > 0 else 0.0
        
        # Policy recommendation
        if col in ["ground_pm25", "pm25_ground", "ground_pm10", "pm10_ground", "aqi_label"]:
            strategy = "Target variable -> Drop in training; Keep/Predict in inference"
        elif "satellite" in col or "column" in col or "aod" in col:
            strategy = "Flag with is_<col>_missing; Tree native split or MICE/KNN"
        elif col in ["temperature", "temperature_2m", "humidity", "relative_humidity_2m", "wind_speed", "wind_speed_10m", "boundary_layer_height"]:
            strategy = "Temporal linear interpolation (<=3h) / Spatial Kriging / Median"
        elif "density" in col or "road" in col or "elevation" in col:
            strategy = "Static default (0.0 for density, median for DEM)"
        else:
            strategy = "Flag & evaluate"

        records.append({
            "column": col,
            "missing_count": null_count,
            "missing_pct": round(pct, 2),
            "strategy": strategy
        })

    return pd.DataFrame(records)


def get_missingness_report(df: pd.DataFrame) -> str:
    """Formats the missingness detection summary as a clean table string."""
    summary_df = detect_missingness(df)
    return summary_df.to_string(index=False)


def handle_missing_data(
    df: pd.DataFrame,
    is_training: bool = True,
    target_cols: Optional[List[str]] = None,
    impute_weather: bool = True,
    impute_satellite: bool = False,  # False for tree-based models (LightGBM/XGBoost handle NaNs natively)
    fill_static_zeros: bool = True
) -> pd.DataFrame:
    """
    Executes principled missing data handling:
      1. Detects missing values.
      2. Creates explicit boolean mask flags (is_<feature>_missing) for sparse sensors.
      3. For training: Drops rows where the training target is unobserved.
      4. Imputes meteorological data via local rolling/median.
      5. Handles static geospatial missingness with physical defaults.
    """
    df = df.copy()

    if target_cols is None:
        target_cols = ["aqi_label", "ground_pm25", "pm25_ground"]

    # 1. Flag missingness for satellite columns
    satellite_cols = [
        "aod_550nm", "aod", "no2_tropospheric_column", "satellite_no2",
        "so2_column", "satellite_so2", "co_column", "satellite_co",
        "o3_column", "satellite_o3", "uv_aerosol_index"
    ]
    for col in satellite_cols:
        if col in df.columns:
            flag_col = f"is_{col}_missing"
            if flag_col not in df.columns:
                df[flag_col] = df[col].isna().astype(int)

    # Standardize alias for AOD
    if "is_aod_550nm_missing" in df.columns and "is_aod_missing" not in df.columns:
        df["is_aod_missing"] = df["is_aod_550nm_missing"]
    elif "is_aod_missing" in df.columns and "is_aod_550nm_missing" not in df.columns:
        df["is_aod_550nm_missing"] = df["is_aod_missing"]

    # 2. Flag missingness for critical boundary layer & weather
    weather_cols = ["boundary_layer_height", "temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
    for col in weather_cols:
        if col in df.columns:
            flag_col = f"is_{col}_missing"
            if flag_col not in df.columns:
                df[flag_col] = df[col].isna().astype(int)

    # 3. Ground target policy: Never hallucinate / impute training target labels
    if is_training:
        for t_col in target_cols:
            if t_col in df.columns:
                df = df[df[t_col].notna()].copy()

    # 4. Weather imputation policy: Weather is smooth; fill minor gaps using spatial/temporal medians
    if impute_weather:
        for col in ["temperature_2m", "temperature"]:
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

        for col in ["relative_humidity_2m", "humidity"]:
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

        for col in ["wind_speed_10m", "wind_speed"]:
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

        for col in ["wind_direction_10m", "wind_direction"]:
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(180.0)

        if "boundary_layer_height" in df.columns and df["boundary_layer_height"].isna().any():
            df["boundary_layer_height"] = df["boundary_layer_height"].fillna(df["boundary_layer_height"].median() if df["boundary_layer_height"].notna().any() else 500.0)

    # 5. Static geospatial filling
    if fill_static_zeros:
        for d_col in ["road_density", "building_density", "precipitation_1h"]:
            if d_col in df.columns:
                df[d_col] = df[d_col].fillna(0.0)

        if "elevation_m" in df.columns and df["elevation_m"].isna().any():
            df["elevation_m"] = df["elevation_m"].fillna(df["elevation_m"].median() if df["elevation_m"].notna().any() else 200.0)

    # 6. Optional satellite imputation (e.g. for models that don't support NaNs)
    if impute_satellite:
        for col in satellite_cols:
            if col in df.columns and df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

    return df
