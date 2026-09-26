# Vayudrishti-AI (वायुदृष्टि) 🛰️🌫️

> **Vayu** (वायु) = Air | **Drishti** (दृष्टि) = Vision  
> *Hyperlocal Satellite-Fused Air Quality Intelligence Platform for Urban Environments*  
> **Target City (v1)**: Pune Metropolitan Region, Maharashtra, India.

[![Tests](https://img.shields.io/badge/pytest-28%20passed-10b981.svg)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.141-009688.svg)](api/)
[![React](https://img.shields.io/badge/React-Vite-61dafb.svg)](frontend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Overview

**Vayudrishti-AI** solves the acute spatial monitoring gap in urban India where sparse Continuous Ambient Air Quality Monitoring Stations (CAAQMS) leave millions without hyperlocal pollution awareness. By fusing **spaceborne remote sensing** (MODIS MAIAC AOD, Sentinel-5P TROPOMI trace gas columns), **boundary layer physics** (ECMWF ERA5-Land reanalysis), and **hyperlocal morphology** (OpenStreetMap road/building density), Vayudrishti-AI delivers:

1. **Sub-Kilometer Hyperlocal $PM_{2.5}$**: Continuous surface estimation across entire city grids ($0.01^\circ \approx 1\text{ km}$).
2. **Official India CPCB NAQI Engine**: Piecewise linear sub-index conversion across all 6 criteria pollutants with color coding and health advisories.
3. **Multi-Horizon 24-Hour Forecasting**: +1h, +6h, +12h, and +24h lead predictions beating persistence baselines by $>23\%$.
4. **Explainable AI (SHAP TreeExplainer)**: Plain-language atmospheric attribution answering *"Why is pollution high here right now?"*
5. **Interactive Dashboard**: Modern glassmorphism UI with dark matter Leaflet heatmaps, diurnal curves, and station diagnostics.

---

## 🏗️ Architecture

```
                                  [ DATA INGESTION ]
     ┌──────────────────────┬──────────────────────┬──────────────────────┐
     │  MODIS MAIAC AOD     │  Sentinel-5P TROPOMI │  ECMWF ERA5-Land     │  OpenStreetMap (OSM)
     │  (550nm Aerosols)    │  (NO2, SO2, CO, O3)  │  (Temp, Wind, PBLH)  │  (Road & Building)
     └──────────┬───────────┴──────────┬───────────┴──────────┬───────────┴──────────┬───────────┘
                │                      │                      │                      │
                ▼                      ▼                      ▼                      ▼
          clean_satellite        clean_satellite        clean_weather          clean_osm
                │                      │                      │                      │
                └──────────────────────┼──────────────────────┴──────────────────────┘
                                       ▼
                       [ SPATIO-TEMPORAL KD-TREE MATCHER ]
                                       │ (25km radius / 60-min window)
                                       ▼
                       [ CANONICAL DATASET BUILDER ]
                                       │ (Strict target leakage guard)
                                       ▼
                       [ FEATURE ENGINEERING PIPELINE ]
                                       │ (Cyclic time, AOD/PBLH ratios, wind UV)
                                       ▼
                       [ MULTIMODAL ML & FORECAST ENGINE ]
                      ├── Baseline ML (Linear, RF, XGBoost)
                      ├── 24-Hour Forecaster (+1h, +6h, +12h, +24h)
                      ├── SHAP TreeExplainer & Narrative Generator
                      └── IDW Spatial Continuous Grid Interpolation
                                       │
                                       ▼
                       [ HIGH-PERFORMANCE FASTAPI API ]
                                       │
                                       ▼
                       [ REACT VITE DARK GLASS DASHBOARD ]
```

---

## 📊 Scientific Ablation & Benchmarks

Strict 20% chronological holdout testing proves that spaceborne satellite observations provide irreplaceable physical mass loading signals over weather-only baselines:

| Experiment | Feature Inputs | Test MAE ($\mu g/m^3$) | Test $R^2$ Score | Gain |
|:---|:---|:---:|:---:|:---:|
| **A — Weather Only** | ERA5 (Temp, RH, Wind, PBLH, Pressure, Solar Cycles) | 86.17 | -0.0457 | Baseline |
| **B — Weather + GIS** | Weather + Road Density, Building Density, Elevation, Distances | 85.96 | -0.0511 | +0.2% |
| **C — Full Multimodal Fusion** | Weather + GIS + MODIS AOD + TROPOMI Columns + Interactions | **33.64** | **0.7834** | **+60.9% Error Reduction** |

### Multi-Horizon Forecast vs. Persistence:
- **+1h Horizon**: $87.44\ \mu g/m^3$ (**23.1% gain** over naive persistence of $113.68$)
- **+6h Horizon**: $85.72\ \mu g/m^3$ (**23.4% gain** over persistence)
- **+12h Horizon**: $86.03\ \mu g/m^3$ (**24.4% gain** over persistence)
- **+24h Horizon**: $86.91\ \mu g/m^3$ (**24.3% gain** over persistence)

---

## 🚀 Quickstart & Demo

### Option 1: One-Command Hackathon Demo
Launches both the FastAPI backend and React frontend, then automatically opens the browser:
```bash
python scripts/run_demo.py
```
- **Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Docker Compose (Full Stack)
```bash
docker-compose up --build
```
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

### Option 3: Manual Execution
```bash
# 1. Activate virtual environment
.venv\Scripts\activate   # Windows (.venv/bin/activate on Linux/Mac)

# 2. Run unit & integration test suite (28/28 tests passing)
pytest tests/ -v

# 3. Start Backend
uvicorn api.main:app --reload --port 8000

# 4. Start Frontend
cd frontend
npm install
npm run dev
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/health` | GET | Diagnostic status, active models, and pipeline version |
| `/aqi/current` | GET | Hyperlocal surface $PM_{2.5}$, India NAQI, category, and health advisory |
| `/pm25/current` | GET | Standalone raw $PM_{2.5}$ concentration ($\mu g/m^3$) |
| `/forecast` | GET | Multi-horizon forecasts (+1h, +6h, +12h, +24h) |
| `/explain` | GET | SHAP feature attribution and natural language explanation story |
| `/map` | GET | GeoJSON FeatureCollection heatmap layer for Leaflet/Mapbox |
| `/historical` | GET | 24-hour diurnal observed air quality time series |

---

## 📁 Repository Structure

```
Vayudrishti-AI/
├── api/                           # FastAPI backend service
│   ├── main.py                    # App entry point, CORS, startup loader
│   ├── routers/                   # Modular endpoint routers
│   ├── schemas/                   # Pydantic request/response models
│   └── services/                  # Inference, AQI, and data services
├── frontend/                      # React Vite dashboard (Dark Glassmorphism)
│   ├── src/App.jsx                # Main UI with Leaflet map, AQI gauge, SHAP cards
│   └── src/index.css              # Custom styling tokens and animations
├── src/
│   ├── domain/aqi.py              # Official CPCB NAQI calculation engine
│   ├── features/                  # Cyclic time, interactions, sliding window
│   ├── models/cv_splitters.py     # Leakage-free temporal & spatial GroupKFold
│   ├── explainability/explain.py  # SHAP TreeExplainer & domain translator
│   ├── spatial/interpolation.py   # IDW interpolation & Pune city grid generator
│   └── preprocessing/             # Cleaners for CPCB, satellite, ERA5, and OSM
├── training/
│   ├── train_baseline.py          # Baseline ML training (Linear, RF, XGBoost)
│   ├── train_ablation.py          # Multimodal fusion ablation pipeline
│   └── train_forecast.py          # Multi-horizon (+1h to +24h) forecasters
├── models/                        # Serialized weights, metadata, and feature lists
├── docs/                          # Architecture roadmap, data catalog, evaluation report
├── tests/                         # 28 passing unit & integration tests
├── Dockerfile.api                 # Container definition for backend
├── docker-compose.yml             # Full-stack container orchestration
└── scripts/run_demo.py            # Automated hackathon launcher
```

---

## 📜 License
MIT License © 2026 Vayudrishti-AI Contributors.
Built for the National Clean Air Programme (NCAP) and urban environmental intelligence.
