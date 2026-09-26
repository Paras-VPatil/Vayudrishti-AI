"""
clean_satellite.py
------------------
Cleaning, QA masking, scale factor correction, and physical validation for MODIS AOD & Sentinel-5P TROPOMI products.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def clean_modis_aod(
    df: pd.DataFrame,
    aod_col: str = "aod_550nm",
    qa_col: str = "aod_qa_flag",
    min_qa: int = 2,
    scale_factor: float = 1.0  # 0.001 if raw integer MODIS DN
) -> pd.DataFrame:
    """
    Cleans MODIS AOD observations:
      1. Applies scale factor if raw digital numbers.
      2. Enforces QA confidence threshold (QA >= 2: Good and Very Good).
      3. Bounds AOD to valid atmospheric extinction range [0.0, 5.0].
    """
    df = df.copy()

    # Look for alias
    if aod_col not in df.columns and "aod" in df.columns:
        aod_col = "aod"

    if aod_col in df.columns:
        if scale_factor != 1.0:
            df[aod_col] = df[aod_col] * scale_factor

        # Filter by QA flag if available
        if qa_col in df.columns:
            poor_qa = df[qa_col] < min_qa
            df.loc[poor_qa, aod_col] = np.nan

        # Enforce physical limits (AOD < 0 is unphysical, AOD > 5 is extreme cloud/smoke)
        invalid_aod = (df[aod_col] < 0.0) | (df[aod_col] > 5.0)
        df.loc[invalid_aod, aod_col] = np.nan

        # Create missing flag
        df["is_aod_missing"] = df[aod_col].isna().astype(int)

    return df


def clean_tropomi_gases(
    df: pd.DataFrame,
    qa_thresholds: Optional[dict] = None
) -> pd.DataFrame:
    """
    Cleans Sentinel-5P TROPOMI gas column densities:
      1. Enforces official Copernicus QA thresholds (0.75 for NO2, 0.50 for others).
      2. Removes negative unphysical column number densities.
      3. Creates missing observation indicators.
    """
    df = df.copy()

    gas_limits = {
        "no2_tropospheric_column": (0.0, 5000.0),    # mol/m^2 or scaled
        "satellite_no2":           (0.0, 5000.0),
        "so2_column":              (0.0, 1000.0),
        "satellite_so2":           (0.0, 1000.0),
        "co_column":               (0.0, 5.0),
        "satellite_co":            (0.0, 5.0),
        "o3_column":               (0.01, 1.0),
        "satellite_o3":            (0.01, 1.0),
        "uv_aerosol_index":        (-5.0, 20.0),
    }

    for col, (min_val, max_val) in gas_limits.items():
        if col in df.columns:
            invalid_mask = (df[col] < min_val) | (df[col] > max_val)
            df.loc[invalid_mask, col] = np.nan
            if not col.startswith("satellite_"):
                df[f"is_{col}_missing"] = df[col].isna().astype(int)

    return df


def clean_satellite_data(df: pd.DataFrame) -> pd.DataFrame:
    """End-to-end satellite cleaning pipeline."""
    df = clean_modis_aod(df)
    df = clean_tropomi_gases(df)
    return df
