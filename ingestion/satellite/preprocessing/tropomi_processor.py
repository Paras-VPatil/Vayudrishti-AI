"""
tropomi_processor.py
--------------------
Preprocessing pipeline for Sentinel-5P TROPOMI GeoTIFF exports from GEE.

Steps:
  1. Load multi-band GeoTIFF (NO₂, SO₂, CO, O₃, UV-AI)
  2. Remove negative / fill values
  3. Reproject to WGS-84 at target resolution
  4. Save as Cloud-Optimised GeoTIFF (COG)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Band name map: GeoTIFF band index → semantic name
BAND_NAMES = {
    1: "no2_tropospheric_column_umolm2",
    2: "so2_column_umolm2",
    3: "co_column_molm2",
    4: "o3_column_molm2",
    5: "uv_aerosol_index",
}

# Physical valid ranges (post-scaling)
VALID_RANGES = {
    "no2_tropospheric_column_umolm2": (0.0, 1000.0),
    "so2_column_umolm2":              (-50.0, 1000.0),
    "co_column_molm2":                (0.0, 1.0),
    "o3_column_molm2":                (0.0, 0.5),
    "uv_aerosol_index":               (-5.0, 25.0),
}


def process_tropomi(
    input_path: str | Path,
    output_path: str | Path,
    target_crs: str = "EPSG:4326",
    target_res: float = 0.05,  # ~5 km in degrees
) -> Path:
    """
    Load, clean, reproject, and save TROPOMI multi-band data.

    Parameters
    ----------
    input_path  : path to raw GEE-exported GeoTIFF
    output_path : destination path for processed COG
    target_crs  : output coordinate reference system
    target_res  : output pixel size in target_crs units

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

    input_path  = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading TROPOMI from %s", input_path)

    with rasterio.open(input_path) as src:
        n_bands = src.count
        raw_bands = {i: src.read(i).astype(np.float32) for i in range(1, n_bands + 1)}
        meta      = src.meta.copy()
        fill_val  = src.nodata if src.nodata is not None else -9999.0

        # ── Remove fill values & apply valid-range masking ────────────────────
        for idx, arr in raw_bands.items():
            name = BAND_NAMES.get(idx)
            arr[arr == fill_val] = np.nan
            if name and name in VALID_RANGES:
                lo, hi = VALID_RANGES[name]
                arr[(arr < lo) | (arr > hi)] = np.nan
            raw_bands[idx] = arr

        # ── Reproject ─────────────────────────────────────────────────────────
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height,
            *src.bounds, resolution=target_res
        )
        meta.update({
            "driver": "GTiff",
            "crs":       target_crs,
            "transform": transform,
            "width":     width,
            "height":    height,
            "count":     n_bands,
            "dtype":     "float32",
            "nodata":    np.nan,
        })

        reprojected: dict[int, np.ndarray] = {}
        for idx, band in raw_bands.items():
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
            reprojected[idx] = dest

    # ── Write COG ─────────────────────────────────────────────────────────────
    tags = {f"band_{i}": BAND_NAMES.get(i, f"band_{i}") for i in range(1, n_bands + 1)}
    tags["source"] = input_path.name

    meta.update({"tiled": True, "compress": "deflate", "blockxsize": 256, "blockysize": 256})
    with rasterio.open(output_path, "w", **meta) as dst:
        for idx, arr in reprojected.items():
            dst.write(arr, idx)
        dst.update_tags(**tags)

    logger.info("Saved processed TROPOMI → %s", output_path)
    return output_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Process Sentinel-5P TROPOMI GeoTIFF")
    parser.add_argument("input",  help="Raw GEE export GeoTIFF")
    parser.add_argument("output", help="Processed output GeoTIFF")
    args = parser.parse_args()

    process_tropomi(args.input, args.output)
