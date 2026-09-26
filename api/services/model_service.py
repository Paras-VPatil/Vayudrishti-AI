"""
api/services/model_service.py
-----------------------------
Model inference service. Loads models ONCE at startup to avoid runtime loading overhead.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.features.feature_engineer import FeatureEngineer
from src.explainability.explain import ModelExplainer

logger = logging.getLogger(__name__)

_MODEL = None
_FEATURE_ENGINEER = None
_FEATURE_LIST = None
_FORECAST_MODELS: Dict[int, Any] = {}
_EXPLAINER = None


def load_artifacts(
    model_dir: str = "models/pm25_model_v1",
    forecast_dir: str = "models/pm25_forecast_v1"
):
    """Loads all model binaries and feature transformers into memory."""
    global _MODEL, _FEATURE_ENGINEER, _FEATURE_LIST, _FORECAST_MODELS, _EXPLAINER

    # 1. Primary PM2.5 Model
    model_json = os.path.join(model_dir, "model.json")
    model_joblib = os.path.join(model_dir, "model.joblib")
    fe_state = os.path.join(model_dir, "feature_engineer.json")
    feat_txt = os.path.join(model_dir, "feature_list.txt")

    if os.path.exists(model_json):
        _MODEL = xgb.XGBRegressor()
        _MODEL.load_model(model_json)
        logger.info("Loaded XGBoost primary model from %s", model_json)
    elif os.path.exists(model_joblib):
        _MODEL = joblib.load(model_joblib)
        logger.info("Loaded Joblib primary model from %s", model_joblib)

    if os.path.exists(fe_state):
        _FEATURE_ENGINEER = FeatureEngineer.load(fe_state)
    else:
        _FEATURE_ENGINEER = FeatureEngineer(feature_group="full")

    if os.path.exists(feat_txt):
        with open(feat_txt, "r", encoding="utf-8") as f:
            _FEATURE_LIST = [line.strip() for line in f if line.strip()]

    if _MODEL is not None:
        _EXPLAINER = ModelExplainer(_MODEL, feature_names=_FEATURE_LIST)

    # 2. Multi-Horizon Forecast Models
    horizons = [1, 6, 12, 24]
    for h in horizons:
        h_path = os.path.join(forecast_dir, f"model_lead_{h}h.json")
        if os.path.exists(h_path):
            m = xgb.XGBRegressor()
            m.load_model(h_path)
            _FORECAST_MODELS[h] = m
            logger.info("Loaded Forecast +%dh model from %s", h, h_path)


def get_primary_model():
    global _MODEL
    if _MODEL is None:
        load_artifacts()
    return _MODEL


def get_feature_engineer():
    global _FEATURE_ENGINEER
    if _FEATURE_ENGINEER is None:
        load_artifacts()
    return _FEATURE_ENGINEER


def get_forecast_models() -> Dict[int, Any]:
    global _FORECAST_MODELS
    if not _FORECAST_MODELS:
        load_artifacts()
    return _FORECAST_MODELS


def get_explainer() -> Optional[ModelExplainer]:
    global _EXPLAINER
    if _EXPLAINER is None:
        load_artifacts()
    return _EXPLAINER


def predict_pm25(input_df: pd.DataFrame) -> np.ndarray:
    """
    Transforms input row(s) and produces continuous PM2.5 prediction.
    """
    model = get_primary_model()
    fe = get_feature_engineer()

    if model is None:
        return np.array([65.0])

    X = fe.transform(input_df) if fe._fitted else input_df.copy()

    exp_cols = None
    if hasattr(model, "feature_names_in_"):
        exp_cols = list(model.feature_names_in_)
    elif hasattr(model, "get_booster") and model.get_booster().feature_names is not None:
        exp_cols = list(model.get_booster().feature_names)

    if exp_cols:
        for c in exp_cols:
            if c not in X.columns:
                X[c] = 0.0
        X = X[exp_cols]

    preds = model.predict(X)
    return np.clip(preds, 0.0, 999.0)


def predict_forecast_horizons(input_df: pd.DataFrame) -> Dict[int, float]:
    """
    Produces predictions across +1h, +6h, +12h, +24h horizons.
    """
    models = get_forecast_models()
    fe = get_feature_engineer()
    base_pred = float(predict_pm25(input_df)[0])

    X = fe.transform(input_df) if fe._fitted else input_df
    # Add dummy lag values if missing in test input
    for lag in [1, 2, 3, 6, 12, 24]:
        col = f"pm25_ground_lag_{lag}h"
        if col not in X.columns:
            X[col] = base_pred
    for rcol in ["pm25_ground_rolling_mean_6h", "pm25_ground_rolling_mean_24h", "pm25_ground_rolling_std_24h"]:
        if rcol not in X.columns:
            X[rcol] = base_pred if "mean" in rcol else 10.0

    predictions = {}
    for h in [1, 6, 12, 24]:
        if h in models:
            m = models[h]
            X_h = X.copy()
            exp_cols = None
            if hasattr(m, "feature_names_in_"):
                exp_cols = list(m.feature_names_in_)
            elif hasattr(m, "get_booster") and m.get_booster().feature_names is not None:
                exp_cols = list(m.get_booster().feature_names)

            if exp_cols:
                for c in exp_cols:
                    if c not in X_h.columns:
                        X_h[c] = 0.0
                X_h = X_h[exp_cols]

            val = float(m.predict(X_h)[0])
            predictions[h] = max(0.0, val)
        else:
            # Fallback slight diurnal drift
            drift = np.sin(h / 24.0 * np.pi) * 15.0
            predictions[h] = max(5.0, base_pred + drift)

    return predictions
