"""
extract_tropomi.py
------------------
Python-side TROPOMI extraction using the GEE Python API.
Extracts NO₂, SO₂, CO, O₃, and UV Aerosol Index for India
and exports each band as a GeoTIFF to Google Drive.

Usage:
    python ingestion/satellite/scripts/extract_tropomi.py --help
    python ingestion/satellite/scripts/extract_tropomi.py \
        --start-date 2024-01-01 \
        --end-date   2024-01-31 \
        --drive-folder vayudrishti_tropomi
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("extract_tropomi")

# ── India bounding box ─────────────────────────────────────────────────────────
INDIA_BBOX = [68.0, 6.5, 97.5, 37.5]   # [lon_min, lat_min, lon_max, lat_max]

# ── TROPOMI product definitions ────────────────────────────────────────────────
PRODUCTS = {
    "no2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band":       "tropospheric_NO2_column_number_density",
        "qa_band":    "qa_value",
        "qa_min":     0.75,
        "scale":      1e6,           # → µmol/m²
        "out_name":   "no2_tropospheric_column_umolm2",
        "description": "Tropospheric NO₂ column density",
        "units":       "µmol/m²",
    },
    "so2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_SO2",
        "band":       "SO2_column_number_density",
        "qa_band":    "qa_value",
        "qa_min":     0.5,
        "scale":      1e6,
        "out_name":   "so2_column_umolm2",
        "description": "SO₂ total column",
        "units":       "µmol/m²",
    },
    "co": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band":       "CO_column_number_density",
        "qa_band":    "qa_value",
        "qa_min":     0.5,
        "scale":      1.0,
        "out_name":   "co_column_molm2",
        "description": "CO total column",
        "units":       "mol/m²",
    },
    "o3": {
        "collection": "COPERNICUS/S5P/OFFL/L3_O3",
        "band":       "O3_column_number_density",
        "qa_band":    "qa_value",
        "qa_min":     0.5,
        "scale":      1.0,
        "out_name":   "o3_column_molm2",
        "description": "O₃ total column",
        "units":       "mol/m²",
    },
    "aer_ai": {
        "collection": "COPERNICUS/S5P/OFFL/L3_AER_AI",
        "band":       "absorbing_aerosol_index",
        "qa_band":    None,          # No QA band for AER_AI
        "qa_min":     None,
        "scale":      1.0,
        "out_name":   "uv_aerosol_index",
        "description": "UV Absorbing Aerosol Index",
        "units":       "dimensionless",
    },
}


def initialize_gee(project: str | None = None) -> None:
    """Initialize the GEE Python API."""
    import ee

    project = project or os.getenv("GEE_PROJECT")
    if not project or project == "your-gee-project-id":
        raise ValueError(
            "GEE project ID not set. "
            "Update GEE_PROJECT in .env or pass --project flag."
        )
    ee.Initialize(project=project)
    logger.info("GEE initialized ✅  project=%s", project)


def export_product(
    product_key: str,
    start_date: str,
    end_date: str,
    region_bbox: list[float],
    drive_folder: str,
    scale: int = 5000,
) -> str:
    """
    Submit a GEE export task for a single TROPOMI product.

    Returns the task description string.
    """
    import ee

    cfg = PRODUCTS[product_key]
    region = ee.Geometry.Rectangle(region_bbox)

    logger.info(
        "Loading %s (%s) %s → %s",
        product_key.upper(), cfg["collection"], start_date, end_date,
    )

    col = (
        ee.ImageCollection(cfg["collection"])
        .filterDate(start_date, end_date)
        .filterBounds(region)
        .select(cfg["band"])
    )

    # QA filtering
    if cfg["qa_band"]:
        full_col = (
            ee.ImageCollection(cfg["collection"])
            .filterDate(start_date, end_date)
            .filterBounds(region)
        )
        col = full_col.map(
            lambda img: img.updateMask(
                img.select(cfg["qa_band"]).gte(cfg["qa_min"])
            ).select(cfg["band"])
        )

    # Monthly median composite
    composite = col.median().multiply(cfg["scale"]).rename(cfg["out_name"]).clip(region)

    # Count valid pixels
    count = col.size().getInfo()
    logger.info("  Images in collection: %d", count)

    description = f"tropomi_{product_key}_{start_date}_to_{end_date}"

    task = ee.batch.Export.image.toDrive(
        image=composite,
        description=description,
        folder=drive_folder,
        fileNamePrefix=f"tropomi_{product_key}_monthly",
        region=region,
        scale=scale,
        crs="EPSG:4326",
        maxPixels=int(1e10),
    )
    task.start()

    logger.info(
        "  ✅ Export task submitted: %s  [Drive folder: %s]",
        description, drive_folder,
    )
    return description


def list_tasks() -> None:
    """Print status of all active GEE export tasks."""
    import ee

    tasks = ee.batch.Task.list()
    if not tasks:
        logger.info("No active GEE tasks found.")
        return

    logger.info("Active GEE tasks:")
    for t in tasks[:20]:
        logger.info(
            "  %-50s  state=%-10s  id=%s",
            t.config.get("description", "?"),
            t.state,
            t.id,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract TROPOMI trace-gas columns via GEE Python API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-date",    required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date",      required=True, help="YYYY-MM-DD")
    parser.add_argument("--project",       default=None,
                        help="GEE Cloud project ID (overrides .env)")
    parser.add_argument("--drive-folder",  default="vayudrishti_tropomi",
                        help="Google Drive folder for exports")
    parser.add_argument("--scale",         type=int, default=5000,
                        help="Output pixel size in metres (default 5000 m)")
    parser.add_argument(
        "--products",
        nargs="+",
        default=list(PRODUCTS.keys()),
        choices=list(PRODUCTS.keys()),
        help="Which TROPOMI products to extract",
    )
    parser.add_argument("--list-tasks", action="store_true",
                        help="List current GEE tasks and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    initialize_gee(args.project)

    if args.list_tasks:
        list_tasks()
        return

    logger.info("=" * 60)
    logger.info("TROPOMI Extraction Pipeline")
    logger.info("  Date range : %s → %s", args.start_date, args.end_date)
    logger.info("  Products   : %s", ", ".join(args.products))
    logger.info("  Drive dir  : %s", args.drive_folder)
    logger.info("  Scale      : %d m", args.scale)
    logger.info("=" * 60)

    submitted = []
    for product in args.products:
        desc = export_product(
            product_key=product,
            start_date=args.start_date,
            end_date=args.end_date,
            region_bbox=INDIA_BBOX,
            drive_folder=args.drive_folder,
            scale=args.scale,
        )
        submitted.append(desc)

    logger.info("=" * 60)
    logger.info("All %d export tasks submitted to GEE.", len(submitted))
    logger.info("Monitor progress at: https://code.earthengine.google.com/tasks")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
