"""
src/ingestion/satellite.py
--------------------------
Satellite data ingestion via Google Earth Engine (GEE) Python API.

Downloads:
  1. MODIS MAIAC AOD  (MCD19A2_GRANULES, 1 km)
  2. Sentinel-5P TROPOMI NO2, SO2, CO, O3

RESPONSIBILITY: Download raw satellite data and save to:
  data/raw/satellite/modis_aod_YYYYMMDD.parquet  + _meta.json
  data/raw/satellite/tropomi_YYYYMMDD.parquet    + _meta.json

DOES NOT:
  - Apply QA filtering (that is src/preprocessing/clean_satellite.py)
  - Compute derived products or indices

Prerequisites
-------------
  1. Google Earth Engine Python API installed: pip install earthengine-api
  2. Authenticated:  earthengine authenticate
  3. A GEE project set: earthengine set_project <your-project>

Usage
-----
  python -m src.ingestion.satellite --product modis --date 2024-06-01
  python -m src.ingestion.satellite --product tropomi --start 2024-01-01 --end 2024-03-31
  python -m src.ingestion.satellite --product all --date 2024-06-01
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.config_loader import get_pipeline_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _init_gee(project: str | None = None) -> None:
    """
    Initialise Google Earth Engine.
    Raises ImportError if earthengine-api is not installed.
    """
    try:
        import ee  # noqa: F401
    except ImportError:
        raise ImportError(
            "Google Earth Engine Python API not installed.\n"
            "Run: pip install earthengine-api\n"
            "Then: earthengine authenticate"
        )
    import ee
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
        logger.info("GEE initialised successfully")
    except Exception as exc:
        raise RuntimeError(
            f"GEE initialisation failed: {exc}\n"
            "Run: earthengine authenticate\n"
            "Then: earthengine set_project <your-gee-project-id>"
        ) from exc


def _bbox_to_ee_geometry(bbox: dict):
    """Convert pipeline_config bbox dict to an ee.Geometry.Rectangle."""
    import ee
    return ee.Geometry.Rectangle([
        bbox["lon_min"], bbox["lat_min"],
        bbox["lon_max"], bbox["lat_max"],
    ])


def _save_with_provenance(
    df: pd.DataFrame,
    product: str,
    date_str: str,
    output_dir: Path,
    cfg: dict,
    extra_meta: dict | None = None,
) -> Path:
    """Save DataFrame + write _meta.json provenance sidecar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_date = date_str.replace("-", "")
    parquet_path = output_dir / f"{product}_{safe_date}.parquet"
    meta_path    = output_dir / f"{product}_{safe_date}_meta.json"

    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    meta = {
        "product":          product,
        "date":             date_str,
        "city":             cfg["city"],
        "acquisition_time": datetime.now(timezone.utc).isoformat(),
        "bbox":             cfg["bbox"],
        "row_count":        len(df),
        "columns":          list(df.columns),
        "schema_version":   cfg.get("schema_version", "1.0.0"),
    }
    if extra_meta:
        meta.update(extra_meta)

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("Saved %d rows → %s", len(df), parquet_path)
    return parquet_path


# ── MODIS AOD ──────────────────────────────────────────────────────────────

def fetch_modis_aod(date_str: str, cfg: dict | None = None) -> Path | None:
    """
    Download MODIS MAIAC AOD for Pune on a given date.

    Raw output columns:
        aod_550nm, aod_qa_flag, latitude, longitude, timestamp_utc

    QA flag semantics (kept raw — cleaning module applies the >= 2 filter):
        0 = Best quality
        1 = Good quality
        2 = Not checked
        ≥3 = Bad / Cloudy

    Parameters
    ----------
    date_str : str   e.g. "2024-06-01"
    cfg : dict, optional

    Returns
    -------
    Path or None
    """
    cfg = cfg or get_pipeline_config()
    _init_gee()

    import ee

    bbox     = _bbox_to_ee_geometry(cfg["bbox"])
    sat_cfg  = cfg["satellite"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_end = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    collection_id = sat_cfg["modis_collection"]
    aod_band      = sat_cfg.get("modis_aod_band", "Optical_Depth_055")
    qa_band       = "AOD_QA"

    logger.info("Fetching MODIS AOD from %s for %s …", collection_id, date_str)

    collection = (
        ee.ImageCollection(collection_id)
        .filterBounds(bbox)
        .filterDate(date_str, date_end)
        .select([aod_band, qa_band])
    )

    image_count = collection.size().getInfo()
    logger.info("Found %d MODIS granules for %s", image_count, date_str)

    if image_count == 0:
        logger.warning("No MODIS granules for %s", date_str)
        return None

    # Sample the collection to points within the bounding box
    # Use a 1 km grid (matching spatial resolution)
    mosaic = collection.mosaic()
    scale  = 1000  # 1 km in metres

    samples = mosaic.sample(
        region=bbox,
        scale=scale,
        projection="EPSG:4326",
        geometries=True,
        numPixels=50000,
    )

    features = samples.getInfo().get("features", [])

    rows = []
    for feat in features:
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {}).get("coordinates", [None, None])
        rows.append({
            "aod_550nm":     props.get(aod_band),
            "aod_qa_flag":   props.get(qa_band),
            "latitude":      geom[1] if geom else None,
            "longitude":     geom[0] if geom else None,
            "timestamp_utc": f"{date_str}T10:30:00Z",  # Terra nominal overpass
        })

    if not rows:
        logger.warning("No pixel samples extracted for MODIS AOD on %s", date_str)
        return None

    df = pd.DataFrame(rows)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)

    output_dir = Path(cfg["paths"]["raw_satellite"])
    return _save_with_provenance(
        df, "modis_aod", date_str, output_dir, cfg,
        extra_meta={"collection": collection_id, "aod_band": aod_band, "scale_m": scale},
    )


# ── Sentinel-5P TROPOMI ────────────────────────────────────────────────────

_TROPOMI_CONFIGS = {
    "no2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band":       "tropospheric_NO2_column_number_density",
        "qa_band":    "qa_value",
        "overpass_time": "13:30:00Z",
        "unit":       "mol/m^2",
    },
    "so2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_SO2",
        "band":       "SO2_column_number_density",
        "qa_band":    "qa_value",
        "overpass_time": "13:30:00Z",
        "unit":       "mol/m^2",
    },
    "co": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band":       "CO_column_number_density",
        "qa_band":    "qa_value",
        "overpass_time": "13:30:00Z",
        "unit":       "mol/m^2",
    },
    "o3": {
        "collection": "COPERNICUS/S5P/OFFL/L3_O3",
        "band":       "O3_column_number_density",
        "qa_band":    "qa_value",
        "overpass_time": "13:30:00Z",
        "unit":       "mol/m^2",
    },
}


def _fetch_single_tropomi_species(
    species: str,
    date_str: str,
    bbox,
    cfg: dict,
) -> pd.DataFrame:
    """
    Download one TROPOMI species for a given date.
    Returns a DataFrame with raw (un-QA-filtered) values.
    """
    import ee

    spec = _TROPOMI_CONFIGS[species]
    date_end = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    collection = (
        ee.ImageCollection(spec["collection"])
        .filterBounds(bbox)
        .filterDate(date_str, date_end)
        .select([spec["band"], spec["qa_band"]])
    )

    count = collection.size().getInfo()
    if count == 0:
        logger.warning("No TROPOMI %s granules for %s", species.upper(), date_str)
        return pd.DataFrame()

    mosaic   = collection.mosaic()
    samples  = mosaic.sample(
        region=bbox,
        scale=7000,  # ~7 km — approximate TROPOMI pixel size
        projection="EPSG:4326",
        geometries=True,
        numPixels=5000,
    )

    features = samples.getInfo().get("features", [])
    rows = []
    for feat in features:
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {}).get("coordinates", [None, None])
        rows.append({
            f"satellite_{species}": props.get(spec["band"]),
            f"{species}_qa_value":  props.get(spec["qa_band"]),
            "latitude":             geom[1] if geom else None,
            "longitude":            geom[0] if geom else None,
            "timestamp_utc":        f"{date_str}T{spec['overpass_time']}",
        })

    return pd.DataFrame(rows)


def fetch_tropomi(date_str: str, cfg: dict | None = None) -> Path | None:
    """
    Download all four TROPOMI species (NO2, SO2, CO, O3) for Pune on a given date
    and merge them into a single parquet by spatial pixel.

    Raw output columns (per species, plus provenance):
        satellite_no2, no2_qa_value
        satellite_so2, so2_qa_value
        satellite_co,  co_qa_value
        satellite_o3,  o3_qa_value
        latitude, longitude, timestamp_utc

    Parameters
    ----------
    date_str : str
    cfg : dict, optional

    Returns
    -------
    Path or None
    """
    cfg = cfg or get_pipeline_config()
    _init_gee()

    import ee

    bbox = _bbox_to_ee_geometry(cfg["bbox"])
    logger.info("Fetching TROPOMI (NO2, SO2, CO, O3) for %s …", date_str)

    species_dfs = {}
    for species in ("no2", "so2", "co", "o3"):
        logger.info("  → %s", species.upper())
        df = _fetch_single_tropomi_species(species, date_str, bbox, cfg)
        if not df.empty:
            species_dfs[species] = df
        time.sleep(1.0)  # avoid GEE rate limits between requests

    if not species_dfs:
        logger.warning("No TROPOMI data retrieved for %s", date_str)
        return None

    # Merge all species on (latitude, longitude) via outer join
    # Each species comes from the same overpass so coordinates should align closely
    merged = None
    for species, df in species_dfs.items():
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
        if merged is None:
            merged = df
        else:
            key_cols = ["latitude", "longitude", "timestamp_utc"]
            merged = pd.merge(merged, df, on=key_cols, how="outer")

    output_dir = Path(cfg["paths"]["raw_satellite"])
    return _save_with_provenance(
        merged, "tropomi", date_str, output_dir, cfg,
        extra_meta={"species": list(species_dfs.keys())},
    )


# ── Date-range helpers ─────────────────────────────────────────────────────

def fetch_modis_aod_range(start_date: str, end_date: str, cfg: dict | None = None) -> list[Path]:
    """Fetch MODIS AOD for a range of dates (inclusive)."""
    cfg = cfg or get_pipeline_config()
    return _fetch_range(fetch_modis_aod, start_date, end_date, cfg)


def fetch_tropomi_range(start_date: str, end_date: str, cfg: dict | None = None) -> list[Path]:
    """Fetch TROPOMI for a range of dates (inclusive)."""
    cfg = cfg or get_pipeline_config()
    return _fetch_range(fetch_tropomi, start_date, end_date, cfg)


def _fetch_range(fn, start_date: str, end_date: str, cfg: dict) -> list[Path]:
    start   = datetime.strptime(start_date, "%Y-%m-%d")
    end     = datetime.strptime(end_date,   "%Y-%m-%d")
    saved   = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        path = fn(date_str, cfg)
        if path:
            saved.append(path)
        current += timedelta(days=1)
    logger.info("Done. Saved %d files.", len(saved))
    return saved


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest satellite data via GEE")
    parser.add_argument(
        "--product",
        choices=["modis", "tropomi", "all"],
        required=True,
        help="Which satellite product to download",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date",  help="Single date (YYYY-MM-DD)")
    group.add_argument("--start", help="Start date for range (YYYY-MM-DD)")
    parser.add_argument("--end",  help="End date for range (YYYY-MM-DD)")
    args = parser.parse_args()

    config = get_pipeline_config()
    end_date = args.end or config["data"]["date_end"]

    if args.date:
        if args.product in ("modis", "all"):
            fetch_modis_aod(args.date, config)
        if args.product in ("tropomi", "all"):
            fetch_tropomi(args.date, config)
    else:
        if args.product in ("modis", "all"):
            fetch_modis_aod_range(args.start, end_date, config)
        if args.product in ("tropomi", "all"):
            fetch_tropomi_range(args.start, end_date, config)
