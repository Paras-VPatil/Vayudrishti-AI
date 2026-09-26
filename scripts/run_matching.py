"""
scripts/run_matching.py
-----------------------
Stage 5 — Run spatial and temporal matching on real interim data.

Pipeline
--------
  satellite_clean.parquet
  +
  cpcb_clean.parquet (stations metadata)
        |
  SpatialTemporalMatcher.match_spatial_nearest()
        |
  satellite_spatial_matched.parquet
        |
  SpatialTemporalMatcher.match_temporal_window()
        |
  collocated_pairs.parquet

Also runs the three-configuration experiment (T5.3) and saves results
to experiments/matching_experiment.csv.

Usage
-----
  python scripts/run_matching.py
  python scripts/run_matching.py --spatial-radius 25 --time-window 60
"""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path

import pandas as pd

from src.config_loader import get_pipeline_config
from src.preprocessing.spatial_temporal_matcher import SpatialTemporalMatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def run_matching(
    satellite_path: Path,
    cpcb_clean_path: Path,
    output_spatial_path: Path,
    output_collocated_path: Path,
    max_radius_km: float,
    max_time_min: float,
) -> tuple[int, int]:
    """
    Execute spatial then temporal matching.

    Returns
    -------
    (n_spatial_matched, n_collocated)
    """
    if not satellite_path.exists():
        log.warning("Satellite clean file not found: %s — skipping", satellite_path)
        return 0, 0
    if not cpcb_clean_path.exists():
        log.warning("CPCB clean file not found: %s — skipping", cpcb_clean_path)
        return 0, 0

    sat_df   = pd.read_parquet(satellite_path)
    cpcb_df  = pd.read_parquet(cpcb_clean_path)

    log.info("Satellite pixels: %d", len(sat_df))
    log.info("CPCB observations: %d", len(cpcb_df))

    # Extract unique station locations for spatial index
    station_meta_cols = [c for c in ["station_id", "latitude", "longitude"] if c in cpcb_df.columns]
    if not all(c in station_meta_cols for c in ["station_id", "latitude", "longitude"]):
        log.error("CPCB data missing station_id / lat / lon columns. Check clean_cpcb output.")
        return 0, 0

    stations_df = (
        cpcb_df[station_meta_cols]
        .drop_duplicates(subset=["station_id"])
        .dropna(subset=["latitude", "longitude"])
        .reset_index(drop=True)
    )
    log.info("Unique CPCB stations in bbox: %d", len(stations_df))

    matcher = SpatialTemporalMatcher(
        max_spatial_distance_km=max_radius_km,
        max_temporal_window_minutes=max_time_min,
    )

    # ── 1. Spatial matching ────────────────────────────────────
    log.info("Running spatial matching (radius=%.0f km)…", max_radius_km)
    spatial_matched = matcher.match_spatial_nearest(sat_df, stations_df)

    n_matched   = spatial_matched["station_id"].notna().sum()
    n_unmatched = spatial_matched["station_id"].isna().sum()
    pct_matched = 100 * n_matched / max(len(spatial_matched), 1)

    log.info("Spatial: %d matched (%.1f%%), %d unmatched", n_matched, pct_matched, n_unmatched)

    output_spatial_path.parent.mkdir(parents=True, exist_ok=True)
    spatial_matched.to_parquet(output_spatial_path, index=False, engine="pyarrow")
    log.info("Saved → %s", output_spatial_path)

    if n_matched == 0:
        log.warning("No pixels matched spatially. Check bbox / station coordinates.")
        return 0, 0

    # ── 2. Temporal matching ───────────────────────────────────
    log.info("Running temporal matching (window=±%.0f min)…", max_time_min)
    valid_spatial = spatial_matched[spatial_matched["station_id"].notna()].copy()

    collocated = matcher.match_temporal_window(valid_spatial, cpcb_df)
    n_collocated = len(collocated)
    log.info("Collocated pairs: %d", n_collocated)

    output_collocated_path.parent.mkdir(parents=True, exist_ok=True)
    collocated.to_parquet(output_collocated_path, index=False, engine="pyarrow")
    log.info("Saved → %s", output_collocated_path)

    return int(n_matched), n_collocated


def run_matching_experiment(cfg: dict, interim: Path, experiments_dir: Path) -> None:
    """
    T5.3 — Run matching with three configurations and log results.
    Saves experiments/matching_experiment.csv.
    """
    satellite_path = interim / "satellite_clean.parquet"
    cpcb_path      = interim / "cpcb_clean.parquet"

    if not satellite_path.exists() or not cpcb_path.exists():
        log.warning("Interim files missing — skipping matching experiment.")
        return

    experiments_dir.mkdir(parents=True, exist_ok=True)
    csv_path = experiments_dir / "matching_experiment.csv"

    configs = [
        {"name": "A",  "radius_km": 10.0, "time_min": 30.0},
        {"name": "B",  "radius_km": 25.0, "time_min": 60.0},
        {"name": "C",  "radius_km": 50.0, "time_min": 90.0},
    ]

    rows = []
    for exp in configs:
        log.info("Experiment %s: radius=%.0f km, window=±%.0f min",
                 exp["name"], exp["radius_km"], exp["time_min"])
        n_spatial, n_collocated = run_matching(
            satellite_path=satellite_path,
            cpcb_clean_path=cpcb_path,
            output_spatial_path=interim / f"spatial_matched_exp{exp['name']}.parquet",
            output_collocated_path=interim / f"collocated_exp{exp['name']}.parquet",
            max_radius_km=exp["radius_km"],
            max_time_min=exp["time_min"],
        )
        rows.append({
            "config":          exp["name"],
            "spatial_radius_km": exp["radius_km"],
            "time_window_min": exp["time_min"],
            "spatial_matched": n_spatial,
            "collocated_pairs": n_collocated,
        })
        log.info("  → %d spatial, %d collocated", n_spatial, n_collocated)

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    log.info("\nMatching Experiment Results:")
    log.info("%-8s %-12s %-12s %-15s %-15s",
             "Config", "Radius (km)", "Window (min)", "Spatial Matched", "Collocated Pairs")
    for row in rows:
        log.info("%-8s %-12.0f %-12.0f %-15d %-15d",
                 row["config"], row["spatial_radius_km"], row["time_window_min"],
                 row["spatial_matched"], row["collocated_pairs"])
    log.info("Saved → %s", csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run spatial+temporal matching pipeline")
    parser.add_argument("--spatial-radius", type=float, default=None,
                        help="Spatial matching radius in km (default: from config)")
    parser.add_argument("--time-window",    type=float, default=None,
                        help="Temporal window in minutes (default: from config)")
    parser.add_argument("--experiment",     action="store_true",
                        help="Run all three configs (T5.3 experiment)")
    args = parser.parse_args()

    config = get_pipeline_config()
    interim = Path(config["paths"]["interim"])
    experiments_dir = Path(config["paths"]["experiments"])

    if args.experiment:
        run_matching_experiment(config, interim, experiments_dir)
    else:
        radius = args.spatial_radius or config["spatial_matching"]["max_radius_km"]
        window = args.time_window    or config["temporal_matching"]["max_difference_minutes"]

        run_matching(
            satellite_path       = interim / "satellite_clean.parquet",
            cpcb_clean_path      = interim / "cpcb_clean.parquet",
            output_spatial_path  = interim / "satellite_spatial_matched.parquet",
            output_collocated_path = interim / "collocated_pairs.parquet",
            max_radius_km        = radius,
            max_time_min         = window,
        )
