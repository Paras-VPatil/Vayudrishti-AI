"""
generate_mock_data.py
---------------------
Generates synthetic AQI feature records that conform to aqi_feature_schema.json.
Useful for pipeline testing without real satellite data.

Usage:
    python mock_data/generate_mock_data.py
    python mock_data/generate_mock_data.py --rows 5000 --seed 99 --output mock_data/mock_aqi_features.csv
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── India bounding box ─────────────────────────────────────────────────────────
LAT_MIN, LAT_MAX = 6.5,  37.5
LON_MIN, LON_MAX = 68.0, 97.5

# ── AQI category thresholds (India NAQI) ──────────────────────────────────────
AQI_CATEGORIES = [
    (0,   50,  "Good"),
    (51,  100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 500, "Severe"),
]

LAND_USE_CLASSES = [
    "Tree cover", "Shrubland", "Grassland", "Cropland",
    "Built-up", "Bare / sparse vegetation", "Snow and ice",
    "Permanent water bodies", "Herbaceous wetland",
]


def aqi_to_category(aqi: float) -> str:
    for lo, hi, cat in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return cat
    return "Severe"


def random_timestamp(base: datetime, jitter_hours: int = 720) -> str:
    """Return an ISO-8601 UTC timestamp within ±jitter_hours of base."""
    delta = timedelta(hours=random.randint(-jitter_hours, jitter_hours))
    return (base + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_record(rng: np.random.Generator, base_dt: datetime) -> dict:
    lat = float(rng.uniform(LAT_MIN, LAT_MAX))
    lon = float(rng.uniform(LON_MIN, LON_MAX))
    ts  = random_timestamp(base_dt)

    # Correlated AQI + AOD (higher AOD → higher AQI with noise)
    aod = float(rng.uniform(0.05, 2.5))
    aqi = float(np.clip(aod * 180 + rng.normal(0, 40), 0, 500))

    # Introduce realistic missingness (~10 % per satellite field)
    def maybe_none(val, p_missing: float = 0.10):
        return None if rng.random() < p_missing else val

    record = {
        "record_id": f"{lat:.4f}_{lon:.4f}_{ts[:13].replace('-','').replace('T','')}",
        "latitude":  round(lat, 6),
        "longitude": round(lon, 6),
        "timestamp_utc": ts,

        # AOD
        "aod_550nm":  maybe_none(round(aod, 4)),
        "aod_470nm":  maybe_none(round(float(aod * rng.uniform(0.9, 1.2)), 4)),
        "aod_qa_flag": maybe_none(int(rng.integers(0, 4))),

        # TROPOMI
        "no2_tropospheric_column": maybe_none(round(float(rng.uniform(0, 300)), 3)),
        "so2_column":              maybe_none(round(float(rng.uniform(0, 50)),  3)),
        "co_column":               maybe_none(round(float(rng.uniform(0, 0.5)), 4)),
        "o3_column":               maybe_none(round(float(rng.uniform(0.1, 0.4)), 4)),
        "uv_aerosol_index":        maybe_none(round(float(rng.uniform(-2, 10)), 3)),

        # ERA5 meteorology
        "wind_speed_10m":       maybe_none(round(float(rng.uniform(0, 20)),   2)),
        "wind_direction_10m":   maybe_none(round(float(rng.uniform(0, 360)),  1)),
        "relative_humidity_2m": maybe_none(round(float(rng.uniform(10, 95)), 1)),
        "temperature_2m":       maybe_none(round(float(rng.uniform(-5, 45)),  1)),
        "surface_pressure":     maybe_none(round(float(rng.uniform(900, 1030)), 1)),
        "boundary_layer_height":maybe_none(round(float(rng.uniform(100, 3000)), 0)),
        "precipitation_1h":     maybe_none(round(float(rng.exponential(0.5)),  3)),

        # Static features
        "land_use_class":          rng.choice(LAND_USE_CLASSES + [None], p=[0.1]*9 + [0.1]),
        "elevation_m":             maybe_none(round(float(rng.uniform(0, 3500)), 0)),
        "population_density":      maybe_none(round(float(rng.exponential(500)),  1)),
        "distance_to_road_km":     maybe_none(round(float(rng.uniform(0, 50)),  2)),
        "distance_to_industry_km": maybe_none(round(float(rng.uniform(0, 100)), 2)),

        # Ground truth
        "pm25_ground": maybe_none(round(float(rng.uniform(5, 300)), 1), p_missing=0.4),
        "pm10_ground": maybe_none(round(float(rng.uniform(10, 500)), 1), p_missing=0.4),

        # Target
        "aqi_label":    round(aqi, 1),
        "aqi_category": aqi_to_category(aqi),

        # Metadata
        "split":       rng.choice(["train", "val", "test"], p=[0.7, 0.15, 0.15]),
        "data_source": "mock_generator_v1",
    }
    return record


def validate_against_schema(df: pd.DataFrame, schema_path: Path) -> None:
    """Optional: validate a sample of rows against the JSON Schema."""
    try:
        import jsonschema
    except ImportError:
        print("  ⚠  jsonschema not installed — skipping schema validation.")
        return

    with open(schema_path) as f:
        schema = json.load(f)

    errors = 0
    sample = df.sample(min(100, len(df))).to_dict(orient="records")
    for row in sample:
        # Replace NaN with None for JSON compatibility
        row = {k: (None if (isinstance(v, float) and np.isnan(v)) else v)
               for k, v in row.items()}
        try:
            jsonschema.validate(instance=row, schema=schema)
        except jsonschema.ValidationError as e:
            print(f"  ❌ Validation error: {e.message}")
            errors += 1

    if errors == 0:
        print(f"  ✅ All {len(sample)} sampled rows passed schema validation.")
    else:
        print(f"  ⚠  {errors}/{len(sample)} rows failed validation.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic AQI feature data")
    parser.add_argument("--rows",   type=int,  default=1000,
                        help="Number of records to generate (default: 1000)")
    parser.add_argument("--seed",   type=int,  default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output", type=str,
                        default="mock_data/mock_aqi_features.csv",
                        help="Output CSV path")
    parser.add_argument("--validate", action="store_true",
                        help="Validate output against schemas/aqi_feature_schema.json")
    args = parser.parse_args()

    rng     = np.random.default_rng(args.seed)
    base_dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    print(f"🔧 Generating {args.rows} mock records (seed={args.seed}) …")
    records = [generate_record(rng, base_dt) for _ in range(args.rows)]
    df      = pd.DataFrame(records)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"✅ Saved → {out}  ({len(df)} rows × {len(df.columns)} columns)")

    # Print quick stats
    print(f"\n📊 AQI distribution:\n{df['aqi_category'].value_counts().to_string()}")
    print(f"\n📊 Split distribution:\n{df['split'].value_counts().to_string()}")
    print(f"\n📊 Missing values (%):\n"
          f"{(df.isnull().mean() * 100).round(1).to_string()}")

    if args.validate:
        schema_path = Path(__file__).parent.parent / "schemas" / "aqi_feature_schema.json"
        if schema_path.exists():
            print("\n🔍 Validating against schema …")
            validate_against_schema(df, schema_path)
        else:
            print(f"  ⚠  Schema not found at {schema_path}")


if __name__ == "__main__":
    main()
