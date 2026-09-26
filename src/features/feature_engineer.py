"""
src/features/feature_engineer.py
----------------------------------
Stage 8 — Feature Engineering.

Transforms the canonical dataset columns into the final ML feature matrix.

Responsibilities
----------------
- Cyclic time encoding (hour → sin/cos, month → sin/cos, doy → sin/cos)
- Log transforms for heavy-tailed satellite columns (AOD, NO₂, CO)
- Interaction features (AOD × PBLH, wind × road_density, …)
- Population-weighted road exposure
- Standardisation / normalisation (fit on train split, apply to val/test)
- OSM features: log-transform of distances

NOT responsible for:
- Imputing missing values (missingness.py handles that)
- Computing AQI (src/domain/aqi.py handles that)
- Train/val/test splitting (src/features/cv_splitters.py handles that)

Usage
-----
  from src.features.feature_engineer import FeatureEngineer
  fe = FeatureEngineer(feature_group="full")
  X_train = fe.fit_transform(train_df)
  X_val   = fe.transform(val_df)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from src.config_loader import get_feature_config

logger = logging.getLogger(__name__)

# ── Feature groups mirror feature_config.yaml ─────────────────────────────
FEATURE_GROUPS = {
    "weather_only": [
        "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
        "wind_direction_10m", "boundary_layer_height", "surface_pressure",
        "precipitation_1h",
    ],
    "weather_gis": [
        "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
        "wind_direction_10m", "boundary_layer_height", "surface_pressure",
        "precipitation_1h",
        "road_density", "building_density", "elevation_m",
        "population_density", "distance_to_road_km", "distance_to_industry_km",
    ],
    "full": [
        "aod_550nm", "satellite_no2", "satellite_so2", "satellite_co",
        "satellite_o3", "uv_aerosol_index",
        "is_aod_missing", "is_no2_missing", "is_so2_missing",
        "is_co_missing", "is_o3_missing",
        "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
        "wind_direction_10m", "boundary_layer_height", "surface_pressure",
        "precipitation_1h",
        "road_density", "building_density", "elevation_m",
        "population_density", "distance_to_road_km", "distance_to_industry_km",
    ],
}

# Columns to log-transform (right-skewed, strictly positive)
LOG_TRANSFORM_COLS = [
    "aod_550nm", "satellite_no2", "satellite_so2", "satellite_co",
    "population_density", "distance_to_road_km", "distance_to_industry_km",
]


class FeatureEngineer:
    """
    Stateful feature engineering pipeline.

    Parameters
    ----------
    feature_group : str
        One of "weather_only", "weather_gis", "full".
        Controls which base feature columns are included.
    add_cyclic : bool
        Whether to add sin/cos cyclic time features.
    add_interactions : bool
        Whether to add engineered interaction features.
    log_transform : bool
        Whether to log1p-transform heavy-tailed columns.
    scale : bool
        Whether to standardize (z-score) numeric features.
    """

    def __init__(
        self,
        feature_group: Literal["weather_only", "weather_gis", "full"] = "full",
        add_cyclic:      bool = True,
        add_interactions: bool = True,
        log_transform:   bool = True,
        scale:           bool = False,  # XGBoost/LightGBM don't need scaling
    ):
        self.feature_group    = feature_group
        self.add_cyclic       = add_cyclic
        self.add_interactions = add_interactions
        self.log_transform    = log_transform
        self.scale            = scale

        self._fitted  = False
        self._means:  pd.Series | None = None
        self._stds:   pd.Series | None = None
        self._feature_names: list[str] = []

    # ── Public API ─────────────────────────────────────────────────────────

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit the transformer on training data and return transformed features."""
        df = self._engineer(df)
        if self.scale:
            numeric = df.select_dtypes(include=[np.number]).columns
            self._means = df[numeric].mean()
            self._stds  = df[numeric].std().replace(0, 1)
            df[numeric] = (df[numeric] - self._means) / self._stds
        self._feature_names = list(df.columns)
        self._fitted = True
        logger.info("FeatureEngineer fit on %d rows → %d features", len(df), len(df.columns))
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the fitted transformer to new data."""
        if not self._fitted:
            raise RuntimeError("Call fit_transform() on training data first.")
        df = self._engineer(df)
        if self.scale and self._means is not None and self._stds is not None:
            numeric = df.select_dtypes(include=[np.number]).columns
            common  = numeric.intersection(self._means.index)
            df[common] = (df[common] - self._means[common]) / self._stds[common]
        # Align to training feature set
        df = self._align_columns(df)
        return df

    @property
    def feature_names(self) -> list[str]:
        """List of output feature column names (after fit_transform)."""
        return self._feature_names

    def save(self, path: str | Path) -> None:
        """Persist fit parameters (means/stds) and feature names to JSON."""
        state = {
            "feature_group":    self.feature_group,
            "add_cyclic":       self.add_cyclic,
            "add_interactions": self.add_interactions,
            "log_transform":    self.log_transform,
            "scale":            self.scale,
            "feature_names":    self._feature_names,
            "means":            self._means.to_dict() if self._means is not None else None,
            "stds":             self._stds.to_dict()  if self._stds  is not None else None,
        }
        Path(path).write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        logger.info("FeatureEngineer state saved → %s", path)

    @classmethod
    def load(cls, path: str | Path) -> "FeatureEngineer":
        """Restore a FeatureEngineer from a saved JSON state."""
        state = json.loads(Path(path).read_text(encoding="utf-8"))
        fe = cls(
            feature_group    = state["feature_group"],
            add_cyclic       = state["add_cyclic"],
            add_interactions = state["add_interactions"],
            log_transform    = state["log_transform"],
            scale            = state["scale"],
        )
        fe._feature_names = state["feature_names"]
        if state["means"]:
            fe._means = pd.Series(state["means"])
            fe._stds  = pd.Series(state["stds"])
        fe._fitted = True
        return fe

    # ── Private pipeline ───────────────────────────────────────────────────

    def _engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Extract datetime components if timestamp is present
        ts_col = None
        for col in ["timestamp_utc", "timestamp", "datetime", "date"]:
            if col in df.columns:
                ts_col = col
                break

        if ts_col is not None:
            ts = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
            df["hour"] = ts.dt.hour
            df["month"] = ts.dt.month
            df["doy"] = ts.dt.dayofyear

        # 1. Select base features
        base_cols = FEATURE_GROUPS[self.feature_group]
        extra_time_cols = ["hour", "month", "doy"]
        available = [c for c in base_cols + extra_time_cols if c in df.columns]
        df = df[available].copy()

        # 2. Cyclic time encoding
        if self.add_cyclic:
            df = self._add_cyclic_features(df)
        else:
            df = df.drop(columns=[c for c in extra_time_cols if c in df.columns], errors="ignore")

        # 3. Log transforms
        if self.log_transform:
            df = self._apply_log_transforms(df)

        # 4. Interaction features
        if self.add_interactions:
            df = self._add_interaction_features(df)

        return df

    def _add_cyclic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode hour, month, and day-of-year cyclically using sin/cos.
        These columns must have been added to df before calling fit_transform
        (see the _load_data() in 01_eda.py and the canonical builder).
        """
        for col, period in [("hour", 24), ("month", 12), ("doy", 365)]:
            if col in df.columns:
                df[f"{col}_sin"] = np.sin(2 * np.pi * df[col] / period)
                df[f"{col}_cos"] = np.cos(2 * np.pi * df[col] / period)
                df = df.drop(columns=[col])

        if "wind_direction_10m" in df.columns:
            wd_rad = np.deg2rad(df["wind_direction_10m"])
            df["wind_u"] = -np.sin(wd_rad)   # eastward component
            df["wind_v"] = -np.cos(wd_rad)   # northward component
            df = df.drop(columns=["wind_direction_10m"])

        return df

    def _apply_log_transforms(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply log1p to right-skewed positive columns."""
        for col in LOG_TRANSFORM_COLS:
            if col in df.columns:
                # Clip to [0, ∞) before log — negative values are physically invalid
                df[col] = np.log1p(df[col].clip(lower=0))
        return df

    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add physically motivated interaction features.

        Interactions
        ------------
        aod_pblh_ratio    : AOD / PBLH — proxy for column-to-surface partitioning
        wind_road_exposure: wind_speed × road_density — traffic emission ventilation
        rh_pblh           : humidity × PBLH — wet deposition vs mixing depth
        """
        if "aod_550nm" in df.columns and "boundary_layer_height" in df.columns:
            # Both may already be log-transformed — compute ratio in log-space is fine
            aod_safe  = df["aod_550nm"].fillna(0)
            pblh_safe = df["boundary_layer_height"].fillna(1)
            df["aod_pblh_ratio"] = aod_safe / pblh_safe.replace(0, np.nan)

        if "wind_speed_10m" in df.columns and "road_density" in df.columns:
            df["wind_road_exposure"] = df["wind_speed_10m"].fillna(0) * df["road_density"].fillna(0)

        if "relative_humidity_2m" in df.columns and "boundary_layer_height" in df.columns:
            pblh = df["boundary_layer_height"].fillna(df["boundary_layer_height"].median())
            rh   = df["relative_humidity_2m"].fillna(df["relative_humidity_2m"].median())
            df["rh_pblh"] = rh * pblh

        if "temperature_2m" in df.columns and "relative_humidity_2m" in df.columns:
            # Heat index proxy — nonlinear temp×humidity interaction
            t = df["temperature_2m"].fillna(df["temperature_2m"].median())
            r = df["relative_humidity_2m"].fillna(df["relative_humidity_2m"].median())
            df["heat_index_proxy"] = t + 0.33 * (r / 100 * 6.1078 * np.exp(17.27 * t / (t + 237.3))) - 4.0

        return df

    def _align_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure val/test DataFrame has the same columns as training.
        Missing columns are filled with 0; extra columns are dropped.
        """
        for col in self._feature_names:
            if col not in df.columns:
                logger.debug("Adding missing column '%s' = 0 (not in val/test)", col)
                df[col] = 0.0
        extra = [c for c in df.columns if c not in self._feature_names]
        if extra:
            df = df.drop(columns=extra)
        return df[self._feature_names]


# ── Convenience functions ──────────────────────────────────────────────────

def build_feature_matrix(
    df: pd.DataFrame,
    feature_group: str = "full",
    target_col: str = "pm25_ground",
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Build (X, y) from a canonical DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Canonical training dataset (may include all columns).
    feature_group : str
        One of "weather_only", "weather_gis", "full".
    target_col : str
        Column name of the prediction target.

    Returns
    -------
    (X, y) : tuple[pd.DataFrame, pd.Series]
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    y = df[target_col].copy()
    fe = FeatureEngineer(feature_group=feature_group)
    X = fe.fit_transform(df)
    return X, y


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Build feature matrix from canonical dataset")
    parser.add_argument("--canonical",  default="data/processed/pune/canonical_dataset.parquet")
    parser.add_argument("--output-dir", default="data/processed/pune")
    parser.add_argument("--group",      default="full",
                        choices=["weather_only", "weather_gis", "full"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    canonical_path = Path(args.canonical)
    if not canonical_path.exists():
        # Fall back to mock data for development
        mock_path = Path("mock_data/mock_aqi_features.csv")
        if mock_path.exists():
            df = pd.read_csv(mock_path)
            print(f"[MOCK] Using mock data ({len(df):,} rows)")
        else:
            raise FileNotFoundError(f"No data: {canonical_path}")
    else:
        df = pd.read_parquet(canonical_path)

    # Alias
    if "ground_pm25" in df.columns and "pm25_ground" not in df.columns:
        df["pm25_ground"] = df["ground_pm25"]
    if "aod" in df.columns and "aod_550nm" not in df.columns:
        df["aod_550nm"] = df["aod"]

    fe = FeatureEngineer(feature_group=args.group)
    X  = fe.fit_transform(df.drop(columns=["pm25_ground"], errors="ignore"))
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Feature names ({len(fe.feature_names)}): {fe.feature_names[:10]}…")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    X.to_parquet(out_dir / f"features_{args.group}.parquet", index=False, engine="pyarrow")
    fe.save(out_dir / f"feature_engineer_{args.group}.json")
    print(f"Saved features → {out_dir}/features_{args.group}.parquet")
