"""
spatial_temporal_matcher.py
----------------------------
High-performance spatial and temporal matching engine to pair spaceborne satellite
retrievals with ground-truth CPCB monitor observations to create canonical training pairs.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def haversine_distance_matrix(
    coords_a: np.ndarray,
    coords_b: np.ndarray
) -> np.ndarray:
    """
    Computes pairwise Haversine distances in kilometers between two arrays
    of [latitude, longitude] in degrees.
    """
    R = 6371.0  # Earth radius in km
    lat1, lon1 = np.radians(coords_a[:, 0]), np.radians(coords_a[:, 1])
    lat2, lon2 = np.radians(coords_b[:, 0]), np.radians(coords_b[:, 1])

    dlat = lat2[None, :] - lat1[:, None]
    dlon = lon2[None, :] - lon1[:, None]

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1[:, None]) * np.cos(lat2[None, :]) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return R * c


class SpatialTemporalMatcher:
    """
    Collocates satellite pixels, ERA5 weather, and static features with ground-truth CPCB stations.
    """

    def __init__(
        self,
        max_spatial_distance_km: float = 25.0,
        max_temporal_window_minutes: float = 60.0
    ):
        self.max_spatial_distance_km = max_spatial_distance_km
        self.max_temporal_window_minutes = max_temporal_window_minutes

    def match_spatial_nearest(
        self,
        satellite_df: pd.DataFrame,
        ground_stations_df: pd.DataFrame,
        sat_lat_col: str = "latitude",
        sat_lon_col: str = "longitude",
        ground_lat_col: str = "latitude",
        ground_lon_col: str = "longitude",
        station_id_col: str = "station_id"
    ) -> pd.DataFrame:
        """
        For each satellite pixel, finds the nearest ground monitoring station within
        the spatial distance cutoff using a 3D Cartesian KD-Tree for fast querying.
        """
        # Convert lat/lon to 3D Cartesian coordinates on unit sphere
        sat_lats = np.radians(satellite_df[sat_lat_col].values)
        sat_lons = np.radians(satellite_df[sat_lon_col].values)
        sat_xyz = np.column_stack([
            np.cos(sat_lats) * np.cos(sat_lons),
            np.cos(sat_lats) * np.sin(sat_lons),
            np.sin(sat_lats)
        ])

        ground_lats = np.radians(ground_stations_df[ground_lat_col].values)
        ground_lons = np.radians(ground_stations_df[ground_lon_col].values)
        ground_xyz = np.column_stack([
            np.cos(ground_lats) * np.cos(ground_lons),
            np.cos(ground_lats) * np.sin(ground_lons),
            np.sin(ground_lats)
        ])

        tree = cKDTree(ground_xyz)
        # Chord distance on unit sphere: d_chord = 2 * sin(d_km / (2 * R))
        R = 6371.0
        max_chord = 2.0 * np.sin(self.max_spatial_distance_km / (2.0 * R))

        distances_chord, indices = tree.query(sat_xyz, k=1, distance_upper_bound=max_chord)

        # Convert chord distance back to surface arc distance in km
        distances_km = 2.0 * R * np.arcsin(np.clip(distances_chord / 2.0, 0.0, 1.0))

        result_df = satellite_df.copy()
        matched_mask = indices < len(ground_stations_df)

        result_df["station_id"] = None
        result_df["distance_to_station_km"] = np.nan

        if np.any(matched_mask):
            matched_indices = indices[matched_mask]
            result_df.loc[matched_mask, "station_id"] = ground_stations_df.iloc[matched_indices][station_id_col].values
            result_df.loc[matched_mask, "distance_to_station_km"] = distances_km[matched_mask]

        return result_df

    def match_temporal_window(
        self,
        satellite_df: pd.DataFrame,
        ground_observations_df: pd.DataFrame,
        sat_time_col: str = "timestamp_utc",
        ground_time_col: str = "timestamp_utc",
        station_id_col: str = "station_id"
    ) -> pd.DataFrame:
        """
        Pairs satellite pixels with ground station observations matching the same station_id
        within the allowable temporal window (+/- max_temporal_window_minutes).
        """
        sat_df = satellite_df.copy()
        ground_df = ground_observations_df.copy()

        sat_df[sat_time_col] = pd.to_datetime(sat_df[sat_time_col], utc=True)
        ground_df[ground_time_col] = pd.to_datetime(ground_df[ground_time_col], utc=True)

        # Merge on station_id
        merged = pd.merge(
            sat_df,
            ground_df,
            on=station_id_col,
            suffixes=("_sat", "_ground"),
            how="inner"
        )

        if len(merged) == 0:
            return merged

        # Calculate absolute time delta in minutes
        time_diff_mins = np.abs((merged[f"{sat_time_col}_sat"] - merged[f"{ground_time_col}_ground"]).dt.total_seconds()) / 60.0
        valid_time = time_diff_mins <= self.max_temporal_window_minutes

        matched_pairs = merged[valid_time].copy()
        matched_pairs["temporal_offset_minutes"] = time_diff_mins[valid_time]

        # In case of multiple observations within window, pick the closest in time
        matched_pairs = matched_pairs.sort_values(by=["station_id", "temporal_offset_minutes"])
        matched_pairs = matched_pairs.drop_duplicates(subset=["record_id" if "record_id" in matched_pairs.columns else "station_id", f"{sat_time_col}_sat"])

        return matched_pairs


def collocate_satellite_and_ground(
    satellite_df: pd.DataFrame,
    ground_df: pd.DataFrame,
    max_distance_km: float = 25.0,
    max_time_diff_min: float = 60.0
) -> pd.DataFrame:
    """
    Convenience wrapper to perform full spatial and temporal collocation.
    """
    matcher = SpatialTemporalMatcher(
        max_spatial_distance_km=max_distance_km,
        max_temporal_window_minutes=max_time_diff_min
    )

    # 1. Spatial Match
    spatially_matched = matcher.match_spatial_nearest(satellite_df, ground_df)
    valid_spatial = spatially_matched[spatially_matched["station_id"].notna()].copy()

    if len(valid_spatial) == 0:
        return spatially_matched

    # 2. Temporal Match
    collocated = matcher.match_temporal_window(valid_spatial, ground_df)
    return collocated
