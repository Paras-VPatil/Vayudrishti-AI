"""
aod_processor.py
----------------
Preprocessing pipeline for MODIS AOD GeoTIFF exports from Google Earth Engine.

Steps:
  1. Load raw GeoTIFF (aod_550nm, aod_470nm, aod_qa bands)
  2. Apply QA masking (keep QA >= 2 : "good" or "very good")
  3. Clip to region of interest
  4. Reproject to WGS-84 at target resolution
  5. Save as Cloud-Optimised GeoTIFF (COG)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# QA threshold: 0=poor, 1=marginal, 2=good, 3=very good
MIN_QA = 2


def process_aod(
    input_path: str | Path,
    output_path: str | Path,
    min_qa: int = MIN_QA,
    target_crs: str = "EPSG:4326",
    target_res: float = 0.025,  # ~2.5 km in degrees
) -> Path:
    """
    Load, QA-filter, reproject, and save MODIS AOD data.

    Parameters
    ----------
    input_path : path to raw GEE-exported GeoTIFF
    output_path : destination path for processed COG
    min_qa : minimum QA flag value to retain (default 2 = "good")
    target_crs : output coordinate reference system
    target_res : output pixel size in target_crs units

    Returns
    -------
    Path to the written output file.
    """
    try:
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.warp import calculate_default_transform, reproject
    except ImportError as e:
        raise ImportError("rasterio is required. Run: pip install rasterio") from e

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading AOD from %s", input_path)

    with rasterio.open(input_path) as src:
        # Band order from GEE export: 1=aod_550nm, 2=aod_470nm, 3=aod_qa
        aod_550 = src.read(1).astype(np.float32)
        aod_470 = src.read(2).astype(np.float32) if src.count >= 2 else None
        qa      = src.read(3).astype(np.int16)   if src.count >= 3 else None

        meta = src.meta.copy()
        nodata = src.nodata if src.nodata is not None else -9999.0

        # ── QA masking ────────────────────────────────────────────────────────
        if qa is not None:
            mask = qa < min_qa
            aod_550[mask] = np.nan
            if aod_470 is not None:
                aod_470[mask] = np.nan
            logger.info("Masked %.1f%% of pixels (QA < %d)",
                        mask.mean() * 100, min_qa)

        # ── Replace fill values ────────────────────────────────────────────────
        fill = nodata if nodata is not None else -28672  # MODIS fill
        aod_550[aod_550 == fill] = np.nan

        # ── Reproject ─────────────────────────────────────────────────────────
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height,
            *src.bounds, resolution=target_res
        )
        meta.update({
            "driver": "GTiff",
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "count": 2 if aod_470 is not None else 1,
            "dtype": "float32",
            "nodata": np.nan,
        })

        bands = [aod_550]
        if aod_470 is not None:
            bands.append(aod_470)

        reprojected = []
        for band in bands:
            dest = np.full((height, width), np.nan, dtype=np.float32)
            reproject(
                source=band,
                destination=dest,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=target_crs,
                resampling=Resampling.bilinear,
            )
            reprojected.append(dest)

    # ── Write Cloud-Optimised GeoTIFF ─────────────────────────────────────────
    meta.update({"tiled": True, "compress": "deflate", "blockxsize": 256, "blockysize": 256})
    with rasterio.open(output_path, "w", **meta) as dst:
        for i, band in enumerate(reprojected, start=1):
            dst.write(band, i)
        dst.update_tags(
            band_1="aod_550nm",
            band_2="aod_470nm" if len(reprojected) > 1 else "n/a",
            min_qa=str(min_qa),
            source=str(input_path.name),
        )

    logger.info("Saved processed AOD → %s", output_path)
    return output_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Process MODIS AOD GeoTIFF")
    parser.add_argument("input",  help="Path to raw GEE-exported GeoTIFF")
    parser.add_argument("output", help="Path for processed output GeoTIFF")
    parser.add_argument("--min-qa", type=int, default=MIN_QA)
    args = parser.parse_args()

    process_aod(args.input, args.output, min_qa=args.min_qa)
