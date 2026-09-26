"""
src/features/sliding_window.py
------------------------------
Stage 12 — Sliding Window Lag Feature Generator for Air Quality Forecasting.

Constructs autoregressive lag features per monitoring station or city time series:
- Historical target lags: t-1h, t-2h, t-3h, t-6h, t-12h, t-24h
- Rolling statistical aggregates: 6h rolling mean, 24h rolling max/min/std
- Forecast horizons: +1h, +6h, +12h, +24h lead targets
"""

from typing import List, Tuple, Optional
import pandas as pd
import numpy as np


LAG_HOURS = [1, 2, 3, 6, 12, 24]
HORIZONS = [1, 6, 12, 24]


def create_sliding_window_dataset(
    df: pd.DataFrame,
    target_col: str = "pm25_ground",
    station_col: str = "station_id",
    timestamp_col: str = "timestamp_utc",
    lags: List[int] = LAG_HOURS,
    horizons: List[int] = HORIZONS
) -> pd.DataFrame:
    """
    Builds lag features and multi-horizon target labels grouped by monitoring station
    or citywide chronological sequence.

    Parameters
    ----------
    df : pd.DataFrame
    target_col : str
        Target pollutant column (default: 'pm25_ground').
    station_col : str
        Station identifier column.
    timestamp_col : str
        Timestamp column.
    lags : List[int]
        Hours in past to lag target.
    horizons : List[int]
        Hours in future to create prediction targets.

    Returns
    -------
    df_windowed : pd.DataFrame
    """
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)

    # Check if station grouping has sufficient depth per station
    has_deep_stations = False
    if station_col in df.columns:
        station_counts = df[station_col].value_counts()
        if len(station_counts) > 0 and station_counts.mean() >= 10:
            has_deep_stations = True

    if has_deep_stations:
        df = df.sort_values(by=[station_col, timestamp_col]).reset_index(drop=True)
        # Compute lags per station
        for lag in lags:
            df[f"{target_col}_lag_{lag}h"] = df.groupby(station_col)[target_col].shift(lag)

        grouped = df.groupby(station_col)[target_col]
        df[f"{target_col}_rolling_mean_6h"] = grouped.transform(lambda s: s.rolling(6, min_periods=1).mean())
        df[f"{target_col}_rolling_mean_24h"] = grouped.transform(lambda s: s.rolling(24, min_periods=1).mean())
        df[f"{target_col}_rolling_std_24h"] = grouped.transform(lambda s: s.rolling(24, min_periods=1).std().fillna(0))

        # Future targets
        for h in horizons:
            df[f"target_lead_{h}h"] = df.groupby(station_col)[target_col].shift(-h)
    else:
        # Chronological sequence across citywide network
        df = df.sort_values(by=timestamp_col).reset_index(drop=True)
        for lag in lags:
            df[f"{target_col}_lag_{lag}h"] = df[target_col].shift(lag)

        df[f"{target_col}_rolling_mean_6h"] = df[target_col].rolling(6, min_periods=1).mean()
        df[f"{target_col}_rolling_mean_24h"] = df[target_col].rolling(24, min_periods=1).mean()
        df[f"{target_col}_rolling_std_24h"] = df[target_col].rolling(24, min_periods=1).std().fillna(0)

        for h in horizons:
            df[f"target_lead_{h}h"] = df[target_col].shift(-h)

    # Impute initial missing lags with global median/backfill to retain dataset volume
    median_val = df[target_col].median()
    for lag in lags:
        df[f"{target_col}_lag_{lag}h"] = df[f"{target_col}_lag_{lag}h"].bfill().fillna(median_val)

    # Drop only rows where future targets are all NaN (very end of sequence)
    lead_cols = [f"target_lead_{h}h" for h in horizons]
    df = df.dropna(subset=[lead_cols[0]]).reset_index(drop=True)
    return df


def compute_persistence_baseline(
    df: pd.DataFrame,
    target_col: str = "pm25_ground",
    horizon: int = 1
) -> Tuple[float, float]:
    """
    Evaluates naive persistence benchmark: y_hat(t+h) = y(t).

    Returns
    -------
    (mae, rmse) : Tuple[float, float]
    """
    future_target = f"target_lead_{horizon}h"
    valid = df.dropna(subset=[target_col, future_target])
    if len(valid) == 0:
        return 0.0, 0.0

    y_true = valid[future_target].values
    y_pred = valid[target_col].values

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    return mae, rmse
