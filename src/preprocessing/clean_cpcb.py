"""
clean_cpcb.py
-------------
Quality Assurance, cleaning, anomaly filtering, and NAQI calculation for CPCB ground station data.

Usage (CLI)
-----------
  python -m src.preprocessing.clean_cpcb \
      --input  data/raw/ground/cpcb_20240601.parquet \
      --output data/interim/cpcb_clean.parquet
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

# ── CPCB Physical Valid Bounds ────────────────────────────────────────────────
PHYSICAL_LIMITS = {
    "pm25": (0.0, 1000.0),       # µg/m³
    "pm10": (0.0, 1500.0),       # µg/m³
    "no2":  (0.0, 500.0),        # µg/m³
    "so2":  (0.0, 500.0),        # µg/m³
    "co":   (0.0, 50.0),         # mg/m³
    "o3":   (0.0, 500.0),        # µg/m³
}

# ── Indian NAQI Breakpoints (CPCB 2014) ───────────────────────────────────────
# (Cp_low, Cp_high, I_low, I_high)
NAQI_BREAKPOINTS: Dict[str, List[Tuple[float, float, float, float]]] = {
    "pm25": [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (250.1, 1000, 401, 500)
    ],
    "pm10": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (430.1, 1500, 401, 500)
    ],
    "no2": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 180, 101, 200),
        (181, 280, 201, 300),
        (281, 400, 301, 400),
        (400.1, 1000, 401, 500)
    ],
    "so2": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 380, 101, 200),
        (381, 800, 201, 300),
        (801, 1600, 301, 400),
        (1600.1, 3000, 401, 500)
    ],
    "co": [
        (0, 1.0, 0, 50),
        (1.1, 2.0, 51, 100),
        (2.1, 10.0, 101, 200),
        (10.1, 17.0, 201, 300),
        (17.1, 34.0, 301, 400),
        (34.1, 100.0, 401, 500)
    ],
    "o3": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 168, 101, 200),
        (169, 208, 201, 300),
        (209, 748, 301, 400),
        (748.1, 1500, 401, 500)
    ]
}


def calculate_naqi_subindex(pollutant: str, conc: float) -> Optional[float]:
    """Calculate the NAQI sub-index for a single pollutant observation."""
    if conc is None or np.isnan(conc) or conc < 0:
        return None
    
    pollutant_key = pollutant.lower().replace(".", "")
    if pollutant_key not in NAQI_BREAKPOINTS:
        return None

    breakpoints = NAQI_BREAKPOINTS[pollutant_key]
    for b_lo, b_hi, i_lo, i_hi in breakpoints:
        if b_lo <= conc <= b_hi:
            subindex = ((i_hi - i_lo) / (b_hi - b_lo)) * (conc - b_lo) + i_lo
            return float(np.clip(subindex, 0, 500))
    
    # Exceeds highest breakpoint
    return 500.0


def aqi_to_category(aqi: float) -> str:
    """Map numeric AQI to India NAQI category."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Satisfactory"
    elif aqi <= 200:
        return "Moderate"
    elif aqi <= 300:
        return "Poor"
    elif aqi <= 400:
        return "Very Poor"
    else:
        return "Severe"


def clean_cpcb_data(
    df: pd.DataFrame,
    station_col: str = "station_id",
    time_col: str = "timestamp_utc",
    flatline_consecutive_hours: int = 4
) -> pd.DataFrame:
    """
    Cleans raw CPCB observations by:
      1. Replacing placeholder / negative numbers (< 0) with NaN.
      2. Enforcing physical plausible thresholds per pollutant.
      3. Detecting flatlined / frozen sensor periods.
      4. Computing the official India NAQI and dominant pollutant sub-index.
    """
    df = df.copy()

    # Standardize column names if alias exists
    rename_map = {
        "pm2.5": "pm25", "PM2.5": "pm25", "ground_pm25": "pm25", "pm25_ground": "pm25",
        "pm10": "pm10", "PM10": "pm10", "ground_pm10": "pm10", "pm10_ground": "pm10",
        "no2": "no2", "NO2": "no2", "ground_no2": "no2",
        "so2": "so2", "SO2": "so2", "ground_so2": "so2",
        "co": "co", "CO": "co", "ground_co": "co",
        "o3": "o3", "O3": "o3", "ground_o3": "o3"
    }
    for old_col, new_col in rename_map.items():
        if old_col in df.columns and new_col not in df.columns:
            df[new_col] = df[old_col]

    # Clean negative values and physical bounds
    for pol, (min_val, max_val) in PHYSICAL_LIMITS.items():
        if pol in df.columns:
            # Mask invalid/negative values
            invalid_mask = (df[pol] < min_val) | (df[pol] > max_val)
            df.loc[invalid_mask, pol] = np.nan

    # Detect frozen sensor periods if station & time are sorted
    if station_col in df.columns and time_col in df.columns:
        df = df.sort_values(by=[station_col, time_col]).reset_index(drop=True)
        for pol in PHYSICAL_LIMITS.keys():
            if pol in df.columns:
                # Count consecutive identical non-null readings per station
                diff = df.groupby(station_col)[pol].diff()
                is_zero = (diff == 0) & df[pol].notna()
                consec_counts = is_zero.groupby((~is_zero).cumsum()).cumsum()
                flatlined = consec_counts >= (flatline_consecutive_hours - 1)
                df.loc[flatlined, pol] = np.nan

    # Compute subindices and composite AQI
    subindex_cols = []
    for pol in ["pm25", "pm10", "no2", "so2", "co", "o3"]:
        if pol in df.columns:
            sub_col = f"{pol}_subindex"
            df[sub_col] = df[pol].apply(lambda val: calculate_naqi_subindex(pol, val))
            subindex_cols.append(sub_col)

    if subindex_cols:
        # NAQI requires at least 3 parameters with at least one being PM2.5 or PM10
        df["aqi_calculated"] = df[subindex_cols].max(axis=1)
        
        # Identify dominant pollutant
        df["dominant_pollutant"] = df[subindex_cols].idxmax(axis=1).str.replace("_subindex", "").str.upper()
        df.loc[df["aqi_calculated"].isna(), "dominant_pollutant"] = None
        
        # Assign NAQI category
        df["aqi_category"] = df["aqi_calculated"].apply(
            lambda x: aqi_to_category(x) if pd.notna(x) else None
        )

    return df


def pivot_openaq_long_to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    OpenAQ v3 API returns data in LONG format (one row per parameter per measurement).
    This pivots it to WIDE format (one row per station+timestamp with pollutants as columns).

    Input columns:  station_id, station_name, city, latitude, longitude,
                    timestamp_utc, parameter, value, unit
    Output columns: station_id, station_name, city, latitude, longitude,
                    timestamp_utc, pm25, pm10, no2, so2, co, o3
    """
    if "parameter" not in df.columns or "value" not in df.columns:
        # Already in wide format — return as-is
        return df

    # Normalise parameter names
    param_map = {
        "pm25": "pm25", "pm2.5": "pm25", "PM2.5": "pm25",
        "pm10": "pm10", "PM10": "pm10",
        "no2":  "no2",  "NO2":  "no2",
        "so2":  "so2",  "SO2":  "so2",
        "co":   "co",   "CO":   "co",
        "o3":   "o3",   "O3":   "o3",
    }
    df = df.copy()
    df["parameter"] = df["parameter"].map(param_map).fillna(df["parameter"])

    # Keep only the 6 pollutants we need
    df = df[df["parameter"].isin(param_map.values())].copy()

    id_cols = [c for c in ["station_id", "station_name", "city", "latitude", "longitude",
                            "timestamp_utc"] if c in df.columns]

    wide = df.pivot_table(
        index=id_cols,
        columns="parameter",
        values="value",
        aggfunc="mean",
    ).reset_index()
    wide.columns.name = None
    return wide


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import logging
    from glob import glob
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Clean CPCB ground station data")
    parser.add_argument("--input",  required=True, help="Input parquet file or glob pattern")
    parser.add_argument("--output", required=True, help="Output parquet file path")
    args = parser.parse_args()

    import pandas as pd

    # Load (supports glob patterns like data/raw/ground/cpcb_*.parquet)
    files = sorted(glob(args.input))
    if not files:
        raise FileNotFoundError(f"No files matched: {args.input}")

    frames = [pd.read_parquet(f) for f in files]
    raw_df = pd.concat(frames, ignore_index=True)
    log.info("Loaded %d rows from %d file(s)", len(raw_df), len(files))

    # Pivot long → wide if needed (OpenAQ format)
    wide_df = pivot_openaq_long_to_wide(raw_df)
    log.info("After pivot: %d rows, columns: %s", len(wide_df), list(wide_df.columns))

    # Clean
    clean_df = clean_cpcb_data(wide_df)
    log.info("After cleaning: %d rows", len(clean_df))

    # Save
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_parquet(out_path, index=False, engine="pyarrow")
    log.info("Saved → %s", out_path)

    # Print missingness summary
    from src.preprocessing.missingness import get_missingness_report
    print("\nMissingness report (interim/cpcb_clean):")
    print(get_missingness_report(clean_df))
