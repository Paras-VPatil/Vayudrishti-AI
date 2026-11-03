"""
src/spatial/interpolation.py
----------------------------
Stage 14 — Spatial Interpolation, Regression-Kriging, and Statewide Raster Overlays.

Provides:
1. Inverse Distance Weighting (IDW) spatial interpolation.
2. Regression-Kriging (ML trend + station residual kriging with variance).
3. Maharashtra statewide regular grid generation (15.6–22.1°N, 72.6–80.9°E).
4. Color-mapped PNG overlay rasterization (CPCB NAQI palette) for smooth Leaflet rendering.
5. Point lookup and GeoJSON conversion.
"""

from typing import Tuple, Optional, Dict, Any, List
import io
import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

# Official CPCB NAQI Category Breakpoints and Colors
CPCB_PALETTE = [
    (0, 50, (0, 228, 0, 180)),       # Good (Green)
    (51, 100, (146, 208, 80, 180)),  # Satisfactory (Light Green)
    (101, 200, (255, 255, 0, 190)),  # Moderate (Yellow)
    (201, 300, (255, 126, 0, 200)),  # Poor (Orange)
    (301, 400, (255, 0, 0, 210)),    # Very Poor (Red)
    (401, 500, (126, 0, 35, 220)),   # Severe (Maroon)
]


def idw_interpolate(
    known_coords: np.ndarray,
    known_values: np.ndarray,
    query_coords: np.ndarray,
    power: float = 2.0,
    min_dist_km: float = 0.05
) -> np.ndarray:
    """
    Computes Inverse Distance Weighting (IDW) interpolation.
    """
    known_coords = np.asarray(known_coords)
    known_values = np.asarray(known_values)
    query_coords = np.asarray(query_coords)

    if len(known_coords) == 0:
        return np.full(len(query_coords), 65.0)

    # Approximate Euclidean distance in km (1 deg ~ 111.0 km)
    scale = np.array([111.0, 111.0 * np.cos(np.radians(np.mean(query_coords[:, 0])))])

    known_scaled = known_coords * scale
    query_scaled = query_coords * scale

    dists = cdist(query_scaled, known_scaled, metric="euclidean")
    dists = np.maximum(dists, min_dist_km)

    weights = 1.0 / (dists ** power)
    weight_sums = np.sum(weights, axis=1, keepdims=True)

    normalized_weights = weights / weight_sums
    interpolated_values = np.dot(normalized_weights, known_values)
    return interpolated_values


class RegressionKrigingInterpolator:
    """
    Regression-Kriging: ML Trend + Spatial Residual Kriging.
    Corrects model biases at physical station locations and estimates kriging variance.
    """

    def __init__(self, correlation_length_km: float = 40.0, nugget: float = 0.1):
        self.correlation_length_km = correlation_length_km
        self.nugget = nugget

    def fit_and_predict(
        self,
        station_coords: np.ndarray,
        station_true_values: np.ndarray,
        station_trend_preds: np.ndarray,
        grid_coords: np.ndarray,
        grid_trend_preds: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fits spatial covariance on residuals and evaluates statewide corrected surface.

        Returns
        -------
        corrected_values : np.ndarray
            Trend + kriged residual.
        kriging_variance : np.ndarray
            Spatial estimation uncertainty.
        """
        station_coords = np.asarray(station_coords)
        residuals = station_true_values - station_trend_preds

        if len(station_coords) == 0 or len(residuals) == 0:
            return grid_trend_preds, np.full(len(grid_coords), 15.0)

        # Scale coordinates to km
        mean_lat = np.mean(grid_coords[:, 0])
        scale = np.array([111.0, 111.0 * np.cos(np.radians(mean_lat))])

        stn_scaled = station_coords * scale
        grid_scaled = grid_coords * scale

        # Pairwise distance matrices
        dist_grid_stn = cdist(grid_scaled, stn_scaled, metric="euclidean")  # (M, N)
        dist_stn_stn = cdist(stn_scaled, stn_scaled, metric="euclidean")    # (N, N)

        # Exponential spatial covariance: C(h) = (1 - nugget) * exp(-h / L)
        L = self.correlation_length_km
        C_stn = (1.0 - self.nugget) * np.exp(-dist_stn_stn / L) + np.eye(len(stn_scaled)) * self.nugget
        C_grid = (1.0 - self.nugget) * np.exp(-dist_grid_stn / L)

        try:
            # Solve kriging weights: C_stn * w = C_grid^T  => w = C_grid * inv(C_stn)
            weights = np.linalg.solve(C_stn, C_grid.T).T  # Shape: (M, N)
            residual_correction = np.dot(weights, residuals)
            # Kriging estimation variance
            kriging_variance = np.maximum(0.0, 1.0 - np.sum(weights * C_grid, axis=1))
            kriging_se = np.sqrt(kriging_variance) * np.std(residuals) if np.std(residuals) > 0 else np.full(len(grid_coords), 10.0)
        except Exception:
            # IDW fallback for residual correction if covariance matrix is singular
            residual_correction = idw_interpolate(station_coords, residuals, grid_coords, power=2.0)
            min_dist = np.min(dist_grid_stn, axis=1)
            kriging_se = 8.0 + 0.15 * np.minimum(min_dist, 100.0)

        corrected_values = grid_trend_preds + residual_correction
        return np.maximum(0.0, corrected_values), kriging_se


def generate_maharashtra_grid(
    lat_min: float = 15.60,
    lat_max: float = 22.10,
    lon_min: float = 72.60,
    lon_max: float = 80.90,
    resolution_deg: float = 0.05
) -> pd.DataFrame:
    """
    Generates a uniform 2D grid covering Maharashtra (~308,000 km²).
    At resolution_deg=0.05 (~5 km), produces ~22,000 cells for lightning fast rendering.
    """
    lats = np.arange(lat_min, lat_max + resolution_deg / 2, resolution_deg)
    lons = np.arange(lon_min, lon_max + resolution_deg / 2, resolution_deg)

    mesh_lat, mesh_lon = np.meshgrid(lats, lons, indexing="ij")
    flat_lats = mesh_lat.ravel()
    flat_lons = mesh_lon.ravel()

    return pd.DataFrame({
        "grid_id": [f"mh_grid_{i:06d}" for i in range(len(flat_lats))],
        "latitude": np.round(flat_lats, 4),
        "longitude": np.round(flat_lons, 4)
    })


def generate_pune_city_grid(
    lat_min: float = 18.40,
    lat_max: float = 18.65,
    lon_min: float = 73.70,
    lon_max: float = 74.00,
    resolution_deg: float = 0.01
) -> pd.DataFrame:
    """
    Generates regular grid covering Pune metropolitan area.
    """
    lats = np.arange(lat_min, lat_max + resolution_deg / 2, resolution_deg)
    lons = np.arange(lon_min, lon_max + resolution_deg / 2, resolution_deg)
    mesh_lat, mesh_lon = np.meshgrid(lats, lons, indexing="ij")
    flat_lats = mesh_lat.ravel()
    flat_lons = mesh_lon.ravel()
    return pd.DataFrame({
        "grid_id": [f"grid_pune_{i:05d}" for i in range(len(flat_lats))],
        "latitude": np.round(flat_lats, 4),
        "longitude": np.round(flat_lons, 4)
    })


def value_to_cpcb_color(aqi_val: float) -> Tuple[int, int, int, int]:
    """Maps AQI value (0-500) to CPCB RGBA color tuple."""
    if aqi_val <= 50:
        return (0, 228, 0, 180)       # Good
    elif aqi_val <= 100:
        return (146, 208, 80, 185)    # Satisfactory
    elif aqi_val <= 200:
        return (255, 255, 0, 190)     # Moderate
    elif aqi_val <= 300:
        return (255, 126, 0, 200)     # Poor
    elif aqi_val <= 400:
        return (255, 0, 0, 215)       # Very Poor
    else:
        return (126, 0, 35, 230)      # Severe


def render_statewide_overlay_png(
    grid_df: pd.DataFrame,
    value_col: str = "aqi",
    lat_min: float = 15.60,
    lat_max: float = 22.10,
    lon_min: float = 72.60,
    lon_max: float = 80.90,
    output_path: Optional[str] = None
) -> bytes:
    """
    Renders high-performance color-mapped RGBA PNG for Leaflet ImageOverlay.
    """
    from PIL import Image

    # Determine unique sorted lat/lons to form image dimensions
    u_lats = np.sort(grid_df["latitude"].unique())[::-1]  # Top to bottom
    u_lons = np.sort(grid_df["longitude"].unique())        # Left to right

    height = len(u_lats)
    width = len(u_lons)

    # Pivot into 2D grid
    grid_pivot = grid_df.pivot(index="latitude", columns="longitude", values=value_col)
    grid_pivot = grid_pivot.reindex(index=u_lats, columns=u_lons)

    rgba = np.zeros((height, width, 4), dtype=np.uint8)

    for i in range(height):
        for j in range(width):
            val = grid_pivot.iloc[i, j]
            if pd.isna(val):
                rgba[i, j] = (0, 0, 0, 0)
            else:
                rgba[i, j] = value_to_cpcb_color(float(val))

    img = Image.fromarray(rgba, "RGBA")
    # Resize slightly for smooth interpolation
    img = img.resize((width * 4, height * 4), resample=Image.Resampling.BILINEAR)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    png_bytes = buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(png_bytes)

    return png_bytes


def grid_to_geojson_heatmap(
    grid_df: pd.DataFrame,
    value_col: str = "pm25_pred"
) -> Dict[str, Any]:
    """
    Converts gridded prediction points into GeoJSON FeatureCollection.
    """
    features = []
    for _, row in grid_df.iterrows():
        val = row.get(value_col, 0.0)
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["longitude"]), float(row["latitude"])]
            },
            "properties": {
                "grid_id": str(row.get("grid_id", "")),
                "value": float(val) if pd.notna(val) else 0.0,
                "pm25": float(row.get("pm25_pred", val)) if pd.notna(row.get("pm25_pred")) else float(val),
                "uncertainty": float(row.get("uncertainty", 12.5)) if pd.notna(row.get("uncertainty")) else 12.5,
                "reliability": float(row.get("reliability", 85)) if pd.notna(row.get("reliability")) else 85.0,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"])
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }
