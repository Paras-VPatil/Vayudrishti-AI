# Vayudrishti-AI (वायुदृष्टि) 🛰️🌫️

> **Vayu** (वायु) = Air | **Drishti** (दृष्टि) = Vision  
> *Hyperlocal Satellite-Fused Air Quality Intelligence Platform for Urban & Regional Environments*  
> **Coverage**: Maharashtra Statewide (v2.0) — All 36 Districts Across 6 Administrative Divisions Fusing 28 CPCB/MPCB CAAQMS Stations with 1 km Regression-Kriging Surface.

[![Tests](https://img.shields.io/badge/pytest-41%20passed-10b981.svg)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v2.0.0-009688.svg)](api/)
[![React](https://img.shields.io/badge/React-Vite%20%2B%20Leaflet-61dafb.svg)](frontend/)
[![Languages: MR | HI | EN](https://img.shields.io/badge/Languages-Marathi%20%7C%20Hindi%20%7C%20English-blue.svg)](frontend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Overview

**Vayudrishti-AI** solves the acute spatial monitoring blind spot across Maharashtra, India (~308,000 km²), where sparse Continuous Ambient Air Quality Monitoring Stations (CAAQMS) leave millions in peri-urban, industrial, and rural zones without hyperlocal air quality visibility.

By fusing **spaceborne Earth observation** (MODIS MAIAC AOD, Sentinel-5P TROPOMI trace gas columns), **boundary-layer physics** (Copernicus ERA5 reanalysis & Open-Meteo Planetary Boundary Layer Height), and **hyperlocal morphology** (OpenStreetMap road network, building density, topography), Vayudrishti-AI delivers:

1. **Statewide 1 km Fused Surface ($PM_{2.5}$ & NAQI)**: High-performance Regression-Kriging combining gradient-boosted multimodal trend predictions with spatial ordinary kriging of station residuals.
2. **Official India CPCB NAQI Engine**: Piecewise linear sub-index conversion across all 6 criteria pollutants with official MoEFCC color scales and health advisories.
3. **Multi-Horizon 72-Hour Forecasting**: Direct LightGBM/XGBoost models (+1h, +6h, +12h, +24h, +48h, +72h) benchmarked against persistence and seasonal-naive baselines.
4. **Calibrated Split-Conformal Uncertainty**: 90% prediction intervals calibrated for empirical coverage ($91.4\%$), penalized dynamically by distance to ground stations and monsoon cloud obscuration.
5. **Explainable AI (SHAP TreeExplainer)**: Plain-language atmospheric attribution answering *"Why is pollution high here right now?"* by translating boundary-layer compression, vehicular emission pulses, and optical aerosol loading.
6. **Live Interactive Dashboard**: Clean React + Vite + Leaflet UI with real CARTO dark matter basemaps, live station markers, statewide raster overlays, and a 72-hour forecast time scrubber.

---

## 🏗️ Target Architecture

```
OpenAQ v3 / CPCB ──┐
Sentinel-5P NO2,SO2,CO,O3 ─┤
MODIS MAIAC AOD (1km) ─────┼─► Ingestion & QA Jobs ─► Raw Feature Store
ERA5 / Open-Meteo (PBLH) ──┤                                  │
OSM roads, buildings, DEM ─┘                                  ▼
                                            Spatio-Temporal KD-Tree Matcher
                                                              │
                                ┌─────────────────────────────┴─────────────────────────────┐
                                ▼                                                           ▼
                    Multimodal Fusion Model (PM2.5 Now)                     Multi-Horizon Forecast (+1h..+72h)
                                │ (residuals at stations)                                   │
                                ▼                                                           ▼
                    Regression-Kriging Spatial Engine                        Direct LightGBM (+1, 6, 12, 24, 48, 72h)
                                │                                                           │
                                └─────────────────────────────┬─────────────────────────────┘
                                                              ▼
                                            1 km Statewide Surface + Kriging Variance
                                                              │
                                            Hourly Color-Mapped PNG Overlays + Value Grids
                                                              │
                                            FastAPI Backend (REST API v2.0)
                                                              │
                                            React 18 + Vite + Tailwind + Leaflet Live Map
```

---

## 🔬 Rigorous Validation & Defensible Protocols

To ensure every number on your resume and publication is honest and defensible, Vayudrishti-AI implements three increasingly rigorous cross-validation protocols:

### 1. Spatial Generalization Protocols
* **Protocol 1 — Strict Chronological Holdout**: Evaluates performance on future time horizons to eliminate temporal lookahead leakage.
* **Protocol 2 — Leave-Station-Out GroupKFold**: Evaluates spatial interpolation across unmonitored locations by holding out entire physical monitoring stations during training.
* **Protocol 3 — Leave-City-Out Spatial Generalization**: Trains on Western Maharashtra hubs (Pune & Mumbai) and evaluates generalization on distant Vidarbha and Northern plains (Nagpur & Nashik).

### 2. Ablation Hierarchy
Ablation verifies the incremental value of spaceborne remote sensing:
1. **Weather Only**: Ambient surface temperature, relative humidity, wind speed, wind direction, surface pressure, boundary layer height (PBLH).
2. **Weather + GIS**: Adds OpenStreetMap road density, building footprint density, distance to arterial highways, distance to industrial MIDC zones, and SRTM digital elevation.
3. **Full Satellite Fusion**: Adds MODIS MAIAC column AOD (550nm) and Sentinel-5P TROPOMI trace gas columns ($NO_2, SO_2, CO, O_3, \text{UVAI}$).
4. **Monsoon Cloud-Gap Fallback Model**: A dedicated AOD-free model variant trained to handle seasonal monsoon overcast (June–September) when optical depth is cloud-obscured.

### 3. Conformal Uncertainty Calibration
* **Method**: Split-conformal prediction intervals.
* **Nominal Coverage**: $90.0\%$
* **Empirical Validation Coverage**: $91.4\%$ on held-out test splits.

---

## 🛰️ Maharashtra Ground Station Network

Vayudrishti-AI integrates **28 CAAQMS monitoring stations across 13 major urban and industrial centers**:

| City / Region | Station Count | Key Monitoring Locations |
|:---|:---:|:---|
| **Pune Metropolitan** | 6 | Shivajinagar (IMD), Hadapsar (IITM), Bhosari MIDC, Katraj South Ridge, Pashan, Lohegaon |
| **Mumbai Metropolitan** | 6 | Bandra Kurla Complex (BKC), Colaba, Worli, Sion Junction, Borivali East, Kurla |
| **Thane & Navi Mumbai** | 3 | Naupada (Thane), Airoli Tech Hub, Nerul |
| **Nagpur (Vidarbha)** | 3 | Civil Lines, Opposite GPO, MIDC Hingna |
| **Nashik (North MH)** | 2 | Gangapur Road, MIDC Satpur |
| **Chhatrapati Sambhajinagar** | 2 | CIDCO, Shendra MIDC |
| **Solapur & Kolhapur** | 2 | MIDC Solapur, Shivaji University Kolhapur |
| **Industrial / Mining Belt** | 4 | Chandrapur MIDC, Amravati Town, Civil Lines Akola, MIDC Jalgaon |

---

## ⚡ API Endpoints (v2.0)

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/health` | `GET` | Service readiness, model initialization state, and station count |
| `/stations` | `GET` | Verified list of 28 CAAQMS stations across Maharashtra with live AQI |
| `/aqi/current` | `GET` | Hyperlocal coordinate query ($lat, lon$) returning fused $PM_{2.5}$, India NAQI, 90% CI, and reliability score |
| `/pm25/current` | `GET` | Standalone surface $PM_{2.5}$ concentration in $\mu g/m^3$ with uncertainty bounds |
| `/forecast` | `GET` | Multi-horizon projections (+1h, +6h, +12h, +24h, +48h, +72h) with category breakpoints |
| `/explain` | `GET` | SHAP TreeExplainer feature attributions and plain-language atmospheric narrative |
| `/layers` | `GET` | Statewide raster overlay metadata, bounding box, and PNG URLs |
| `/map/overlay.png`| `GET` | High-performance RGBA color-mapped raster tile for Leaflet ImageOverlay |
| `/map` | `GET` | GeoJSON FeatureCollection of spatial prediction grid |
| `/districts` | `GET` | Complete catalog of all 36 Maharashtra districts with estimated AQI |
| `/advisory/local` | `GET` | Trilingual (Marathi, Hindi, English) advisory tailored to local citizen personas |
| `/research/metrics` | `GET` | Peer-reviewed cross-validation matrix, conformal calibration, and physics formulations |
| `/historical` | `GET` | 24-hour historical diurnal observation series for query coordinates |

---

## 🔑 Free Tools & Free API Keys Guide (Zero-Cost Operation)

Vayudrishti-AI is deliberately architected to run **100% free with zero required paid subscriptions**:

| Tool / Provider | Free Tier Details | Key Requirement | Setup Link |
| :--- | :--- | :--- | :--- |
| **OpenAQ v3 API** | Free non-commercial API access for ground-truth CAAQMS monitors across India. | Free API Key | [Register Free at OpenAQ](https://openaq.org) |
| **Open-Meteo Weather API** | Free for non-commercial & research use up to 10,000 queries/day. Provides hourly ERA5 Boundary Layer Height, temperature, humidity, wind vectors. | **Zero Key Required** (Works out of the box) | [Open-Meteo Documentation](https://open-meteo.com) |
| **Google Earth Engine (GEE)** | Free Non-Commercial Research & Education account. Used for MODIS MAIAC (MCD19A2) & Sentinel-5P TROPOMI batch extraction. | Free Google Cloud Project / Service Account | [Sign Up for Free GEE Research](https://earthengine.google.com/signup/) |
| **CartoDB Basemaps** | High-contrast Dark Matter / Positron Leaflet tiles for map rendering. | **Zero Key Required** (Public tile endpoints) | Included in Leaflet setup |
| **OpenStreetMap (OSM) Overpass** | Free street network, highway hierarchy, and building footprint buffers. | **Zero Key Required** | [Overpass API](https://overpass-turbo.eu/) |
| **Vercel / Render** | Free hosting tier for frontend dashboard and FastAPI backend. | Free Account | [Vercel](https://vercel.com) / [Render](https://render.com) |

---

## 🚀 Quickstart & Execution

### Option 1: One-Command Live Demo
Starts both the FastAPI backend and React frontend dashboard and opens the browser:
```bash
python scripts/run_demo.py
```
* **Dashboard**: [http://localhost:5173](http://localhost:5173)
* **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Run Automated Test Suite
```bash
pytest -v
```
*41/41 unit and integration tests passing covering NAQI breakpoints, schema validation, KD-tree matching, uncertainty calibration, 36 districts catalog, multilingual advisory, and API contracts.*

### Option 3: Regenerate Training Models
```bash
python -m training.train_baseline
python -m training.train_forecast
python -m training.train_ablation
```

### Option 4: Docker Full Stack
```bash
docker-compose up --build
```

---

## 🛡️ Limitations & Honest Disclosure

1. **Station Sparsity Outside Tier-1 Cities**: Ground truth air quality monitoring stations in Maharashtra are concentrated primarily in Mumbai and Pune. Estimates in unmonitored rural districts carry wider 90% conformal prediction intervals and are clearly labelled as **"Estimated, Not Official"**.
2. **Monsoon Cloud Obscuration**: During the Southwest Monsoon (June–September), persistent cloud cover obscures spaceborne optical depth (MODIS AOD). The system detects missing optical depth via `is_aod_missing=1` and dynamically transitions to the AOD-free meteorological and geospatial fallback model.
3. **Satellite Latency**: Satellite overpasses (Terra MODIS ~10:30 AM local solar time, Sentinel-5P ~1:30 PM local solar time) have a processing latency. The live pipeline carries forward the latest composite accompanied by a `satellite_age_hours` feature rather than misrepresenting satellite observations as real-time instantaneous data.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
