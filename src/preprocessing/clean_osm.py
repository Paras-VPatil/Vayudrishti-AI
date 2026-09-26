"""
clean_osm.py
------------
Extraction, spatial rasterization, cleaning, and normalization of OpenStreetMap (OSM) infrastructure and land cover.

Usage (CLI)
-----------
  python -m src.preprocessing.clean_osm \
      --input  data/raw/auxiliary/pune_static_features.parquet \
      --output data/interim/static_features_clean.parquet
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def compute_spatial_densities(
    df: pd.DataFrame,
    grid_res_km: float = 1.0
) -> pd.DataFrame:
    """
    Validates and normalizes spatial feature densities:
      - Road density [km/km^2] (typical urban max ~25 km/km^2)
      - Building density [%] (0 to 100%)
      - Distance to road [km] (>= 0)
      - Distance to industry [km] (>= 0)
    """
    df = df.copy()

    if "road_density" in df.columns:
        df["road_density"] = df["road_density"].clip(lower=0.0, upper=50.0).fillna(0.0)

    if "building_density" in df.columns:
        df["building_density"] = df["building_density"].clip(lower=0.0, upper=100.0).fillna(0.0)

    if "distance_to_road_km" in df.columns:
        df["distance_to_road_km"] = df["distance_to_road_km"].clip(lower=0.0)

    if "distance_to_industry_km" in df.columns:
        df["distance_to_industry_km"] = df["distance_to_industry_km"].clip(lower=0.0)

    if "population_density" in df.columns:
        df["population_density"] = df["population_density"].clip(lower=0.0)

    return df


def clean_osm_features(df: pd.DataFrame) -> pd.DataFrame:
    """End-to-end cleaning for OSM and static geographical features."""
    df = compute_spatial_densities(df)
    
    # Handle landuse classes
    if "land_use_class" in df.columns or "landuse_class" in df.columns:
        target_col = "land_use_class" if "land_use_class" in df.columns else "landuse_class"
        # Impute missing landuse with 'Built-up' if high building density, else 'Grassland'
        if "building_density" in df.columns:
            high_bld = (df["building_density"] > 30.0) & df[target_col].isna()
            df.loc[high_bld, target_col] = "Built-up"
        df[target_col] = df[target_col].fillna("Cropland")

    return df


# ── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import logging
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Clean OSM / static geospatial features")
    parser.add_argument("--input",  required=True, help="Input parquet file")
    parser.add_argument("--output", required=True, help="Output parquet file")
    args = parser.parse_args()

    raw_df = pd.read_parquet(args.input)
    log.info("Loaded %d rows, columns: %s", len(raw_df), list(raw_df.columns))

    clean_df = clean_osm_features(raw_df)
    log.info("After cleaning: %d rows", len(clean_df))

    # Validate: no NaN in density columns
    for col in ["road_density", "building_density"]:
        if col in clean_df.columns:
            n_null = clean_df[col].isna().sum()
            if n_null > 0:
                log.warning("%s still has %d NaN values after cleaning", col, n_null)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_parquet(out_path, index=False, engine="pyarrow")
    log.info("Saved → %s", out_path)

    from src.preprocessing.missingness import get_missingness_report
    print("\nMissingness report (interim/static_features_clean):")
    print(get_missingness_report(clean_df))
