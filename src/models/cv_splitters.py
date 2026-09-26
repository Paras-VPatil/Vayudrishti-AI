"""
src/models/cv_splitters.py
--------------------------
Cross-validation and dataset splitting strategies for spatiotemporal environmental data.

Splitting Principles:
---------------------
1. Temporal Holdout: The test set consists of the most recent time window (e.g. final 2-3 months).
   Random splitting leads to massive data leakage across time autocorrelation.
2. Spatial GroupKFold: Cross-validation within the training set groups by station_id
   so that a station in the validation fold never appears in the training fold.
   This tests true spatial generalization (hyperlocal prediction at unseen locations).
"""

from typing import Tuple, Generator, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold


def temporal_train_test_split(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp_utc",
    split_date: Optional[str] = None,
    test_ratio: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits dataframe strictly chronologically into train and test sets.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with a timestamp column.
    timestamp_col : str
        Name of timestamp column.
    split_date : Optional[str]
        ISO-8601 date string (e.g. '2024-10-01'). If None, uses test_ratio quantiles.
    test_ratio : float
        Fraction of data reserved for test set if split_date is None.

    Returns
    -------
    train_df, test_df : Tuple[pd.DataFrame, pd.DataFrame]
    """
    df_sorted = df.sort_values(by=timestamp_col).reset_index(drop=True)

    if split_date is not None:
        split_dt = pd.to_datetime(split_date, utc=True)
        ts_series = pd.to_datetime(df_sorted[timestamp_col], utc=True)
        train_df = df_sorted[ts_series < split_dt].copy().reset_index(drop=True)
        test_df = df_sorted[ts_series >= split_dt].copy().reset_index(drop=True)
    else:
        split_idx = int(len(df_sorted) * (1.0 - test_ratio))
        train_df = df_sorted.iloc[:split_idx].copy().reset_index(drop=True)
        test_df = df_sorted.iloc[split_idx:].copy().reset_index(drop=True)

    return train_df, test_df


def spatial_group_kfold(
    df: pd.DataFrame,
    group_col: str = "station_id",
    n_splits: int = 5
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    Generates Spatial GroupKFold train/val index splits based on station ID or spatial cluster.
    Guarantees no station leakage between train and val folds.
    Gracefully falls back to spatial coordinate clustering or KFold if station_id is single/missing.

    Parameters
    ----------
    df : pd.DataFrame
    group_col : str
        Column to group by (typically 'station_id' or 'location_id').
    n_splits : int
        Number of folds.

    Yields
    -------
    train_indices, val_indices : Tuple[np.ndarray, np.ndarray]
    """
    df_len = len(df)
    if df_len == 0:
        return

    # Check if grouping column is available with multiple distinct values
    if group_col in df.columns and df[group_col].dropna().nunique() >= 2:
        groups = df[group_col].fillna("station_unassigned").astype(str).values
        n_unique = len(np.unique(groups))
        actual_splits = min(n_splits, n_unique)
        gkf = GroupKFold(n_splits=actual_splits)
        X = np.zeros(df_len)
        for tr_idx, val_idx in gkf.split(X, groups=groups):
            yield tr_idx, val_idx
    elif "latitude" in df.columns and "longitude" in df.columns and df["latitude"].nunique() >= 5:
        # Spatial binning fallback
        lat_bins = pd.qcut(df["latitude"], q=min(n_splits, 5), labels=False, duplicates="drop")
        groups = lat_bins.fillna(0).astype(str).values
        actual_splits = min(n_splits, len(np.unique(groups)))
        gkf = GroupKFold(n_splits=actual_splits)
        X = np.zeros(df_len)
        for tr_idx, val_idx in gkf.split(X, groups=groups):
            yield tr_idx, val_idx
    else:
        # Standard KFold fallback
        kf = KFold(n_splits=min(n_splits, max(2, df_len)), shuffle=True, random_state=42)
        X = np.zeros(df_len)
        for tr_idx, val_idx in kf.split(X):
            yield tr_idx, val_idx
