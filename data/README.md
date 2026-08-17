# Data Directory

This directory stores all satellite, meteorological, and ground-sensor data.

> [!IMPORTANT]
> **Raw and processed data files are excluded from Git** (see `.gitignore`).
> Use DVC or Git LFS to track large files, or document download instructions below.

## Structure

```
data/
├── raw/           ← Unmodified GEE exports, CPCB sensor CSVs, etc.
│   ├── modis/     ← MOD04_3K AOD GeoTIFFs
│   ├── tropomi/   ← Sentinel-5P TROPOMI GeoTIFFs
│   └── era5/      ← ERA5-Land GeoTIFFs
│
└── processed/     ← Cleaned, reprojected, merged feature datasets
    ├── aod_processed.tif
    ├── tropomi_processed.tif
    ├── era5_processed.tif
    └── features_merged.parquet
```

## Downloading Raw Data

1. Authenticate with GEE: `earthengine authenticate`
2. Run the export scripts in `ingestion/satellite/gee/`
3. Download the exported files from Google Drive to `data/raw/<product>/`
4. Run the ingestion pipeline:

```bash
python ingestion/satellite/scripts/run_ingestion.py \
    --start-date 2024-01-01 \
    --end-date   2024-01-31 \
    --raw-dir    data/raw/satellite \
    --output-dir data/processed
```
