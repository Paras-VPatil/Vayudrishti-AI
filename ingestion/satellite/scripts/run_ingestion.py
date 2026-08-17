"""
run_ingestion.py
----------------
CLI orchestrator for the full Vayudrishti-AI satellite ingestion pipeline.

Runs in sequence:
  1. AOD preprocessing  (MODIS MOD04_3K)
  2. TROPOMI preprocessing (Sentinel-5P)
  3. ERA5 preprocessing
  4. Feature merging → processed Parquet

Usage:
    python ingestion/satellite/scripts/run_ingestion.py --help
    python ingestion/satellite/scripts/run_ingestion.py \
        --start-date 2024-01-01 \
        --end-date   2024-01-31 \
        --raw-dir    data/raw/satellite \
        --output-dir data/processed
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

# Ensure project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.satellite.preprocessing.aod_processor    import process_aod
from ingestion.satellite.preprocessing.era5_processor   import process_era5
from ingestion.satellite.preprocessing.tropomi_processor import process_tropomi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_ingestion")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vayudrishti-AI — satellite ingestion pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-date", required=True,
                        help="Ingestion start date (YYYY-MM-DD)")
    parser.add_argument("--end-date",   required=True,
                        help="Ingestion end date   (YYYY-MM-DD)")
    parser.add_argument("--raw-dir",    default="data/raw/satellite",
                        help="Root directory containing raw GEE GeoTIFF exports")
    parser.add_argument("--output-dir", default="data/processed",
                        help="Root directory for processed outputs")
    parser.add_argument("--skip-aod",     action="store_true")
    parser.add_argument("--skip-tropomi", action="store_true")
    parser.add_argument("--skip-era5",    action="store_true")
    return parser.parse_args()


def find_geotiff(raw_dir: Path, prefix: str) -> Path | None:
    """Locate the first GeoTIFF matching a prefix in raw_dir."""
    matches = list(raw_dir.glob(f"{prefix}*.tif")) + list(raw_dir.glob(f"{prefix}*.tiff"))
    if not matches:
        logger.warning("No GeoTIFF found for prefix '%s' in %s", prefix, raw_dir)
        return None
    if len(matches) > 1:
        logger.warning("Multiple files found for '%s'; using first: %s", prefix, matches[0])
    return matches[0]


def run_pipeline(args: argparse.Namespace) -> None:
    raw_dir    = Path(args.raw_dir)
    output_dir = Path(args.output_dir)

    logger.info("=" * 60)
    logger.info("Vayudrishti-AI Ingestion Pipeline")
    logger.info("  Date range : %s → %s", args.start_date, args.end_date)
    logger.info("  Raw dir    : %s", raw_dir)
    logger.info("  Output dir : %s", output_dir)
    logger.info("=" * 60)

    processed = {}

    # ── 1. AOD ────────────────────────────────────────────────────────────────
    if not args.skip_aod:
        src = find_geotiff(raw_dir / "modis", "modis_aod")
        if src:
            dst = output_dir / "aod_processed.tif"
            processed["aod"] = process_aod(src, dst)
        else:
            logger.warning("AOD step skipped — no source file found.")
    else:
        logger.info("AOD step skipped (--skip-aod).")

    # ── 2. TROPOMI ────────────────────────────────────────────────────────────
    if not args.skip_tropomi:
        src = find_geotiff(raw_dir / "tropomi", "tropomi")
        if src:
            dst = output_dir / "tropomi_processed.tif"
            processed["tropomi"] = process_tropomi(src, dst)
        else:
            logger.warning("TROPOMI step skipped — no source file found.")
    else:
        logger.info("TROPOMI step skipped (--skip-tropomi).")

    # ── 3. ERA5 ───────────────────────────────────────────────────────────────
    if not args.skip_era5:
        src = find_geotiff(raw_dir / "era5", "era5")
        if src:
            dst = output_dir / "era5_processed.tif"
            processed["era5"] = process_era5(src, dst)
        else:
            logger.warning("ERA5 step skipped — no source file found.")
    else:
        logger.info("ERA5 step skipped (--skip-era5).")

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Pipeline complete. Processed outputs:")
    for name, path in processed.items():
        logger.info("  %-10s → %s", name.upper(), path)
    if not processed:
        logger.warning("  No outputs produced — check raw data directory.")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline(parse_args())
