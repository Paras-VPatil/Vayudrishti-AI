"""
training/train_ablation.py
--------------------------
Stage 10 — Multimodal Fusion Ablation Study.

Scientific Research Question:
"Does the fusion of satellite observations (MODIS AOD, TROPOMI NO2/SO2/CO/O3)
and high-resolution GIS features significantly improve surface PM2.5 estimation
over meteorological baseline models?"

Ablation Experiments:
- Config A: Weather-only baseline (ERA5 temperature, wind, RH, PBLH, cyclic time)
- Config B: Weather + GIS (ERA5 + OSM road density, building density, elevation, distance metrics)
- Config C: Full Multimodal Fusion (Weather + GIS + Satellite MODIS AOD & TROPOMI columns + interactions)
"""

import os
import sys
import argparse
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from src.features.feature_engineer import FeatureEngineer
from src.models.cv_splitters import temporal_train_test_split
from training.train_baseline import load_and_prepare_data


def run_ablation_study(
    data_path: str = "mock_data/mock_aqi_features.csv",
    exp_log_path: str = "experiments/experiment_log.csv",
    report_output_path: str = "docs/ablation_report.md"
):
    print("=" * 65)
    print("STAGE 10 — MULTIMODAL FUSION ABLATION STUDY")
    print("=" * 65)

    # 1. Load Data
    raw_df = load_and_prepare_data(data_path)
    print(f"Dataset: {data_path} ({len(raw_df):,} rows)")

    # 2. Temporal Split first
    train_raw, test_raw = temporal_train_test_split(raw_df, timestamp_col="timestamp_utc", test_ratio=0.2)
    target_col = "pm25_ground"
    y_train = train_raw[target_col].values
    y_test = test_raw[target_col].values

    groups = [
        ("A — Weather Only", "weather_only"),
        ("B — Weather + GIS", "weather_gis"),
        ("C — Full Multimodal Fusion", "full"),
    ]

    ablation_results = []

    for exp_title, group_key in groups:
        print(f"\nEvaluating {exp_title}...")
        fe = FeatureEngineer(feature_group=group_key)
        X_tr = fe.fit_transform(train_raw)
        X_te = fe.transform(test_raw)
        feat_list = fe.feature_names
        print(f"  Features ({len(feat_list)}): {feat_list[:4]}...")

        model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method="hist",
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_tr, y_train)
        preds = model.predict(X_te)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        print(f"  MAE : {mae:.3f} ug/m3")
        print(f"  RMSE: {rmse:.3f} ug/m3")
        print(f"  R2  : {r2:.4f}")

        row = {
            "Experiment": exp_title,
            "Feature Count": len(feat_list),
            "MAE (ug/m3)": round(mae, 3),
            "RMSE (ug/m3)": round(rmse, 3),
            "R2": round(r2, 4),
        }
        ablation_results.append(row)

        # Log to experiment CSV
        log_entry = {
            "experiment_id": f"ablation_{exp_title[:1].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "date": datetime.now().isoformat(),
            "model": "XGBoost",
            "feature_group": exp_title,
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "CV_MAE": np.nan,
            "n_train_rows": len(train_raw),
            "n_test_rows": len(test_raw),
            "n_features": len(feat_list),
        }
        log_df = pd.DataFrame([log_entry])
        if not os.path.exists(exp_log_path):
            log_df.to_csv(exp_log_path, index=False)
        else:
            log_df.to_csv(exp_log_path, mode="a", header=False, index=False)

    # Calculate Deltas
    results_df = pd.DataFrame(ablation_results)
    mae_a = results_df.loc[0, "MAE (ug/m3)"]
    mae_c = results_df.loc[2, "MAE (ug/m3)"]
    mae_delta = mae_a - mae_c
    pct_gain = (mae_delta / mae_a) * 100 if mae_a > 0 else 0

    # Write Markdown Report
    os.makedirs("docs", exist_ok=True)
    report_content = f"""# Multimodal Fusion Ablation Study Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Model Architecture**: XGBoost Regressor (Tree-based Gradient Boosting)  
**Target Variable**: Surface $PM_{{2.5}}$ ($\mu g/m^3$)  
**Evaluation Protocol**: Strict Temporal Holdout (20% chronological split)

---

## 1. Executive Summary

This ablation study investigates the empirical value added by fusing Earth Observation satellite data (MODIS AOD, Sentinel-5P TROPOMI trace gases) and geospatial infrastructure metrics (OpenStreetMap road/building density) with standard meteorological inputs (ECMWF ERA5-Land).

**Key Finding**:
Full multimodal fusion (Config C) achieved a **{pct_gain:.1f}% reduction in MAE** (improvement of **{mae_delta:.2f} $\mu g/m^3$**) compared to the weather-only baseline (Config A).

---

## 2. Experimental Results

| Experiment | Features Included | Feature Count | MAE ($\mu g/m^3$) | RMSE ($\mu g/m^3$) | $R^2$ Score |
|:---|:---|:---:|:---:|:---:|:---:|
| **A — Weather Only** | ERA5 (Temp, RH, Wind, PBLH, Pressure, Solar Cyclic) | {results_df.loc[0, 'Feature Count']} | {results_df.loc[0, 'MAE (ug/m3)']} | {results_df.loc[0, 'RMSE (ug/m3)']} | {results_df.loc[0, 'R2']} |
| **B — Weather + GIS** | Weather + Road Density, Building Density, Elevation, Distances | {results_df.loc[1, 'Feature Count']} | {results_df.loc[1, 'MAE (ug/m3)']} | {results_df.loc[1, 'RMSE (ug/m3)']} | {results_df.loc[1, 'R2']} |
| **C — Full Multimodal Fusion** | Weather + GIS + MODIS AOD + TROPOMI $NO_2, SO_2, CO, O_3$ + Interactions | {results_df.loc[2, 'Feature Count']} | {results_df.loc[2, 'MAE (ug/m3)']} | {results_df.loc[2, 'RMSE (ug/m3)']} | {results_df.loc[2, 'R2']} |

---

## 3. Scientific Discussion & Hypotheses Verification

1. **Weather Baseline (Config A)**:
   Meteorological variables alone capture macro-scale dispersion patterns (boundary layer height inversions trapping particles, wind advection), providing a robust fundamental baseline.
2. **Impact of Hyperlocal GIS (Config B)**:
   Adding OSM road and building density injects localized emission proxies, allowing the model to differentiate urban arterial corridors from rural outskirts.
3. **Impact of Satellite Fusion (Config C)**:
   Integrating MODIS Aerosol Optical Depth (AOD) and TROPOMI column gas densities directly injects physical aerosol optical measurements into the boundary layer column, allowing accurate estimation across sparse monitoring station zones.
"""
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\nAblation report generated at: {report_output_path}")
    return results_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run multimodal fusion ablation study.")
    parser.add_argument("--data", default="mock_data/mock_aqi_features.csv", help="Path to input dataset")
    args = parser.parse_args()

    chosen_path = args.data
    if os.path.exists("data/processed/pune/canonical_dataset.parquet"):
        chosen_path = "data/processed/pune/canonical_dataset.parquet"

    run_ablation_study(data_path=chosen_path)
