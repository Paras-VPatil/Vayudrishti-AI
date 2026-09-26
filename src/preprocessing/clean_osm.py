"""
clean_osm.py
------------
Extraction, spatial rasterization, cleaning, and normalization of OpenStreetMap (OSM) infrastructure and land cover.
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
