"""
src/ingestion/weather.py
------------------------
ERA5-Land hourly reanalysis ingestion via Google Earth Engine (GEE).

Downloads:
  - 2m temperature           (K → kept raw)
  - 2m dewpoint temperature   (K → kept raw, used to derive RH in cleaning)
  - 10m U wind component      (m/s)
  - 10m V wind component      (m/s)
  - Surface pressure          (Pa → kept raw)
  - Total precipitation       (m/hr → kept raw)
  - Boundary layer height     (m)

RESPONSIBILITY: Download and save raw ERA5 observations to:
  data/raw/weather/era5_YYYYMMDD.parquet  +  _meta.json

DOES NOT:
  - Convert units (Kelvin → Celsius etc.) — that is clean_weather.py
  - Derive RH or wind speed/direction — that is clean_weather.py

Usage
-----
  python -m src.ingestion.weather --date 2024-06-01
  python -m src.ingestion.weather --start 2024-01-01 --end 2024-03-31
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.config_loader import get_pipeline_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ERA5-Land bands we download (raw names from GEE)
ERA5_BANDS = [
    "temperature_2m",             # K
    "dewpoint_temperature_2m",    # K  — used to compute RH
    "u_component_of_wind_10m",    # m/s
    "v_component_of_wind_10m",    # m/s
    "surface_pressure",           # Pa
    "total_precipitation",        # m/hr (accumulated per hour)
    "boundary_layer_height",      # m
]


def _init_gee() -> None:
    try:
        import ee  # noqa: F401
    except ImportError:
        raise ImportError(
            "GEE Python API not installed.\n"
            "Run: pip install earthengine-api && earthengine authenticate"
        )
    import ee
    try:
        ee.Initialize()
        logger.info("GEE initialised")
    except Exception as exc:
        raise RuntimeError(f"GEE init failed: {exc}") from exc


def _bbox_to_ee_geometry(bbox: dict):
    import ee
    return ee.Geometry.Rectangle([
        bbox["lon_min"], bbox["lat_min"],
        bbox["lon_max"], bbox["lat_max"],
    ])


def _save_with_provenance(
    df: pd.DataFrame,
    date_str: str,
    output_dir: Path,
    cfg: dict,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_date    = date_str.replace("-", "")
    parquet_path = output_dir / f"era5_{safe_date}.parquet"
    meta_path    = output_dir / f"era5_{safe_date}_meta.json"

    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    meta = {
        "product":          "ERA5-Land Hourly",
        "collection":       cfg["era5"]["collection"],
        "date":             date_str,
        "city":             cfg["city"],
        "acquisition_time": datetime.now(timezone.utc).isoformat(),
        "bbox":             cfg["bbox"],
        "bands":            ERA5_BANDS,
        "units_raw": {
            "temperature_2m":           "K",
            "dewpoint_temperature_2m":  "K",
            "u_component_of_wind_10m":  "m/s",
            "v_component_of_wind_10m":  "m/s",
            "surface_pressure":         "Pa",
            "total_precipitation":      "m/hr",
            "boundary_layer_height":    "m",
        },
        "note": "Units are RAW from ERA5. Conversions applied in clean_weather.py.",
        "row_count":      len(df),
        "schema_version": cfg.get("schema_version", "1.0.0"),
    }

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("Saved %d rows → %s", len(df), parquet_path)
    return parquet_path


def fetch_era5_for_date(date_str: str, cfg: dict | None = None) -> Path | None:
    """
    Fetch ERA5-Land hourly data for all 24 hours of the given date
    over the Pune bounding box.

    Parameters
    ----------
    date_str : str   "YYYY-MM-DD"
    cfg : dict, optional

    Returns
    -------
    Path or None
    """
    cfg = cfg or get_pipeline_config()
    _init_gee()

    import ee

    bbox     = _bbox_to_ee_geometry(cfg["bbox"])
    date_end = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    scale_m  = int(cfg["era5"]["grid_resolution_deg"] * 111_000)  # approx metres

    logger.info("Fetching ERA5 for %s (scale ~%dm) …", date_str, scale_m)

    collection = (
        ee.ImageCollection(cfg["era5"]["collection"])
        .filterBounds(bbox)
        .filterDate(date_str, date_end)
        .select(ERA5_BANDS)
    )

    count = collection.size().getInfo()
    logger.info("Found %d ERA5 hourly images for %s", count, date_str)

    if count == 0:
        logger.warning("No ERA5 images for %s", date_str)
        return None

    all_rows = []

    # Iterate over each hourly image to preserve the timestamp
    images = collection.toList(collection.size())
    for i in range(count):
        image = ee.Image(images.get(i))

        # Extract the image's system:time_start (milliseconds since epoch)
        ts_ms = image.get("system:time_start").getInfo()
        ts_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

        samples = image.sample(
            region=bbox,
            scale=scale_m,
            projection="EPSG:4326",
            geometries=True,
            numPixels=2000,
        )

        features = samples.getInfo().get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            geom  = feat.get("geometry", {}).get("coordinates", [None, None])
            row = {
                "latitude":     geom[1] if geom else None,
                "longitude":    geom[0] if geom else None,
                "timestamp_utc": ts_utc.isoformat(),
            }
            for band in ERA5_BANDS:
                row[band] = props.get(band)
            all_rows.append(row)

    if not all_rows:
        logger.warning("No ERA5 samples for %s", date_str)
        return None

    df = pd.DataFrame(all_rows)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)

    output_dir = Path(cfg["paths"]["raw_weather"])
    return _save_with_provenance(df, date_str, output_dir, cfg)


def fetch_era5_range(start_date: str, end_date: str, cfg: dict | None = None) -> list[Path]:
    """Fetch ERA5 for a range of dates (inclusive)."""
    cfg = cfg or get_pipeline_config()
    start   = datetime.strptime(start_date, "%Y-%m-%d")
    end     = datetime.strptime(end_date,   "%Y-%m-%d")
    saved   = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        path = fetch_era5_for_date(date_str, cfg)
        if path:
            saved.append(path)
        current += timedelta(days=1)
    logger.info("ERA5 ingestion complete. Saved %d files.", len(saved))
    return saved


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest ERA5 weather data via GEE")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date",  help="Single date (YYYY-MM-DD)")
    group.add_argument("--start", help="Start date for range (YYYY-MM-DD)")
    parser.add_argument("--end",  help="End date for range (YYYY-MM-DD)")
    args = parser.parse_args()

    config = get_pipeline_config()
    end_date = args.end or config["data"]["date_end"]

    if args.date:
        fetch_era5_for_date(args.date, config)
    else:
        fetch_era5_range(args.start, end_date, config)
