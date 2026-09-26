"""
src/ingestion/osm.py
---------------------
Static geospatial / auxiliary layer ingestion for Pune.

Downloads and rasterizes to a 1 km x 1 km grid:
  1. OSM road network  →  road_density, distance_to_road_km
  2. OSM industrial areas  →  distance_to_industry_km, building_density (proxy)
  3. ESA WorldCover 2021 land use  →  land_use_class      (via GEE)
  4. SRTM DEM elevation            →  elevation_m          (via GEE)
  5. WorldPop 2020 population      →  population_density   (via GEE)

RESPONSIBILITY: Download and save raw static features to:
  data/raw/auxiliary/pune_static_features.parquet  +  _meta.json

DOES NOT:
  - Normalise densities — that is clean_osm.py
  - Impute missing land use — that is clean_osm.py

Dependencies
------------
  pip install osmnx geopandas shapely earthengine-api pyarrow

Usage
-----
  python -m src.ingestion.osm
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_loader import get_pipeline_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ESA WorldCover 2021 class mapping (integer value → label)
WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / Sparse vegetation",
    70: "Snow and Ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


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
    except Exception as exc:
        raise RuntimeError(f"GEE init failed: {exc}") from exc


def _bbox_to_ee_geometry(bbox: dict):
    import ee
    return ee.Geometry.Rectangle([
        bbox["lon_min"], bbox["lat_min"],
        bbox["lon_max"], bbox["lat_max"],
    ])


def _generate_pune_grid(bbox: dict, resolution_deg: float = 0.01) -> pd.DataFrame:
    """
    Generate a regular lat/lon grid over Pune at ~1 km resolution.

    Parameters
    ----------
    bbox : dict
        lat_min, lat_max, lon_min, lon_max from config
    resolution_deg : float
        Grid spacing in decimal degrees (~0.01 deg ≈ 1 km)

    Returns
    -------
    pd.DataFrame
        Columns: latitude, longitude, location_id
    """
    lats = np.arange(bbox["lat_min"], bbox["lat_max"], resolution_deg)
    lons = np.arange(bbox["lon_min"], bbox["lon_max"], resolution_deg)

    rows = []
    for lat in lats:
        for lon in lons:
            rows.append({
                "latitude":    round(float(lat), 4),
                "longitude":   round(float(lon), 4),
                "location_id": f"pune_{lat:.2f}_{lon:.2f}".replace(".", ""),
            })
    logger.info("Generated %d grid cells (%s x %s)", len(rows),
                len(lats), len(lons))
    return pd.DataFrame(rows)


def _fetch_osm_road_features(grid_df: pd.DataFrame, bbox: dict) -> pd.DataFrame:
    """
    Download Pune road network from OpenStreetMap via OSMnx and
    compute for each grid cell:
      - road_density:           km of road per km² (all road types)
      - distance_to_road_km:    distance to nearest road segment (km)

    Requires: pip install osmnx geopandas shapely

    Parameters
    ----------
    grid_df : pd.DataFrame  (latitude, longitude, location_id)
    bbox : dict

    Returns
    -------
    pd.DataFrame  merged with road features
    """
    try:
        import osmnx as ox
        from shapely.geometry import Point
        import geopandas as gpd
    except ImportError:
        logger.warning(
            "osmnx / geopandas not installed. Skipping road features.\n"
            "Install: pip install osmnx geopandas"
        )
        grid_df["road_density"]        = np.nan
        grid_df["distance_to_road_km"] = np.nan
        return grid_df

    logger.info("Downloading Pune road network from OSM…")
    try:
        # Download road network within bounding box
        G = ox.graph_from_bbox(
            north=bbox["lat_max"],
            south=bbox["lat_min"],
            east=bbox["lon_max"],
            west=bbox["lon_min"],
            network_type="drive",
            simplify=True,
        )
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        edges = edges.to_crs("EPSG:32643")  # UTM zone 43N for Pune (metres)

        # Compute road density per 1 km² cell
        # Approximate: count edges within ~500m of each grid point
        grid_gdf = gpd.GeoDataFrame(
            grid_df,
            geometry=[Point(row.longitude, row.latitude) for _, row in grid_df.iterrows()],
            crs="EPSG:4326",
        ).to_crs("EPSG:32643")

        road_densities = []
        dist_to_roads  = []

        for geom in grid_gdf.geometry:
            cell_buffer = geom.buffer(500)  # 500m radius ≈ 1 km²

            # Edges intersecting the buffer
            clipped_len = edges[edges.intersects(cell_buffer)].length.sum() / 1000  # km
            road_densities.append(round(clipped_len, 3))

            # Distance to nearest road edge centroid
            nearest_dist = edges.distance(geom).min() / 1000  # km
            dist_to_roads.append(round(float(nearest_dist), 4))

        grid_df["road_density"]        = road_densities
        grid_df["distance_to_road_km"] = dist_to_roads

    except Exception as exc:
        logger.error("OSM road download failed: %s. Setting NaN.", exc)
        grid_df["road_density"]        = np.nan
        grid_df["distance_to_road_km"] = np.nan

    return grid_df


def _fetch_osm_industrial_distance(grid_df: pd.DataFrame, bbox: dict) -> pd.DataFrame:
    """
    Download OSM industrial landuse polygons and compute distance
    from each grid cell to the nearest industrial area.

    Returns
    -------
    pd.DataFrame  with distance_to_industry_km, building_density columns added
    """
    try:
        import osmnx as ox
        from shapely.geometry import Point
        import geopandas as gpd
    except ImportError:
        grid_df["distance_to_industry_km"] = np.nan
        grid_df["building_density"]        = np.nan
        return grid_df

    logger.info("Downloading OSM industrial + building footprints…")

    try:
        # Industrial zones
        industrial = ox.features_from_bbox(
            north=bbox["lat_max"],
            south=bbox["lat_min"],
            east=bbox["lon_max"],
            west=bbox["lon_min"],
            tags={"landuse": "industrial"},
        )
        ind_gdf = industrial.to_crs("EPSG:32643")

        # Building footprints (for building density)
        buildings = ox.features_from_bbox(
            north=bbox["lat_max"],
            south=bbox["lat_min"],
            east=bbox["lon_max"],
            west=bbox["lon_min"],
            tags={"building": True},
        )
        bld_gdf = buildings.to_crs("EPSG:32643")

        grid_gdf = gpd.GeoDataFrame(
            grid_df,
            geometry=[Point(row.longitude, row.latitude) for _, row in grid_df.iterrows()],
            crs="EPSG:4326",
        ).to_crs("EPSG:32643")

        dist_industry = []
        bld_density   = []

        for geom in grid_gdf.geometry:
            # Distance to nearest industrial polygon boundary
            if not ind_gdf.empty:
                d = ind_gdf.distance(geom).min() / 1000
            else:
                d = np.nan
            dist_industry.append(round(float(d), 4) if not np.isnan(d) else np.nan)

            # Building density: area of buildings within 500m buffer / (pi * 500^2)
            buf = geom.buffer(500)
            if not bld_gdf.empty:
                covered = bld_gdf[bld_gdf.intersects(buf)].area.sum()
                density = (covered / buf.area) * 100  # percentage
            else:
                density = np.nan
            bld_density.append(round(float(density), 2) if not np.isnan(density) else np.nan)

        grid_df["distance_to_industry_km"] = dist_industry
        grid_df["building_density"]        = bld_density

    except Exception as exc:
        logger.error("OSM industrial download failed: %s. Setting NaN.", exc)
        grid_df["distance_to_industry_km"] = np.nan
        grid_df["building_density"]        = np.nan

    return grid_df


def _fetch_gee_static_layers(grid_df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Fetch GEE raster layers sampled at each grid point:
      - ESA WorldCover 2021 → land_use_class (integer + string label)
      - SRTM DEM → elevation_m
      - WorldPop 2020 → population_density (persons/km²)

    Returns
    -------
    pd.DataFrame  with land_use_class, land_use_label, elevation_m,
                  population_density columns added
    """
    _init_gee()

    import ee

    bbox   = _bbox_to_ee_geometry(cfg["bbox"])
    logger.info("Fetching GEE static layers (WorldCover, DEM, WorldPop)…")

    # ESA WorldCover 2021
    worldcover = ee.ImageCollection("ESA/WorldCover/v200") \
        .first() \
        .select("Map") \
        .clip(bbox)

    # SRTM DEM
    srtm = ee.Image("USGS/SRTMGL1_003") \
        .select("elevation") \
        .clip(bbox)

    # WorldPop 2020 (unconstrained, persons per pixel)
    worldpop = ee.ImageCollection("WorldPop/GP/100m/pop") \
        .filter(ee.Filter.eq("year", 2020)) \
        .filter(ee.Filter.eq("country", "IND")) \
        .first() \
        .select("population") \
        .clip(bbox)

    # Stack all bands into one image
    stacked = worldcover.rename("lc") \
        .addBands(srtm.rename("elev")) \
        .addBands(worldpop.rename("pop"))

    # Build an ee.FeatureCollection from the grid points
    features_list = []
    for _, row in grid_df.iterrows():
        feat = ee.Feature(
            ee.Geometry.Point([row["longitude"], row["latitude"]]),
            {"location_id": row["location_id"]},
        )
        features_list.append(feat)

    fc = ee.FeatureCollection(features_list)

    # Sample the stacked image at each point
    sampled = stacked.sampleRegions(
        collection=fc,
        scale=100,
        geometries=True,
    )

    results = sampled.getInfo().get("features", [])

    # Map results back to location_id
    lookup = {}
    for feat in results:
        props = feat.get("properties", {})
        lid   = props.get("location_id")
        lookup[lid] = {
            "land_use_class":    int(props.get("lc", 0)) if props.get("lc") is not None else None,
            "elevation_m":       round(float(props.get("elev", 0)), 1) if props.get("elev") is not None else None,
            "population_density": round(float(props.get("pop", 0)), 1) if props.get("pop") is not None else None,
        }

    grid_df["land_use_class"]    = grid_df["location_id"].map(lambda x: lookup.get(x, {}).get("land_use_class"))
    grid_df["land_use_label"]    = grid_df["land_use_class"].map(WORLDCOVER_CLASSES)
    grid_df["elevation_m"]       = grid_df["location_id"].map(lambda x: lookup.get(x, {}).get("elevation_m"))
    grid_df["population_density"]= grid_df["location_id"].map(lambda x: lookup.get(x, {}).get("population_density"))

    logger.info("GEE static layers joined for %d grid cells", len(grid_df))
    return grid_df


def fetch_static_features(cfg: dict | None = None) -> Path:
    """
    Main function: build the complete static feature grid for Pune.

    Steps:
    1. Generate 1 km grid over Pune bbox
    2. Fetch OSM road density + distance
    3. Fetch OSM industrial distance + building density
    4. Fetch GEE WorldCover + DEM + WorldPop
    5. Save to data/raw/auxiliary/pune_static_features.parquet

    Returns
    -------
    Path
        Path to the saved parquet file.
    """
    cfg = cfg or get_pipeline_config()
    bbox = cfg["bbox"]
    resolution = cfg["era5"].get("grid_resolution_deg", 0.01)

    # Step 1 — Grid
    grid_df = _generate_pune_grid(bbox, resolution_deg=resolution)

    # Step 2 — OSM roads
    grid_df = _fetch_osm_road_features(grid_df, bbox)

    # Step 3 — OSM industrial + buildings
    grid_df = _fetch_osm_industrial_distance(grid_df, bbox)

    # Step 4 — GEE static layers
    try:
        grid_df = _fetch_gee_static_layers(grid_df, cfg)
    except Exception as exc:
        logger.error("GEE static layers failed: %s. Setting NaN.", exc)
        grid_df["land_use_class"]    = None
        grid_df["land_use_label"]    = None
        grid_df["elevation_m"]       = np.nan
        grid_df["population_density"]= np.nan

    # Step 5 — Save
    output_dir  = Path(cfg["paths"]["raw_auxiliary"])
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "pune_static_features.parquet"
    meta_path    = output_dir / "pune_static_features_meta.json"

    grid_df.to_parquet(parquet_path, index=False, engine="pyarrow")

    meta = {
        "product":          "Pune Static Features",
        "city":             cfg["city"],
        "acquisition_time": datetime.now(timezone.utc).isoformat(),
        "bbox":             bbox,
        "grid_resolution_deg": resolution,
        "grid_cells":       len(grid_df),
        "sources": {
            "roads":        "OpenStreetMap via OSMnx",
            "buildings":    "OpenStreetMap via OSMnx",
            "land_use":     "ESA WorldCover 2021 (GEE)",
            "elevation":    "SRTM GL1 (GEE)",
            "population":   "WorldPop 2020 (GEE)",
        },
        "columns":        list(grid_df.columns),
        "schema_version": cfg.get("schema_version", "1.0.0"),
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info("Static features saved → %s (%d cells)", parquet_path, len(grid_df))
    return parquet_path


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest Pune static geospatial features")
    parser.add_argument("--config", default=None, help="Path to pipeline_config.yaml")
    args = parser.parse_args()
    config = get_pipeline_config(args.config)
    fetch_static_features(config)
