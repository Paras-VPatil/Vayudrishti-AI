# Satellite Data Ingestion

This module handles downloading, preprocessing, and exporting satellite-derived features for the Vayudrishti-AI pipeline.

## Supported Data Products

| Satellite | Product | Variables | Temporal Res. | Spatial Res. |
|-----------|---------|-----------|---------------|--------------|
| MODIS Terra/Aqua | MOD04_3K / MYD04_3K | AOD 550 nm, 470 nm, QA | Daily | 3 km |
| Sentinel-5P | TROPOMI L2 | NO₂, SO₂, CO, O₃, AER_AI | Daily | 3.5 × 5.5 km |
| ERA5 | Reanalysis (hourly) | Wind, RH, Temp, BLH, Precip | Hourly | ~31 km |
| ESA WorldCover | 2021 10m | Land-use classification | Annual | 10 m |
| SRTM | DEM | Elevation | Static | 30 m |

## Directory Structure

```
satellite/
├── README.md            ← This file
├── gee/                 ← Google Earth Engine (JavaScript + Python) export scripts
│   ├── export_modis_aod.js
│   ├── export_tropomi.js
│   └── export_era5.js
├── preprocessing/       ← Band extraction, reprojection, QA filtering
│   ├── aod_processor.py
│   ├── tropomi_processor.py
│   └── era5_processor.py
└── scripts/             ← End-to-end CLI ingestion orchestrators
    └── run_ingestion.py
```

## Prerequisites

```bash
# Authenticate with Google Earth Engine
earthengine authenticate

# Set your GEE project in .env
echo "GEE_PROJECT=your-gee-project-id" >> .env
```

## Usage

```bash
# Run full ingestion for a date range
python ingestion/satellite/scripts/run_ingestion.py \
    --start-date 2024-01-01 \
    --end-date   2024-01-31 \
    --region     india \
    --output-dir data/raw/satellite/
```
