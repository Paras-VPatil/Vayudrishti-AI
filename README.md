# Vayudrishti-AI 🛰️🌫️

> **Vayu** (वायु) = Air | **Drishti** (दृष्टि) = Vision  
> *Seeing the air — AI-powered satellite-based AQI estimation*

## Overview

Vayudrishti-AI is a machine learning pipeline that estimates Air Quality Index (AQI) at high spatial resolution by fusing satellite remote sensing data (aerosol optical depth, land surface reflectance, meteorological variables) with ground-truth sensor observations.

## Project Structure

```
Vayudrishti-AI/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore
│
├── schemas/
│   └── aqi_feature_schema.json  # Canonical feature schema
│
├── ingestion/
│   └── satellite/
│       ├── README.md            # Satellite ingestion docs
│       ├── gee/                 # Google Earth Engine scripts
│       ├── preprocessing/       # Band extraction & normalization
│       └── scripts/             # CLI ingestion scripts
│
├── mock_data/
│   ├── generate_mock_data.py    # Script to generate synthetic data
│   └── mock_aqi_features.csv    # Pre-generated mock features
│
├── data/
│   ├── raw/                     # Raw satellite & sensor data
│   ├── processed/               # Cleaned, merged, feature-engineered data
│   └── README.md
│
├── notebooks/                   # Exploratory analysis notebooks
│
├── models/
│   └── fusion/                  # Sensor-satellite fusion models
│
└── docs/
    └── satellite_data.md        # Satellite dataset documentation
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/Vayudrishti-AI.git
cd Vayudrishti-AI

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate mock data for development
python mock_data/generate_mock_data.py
```

## Key Features

- 🛰️ **Satellite Ingestion** — Google Earth Engine (GEE) pipelines for MODIS, Sentinel-5P, Landsat
- 🔀 **Data Fusion** — Merges satellite retrievals with CPCB/ground sensor AQI readings
- 🤖 **ML Models** — Gradient boosting & deep learning models for AQI estimation
- 📊 **Evaluation** — Spatial cross-validation, temporal hold-out metrics

## Data Sources

| Source | Product | Variable |
|--------|---------|----------|
| MODIS (Terra/Aqua) | MOD04_3K | Aerosol Optical Depth (AOD) |
| Sentinel-5P | TROPOMI | NO₂, SO₂, CO, O₃ |
| ERA5 | Reanalysis | Wind, humidity, temperature |
| CPCB | Ground stations | PM2.5, PM10, AQI |

## License

MIT License © 2024 Vayudrishti-AI Contributors
