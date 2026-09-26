"""
src/preprocessing/build_canonical_dataset.py
---------------------------------------------
Stage 6 — Build the canonical training dataset.

This is the single most important module in the project.
Everything downstream (EDA, ML, forecasting, API) depends on this file.

Pipeline
--------
  collocated_pairs.parquet      ← satellite pixels matched to CPCB stations
          +
  weather_clean.parquet         ← ERA5 joined by nearest timestamp + spatial cell
          +
  static_features_clean.parquet ← OSM + DEM + WorldPop, joined by 1 km grid cell
          |
  handle_missing_data()         ← apply missingness policy
          |
  validate_canonical_schema()   ← hard assertions before saving
          |
  canonical_dataset.parquet
  canonical_dataset_meta.json

Target column
-------------
  pm25_ground — THE ONLY ML TARGET.
  aqi_label and aqi_category are NOT included.
  AQI is derived AFTER prediction in src/domain/aqi.py.

Usage
-----
  python -m src.preprocessing.build_canonical_dataset
  python scripts/build_canonical.py  (alias)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_loader import get_pipeline_config
from src.preprocessing.missingness import handle_missing_data, detect_missingness

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Required columns in the canonical dataset ─────────────────────────────
# Provenance (never fed into model)
PROVENANCE_COLS = [
    "location_id",
    "station_id",
    "latitude",
    "longitude",
    "timestamp_utc",
    "distance_to_station_km",
    "temporal_offset_minutes",
]

# Satellite features
SATELLITE_COLS = [
    "aod_550nm",
    "satellite_no2",
    "satellite_so2",
    "satellite_co",
    "satellite_o3",
    "uv_aerosol_index",
    "is_aod_missing",
    "is_no2_missing",
    "is_so2_missing",
    "is_co_missing",
    "is_o3_missing",
]

# Weather features
WEATHER_COLS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "boundary_layer_height",
    "surface_pressure",
    "precipitation_1h",
]

# Static geospatial features
STATIC_COLS = [
    "road_density",
    "building_density",
    "land_use_class",
    "elevation_m",
    "population_density",
    "distance_to_road_km",
    "distance_to_industry_km",
]

# ML target — ONLY this column. AQI is derived post-prediction.
TARGET_COL = "pm25_ground"

# Columns that must NEVER appear (target leakage guard)
LEAKAGE_FORBIDDEN = {"aqi_label", "aqi_category", "aqi_calculated", "aqi_index", "pm25_predicted"}


# ── Weather join helper ────────────────────────────────────────────────────

def _join_weather(
    collocated: pd.DataFrame,
    weather: pd.DataFrame,
    time_tolerance_h: float = 1.5,
) -> pd.DataFrame:
    """
    Join ERA5 weather to collocated pairs using nearest timestamp + spatial cell.

    Strategy:
    1. Round each collocated timestamp to the nearest ERA5 hour.
    2. Merge on (rounded_timestamp, approximate 1 km grid cell).
    3. If no exact grid match, fall back to nearest station cell.

    Parameters
    ----------
    collocated : pd.DataFrame   collocated satellite+ground pairs
    weather    : pd.DataFrame   cleaned ERA5 interim data
    time_tolerance_h : float    max hour offset for timestamp rounding

    Returns
    -------
    pd.DataFrame  with weather columns appended
    """
    col = collocated.copy()
    wx  = weather.copy()

    # Parse timestamps
    col["timestamp_utc"] = pd.to_datetime(col.get("timestamp_utc", col.get("timestamp_utc_sat")), utc=True)
    wx["timestamp_utc"]  = pd.to_datetime(wx["timestamp_utc"], utc=True)

    # Round to nearest hour for ERA5 join
    col["_ts_hour"] = col["timestamp_utc"].dt.round("1h")
    wx["_ts_hour"]  = wx["timestamp_utc"].dt.round("1h")

    # Create ~1 km grid bucket keys (round to 2 decimal places ≈ 1 km)
    for df in (col, wx):
        df["_lat_bucket"] = df["latitude"].round(2)
        df["_lon_bucket"] = df["longitude"].round(2)

    weather_cols_to_join = [c for c in WEATHER_COLS if c in wx.columns]
    if not weather_cols_to_join:
        log.warning("No weather columns found to join. Check clean_weather output.")
        return col

    wx_sub = wx[["_ts_hour", "_lat_bucket", "_lon_bucket"] + weather_cols_to_join].copy()

    # Deduplicate: average ERA5 pixels within the same hour+cell
    wx_sub = wx_sub.groupby(["_ts_hour", "_lat_bucket", "_lon_bucket"]).mean(numeric_only=True).reset_index()

    merged = pd.merge(
        col,
        wx_sub,
        on=["_ts_hour", "_lat_bucket", "_lon_bucket"],
        how="left",
    )

    n_missing_wx = merged[weather_cols_to_join[0]].isna().sum() if weather_cols_to_join else 0
    log.info("Weather join: %d/%d rows have weather data (%d missing)",
             len(merged) - n_missing_wx, len(merged), n_missing_wx)

    # Clean up join keys
    merged = merged.drop(columns=["_ts_hour", "_lat_bucket", "_lon_bucket"], errors="ignore")
    return merged


# ── Static features join helper ────────────────────────────────────────────

def _join_static(
    df: pd.DataFrame,
    static: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join static geospatial features by nearest 1 km grid cell.

    Parameters
    ----------
    df     : pd.DataFrame  working canonical table
    static : pd.DataFrame  cleaned static features (1 km grid)

    Returns
    -------
    pd.DataFrame  with static columns appended
    """
    df = df.copy()
    st = static.copy()

    # Round lat/lon to 2 decimal places for grid matching
    df["_lat_bucket"] = df["latitude"].round(2)
    df["_lon_bucket"] = df["longitude"].round(2)
    st["_lat_bucket"] = st["latitude"].round(2)
    st["_lon_bucket"] = st["longitude"].round(2)

    static_cols_to_join = [c for c in STATIC_COLS if c in st.columns]
    if not static_cols_to_join:
        log.warning("No static columns found to join. Check clean_osm output.")
        return df

    st_sub = st[["_lat_bucket", "_lon_bucket"] + static_cols_to_join].drop_duplicates(
        subset=["_lat_bucket", "_lon_bucket"]
    )

    merged = pd.merge(
        df,
        st_sub,
        on=["_lat_bucket", "_lon_bucket"],
        how="left",
    )

    n_missing_st = merged[static_cols_to_join[0]].isna().sum() if static_cols_to_join else 0
    log.info("Static join: %d/%d rows have static data (%d missing)",
             len(merged) - n_missing_st, len(merged), n_missing_st)

    merged = merged.drop(columns=["_lat_bucket", "_lon_bucket"], errors="ignore")
    return merged


# ── Canonical schema normaliser ────────────────────────────────────────────

def _normalise_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply column aliases and renames to harmonise across ingestion sources.
    This handles common naming differences between ingestion and cleaning modules.
    """
    alias_map = {
        # Timestamp aliases
        "timestamp_utc_sat":    "satellite_timestamp",
        "timestamp_utc_ground": "ground_timestamp",
        # CPCB target
        "pm25":                 "pm25_ground",
        "ground_pm25":          "pm25_ground",
        # TROPOMI aliases
        "no2_tropospheric_column": "satellite_no2",
        "so2_column":              "satellite_so2",
        "co_column":               "satellite_co",
        "o3_column":               "satellite_o3",
        # Land use
        "landuse_class":           "land_use_class",
        "land_use_label":          "land_use_class",  # use label if integer class missing
        # Population
        "pop_density":             "population_density",
    }
    for old, new in alias_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    return df


# ── Leakage guard ──────────────────────────────────────────────────────────

def _enforce_no_leakage(df: pd.DataFrame) -> pd.DataFrame:
    """Drop any AQI-derived or target-leaking columns. Raises if pm25_ground is missing."""
    leaked = LEAKAGE_FORBIDDEN & set(df.columns)
    if leaked:
        log.warning("Dropping leakage columns: %s", leaked)
        df = df.drop(columns=list(leaked))

    if TARGET_COL not in df.columns:
        raise ValueError(
            f"Target column '{TARGET_COL}' not found in dataset. "
            "Verify that cpcb_clean.parquet contains a 'pm25' or 'pm25_ground' column "
            "and that the temporal match preserved it."
        )
    return df


# ── Canonical schema validation ────────────────────────────────────────────

def validate_canonical_schema(df: pd.DataFrame, cfg: dict) -> None:
    """
    Assertion-based validation. Raises AssertionError on failure.
    Identical logic to scripts/validate_canonical.py but callable from code.
    """
    bbox = cfg["bbox"]
    errors = []

    if len(df) < 100:
        errors.append(f"Too few rows: {len(df)}")

    if "latitude" in df.columns:
        bad = (~df["latitude"].between(bbox["lat_min"] - 0.1, bbox["lat_max"] + 0.1)).sum()
        if bad > 0:
            errors.append(f"{bad} rows outside latitude bounds")

    if "longitude" in df.columns:
        bad = (~df["longitude"].between(bbox["lon_min"] - 0.1, bbox["lon_max"] + 0.1)).sum()
        if bad > 0:
            errors.append(f"{bad} rows outside longitude bounds")

    ts = pd.to_datetime(df.get("timestamp_utc", pd.Series(dtype="object")), utc=True, errors="coerce")
    if ts.isna().sum() > 0:
        errors.append(f"{ts.isna().sum()} rows have invalid timestamp_utc")

    leaked = LEAKAGE_FORBIDDEN & set(df.columns)
    if leaked:
        errors.append(f"TARGET LEAKAGE: forbidden columns present: {leaked}")

    if TARGET_COL not in df.columns:
        errors.append(f"Missing target column '{TARGET_COL}'")
    elif df[TARGET_COL].notna().sum() < 100:
        errors.append(f"Too few non-null target values: {df[TARGET_COL].notna().sum()}")

    dups = df.duplicated().sum()
    if dups > 0:
        log.warning("%d duplicate rows will be dropped before saving", dups)

    if errors:
        raise AssertionError("Canonical dataset validation failed:\n  " + "\n  ".join(errors))

    log.info("Schema validation PASSED — %d rows, %d columns", len(df), len(df.columns))


# ── Main builder ───────────────────────────────────────────────────────────

def build_canonical_dataset(cfg: dict | None = None) -> Path:
    """
    Build the canonical training dataset from interim pipeline outputs.

    Parameters
    ----------
    cfg : dict, optional
        Pipeline config. Loaded from file if not provided.

    Returns
    -------
    Path
        Path to saved canonical_dataset.parquet.
    """
    cfg = cfg or get_pipeline_config()
    interim   = Path(cfg["paths"]["interim"])
    processed = Path(cfg["paths"]["processed"])

    # ── Load interim files ────────────────────────────────────
    collocated_path = interim / "collocated_pairs.parquet"
    weather_path    = interim / "weather_clean.parquet"
    static_path     = interim / "static_features_clean.parquet"

    if not collocated_path.exists():
        raise FileNotFoundError(
            f"Collocated pairs not found: {collocated_path}\n"
            "Run: python scripts/run_matching.py"
        )

    log.info("Loading collocated pairs…")
    df = pd.read_parquet(collocated_path)
    log.info("  %d rows, %d columns", len(df), len(df.columns))

    # ── Normalise column names ────────────────────────────────
    df = _normalise_schema(df)

    # ── Join ERA5 weather ─────────────────────────────────────
    if weather_path.exists():
        log.info("Joining ERA5 weather…")
        weather = pd.read_parquet(weather_path)
        df = _join_weather(df, weather)
    else:
        log.warning("Weather clean file not found: %s — weather columns will be NaN", weather_path)
        for col in WEATHER_COLS:
            if col not in df.columns:
                df[col] = np.nan

    # ── Join static features ──────────────────────────────────
    if static_path.exists():
        log.info("Joining static features…")
        static = pd.read_parquet(static_path)
        df = _join_static(df, static)
    else:
        log.warning("Static features file not found: %s — static columns will be NaN", static_path)
        for col in STATIC_COLS:
            if col not in df.columns:
                df[col] = np.nan

    # ── Add location_id if missing ─────────────────────────────
    if "location_id" not in df.columns and "latitude" in df.columns:
        df["location_id"] = (
            "pune_"
            + df["latitude"].round(2).astype(str).str.replace(".", "", regex=False)
            + "_"
            + df["longitude"].round(2).astype(str).str.replace(".", "", regex=False)
        )

    # ── Enforce no leakage ─────────────────────────────────────
    df = _enforce_no_leakage(df)

    # ── Handle missing data ────────────────────────────────────
    log.info("Applying missingness policy…")
    df = handle_missing_data(
        df,
        is_training=True,
        target_cols=[TARGET_COL],
        impute_weather=True,
        impute_satellite=False,   # XGBoost handles NaN natively
        fill_static_zeros=True,
    )
    log.info("After missingness handling: %d rows", len(df))

    # ── Drop exact duplicates ──────────────────────────────────
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if len(df) < n_before:
        log.info("Dropped %d duplicate rows", n_before - len(df))

    # ── Schema validation ─────────────────────────────────────
    validate_canonical_schema(df, cfg)

    # ── Save ──────────────────────────────────────────────────
    processed.mkdir(parents=True, exist_ok=True)
    parquet_path = processed / "canonical_dataset.parquet"
    meta_path    = processed / "canonical_dataset_meta.json"

    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    log.info("canonical_dataset.parquet saved → %s (%d rows, %d cols)",
             parquet_path, len(df), len(df.columns))

    # Compute missingness stats for meta
    missing_stats = {}
    for col in ["aod_550nm", "satellite_no2", "satellite_so2", "satellite_co", "satellite_o3",
                "temperature_2m", TARGET_COL]:
        if col in df.columns:
            missing_stats[f"missing_{col}_pct"] = round(df[col].isna().mean() * 100, 2)

    meta = {
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "city":          cfg["city"],
        "date_range":    [cfg["data"]["date_start"], cfg["data"]["date_end"]],
        "rows":          len(df),
        "columns":       len(df.columns),
        "target_col":    TARGET_COL,
        "missing_stats": missing_stats,
        "schema_version": cfg.get("schema_version", "1.0.0"),
        "column_list":   list(df.columns),
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)
    log.info("canonical_dataset_meta.json saved → %s", meta_path)

    # Print missingness summary
    log.info("\nMissingness summary:")
    summary = detect_missingness(df)
    high_missing = summary[summary["missing_pct"] > 0].sort_values("missing_pct", ascending=False)
    if len(high_missing) > 0:
        print(high_missing.to_string(index=False))
    else:
        log.info("  No missing values in canonical dataset.")

    return parquet_path


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    config = get_pipeline_config()
    path   = build_canonical_dataset(config)
    print(f"\nCanonical dataset ready: {path}")
    print("Next: python scripts/generate_data_quality_report.py")
    print("Then: open notebooks/01_eda.ipynb")
