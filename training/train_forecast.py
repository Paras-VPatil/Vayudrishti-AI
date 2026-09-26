"""
training/train_forecast.py
--------------------------
Stage 12 — Multi-Horizon Air Quality Forecasting Pipeline.

Horizons:
- 1-Hour Ahead  (Immediate tactical forecasting)
- 6-Hour Ahead  (Commute & morning/evening advisory)
- 12-Hour Ahead (Half-day trajectory)
- 24-Hour Ahead (Next-day daily health advisory)

Benchmarks:
- Evaluates against Naive Persistence Benchmark (y_hat(t+h) = y(t)) to prove forecasting value add.
- Serializes multi-horizon models to models/pm25_forecast_v1/.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from src.features.feature_engineer import FeatureEngineer
from src.features.sliding_window import create_sliding_window_dataset, compute_persistence_baseline
from src.models.cv_splitters import temporal_train_test_split
from training.train_baseline import load_and_prepare_data


def run_forecast_training(
    data_path: str = "mock_data/mock_aqi_features.csv",
    output_dir: str = "models/pm25_forecast_v1",
    exp_log_path: str = "experiments/experiment_log.csv"
):
    print("=" * 65)
    print("STAGE 12 — MULTI-HORIZON AIR QUALITY FORECASTING")
    print("=" * 65)

    # 1. Load Data
    raw_df = load_and_prepare_data(data_path)
    print(f"Loaded {len(raw_df):,} rows from {data_path}")

    # 2. Sliding Window Lag Construction
    windowed_df = create_sliding_window_dataset(raw_df, target_col="pm25_ground")
    print(f"Constructed sliding window dataset: {len(windowed_df):,} rows")

    # 3. Temporal Train/Test Split
    train_df, test_df = temporal_train_test_split(windowed_df, timestamp_col="timestamp_utc", test_ratio=0.2)

    # 4. Feature Engineering
    fe = FeatureEngineer(feature_group="full")
    X_train_base = fe.fit_transform(train_df)
    X_test_base = fe.transform(test_df)

    # Add lag features to feature matrix
    lag_cols = [c for c in windowed_df.columns if "lag_" in c or "rolling_" in c]
    for c in lag_cols:
        X_train_base[c] = train_df[c].values
        X_test_base[c] = test_df[c].values

    feature_cols = list(X_train_base.columns)
    print(f"Total forecast feature count: {len(feature_cols)}")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("experiments", exist_ok=True)

    horizons = [1, 6, 12, 24]
    summary_table = []

    for h in horizons:
        target_name = f"target_lead_{h}h"
        print(f"\n--- Training Horizon: +{h} Hour(s) ---")

        # Drop rows where target lead is NaN (at the tail of time series)
        train_valid_mask = train_df[target_name].notna()
        test_valid_mask = test_df[target_name].notna()

        X_tr = X_train_base[train_valid_mask]
        y_tr = train_df.loc[train_valid_mask, target_name].values

        X_te = X_test_base[test_valid_mask]
        y_te = test_df.loc[test_valid_mask, target_name].values

        # 1. Evaluate Naive Persistence Baseline
        pers_mae, pers_rmse = compute_persistence_baseline(test_df, target_col="pm25_ground", horizon=h)
        print(f"  [Baseline] Persistence MAE : {pers_mae:.3f} ug/m3")

        # 2. Train XGBoost Forecaster
        model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.04,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method="hist",
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)

        mae = float(mean_absolute_error(y_te, preds))
        rmse = float(np.sqrt(mean_squared_error(y_te, preds)))
        r2 = float(r2_score(y_te, preds))
        beats_persistence = mae < pers_mae
        pct_gain = ((pers_mae - mae) / pers_mae) * 100 if pers_mae > 0 else 0

        print(f"  [XGBoost]  Forecast MAE    : {mae:.3f} ug/m3")
        print(f"  [XGBoost]  Forecast RMSE   : {rmse:.3f} ug/m3")
        print(f"  [XGBoost]  Forecast R2     : {r2:.4f}")
        print(f"  [Result]   Beats Baseline? : {'YES (' + f'{pct_gain:.1f}% gain)' if beats_persistence else 'NO'}")

        # Save model per horizon
        horizon_model_path = os.path.join(output_dir, f"model_lead_{h}h.json")
        model.save_model(horizon_model_path)

        summary_table.append({
            "Horizon": f"+{h} Hour(s)",
            "Persistence MAE (ug/m3)": round(pers_mae, 3),
            "Forecast MAE (ug/m3)": round(mae, 3),
            "Forecast RMSE (ug/m3)": round(rmse, 3),
            "R2": round(r2, 4),
            "Beats Persistence": "YES" if beats_persistence else "NO",
            "Gain (%)": round(pct_gain, 1)
        })

        # Log to experiment CSV
        log_entry = {
            "experiment_id": f"forecast_{h}h_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "date": datetime.now().isoformat(),
            "model": f"XGBoost_Forecast_{h}h",
            "feature_group": "autoregressive_lag_multimodal",
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "CV_MAE": np.nan,
            "n_train_rows": len(X_tr),
            "n_test_rows": len(X_te),
            "n_features": len(feature_cols),
        }
        log_df = pd.DataFrame([log_entry])
        if not os.path.exists(exp_log_path):
            log_df.to_csv(exp_log_path, index=False)
        else:
            log_df.to_csv(exp_log_path, mode="a", header=False, index=False)

    # Save feature list and metadata
    with open(os.path.join(output_dir, "feature_list.txt"), "w", encoding="utf-8") as f:
        for c in feature_cols:
            f.write(f"{c}\n")

    summary_df = pd.DataFrame(summary_table)
    print("\n" + "=" * 65)
    print("MULTI-HORIZON FORECAST BENCHMARK SUMMARY")
    print("=" * 65)
    print(summary_df.to_string(index=False))

    meta = {
        "model_type": "XGBoost Multi-Horizon Forecaster",
        "horizons": horizons,
        "trained_on": datetime.now().isoformat(),
        "summary": summary_table,
        "feature_count": len(feature_cols)
    }
    with open(os.path.join(output_dir, "forecast_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\nAll 4 horizon models saved in {output_dir}")
    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train multi-horizon forecasters.")
    parser.add_argument("--data", default="mock_data/mock_aqi_features.csv", help="Path to input dataset")
    args = parser.parse_args()

    chosen_path = args.data
    if os.path.exists("data/processed/pune/canonical_dataset.parquet"):
        chosen_path = "data/processed/pune/canonical_dataset.parquet"

    run_forecast_training(data_path=chosen_path)
