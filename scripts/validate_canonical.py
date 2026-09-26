"""
scripts/validate_canonical.py
------------------------------
Validates that canonical_dataset.parquet meets the required schema
and data-quality invariants before ML training begins.

Fails loudly (raises AssertionError) if any check fails.
Prints a green summary on success.

Usage
-----
  python scripts/validate_canonical.py
  python scripts/validate_canonical.py --path data/processed/pune/canonical_dataset.parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Required columns (provenance + features + target)
REQUIRED_COLUMNS = [
    "location_id",
    "station_id",
    "latitude",
    "longitude",
    "timestamp_utc",
    "distance_to_station_km",
    "temporal_offset_minutes",
    "aod_550nm",
    "satellite_no2",
    "satellite_so2",
    "satellite_co",
    "satellite_o3",
    "is_aod_missing",
    "is_no2_missing",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "boundary_layer_height",
    "surface_pressure",
    "road_density",
    "building_density",
    "elevation_m",
    "pm25_ground",   # THE ONLY ML TARGET
]

# Leakage — these must NOT appear anywhere
FORBIDDEN_COLUMNS = {
    "aqi_label",
    "aqi_category",
    "aqi_calculated",
    "aqi_index",
    "pm25_predicted",   # never include model output in training features
}

# Pune spatial bounds
LAT_MIN, LAT_MAX = 18.0, 19.0
LON_MIN, LON_MAX = 73.0, 75.0

# Physical bounds
PHYSICAL_BOUNDS = {
    "pm25_ground":          (0.0,   1000.0),
    "aod_550nm":            (0.0,   5.0),
    "temperature_2m":       (-50.0, 60.0),
    "relative_humidity_2m": (0.0,   100.0),
    "wind_speed_10m":       (0.0,   100.0),
    "boundary_layer_height":(50.0,  6000.0),
    "surface_pressure":     (800.0, 1100.0),
}


def validate(path: Path) -> bool:
    """
    Run all validation checks on the canonical dataset.

    Returns True on success, raises AssertionError on failure.
    """
    print(f"\nValidating: {path}")
    print("=" * 60)

    if not path.exists():
        raise FileNotFoundError(f"Canonical dataset not found: {path}")

    df = pd.read_parquet(path)
    print(f"  Rows:    {len(df):,}")
    print(f"  Columns: {len(df.columns)}")

    errors = []

    # ── 1. Minimum row count ──────────────────────────────────
    if len(df) < 1000:
        errors.append(f"Too few rows: {len(df)} (minimum 1000 required)")

    # ── 2. Required columns present ──────────────────────────
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # ── 3. No leakage columns ────────────────────────────────
    leaked = FORBIDDEN_COLUMNS & set(df.columns)
    if leaked:
        errors.append(f"TARGET LEAKAGE DETECTED — forbidden columns present: {leaked}")

    # ── 4. Coordinate bounds ─────────────────────────────────
    if "latitude" in df.columns:
        bad_lat = (~df["latitude"].between(LAT_MIN, LAT_MAX)).sum()
        if bad_lat > 0:
            errors.append(f"{bad_lat} rows have latitude outside Pune range [{LAT_MIN}, {LAT_MAX}]")

    if "longitude" in df.columns:
        bad_lon = (~df["longitude"].between(LON_MIN, LON_MAX)).sum()
        if bad_lon > 0:
            errors.append(f"{bad_lon} rows have longitude outside Pune range [{LON_MIN}, {LON_MAX}]")

    # ── 5. Timestamp parseable as UTC ────────────────────────
    if "timestamp_utc" in df.columns:
        ts = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
        n_nat = ts.isna().sum()
        if n_nat > 0:
            errors.append(f"{n_nat} rows have unparseable timestamp_utc")

    # ── 6. Target must be non-null (for at least 50% of rows) ─
    if "pm25_ground" in df.columns:
        n_target_null = df["pm25_ground"].isna().sum()
        pct_null = n_target_null / len(df) * 100
        if pct_null > 50:
            errors.append(
                f"pm25_ground is null for {pct_null:.1f}% of rows "
                f"(threshold: max 50% null)"
            )
        print(f"  pm25_ground: {n_target_null:,} null ({pct_null:.1f}%)")

    # ── 7. Duplicates ────────────────────────────────────────
    n_dup = df.duplicated().sum()
    if n_dup > 0:
        errors.append(f"{n_dup} duplicate rows detected")

    # ── 8. Physical bounds ───────────────────────────────────
    for col, (lo, hi) in PHYSICAL_BOUNDS.items():
        if col not in df.columns:
            continue
        valid = df[col].dropna()
        n_oob = ((valid < lo) | (valid > hi)).sum()
        if n_oob > 0:
            errors.append(
                f"{n_oob} rows in '{col}' are outside physical bounds [{lo}, {hi}]"
            )

    # ── 9. Temporal offset within acceptable window ──────────
    if "temporal_offset_minutes" in df.columns:
        max_offset = df["temporal_offset_minutes"].abs().max()
        if max_offset > 90:
            errors.append(
                f"temporal_offset_minutes max = {max_offset:.1f} "
                "(expected ≤ 90 min — check matching parameters)"
            )

    # ── Summary ───────────────────────────────────────────────
    if errors:
        print("\n  FAILED — errors found:")
        for i, err in enumerate(errors, 1):
            print(f"    [{i}] {err}")
        raise AssertionError(f"Canonical dataset validation failed with {len(errors)} error(s).")

    print("\n  ALL CHECKS PASSED")
    print(f"  Rows:              {len(df):,}")
    print(f"  Columns:           {len(df.columns)}")
    if "latitude" in df.columns:
        print(f"  Lat range:         {df['latitude'].min():.4f} – {df['latitude'].max():.4f}")
    if "pm25_ground" in df.columns:
        print(f"  PM2.5 range:       {df['pm25_ground'].min():.1f} – {df['pm25_ground'].max():.1f} µg/m³")
    print("=" * 60)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate canonical_dataset.parquet")
    parser.add_argument(
        "--path",
        default="data/processed/pune/canonical_dataset.parquet",
        help="Path to the canonical dataset parquet file",
    )
    args = parser.parse_args()

    try:
        validate(Path(args.path))
        sys.exit(0)
    except (AssertionError, FileNotFoundError) as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
