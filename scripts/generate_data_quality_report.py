"""
scripts/generate_data_quality_report.py
----------------------------------------
Scans the interim/ and processed/ directories and generates a
structured data quality report showing how many rows survived each
pipeline stage.

Output: data/processed/pune/data_quality_report.json

Usage
-----
  python scripts/generate_data_quality_report.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config_loader import get_pipeline_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _count_parquet_rows(path: Path) -> int | None:
    """Return number of rows in a parquet file, or None if not found."""
    if not path.exists():
        return None
    try:
        return len(pd.read_parquet(path, columns=["latitude"]))
    except Exception:
        try:
            return len(pd.read_parquet(path))
        except Exception:
            return None


def _pct_missing(path: Path, column: str) -> float | None:
    """Return percentage of null values in a specific column."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=[column])
        return round(df[column].isna().mean() * 100, 2)
    except Exception:
        return None


def _count_duplicates(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
        return int(df.duplicated().sum())
    except Exception:
        return None


def _count_invalid_coords(path: Path) -> int | None:
    """Count rows with invalid lat/lon for Pune bbox."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=["latitude", "longitude"])
        invalid = (
            ~df["latitude"].between(18.0, 19.0) |
            ~df["longitude"].between(73.0, 75.0)
        )
        return int(invalid.sum())
    except Exception:
        return None


def generate_report(cfg: dict | None = None) -> Path:
    """
    Generate the data quality report and save it as JSON.

    Returns
    -------
    Path  to the saved JSON report.
    """
    cfg = cfg or get_pipeline_config()
    paths = cfg["paths"]

    # ── Raw counts ────────────────────────────────────────────
    raw_ground_files  = list(Path(paths["raw_ground"]).glob("cpcb_*.parquet"))
    raw_sat_files_mod = list(Path(paths["raw_satellite"]).glob("modis_aod_*.parquet"))
    raw_sat_files_tro = list(Path(paths["raw_satellite"]).glob("tropomi_*.parquet"))
    raw_weather_files = list(Path(paths["raw_weather"]).glob("era5_*.parquet"))

    rows_raw_cpcb     = sum(_count_parquet_rows(f) or 0 for f in raw_ground_files)
    rows_raw_modis    = sum(_count_parquet_rows(f) or 0 for f in raw_sat_files_mod)
    rows_raw_tropomi  = sum(_count_parquet_rows(f) or 0 for f in raw_sat_files_tro)
    rows_raw_era5     = sum(_count_parquet_rows(f) or 0 for f in raw_weather_files)

    # ── Interim counts ────────────────────────────────────────
    interim = Path(paths["interim"])
    rows_clean_cpcb    = _count_parquet_rows(interim / "cpcb_clean.parquet")
    rows_clean_sat     = _count_parquet_rows(interim / "satellite_clean.parquet")
    rows_clean_weather = _count_parquet_rows(interim / "weather_clean.parquet")
    rows_spatial_match = _count_parquet_rows(interim / "satellite_spatial_matched.parquet")
    rows_collocated    = _count_parquet_rows(interim / "collocated_pairs.parquet")

    # ── Canonical counts ──────────────────────────────────────
    processed = Path(paths["processed"])
    canonical_path = processed / "canonical_dataset.parquet"
    rows_canonical = _count_parquet_rows(canonical_path)

    # ── Missing value rates ───────────────────────────────────
    missing_aod_pct = _pct_missing(interim / "satellite_clean.parquet", "aod_550nm")
    missing_no2_pct = _pct_missing(interim / "satellite_clean.parquet", "satellite_no2")
    missing_wth_pct = _pct_missing(interim / "weather_clean.parquet",   "temperature_2m")

    # ── Canonical-level quality ───────────────────────────────
    dup_canonical        = _count_duplicates(canonical_path)
    invalid_coords_canon = _count_invalid_coords(canonical_path)

    # ── Build report dict ─────────────────────────────────────
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "city":         cfg["city"],

        "raw_data": {
            "cpcb_measurement_rows":  rows_raw_cpcb,
            "cpcb_files":             len(raw_ground_files),
            "modis_aod_rows":         rows_raw_modis,
            "modis_files":            len(raw_sat_files_mod),
            "tropomi_rows":           rows_raw_tropomi,
            "tropomi_files":          len(raw_sat_files_tro),
            "era5_rows":              rows_raw_era5,
            "era5_files":             len(raw_weather_files),
        },

        "after_cleaning": {
            "cpcb_clean_rows":        rows_clean_cpcb,
            "satellite_clean_rows":   rows_clean_sat,
            "weather_clean_rows":     rows_clean_weather,
        },

        "after_matching": {
            "spatially_matched_rows": rows_spatial_match,
            "collocated_pairs_rows":  rows_collocated,
        },

        "canonical_dataset": {
            "path":                   str(canonical_path),
            "rows":                   rows_canonical,
            "exists":                 canonical_path.exists(),
        },

        "missing_value_rates_pct": {
            "aod_550nm":              missing_aod_pct,
            "satellite_no2":          missing_no2_pct,
            "temperature_2m":         missing_wth_pct,
        },

        "data_quality": {
            "canonical_duplicates":   dup_canonical,
            "canonical_invalid_coords": invalid_coords_canon,
        },

        "pipeline_status": {
            "raw_cpcb_ingested":      rows_raw_cpcb > 0,
            "raw_satellite_ingested": (rows_raw_modis + rows_raw_tropomi) > 0,
            "raw_era5_ingested":      rows_raw_era5 > 0,
            "cpcb_cleaned":           (rows_clean_cpcb or 0) > 0,
            "satellite_cleaned":      (rows_clean_sat or 0) > 0,
            "matching_done":          (rows_collocated or 0) > 0,
            "canonical_ready":        canonical_path.exists() and (rows_canonical or 0) > 1000,
        },
    }

    # ── Save ──────────────────────────────────────────────────
    processed.mkdir(parents=True, exist_ok=True)
    output_path = processed / "data_quality_report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # ── Print summary ─────────────────────────────────────────
    print("\nDATA QUALITY REPORT")
    print("=" * 50)
    print(f"Raw CPCB rows:          {rows_raw_cpcb:>10,}")
    print(f"After CPCB cleaning:    {rows_clean_cpcb or 'N/A':>10}")
    print(f"Raw satellite rows:     {rows_raw_modis + rows_raw_tropomi:>10,}")
    print(f"After satellite QA:     {rows_clean_sat or 'N/A':>10}")
    print(f"After temporal match:   {rows_collocated or 'N/A':>10}")
    print(f"Canonical dataset:      {rows_canonical or 'N/A':>10}")
    print(f"Missing AOD (%):        {missing_aod_pct or 'N/A':>10}")
    print(f"Missing NO2 (%):        {missing_no2_pct or 'N/A':>10}")
    print(f"Missing weather (%):    {missing_wth_pct or 'N/A':>10}")
    if dup_canonical is not None:
        print(f"Canonical duplicates:   {dup_canonical:>10,}")
    print("=" * 50)
    print(f"Saved → {output_path}")

    return output_path


if __name__ == "__main__":
    config = get_pipeline_config()
    generate_report(config)
