"""
src/ingestion/cpcb.py
----------------------
CPCB ground station data ingestion via OpenAQ v3 API.

RESPONSIBILITY: Download raw CPCB observations and save them to
  data/raw/ground/cpcb_YYYYMMDD.parquet  +  _meta.json sidecar.

DOES NOT:
  - Clean data (that is src/preprocessing/clean_cpcb.py)
  - Compute AQI (that is src/domain/aqi.py)
  - Impute missing values

Usage
-----
  python -m src.ingestion.cpcb --date 2024-06-01
  python -m src.ingestion.cpcb --start 2024-01-01 --end 2024-12-31
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config_loader import get_pipeline_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── OpenAQ parameter IDs (v3 API) ──────────────────────────────────────────
# These are the integer IDs used by OpenAQ for each pollutant.
OPENAQ_PARAM_IDS = {
    "pm25":  2,
    "pm10":  1,
    "no2":   7,
    "so2":   9,
    "co":    4,
    "o3":    3,
}


# ── Column schema for saved parquet ───────────────────────────────────────
CPCB_SCHEMA_COLUMNS = [
    "station_id",
    "station_name",
    "city",
    "country",
    "latitude",
    "longitude",
    "timestamp_utc",
    "parameter",
    "value",
    "unit",
]


def fetch_pune_stations(cfg: dict) -> pd.DataFrame:
    """
    Fetch all OpenAQ locations (stations) within the Pune bounding box.

    Returns
    -------
    pd.DataFrame
        Columns: station_id, station_name, city, latitude, longitude
    """
    bbox = cfg["bbox"]
    base_url = cfg["cpcb"]["openaq_api_base"]
    url = f"{base_url}/locations"

    params = {
        "bbox": f"{bbox['lon_min']},{bbox['lat_min']},{bbox['lon_max']},{bbox['lat_max']}",
        "limit": 200,
        "page": 1,
        "countryId": 105,   # India
    }

    logger.info("Fetching Pune station list from OpenAQ…")
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for loc in data.get("results", []):
        coords = loc.get("coordinates") or {}
        records.append({
            "station_id":   str(loc.get("id", "")),
            "station_name": loc.get("name", ""),
            "city":         loc.get("city", "Pune"),
            "country":      loc.get("country", {}).get("code", "IN"),
            "latitude":     coords.get("latitude"),
            "longitude":    coords.get("longitude"),
        })

    df = pd.DataFrame(records)
    logger.info("Found %d stations in Pune bounding box", len(df))
    return df


def fetch_measurements_for_station(
    station_id: str,
    date_str: str,
    cfg: dict,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch all hourly measurements for a single station on a given date.

    Parameters
    ----------
    station_id : str
        OpenAQ location ID.
    date_str : str
        Date string in YYYY-MM-DD format (UTC).
    cfg : dict
        Pipeline config.
    max_retries : int
        Number of retry attempts on HTTP errors.

    Returns
    -------
    pd.DataFrame
        Columns matching CPCB_SCHEMA_COLUMNS, one row per measurement.
    """
    base_url = cfg["cpcb"]["openaq_api_base"]
    url = f"{base_url}/measurements"

    date_from = f"{date_str}T00:00:00Z"
    date_to   = f"{date_str}T23:59:59Z"

    params = {
        "locationsId": station_id,
        "dateFrom":    date_from,
        "dateTo":      date_to,
        "limit":       1000,
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Rate limited. Waiting %ds…", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt == max_retries:
                logger.error("Failed fetching station %s: %s", station_id, exc)
                return pd.DataFrame(columns=CPCB_SCHEMA_COLUMNS)
            time.sleep(2 ** attempt)

    rows = []
    for m in resp.json().get("results", []):
        rows.append({
            "station_id":   str(station_id),
            "station_name": m.get("location", ""),
            "city":         "pune",
            "country":      "IN",
            "latitude":     m.get("coordinates", {}).get("latitude"),
            "longitude":    m.get("coordinates", {}).get("longitude"),
            "timestamp_utc": m.get("date", {}).get("utc"),
            "parameter":    m.get("parameter"),
            "value":        m.get("value"),
            "unit":         m.get("unit"),
        })
    return pd.DataFrame(rows, columns=CPCB_SCHEMA_COLUMNS)


def _validate_raw(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Apply a light validation gate before saving raw data.
    This does NOT clean — it just removes structurally broken rows.
    - Invalid coordinates (outside Pune bounding box ± 0.5 deg)
    - Rows where timestamp is missing or unparseable
    - Rows where value is missing (null observations are useless)
    """
    bbox = cfg["cpcb"]
    lat_min, lat_max = cfg["cpcb"]["lat_valid_min"], cfg["cpcb"]["lat_valid_max"]
    lon_min, lon_max = cfg["cpcb"]["lon_valid_min"], cfg["cpcb"]["lon_valid_max"]

    n_before = len(df)

    # Coordinate validity
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[
        df["latitude"].between(lat_min, lat_max) &
        df["longitude"].between(lon_min, lon_max)
    ]

    # Timestamp validity
    df = df.dropna(subset=["timestamp_utc"])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp_utc"])

    # Value must be present
    df = df.dropna(subset=["value"])

    n_after = len(df)
    logger.info("Validation gate: %d → %d rows (dropped %d)", n_before, n_after, n_before - n_after)
    return df.reset_index(drop=True)


def _save_with_provenance(
    df: pd.DataFrame,
    date_str: str,
    output_dir: Path,
    cfg: dict,
) -> Path:
    """
    Save DataFrame to parquet + write a _meta.json provenance sidecar.

    Returns
    -------
    Path
        Path to the saved .parquet file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / f"cpcb_{date_str.replace('-', '')}.parquet"
    meta_path    = output_dir / f"cpcb_{date_str.replace('-', '')}_meta.json"

    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    meta = {
        "source":           "OpenAQ v3 API",
        "dataset":          "CPCB_CAAQMS",
        "city":             cfg["city"],
        "date":             date_str,
        "acquisition_time": datetime.now(timezone.utc).isoformat(),
        "bbox": {
            "lat_min": cfg["bbox"]["lat_min"],
            "lat_max": cfg["bbox"]["lat_max"],
            "lon_min": cfg["bbox"]["lon_min"],
            "lon_max": cfg["bbox"]["lon_max"],
        },
        "row_count":        len(df),
        "parameters":       sorted(df["parameter"].dropna().unique().tolist()),
        "station_count":    df["station_id"].nunique(),
        "schema_version":   cfg.get("schema_version", "1.0.0"),
    }

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("Saved %d rows → %s", len(df), parquet_path)
    logger.info("Provenance  → %s", meta_path)
    return parquet_path


def ingest_cpcb_for_date(date_str: str, cfg: dict | None = None) -> Path | None:
    """
    Main ingestion function: fetch all Pune CPCB measurements for one date.

    Parameters
    ----------
    date_str : str
        Date in YYYY-MM-DD format.
    cfg : dict, optional
        Pipeline config dict. Loaded from file if not provided.

    Returns
    -------
    Path or None
        Path to saved parquet, or None if no data retrieved.
    """
    cfg = cfg or get_pipeline_config()
    output_dir = Path(cfg["paths"]["raw_ground"])

    # 1. Fetch station list
    stations_df = fetch_pune_stations(cfg)
    if stations_df.empty:
        logger.warning("No stations found in Pune bbox for date %s", date_str)
        return None

    # 2. Fetch measurements per station and combine
    all_dfs = []
    for _, row in stations_df.iterrows():
        df = fetch_measurements_for_station(row["station_id"], date_str, cfg)
        if not df.empty:
            # Enrich with station metadata from the location lookup
            df["station_name"] = df["station_name"].fillna(row["station_name"])
            df["city"]         = row["city"]
            df["latitude"]     = df["latitude"].fillna(row["latitude"])
            df["longitude"]    = df["longitude"].fillna(row["longitude"])
            all_dfs.append(df)
        time.sleep(0.3)  # polite rate limiting

    if not all_dfs:
        logger.warning("No measurements returned for %s", date_str)
        return None

    combined = pd.concat(all_dfs, ignore_index=True)

    # 3. Light validation gate
    combined = _validate_raw(combined, cfg)
    if combined.empty:
        logger.warning("All rows dropped by validation gate for %s", date_str)
        return None

    # 4. Save with provenance
    return _save_with_provenance(combined, date_str, output_dir, cfg)


def ingest_cpcb_date_range(start_date: str, end_date: str, cfg: dict | None = None) -> list[Path]:
    """
    Ingest CPCB data for a range of dates (inclusive).

    Parameters
    ----------
    start_date : str  e.g. "2024-01-01"
    end_date   : str  e.g. "2024-12-31"

    Returns
    -------
    list[Path]
        List of saved parquet file paths.
    """
    cfg = cfg or get_pipeline_config()
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = datetime.strptime(end_date,   "%Y-%m-%d")

    saved = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        path = ingest_cpcb_for_date(date_str, cfg)
        if path:
            saved.append(path)
        current += timedelta(days=1)

    logger.info("Ingestion complete. Saved %d files.", len(saved))
    return saved


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest CPCB data via OpenAQ")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date",  help="Single date (YYYY-MM-DD)")
    group.add_argument("--start", help="Start date for range (YYYY-MM-DD)")
    parser.add_argument("--end",  help="End date for range (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    config = get_pipeline_config()

    if args.date:
        ingest_cpcb_for_date(args.date, config)
    else:
        end = args.end or config["data"]["date_end"]
        ingest_cpcb_date_range(args.start, end, config)
