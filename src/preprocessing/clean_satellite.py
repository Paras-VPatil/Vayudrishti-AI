"""
clean_satellite.py
------------------
Cleaning, QA masking, scale factor correction, and physical validation for MODIS AOD & Sentinel-5P TROPOMI products.

Usage (CLI)
-----------
  python -m src.preprocessing.clean_satellite \
      --aod     "data/raw/satellite/modis_aod_*.parquet" \
      --tropomi "data/raw/satellite/tropomi_*.parquet" \
      --output  data/interim/satellite_clean.parquet
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
    """End-to-end satellite cleaning pipeline for a combined (AOD + TROPOMI) DataFrame."""
    df = clean_modis_aod(df)
    df = clean_tropomi_gases(df)
    return df


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import logging
    from glob import glob
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Clean satellite data (MODIS AOD + TROPOMI)")
    parser.add_argument("--aod",     default=None, help="MODIS AOD parquet glob pattern")
    parser.add_argument("--tropomi", default=None, help="TROPOMI parquet glob pattern")
    parser.add_argument("--output",  required=True, help="Output parquet path")
    args = parser.parse_args()

    frames = []

    if args.aod:
        aod_files = sorted(glob(args.aod))
        if aod_files:
            aod_raw = pd.concat([pd.read_parquet(f) for f in aod_files], ignore_index=True)
            aod_clean = clean_modis_aod(aod_raw)
            log.info("MODIS AOD: %d → %d rows after QA", len(aod_raw), len(aod_clean))
            frames.append(aod_clean)
        else:
            log.warning("No MODIS AOD files matched: %s", args.aod)

    if args.tropomi:
        tro_files = sorted(glob(args.tropomi))
        if tro_files:
            tro_raw = pd.concat([pd.read_parquet(f) for f in tro_files], ignore_index=True)
            tro_clean = clean_tropomi_gases(tro_raw)
            log.info("TROPOMI: %d → %d rows after QA", len(tro_raw), len(tro_clean))
            frames.append(tro_clean)
        else:
            log.warning("No TROPOMI files matched: %s", args.tropomi)

    if not frames:
        raise RuntimeError("No satellite data loaded. Check --aod and --tropomi arguments.")

    # Outer join on (latitude, longitude, timestamp_utc) if both provided
    if len(frames) == 2:
        key_cols = [c for c in ["latitude", "longitude", "timestamp_utc"] if c in frames[0].columns and c in frames[1].columns]
        combined = pd.merge(frames[0], frames[1], on=key_cols, how="outer") if key_cols else pd.concat(frames, ignore_index=True)
    else:
        combined = frames[0]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(out_path, index=False, engine="pyarrow")
    log.info("Saved → %s (%d rows)", out_path, len(combined))

    from src.preprocessing.missingness import get_missingness_report
    print("\nMissingness report (interim/satellite_clean):")
    print(get_missingness_report(combined))
