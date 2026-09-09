"""
extract_modis_aod.py
--------------------
Python-side MODIS AOD extraction using the GEE Python API.
Extracts AOD 550nm from MOD04_3K and exports to Google Drive.

Usage:
    python ingestion/satellite/scripts/extract_modis_aod.py --help
    python ingestion/satellite/scripts/extract_modis_aod.py \
        --start-date 2024-01-01 \
        --end-date   2024-01-31 \
        --drive-folder vayudrishti_modis_aod
"""

from __future__ import annotations

import argparse
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("extract_modis_aod")

INDIA_BBOX     = [68.0, 6.5, 97.5, 37.5]
MODIS_SCALE    = 3000   # 3 km native
AOD_SCALE_FACTOR = 0.001


def initialize_gee(project: str | None = None) -> None:
    import ee

    project = project or os.getenv("GEE_PROJECT")
    if not project or project == "your-gee-project-id":
        raise ValueError(
            "GEE project not set. Update GEE_PROJECT in .env or use --project."
        )
    ee.Initialize(project=project)
    logger.info("GEE initialized ✅  project=%s", project)


def export_modis_aod(
    start_date: str,
    end_date: str,
    region_bbox: list[float],
    drive_folder: str,
    scale: int = MODIS_SCALE,
    min_qa: int = 2,
) -> None:
    """Submit GEE export tasks for MODIS AOD 550nm (Terra + Aqua)."""
    import ee

    region = ee.Geometry.Rectangle(region_bbox)

    def process_collection(collection_id: str, label: str) -> None:
        col = (
            ee.ImageCollection(collection_id)
            .filterDate(start_date, end_date)
            .filterBounds(region)
        )

        count = col.size().getInfo()
        logger.info("%s: %d images found (%s → %s)", label, count, start_date, end_date)

        # Apply QA mask and scale
        def scale_and_mask(image):
            qa = image.select("AOD_QA")
            aod = (
                image.select("Optical_Depth_Land_And_Ocean")
                .updateMask(qa.gte(min_qa))
                .multiply(AOD_SCALE_FACTOR)
                .rename("aod_550nm")
            )
            aod_470 = (
                image.select("Optical_Depth_055")
                .updateMask(qa.gte(min_qa))
                .multiply(AOD_SCALE_FACTOR)
                .rename("aod_470nm")
            )
            return aod.addBands(aod_470).copyProperties(image, ["system:time_start"])

        processed = col.map(scale_and_mask)
        composite = processed.median().clip(region)

        # Also export pixel-count band as data-coverage map
        count_band = processed.select("aod_550nm").count().rename("pixel_count").clip(region)
        composite = composite.addBands(count_band)

        safe_label = label.lower().replace(" ", "_")
        description = f"modis_aod_{safe_label}_{start_date}_to_{end_date}"

        task = ee.batch.Export.image.toDrive(
            image=composite,
            description=description,
            folder=drive_folder,
            fileNamePrefix=f"modis_aod_{safe_label}_monthly",
            region=region,
            scale=scale,
            crs="EPSG:4326",
            maxPixels=int(1e10),
        )
        task.start()
        logger.info("  ✅ Submitted: %s", description)

    # Terra
    process_collection("MODIS/061/MOD04_3K", "terra")
    # Aqua
    process_collection("MODIS/061/MYD04_3K", "aqua")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract MODIS AOD via GEE Python API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start-date",   required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date",     required=True, help="YYYY-MM-DD")
    parser.add_argument("--project",      default=None,
                        help="GEE Cloud project ID (overrides .env)")
    parser.add_argument("--drive-folder", default="vayudrishti_modis_aod")
    parser.add_argument("--scale",        type=int, default=MODIS_SCALE,
                        help="Output pixel size in metres")
    parser.add_argument("--min-qa",       type=int, default=2,
                        help="Minimum MODIS QA flag to keep (0–3)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    initialize_gee(args.project)

    logger.info("=" * 60)
    logger.info("MODIS AOD Extraction")
    logger.info("  Date range : %s → %s", args.start_date, args.end_date)
    logger.info("  Min QA     : %d", args.min_qa)
    logger.info("  Drive dir  : %s", args.drive_folder)
    logger.info("  Scale      : %d m", args.scale)
    logger.info("=" * 60)

    export_modis_aod(
        start_date=args.start_date,
        end_date=args.end_date,
        region_bbox=INDIA_BBOX,
        drive_folder=args.drive_folder,
        scale=args.scale,
        min_qa=args.min_qa,
    )

    logger.info("Export tasks submitted. Monitor at: https://code.earthengine.google.com/tasks")


if __name__ == "__main__":
    main()
