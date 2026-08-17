"""
era5_processor.py
-----------------
Preprocessing pipeline for ERA5-Land GeoTIFF exports from Google Earth Engine.

Steps:
  1. Load multi-band GeoTIFF (wind speed, wind direction, temperature,
     relative humidity, surface pressure, precipitation)
  2. Remove fill values and apply physical range clipping
  3. Reproject to WGS-84 at target resolution
  4. Save as Cloud-Optimised GeoTIFF (COG)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

BAND_NAMES = {
    1: "wind_speed_10m",
    2: "wind_direction_10m",
    3: "temperature_2m_celsius",
    4: "relative_humidity_2m_pct",
    5: "surface_pressure_hpa",
    6: "precipitation_1h_mm",
}

VALID_RANGES = {
    "wind_speed_10m":         (0.0,  100.0),
    "wind_direction_10m":     (0.0,  360.0),
    "temperature_2m_celsius": (-80.0, 60.0),
    "relative_humidity_2m_pct": (0.0, 105.0),  # slight tolerance
    "surface_pressure_hpa":   (600.0, 1100.0),
    "precipitation_1h_mm":    (0.0,  200.0),
}


def process_era5(
    input_path: str | Path,
    output_path: str | Path,
    target_crs: str = "EPSG:4326",
    target_res: float = 0.1,   # 0.1° ≈ ERA5-Land native
) -> Path:
    """
    Load, clean, reproject, and save ERA5 reanalysis data.

    Parameters
    ----------
    input_path  : path to raw GEE-exported GeoTIFF
    output_path : destination path for processed COG
    target_crs  : output CRS (default WGS-84)
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

    logger.info("Loading ERA5 from %s", input_path)

    with rasterio.open(input_path) as src:
        n_bands  = src.count
        raw      = {i: src.read(i).astype(np.float32) for i in range(1, n_bands + 1)}
        meta     = src.meta.copy()
        fill     = src.nodata if src.nodata is not None else -9999.0

        for idx, arr in raw.items():
            arr[arr == fill] = np.nan
            name = BAND_NAMES.get(idx)
            if name and name in VALID_RANGES:
                lo, hi = VALID_RANGES[name]
                arr[(arr < lo) | (arr > hi)] = np.nan
            raw[idx] = arr

        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height,
            *src.bounds, resolution=target_res
        )

        meta.update({
            "driver":    "GTiff",
            "crs":       target_crs,
            "transform": transform,
            "width":     width,
            "height":    height,
            "count":     n_bands,
            "dtype":     "float32",
            "nodata":    np.nan,
        })

        reprojected: dict[int, np.ndarray] = {}
        for idx, band in raw.items():
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

    tags = {f"band_{i}": BAND_NAMES.get(i, f"band_{i}") for i in range(1, n_bands + 1)}
    tags["source"] = input_path.name
    meta.update({"tiled": True, "compress": "deflate", "blockxsize": 256, "blockysize": 256})

    with rasterio.open(output_path, "w", **meta) as dst:
        for idx, arr in reprojected.items():
            dst.write(arr, idx)
        dst.update_tags(**tags)

    logger.info("Saved processed ERA5 → %s", output_path)
    return output_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Process ERA5 GeoTIFF")
    parser.add_argument("input",  help="Raw GEE export GeoTIFF")
    parser.add_argument("output", help="Processed output GeoTIFF")
    args = parser.parse_args()

    process_era5(args.input, args.output)
