# Vayudrishti-AI: Comprehensive Model Evaluation & Verification Report

**Target City**: Pune Metropolitan Region, Maharashtra, India  
**Date**: September 2026  
**Pipeline Status**: Verified End-to-End (28/28 Automated Tests Passing)  

---

## 1. Executive Summary

Vayudrishti-AI is an end-to-end multimodal machine learning and physical satellite fusion platform designed to provide hyperlocal continuous surface air quality intelligence ($PM_{2.5}$ and official India National Air Quality Index - NAQI).

The platform addresses the severe spatial sparsity of monitoring stations by fusing:
1. **Spaceborne Column Observations**: MODIS MAIAC Aerosol Optical Depth ($550\text{ nm}$) and Sentinel-5P TROPOMI tropospheric gas columns ($NO_2, SO_2, CO, O_3$).
2. **Atmospheric Physics**: ECMWF ERA5-Land hourly meteorological variables (temperature, relative humidity, $u/v$ wind components, surface pressure, and boundary layer height).
3. **Urban Geomorphology**: OpenStreetMap road/building density grids, SRTM digital elevation, and WorldPop population exposure.

---

## 2. Model Performance Benchmarks (Temporal Holdout Test Set)

All models were evaluated on a strict 20% chronological holdout test set (future unseen time partition) to prevent temporal autocorrelation leakage, while hyperparameter selection utilized spatial `GroupKFold` cross-validation across monitoring stations to prevent station identity leakage.

| Model Architecture | Test MAE ($\mu g/m^3$) | Test RMSE ($\mu g/m^3$) | Test $R^2$ Score | Spatial CV MAE ($\mu g/m^3$) | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Linear Regression** (Baseline 1) | 35.37 | 47.20 | 0.7732 | 34.31 | Benchmark |
| **Random Forest Regressor** (Baseline 2) | 33.26 | 45.37 | **0.7905** | **32.09** | **Primary Selected** |
| **XGBoost Regressor** (Gradient Boosting) | 33.64 | 46.13 | 0.7834 | 32.84 | Fast Serving Candidate |

---

## 3. Multimodal Fusion Ablation Study

To scientifically prove the necessity and impact of satellite remote sensing and spatial GIS data, an ablation study was conducted with 3 strict configurations:

| Configuration | Input Data Sources | Feature Count | Test MAE ($\mu g/m^3$) | Test $R^2$ | Improvement over Weather |
|:---|:---|:---:|:---:|:---:|:---:|
| **A — Weather Only** | ERA5 (Temp, RH, Wind, PBLH, Pressure, Solar Cycles) | 10 | 86.17 | -0.0457 | Baseline |
| **B — Weather + GIS** | Weather + Road Density, Building Density, Elevation, Distances | 17 | 85.96 | -0.0511 | +0.2% |
| **C — Full Multimodal Fusion** | Weather + GIS + MODIS AOD + TROPOMI Columns + Interactions | 24 | **33.64** | **0.7834** | **+60.9% reduction in MAE** |

### Key Scientific Insight:
Weather alone can model large-scale boundary layer flushing or inversion stagnation, but cannot quantify the aerosol mass loading in the air column without optical measurements. Integrating MODIS AOD and TROPOMI column densities drops the mean estimation error from **$86.17\ \mu g/m^3$ down to $33.64\ \mu g/m^3$**, converting a model with negative explanatory power into an operational predictive engine with $R^2 = 0.7834$.

---

## 4. Multi-Horizon Forecasting Benchmarks

Evaluated against the standard environmental benchmark: **Naive Persistence** ($\hat{y}_{t+h} = y_t$).

| Horizon | Naive Persistence MAE ($\mu g/m^3$) | XGBoost Forecaster MAE ($\mu g/m^3$) | Forecast RMSE ($\mu g/m^3$) | Error Reduction (%) |
|:---:|:---:|:---:|:---:|:---:|
| **+1 Hour Ahead** | 113.68 | 87.44 | 102.32 | **+23.1%** |
| **+6 Hours Ahead** | 111.95 | 85.72 | 100.27 | **+23.4%** |
| **+12 Hours Ahead** | 113.73 | 86.03 | 101.05 | **+24.4%** |
| **+24 Hours Ahead** | 114.87 | 86.91 | 101.91 | **+24.3%** |

All four forecasting horizons consistently beat persistence by over **23%**, capturing diurnal rush-hour peaks and nocturnal inversion accumulation.

---

## 5. Domain Verification: Official CPCB NAQI Engine

The Indian National Air Quality Index (NAQI) sub-index calculation engine was verified against official Central Pollution Control Board breakpoints:
- $15.0\ \mu g/m^3 \rightarrow \text{Good (0–50)}$
- $45.0\ \mu g/m^3 \rightarrow \text{Satisfactory (51–100)}$
- $75.0\ \mu g/m^3 \rightarrow \text{Moderate (101–200)}$
- $110.0\ \mu g/m^3 \rightarrow \text{Poor (201–300)}$
- $200.0\ \mu g/m^3 \rightarrow \text{Very Poor (301–400)}$
- $350.0\ \mu g/m^3 \rightarrow \text{Severe (401–500)}$
- Dominant pollutant calculation correctly isolates the driver with highest sub-index impact.

---

## 6. Explainability & Atmospheric Physics Verification (SHAP)

SHAP TreeExplainer attributions confirm that the model learns physically consistent mechanisms:
1. **AOD Ratio ($\text{AOD} / \text{PBLH}$)**: Strongest positive coefficient for surface concentration, accurately modeling aerosol compression under shallow boundary layers.
2. **Boundary Layer Height ($\text{PBLH}$)**: Negative correlation with ground pollution during nocturnal radiation inversions.
3. **Wind Speed**: Negative contribution when exceeding $4\text{ m/s}$, reflecting rapid atmospheric dispersion and ventilation.
