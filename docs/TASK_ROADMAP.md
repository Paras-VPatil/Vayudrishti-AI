# Vayudrishti-AI — Complete Sequential Task Roadmap

> **Product Vision**: An intelligent hyperlocal air-quality intelligence platform.
> **Target City (v1)**: Pune, Maharashtra, India.
> **Rule**: Always build bottom to top. Never skip a layer.
> **Principle**: Mock data proves code works. Real data proves science works.

---

## Current Status Snapshot

```
DONE                             NOT STARTED
─────────────────────────────    ─────────────────────────────
Project structure                Real data ingestion
requirements.txt                 Canonical dataset
aqi_feature_schema.json          EDA notebook
aqi_prediction_schema.json       Baseline ML models
cpcb_station_schema.json         AQI engine
data_catalog.md                  Forecasting
mock generator (10k rows)        SHAP
clean_cpcb.py                    Spatial interpolation
clean_satellite.py               FastAPI backend
clean_weather.py                 React frontend
clean_osm.py                     Docker
missingness.py                   Deployment
spatial_temporal_matcher.py
6/6 tests passing
```

---

## Mental Model — Always Ask "Which Layer?"

```
Stage 20: Multi-city Expansion
Stage 19: Hackathon Packaging
Stage 17-18: Docker + Evaluation
Stage 15-16: FastAPI + React Frontend
Stage 14: Spatial Interpolation (IDW / Raster)
Stage 11-13: AQI Engine + Forecasting + SHAP
Stage 9-10: Baseline ML + Fusion Ablation
Stage 8: Feature Engineering
Stage 7: EDA (Before ANY training)
Stage 6: canonical_dataset.parquet     <-- KEY MILESTONE
Stage 5: Spatial + Temporal Matching
Stage 4: Run Each Dataset Through Cleaners
Stage 3: Real Data Ingestion           <-- YOU ARE HERE
Stage 2: Repository Restructure + Config
Stage 1: Foundation (DONE)
```

---

## STAGE 1 — Foundation (COMPLETE)

| Task | File | Status |
|:-----|:-----|:------:|
| T1.1 | `schemas/aqi_feature_schema.json` | DONE |
| T1.2 | `schemas/aqi_prediction_schema.json` | DONE |
| T1.3 | `schemas/cpcb_station_schema.json` | DONE |
| T1.4 | `docs/data_catalog.md` | DONE |
| T1.5 | `mock_data/generate_mock_data.py` | DONE |
| T1.6 | `mock_data/mock_aqi_features.csv` (10,000 rows) | DONE |
| T1.7 | `src/preprocessing/clean_cpcb.py` | DONE |
| T1.8 | `src/preprocessing/clean_satellite.py` | DONE |
| T1.9 | `src/preprocessing/clean_weather.py` | DONE |
| T1.10 | `src/preprocessing/clean_osm.py` | DONE |
| T1.11 | `src/preprocessing/missingness.py` | DONE |
| T1.12 | `src/preprocessing/spatial_temporal_matcher.py` | DONE |
| T1.13 | `tests/test_preprocessing_pipeline.py` — 6/6 pass | DONE |

**Stage 1 DONE when**: `pytest tests/ -v` runs and all pass.

---

## STAGE 2 — Repository Restructure + Config

> **Why now**: Before ingesting real data, the folder structure must match the product architecture. Ingestion != Preprocessing. Separation matters at pipeline automation time.

---

### T2.1 — Create the full `src/` directory structure

Create `__init__.py` files to scaffold all future modules:

```
src/
├── ingestion/
│   ├── __init__.py
│   ├── cpcb.py              <- downloads raw CPCB data
│   ├── satellite.py         <- GEE downloads (TROPOMI + MODIS)
│   ├── weather.py           <- ERA5 downloads
│   └── osm.py               <- OSM road/building queries
├── preprocessing/           <- already exists
├── features/
│   └── __init__.py
├── domain/
│   └── __init__.py          <- AQI engine later
├── models/
│   ├── baseline/
│   ├── fusion/
│   └── forecast/
├── evaluation/
│   └── __init__.py
├── explainability/
│   └── __init__.py
├── spatial/
│   └── __init__.py
└── inference/
    └── __init__.py
```

**Done when**: `python -c "import src.ingestion"` works without error.

---

### T2.2 — Create the `data/` directory structure

```
data/
├── raw/
│   ├── ground/              <- raw CPCB parquet files
│   ├── satellite/           <- raw MODIS + TROPOMI CSVs / GeoTIFFs
│   ├── weather/             <- raw ERA5 NetCDF / CSVs
│   └── auxiliary/           <- OSM / DEM / WorldPop / WorldCover
├── interim/                 <- cleaned but not yet joined
└── processed/
    └── pune/                <- canonical_dataset.parquet lives here
```

Add `.gitkeep` in each empty folder so Git tracks them.

**Done when**: All four `data/raw/` subdirectories exist and are committed.

---

### T2.3 — Create the `configs/` system

**File**: `configs/pipeline_config.yaml`

```yaml
city: pune
bbox:
  lat_min: 18.40
  lat_max: 18.65
  lon_min: 73.70
  lon_max: 74.00

data:
  date_start: "2023-01-01"
  date_end:   "2024-12-31"

spatial_matching:
  max_radius_km: 25.0
  pixel_assignment_radius_km: 1.0

temporal_matching:
  max_difference_minutes: 60
  morning_window_lt: [9, 30, 11, 30]
  afternoon_window_lt: [12, 30, 14, 30]

satellite:
  modis_collection: "MODIS/061/MCD19A2_GRANULES"
  tropomi_no2:      "COPERNICUS/S5P/OFFL/L3_NO2"
  tropomi_so2:      "COPERNICUS/S5P/OFFL/L3_SO2"
  tropomi_co:       "COPERNICUS/S5P/OFFL/L3_CO"
  tropomi_o3:       "COPERNICUS/S5P/OFFL/L3_O3"
  modis_qa_min: 2
  tropomi_qa_no2: 0.75
  tropomi_qa_others: 0.50

era5:
  collection: "ECMWF/ERA5_LAND/HOURLY"
  grid_resolution_deg: 0.01

paths:
  raw_ground:     "data/raw/ground"
  raw_satellite:  "data/raw/satellite"
  raw_weather:    "data/raw/weather"
  raw_auxiliary:  "data/raw/auxiliary"
  interim:        "data/interim"
  processed:      "data/processed/pune"
  models:         "models"
  experiments:    "experiments"
```

**Done when**: `python -c "import yaml; yaml.safe_load(open('configs/pipeline_config.yaml'))"` succeeds.

---

### T2.4 — Add 3 additional data-quality tests

Add to `tests/test_preprocessing_pipeline.py`:

```python
def test_no_target_leakage():
    """aqi_label / aqi_category must NOT appear as feature columns."""
    ...

def test_canonical_schema_coordinates():
    """Every row must have valid lat/lon/timestamp."""
    ...

def test_realistic_value_ranges():
    """Feature values must be physically realistic (no -999 sentinels)."""
    ...
```

**Done when**: `pytest tests/ -v` shows 9/9 passing.

---

## STAGE 3 — Real Data Ingestion

> **Critical rule**: Ingestion modules download and store raw data ONLY.
> Cleaning always happens in `src/preprocessing/`. Keep these concerns separate.

---

### T3.1 — CPCB Ground Data Ingestion

**File**: `src/ingestion/cpcb.py`

**What it does**:
- Queries CPCB / OpenAQ API for Pune stations
- Fetches PM2.5, PM10, NO2, SO2, CO, O3 with timestamps
- Saves to `data/raw/ground/cpcb_YYYYMMDD.parquet`
- Stores station metadata (station_id, lat, lon, name)

**Validation gate before saving**:
- Latitude in 18.0 to 19.0 (Pune bounding box)
- Timestamp is valid ISO-8601 UTC
- At least one pollutant column is non-null

**Done when**:
- `data/raw/ground/cpcb_20240101.parquet` exists with > 0 rows
- Columns match `schemas/cpcb_station_schema.json`

---

### T3.2 — Satellite: MODIS AOD Ingestion

**File**: `src/ingestion/satellite.py` — function `fetch_modis_aod()`

**What it does**:
- Uses Google Earth Engine Python API
- Downloads `MODIS/061/MCD19A2_GRANULES` for Pune bbox and date range from config
- Exports: `aod_550nm`, `aod_qa_flag`, `latitude`, `longitude`, `timestamp_utc`
- Saves to `data/raw/satellite/modis_aod_YYYYMMDD.parquet`

**Done when**:
- File exists with valid AOD values (range 0.0 to 5.0)
- QA flag column present
- Spatial coverage includes Pune bounding box

---

### T3.3 — Satellite: Sentinel-5P TROPOMI Ingestion

**File**: `src/ingestion/satellite.py` — function `fetch_tropomi()`

**What it does**:
- Downloads all 4 TROPOMI products: NO2, SO2, CO, O3
- GEE collections from `pipeline_config.yaml`
- Saves to `data/raw/satellite/tropomi_YYYYMMDD.parquet`

**Fields to capture**:
```
no2_tropospheric_column (mol/m2)
so2_column (mol/m2)
co_column (mol/m2)
o3_column (mol/m2)
uv_aerosol_index
qa_value (per product)
latitude, longitude, timestamp_utc
```

**Done when**:
- At least 90 days of Pune data present
- All 4 gas species in the same file

---

### T3.4 — Weather: ERA5 Ingestion

**File**: `src/ingestion/weather.py`

**What it does**:
- Downloads `ECMWF/ERA5_LAND/HOURLY` via GEE
- Variables: `temperature_2m`, `dewpoint_temperature_2m`, `u_component_of_wind_10m`, `v_component_of_wind_10m`, `surface_pressure`, `total_precipitation`, `boundary_layer_height`
- Saves to `data/raw/weather/era5_YYYYMMDD.parquet`

**Done when**:
- Hourly data covers Pune bbox
- All 7 meteorological variables present

---

### T3.5 — Geography: OSM + Static Layers Ingestion

**File**: `src/ingestion/osm.py`

**What it does**:
- Downloads Pune road network from Overpass API
- Rasterizes to 1 km grid: road density, distance to road, distance to industrial zones
- Downloads ESA WorldCover 2021 land use via GEE
- Downloads SRTM DEM elevation via GEE
- Downloads WorldPop 2020 population density via GEE
- Saves to `data/raw/auxiliary/pune_static_features.parquet`

**Done when**:
- Grid file covers Pune at 1 km x 1 km resolution
- Columns present: `road_density`, `building_density`, `land_use_class`, `elevation_m`, `population_density`, `distance_to_road_km`, `distance_to_industry_km`

---

### T3.6 — Data Provenance Sidecar

Every raw file saved must have a `_meta.json` sidecar:

```json
{
  "source": "OpenAQ",
  "dataset": "CPCB_CAAQMS",
  "acquisition_time": "2026-09-27T06:00:00Z",
  "processing_time": "2026-09-27T06:05:00Z",
  "city": "pune",
  "bbox": [18.40, 73.70, 18.65, 74.00],
  "row_count": 1842,
  "schema_version": "1.0.0"
}
```

**Done when**: Every raw data file has a corresponding `_meta.json`.

---

## STAGE 4 — Run Each Dataset Through Cleaners

> Clean each raw dataset independently before joining.
> Bugs found here are far easier to diagnose than inside a 30-column merged table.

---

### T4.1 — Clean CPCB Data

```bash
python -m src.preprocessing.clean_cpcb \
    --input data/raw/ground/cpcb_20240101.parquet \
    --output data/interim/cpcb_clean.parquet
```

Checks run: negative values to NaN, physical limit violations, sensor freeze detection, NAQI sub-index calculation, dominant pollutant identification.

**Done when**: `data/interim/cpcb_clean.parquet` exists, 0 negative values, `aqi_calculated` column present.

---

### T4.2 — Clean Satellite Data

```bash
python -m src.preprocessing.clean_satellite \
    --aod data/raw/satellite/modis_aod_*.parquet \
    --tropomi data/raw/satellite/tropomi_*.parquet \
    --output data/interim/satellite_clean.parquet
```

Checks run: MODIS AOD QA >= 2, bounds [0.0, 5.0]; TROPOMI NO2 QA >= 0.75; missing indicator flags created.

**Done when**: `data/interim/satellite_clean.parquet` exists with all missingness indicator columns.

---

### T4.3 — Clean Weather Data

```bash
python -m src.preprocessing.clean_weather \
    --input data/raw/weather/era5_*.parquet \
    --output data/interim/weather_clean.parquet
```

Checks run: Kelvin to Celsius, RH via Magnus formula from dewpoint, wind speed/direction from u/v components, PBLH clipped to [50m, 6000m].

**Done when**: `data/interim/weather_clean.parquet` exists with `wind_speed_10m`, `wind_direction_10m`, `relative_humidity_2m`.

---

### T4.4 — Clean OSM/Static Features

```bash
python -m src.preprocessing.clean_osm \
    --input data/raw/auxiliary/pune_static_features.parquet \
    --output data/interim/static_features_clean.parquet
```

Checks run: road density bounded [0, 50 km/km2], building density bounded [0%, 100%], missing landuse imputed by building density threshold.

**Done when**: `data/interim/static_features_clean.parquet` exists with no NaN in density columns.

---

### T4.5 — Missing Data Audit Report

```python
import pandas as pd
from src.preprocessing.missingness import get_missingness_report
df = pd.read_parquet('data/interim/satellite_clean.parquet')
print(get_missingness_report(df))
```

**Done when**: You can explain every column above 5% missingness — why it is missing, and what the handling policy is. Write this down in `docs/missing_data_strategy.md`.

---

## STAGE 5 — Spatial + Temporal Matching (Real Data)

> This is where real satellite pixels meet real CPCB ground truth. This is the science. Get it right.

---

### T5.1 — Run Spatial Matching

Using `SpatialTemporalMatcher.match_spatial_nearest()`:

- Input: `data/interim/satellite_clean.parquet` + CPCB station metadata
- Output: Each satellite row gets nearest CPCB `station_id` and `distance_to_station_km`
- Cutoff: `max_radius_km` from config (default 25 km)
- Log: matched pixel count vs. unmatched

**Done when**:
- `data/interim/satellite_spatial_matched.parquet` exists
- `station_id` and `distance_to_station_km` present
- At least 70% of Pune pixels have a match

---

### T5.2 — Run Temporal Matching

Using `SpatialTemporalMatcher.match_temporal_window()`:

- Window: Morning (09:30-11:30 LT) for Terra MODIS; Afternoon (12:30-14:30 LT) for Aqua/TROPOMI
- Columns added: `satellite_timestamp`, `ground_timestamp`, `temporal_offset_minutes`

**Done when**:
- `data/interim/collocated_pairs.parquet` exists
- `temporal_offset_minutes` <= 60 for all rows

---

### T5.3 — Experiment: Compare Three Matching Configurations

Run with three configurations and record in `experiments/matching_experiment.csv`:

| Config | Spatial Radius | Time Window | Matched Pairs |
|:-------|:--------------|:------------|:-------------|
| A | 10 km | +/- 30 min | ? |
| B | 25 km | +/- 60 min | ? |
| C | 50 km | +/- 90 min | ? |

**Done when**: You can justify your chosen config with actual numbers. This becomes your scientific methodology.

---

## STAGE 6 — Build the Canonical Dataset

> The single most important milestone. Everything downstream depends on this.

---

### T6.1 — Create the Canonical Dataset Builder

**File**: `src/preprocessing/build_canonical_dataset.py`

Logic:
```
collocated_pairs.parquet      <- satellite + ground match
        +
weather_clean.parquet         <- ERA5 joined by timestamp + spatial grid
        +
static_features_clean         <- joined by lat/lon grid cell
        |
handle_missing_data()         <- apply missingness policy
        |
canonical_dataset.parquet
```

Schema of each row:
```
location_id, station_id, latitude, longitude
timestamp_utc, satellite_timestamp, ground_timestamp
distance_to_station_km, temporal_offset_minutes

aod_550nm, satellite_no2, satellite_so2, satellite_co, satellite_o3
uv_aerosol_index, is_aod_missing, is_no2_missing

temperature_2m, relative_humidity_2m, wind_speed_10m, wind_direction_10m
boundary_layer_height, surface_pressure, precipitation_1h

road_density, building_density, land_use_class
elevation_m, population_density, distance_to_road_km, distance_to_industry_km

pm25_ground          <- THE ONLY ML TARGET
```

> IMPORTANT: `aqi_label` and `aqi_category` are NOT in the schema.
> PM2.5 is the only target. AQI is derived after prediction. This prevents target leakage.

---

### T6.2 — Validate the Canonical Dataset

```python
# scripts/validate_canonical.py
assert df["latitude"].between(18.0, 19.0).all()
assert df["longitude"].between(73.0, 75.0).all()
assert pd.to_datetime(df["timestamp_utc"], utc=True).notna().all()
assert df["pm25_ground"].notna().sum() > 1000
assert "aqi_label" not in df.columns         # No target leakage
assert "aqi_category" not in df.columns      # No target leakage
assert df.duplicated().sum() == 0
```

**Done when**: All assertions pass.

---

### T6.3 — Save Canonical Dataset + Metadata

```
data/processed/pune/canonical_dataset.parquet
data/processed/pune/canonical_dataset_meta.json
```

```json
{
  "created_at": "...",
  "city": "pune",
  "date_range": ["2023-01-01", "2024-12-31"],
  "rows": 84392,
  "missing_aod_pct": 12.4,
  "missing_no2_pct": 8.7,
  "schema_version": "1.0.0"
}
```

---

### T6.4 — Generate Automatic Data Quality Report

**File**: `scripts/generate_data_quality_report.py`
**Output**: `data/processed/pune/data_quality_report.json`

```json
{
  "rows_received_cpcb": 152340,
  "after_cpcb_cleaning": 146820,
  "after_satellite_qa": 121450,
  "after_temporal_matching": 98214,
  "after_spatial_matching": 84392,
  "missing_aod_pct": 12.4,
  "missing_no2_pct": 8.7,
  "missing_weather_pct": 0.2,
  "duplicate_rows": 213,
  "invalid_coordinates": 7,
  "final_training_records": 84392
}
```

**Stage 6 DONE when**:
- `canonical_dataset.parquet` exists with row count > 10,000
- `data_quality_report.json` exists
- All validation assertions pass

**DATA ENGINEERING PHASE COMPLETE.**

---

## STAGE 7 — EDA (Before Any ML)

> Never train before you understand your data. EDA is not optional.

---

### T7.1 — Create EDA Notebook

**File**: `notebooks/01_eda.ipynb`

18 required sections:
```
01. Load canonical_dataset.parquet
02. Shape, dtypes, basic stats
03. Missing value heatmap
04. PM2.5 distribution (histogram + box)
05. AOD vs PM2.5 scatter + Pearson r
06. NO2 vs PM2.5
07. Wind speed vs PM2.5
08. PBLH vs PM2.5 (critical: inversions!)
09. Temperature vs PM2.5
10. Temporal: hourly mean PM2.5
11. Temporal: monthly mean PM2.5
12. Temporal: seasonal box plots
13. Spatial: PM2.5 by station on map
14. Land use category vs PM2.5 box plots
15. Road density vs PM2.5
16. Outlier investigation
17. Correlation heatmap (all features)
18. Feature importance pre-check (mutual information)
```

**Done when**: Each section has a plot and 2-3 written observations.

---

### T7.2 — Write EDA Summary Cell

At the end of the notebook, write a markdown summary. Example:
```
EDA Key Findings

1. AOD-PM2.5 Pearson r = 0.XX
2. PBLH inversions clearly increase surface PM2.5
3. Monsoon months show lowest PM2.5 due to wet deposition
4. Wind speed > 5 m/s strongly suppresses PM2.5
5. Built-up land use shows 2x higher PM2.5 than Cropland
```

**Done when**: You can present 5+ findings verbally from memory.

---

## STAGE 8 — Feature Engineering

### T8.1 — Create Feature Engineering Module

**File**: `src/features/feature_engineer.py`

Key features to generate:

```python
# Cyclic time encoding (avoids 23:59 -> 00:00 discontinuity)
df["hour_sin"]  = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"]  = np.cos(2 * np.pi * df["hour"] / 24)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

# Wind decomposition (avoids circular 359->1 jump)
df["wind_u"] = df["wind_speed_10m"] * np.cos(np.radians(df["wind_direction_10m"]))
df["wind_v"] = df["wind_speed_10m"] * np.sin(np.radians(df["wind_direction_10m"]))

# Atmospheric stability proxy
df["pblh_log"] = np.log1p(df["boundary_layer_height"])

# Interaction: high AOD + low PBLH = worse surface PM
df["aod_pblh_ratio"] = df["aod_550nm"] / (df["boundary_layer_height"] + 1)

# Season label
df["season"] = df["month"].map({
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring",  4: "Spring",  5: "Spring",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-Monsoon", 11: "Post-Monsoon"
})
```

**Done when**: Module implemented and unit tested.

---

### T8.2 — Define Three Feature Groups in Config

**File**: `configs/feature_config.yaml`

```yaml
target: pm25_ground

features_weather_only:
  - temperature_2m
  - relative_humidity_2m
  - wind_speed_10m
  - wind_direction_10m
  - boundary_layer_height
  - hour_sin
  - hour_cos

features_weather_gis:
  - temperature_2m
  - relative_humidity_2m
  - wind_speed_10m
  - wind_direction_10m
  - boundary_layer_height
  - road_density
  - building_density
  - elevation_m
  - distance_to_road_km

features_full:
  - aod_550nm
  - satellite_no2
  - satellite_so2
  - satellite_co
  - satellite_o3
  - uv_aerosol_index
  - temperature_2m
  - relative_humidity_2m
  - wind_speed_10m
  - wind_direction_10m
  - boundary_layer_height
  - surface_pressure
  - precipitation_1h
  - road_density
  - building_density
  - elevation_m
  - population_density
  - distance_to_road_km
  - distance_to_industry_km
  - hour_sin
  - hour_cos
  - month_sin
  - month_cos
  - wind_u
  - wind_v
  - pblh_log
  - aod_pblh_ratio
  - is_aod_missing
  - is_no2_missing
```

---

## STAGE 9 — Baseline ML (PM2.5 Prediction)

> Target: `pm25_ground`. NEVER `aqi_label`. NEVER `aqi_category`.

---

### T9.1 — Implement Proper Train/Val/Test Split

**File**: `src/models/cv_splitters.py`

Do NOT use random `train_test_split`.

```python
# Temporal holdout: last 3 months = unseen test set
train = df[df["timestamp_utc"] < "2024-10-01"]
test  = df[df["timestamp_utc"] >= "2024-10-01"]

# Spatial K-Fold within train (prevents station leakage in CV)
from sklearn.model_selection import GroupKFold
gkf = GroupKFold(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=df["station_id"])):
    ...
```

**Done when**: No station ID appears in both train and val folds.

---

### T9.2 — Train: Linear Regression

**File**: `training/train_baseline.py`

```python
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
```

Record in `experiments/experiment_log.csv`:
```
experiment_id, date, model, features_group, MAE, RMSE, R2, notes
```

---

### T9.3 — Train: Random Forest

```python
from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
```

Record metrics.

---

### T9.4 — Train: XGBoost

```python
import xgboost as xgb
model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    tree_method="hist",
    random_state=42
)
```

Note: XGBoost handles NaN natively — no imputation needed for satellite missingness indicators.

Record metrics.

---

### T9.5 — Evaluate and Compare All Three Models

| Model | MAE (ug/m3) | RMSE (ug/m3) | R2 | Notes |
|:------|:------------|:-------------|:---|:------|
| Linear Regression | ? | ? | ? | |
| Random Forest | ? | ? | ? | |
| XGBoost | ? | ? | ? | |

**Done when**: Table has real numbers and you can explain why one model outperforms.

---

### T9.6 — Save Best Model

```
models/pm25_model_v1/
├── model.json               <- XGBoost native format
├── model_metadata.json
└── feature_list.txt         <- exact column order
```

`model_metadata.json`:
```json
{
  "model": "XGBoost",
  "version": "v1",
  "trained_on": "2026-09-27",
  "training_period": "2023-01-01 to 2024-09-30",
  "test_period": "2024-10-01 to 2024-12-31",
  "n_features": 28,
  "MAE": "...",
  "RMSE": "...",
  "R2": "...",
  "dataset": "canonical_dataset.parquet",
  "dataset_rows": 84392
}
```

**Done when**: `xgb.XGBRegressor().load_model("models/pm25_model_v1/model.json")` works.

---

## STAGE 10 — Fusion Ablation Study

> Research question: "Does adding satellite data improve PM2.5 estimation?"

---

### T10.1 — Run Three Ablation Experiments

Using XGBoost (best baseline from Stage 9):

| Experiment | Feature Group | MAE | RMSE | R2 |
|:-----------|:-------------|:----|:-----|:---|
| A — Weather only | `features_weather_only` | ? | ? | ? |
| B — Weather + GIS | `features_weather_gis` | ? | ? | ? |
| C — Full | `features_full` | ? | ? | ? |

Record all in `experiments/experiment_log.csv`.

---

### T10.2 — Write Ablation Report

**File**: `docs/ablation_report.md`

Answer:
1. What is the MAE improvement from A to C?
2. Which single feature contributes most (by SHAP)?
3. Is the improvement statistically meaningful?

**Done when**: You can say: "Adding MODIS AOD + TROPOMI NO2 reduced MAE by X ug/m3 over weather-only baseline."

---

## STAGE 11 — AQI Engine

### T11.1 — Create AQI Module

**File**: `src/domain/aqi.py`

```python
def pm25_to_naqi(pm25: float) -> tuple[float, str]:
    """Convert PM2.5 (ug/m3) to India NAQI value and category string."""
    ...

def get_dominant_pollutant(pm25, pm10, no2, so2, co, o3) -> str:
    """Return the pollutant driving the highest NAQI sub-index."""
    ...
```

---

### T11.2 — Validate Against CPCB Reference Breakpoints

```python
assert pm25_to_naqi(15)[1] == "Good"
assert pm25_to_naqi(75)[1] == "Moderate"
assert pm25_to_naqi(200)[1] == "Poor"
assert pm25_to_naqi(350)[1] == "Very Poor"
```

**Done when**: All reference tests pass.

---

## STAGE 12 — Forecasting

### T12.1 — Build Sliding Window Dataset

**File**: `src/features/sliding_window.py`

Create lagged features per station:
- PM2.5 at t-1h, t-2h, t-3h, t-6h, t-12h, t-24h
- Weather NWP forecast values from ERA5
- Time cyclic encodings

### T12.2 — Persistence Baseline

"Predict next hour PM2.5 = current PM2.5". Any real model must beat this. Compute MAE first.

### T12.3 — Train Tree-Based Forecaster

XGBoost with lagged features. Targets: `pm25_1h`, `pm25_6h`, `pm25_12h`, `pm25_24h`.

### T12.4 — Evaluate Forecast Horizon

| Horizon | MAE | RMSE | Beats Persistence? |
|:--------|:----|:-----|:-------------------|
| 1 hour  | ?   | ?    | ?                  |
| 6 hours | ?   | ?    | ?                  |
| 12 hours| ?   | ?    | ?                  |
| 24 hours| ?   | ?    | ?                  |

**Done when**: All 4 horizons have results, all beat persistence baseline.

---

## STAGE 13 — Explainability (SHAP)

### T13.1 — SHAP Integration

```python
import shap
explainer = shap.TreeExplainer(best_model)
shap_values = explainer(X_test)
```

### T13.2 — Global Explanation

```python
shap.summary_plot(shap_values, X_test)
```

Save as `docs/shap_global_importance.png`.

### T13.3 — Local Explanation (Single Prediction)

```python
shap.waterfall_plot(shap_values[0])
```

Use a sample high-pollution day in Pune.

### T13.4 — Domain Language Translation

**File**: `src/explainability/explain.py`

```python
def generate_human_explanation(shap_row: dict) -> str:
    """
    Example output:
    "PM2.5 is HIGH (predicted 142 ug/m3).
    Main contributors: Aerosol load (AOD +38%),
    Light winds allowing buildup (+22%),
    Low boundary layer trapping pollutants (+18%)."
    """
```

**Done when**: Any prediction returns a human-readable explanation string.

---

## STAGE 14 — Spatial Interpolation

### T14.1 — Implement IDW Interpolation

**File**: `src/spatial/interpolation.py`

```python
def idw_interpolate(
    known_points: np.ndarray,  # (N, 2) lat/lon
    known_values: np.ndarray,  # (N,) PM2.5
    query_points: np.ndarray,  # (M, 2) grid lat/lon
    power: float = 2.0
) -> np.ndarray:
    ...
```

### T14.2 — Generate Pune City Grid

```python
lats = np.arange(18.40, 18.65, 0.01)
lons = np.arange(73.70, 74.00, 0.01)
grid = np.array([(lat, lon) for lat in lats for lon in lons])
```

### T14.3 — Produce PM2.5 Raster

1. Run model on every grid cell
2. Save as GeoTIFF: `data/processed/pune/pm25_YYYYMMDD.tif`
3. Visualize as choropleth map in notebook

**Done when**: A pollution heatmap image of Pune exists.

---

## STAGE 15 — FastAPI Backend

### T15.1 — Create FastAPI Project Structure

```
api/
├── main.py
├── routers/
│   ├── health.py
│   ├── prediction.py
│   ├── forecast.py
│   ├── explain.py
│   └── map.py
├── services/
│   ├── model_service.py      <- loads model ONCE at startup
│   ├── aqi_service.py
│   └── data_service.py
└── schemas/
    ├── request.py
    └── response.py
```

### T15.2 — Implement Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | API version + model status |
| `/aqi/current` | GET | Current PM2.5 + AQI for lat/lon |
| `/pm25/current` | GET | PM2.5 value only |
| `/forecast` | GET | 24-hour PM2.5 forecast |
| `/explain` | GET | SHAP explanation for current prediction |
| `/map` | GET | GeoJSON heatmap layer |
| `/historical` | GET | Historical PM2.5 time series |

### T15.3 — Load Model at Startup (Never Train Inside API)

```python
# api/services/model_service.py
import xgboost as xgb
_model = None

def get_model():
    global _model
    if _model is None:
        _model = xgb.XGBRegressor()
        _model.load_model("models/pm25_model_v1/model.json")
    return _model
```

### T15.4 — API Tests

**File**: `tests/test_api.py`

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200

def test_prediction_returns_finite():
    r = client.get("/aqi/current?lat=18.52&lon=73.85")
    assert 0 <= r.json()["predicted_aqi"] <= 500
```

**Done when**: `pytest tests/test_api.py -v` passes.

---

## STAGE 16 — React Frontend

### T16.1 — Create React Application

```bash
npx create-react-app frontend --template typescript
```

### T16.2 — Dashboard Layout

```
+----------------------------------------------+
|          VAYUDRISHTI-AI                      |
+----------------------------------------------+
|                                              |
|         Pune pollution heatmap               |
|    Green / Yellow / Orange / Red / Purple    |
|                                              |
+----------------------------------------------+
| Selected: Shivajinagar                       |
|                                              |
| PM2.5: 82 ug/m3   AQI: 178   Moderate       |
|                                              |
| Forecast (next 24 hours)                     |
| -------------------\                         |
|                     \___________             |
|                                              |
| WHY IS IT HIGH?                              |
| High aerosol load (AOD)                      |
| Low wind speed (buildup)                     |
| Low boundary layer (trapping)                |
+----------------------------------------------+
```

### T16.3 — Components to Build

| Component | Description |
|:----------|:------------|
| `PollutionMap` | Leaflet.js map with AQI color overlay |
| `AQICard` | PM2.5, AQI value, and category badge |
| `ForecastChart` | 24-hour line chart (Recharts) |
| `ExplanationPanel` | Top 3 SHAP factors in plain language |
| `HistoricalChart` | 30-day PM2.5 time series |
| `LocationSearch` | Click or search to select station |
| `AQILegend` | Color scale legend |

---

## STAGE 17 — Docker + Deployment

### T17.1 — Dockerize Backend

**File**: `Dockerfile.api`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### T17.2 — Dockerize Frontend

**File**: `frontend/Dockerfile`

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
```

### T17.3 — Docker Compose

**File**: `docker-compose.yml`

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data/processed:/app/data/processed

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api
```

**Done when**: `docker-compose up` starts both services and the dashboard loads in browser.

---

## STAGE 18 — Evaluation + Ablation Report

### T18.1 — Final Evaluation Report

**File**: `docs/evaluation_report.md`

Include:
- PM2.5 model: MAE, RMSE, R2 on temporal holdout test set
- AQI category classification accuracy
- Forecast metrics per horizon (1h, 6h, 12h, 24h)
- Ablation study results table (from Stage 10)
- Spatial error map: which areas have highest prediction error?
- Seasonal breakdown: is model worse during monsoon?

### T18.2 — Experiment Log Final State

`experiments/experiment_log.csv` should have all experiments with reproducible results. Every row = one training run.

---

## STAGE 19 — Hackathon Packaging

Demo flow must work end-to-end within 2 minutes of `docker-compose up`:

```
Judge opens browser
        |
Sees Pune pollution heatmap
        |
Clicks a location
        |
Sees PM2.5 = 142 ug/m3, AQI = Moderate
        |
Sees 24-hour forecast trending down
        |
Clicks "Why?"
        |
Sees: "High aerosol load + low boundary layer + light winds"
        |
Impressed
```

**Checklist**:
- [ ] `docker-compose up` runs cleanly in under 2 minutes
- [ ] No hardcoded credentials (use `.env` file)
- [ ] `README.md` has one-command setup: `make demo`
- [ ] 30-second demo video recorded
- [ ] `docs/` folder clean and presentable
- [ ] `.gitignore` excludes model files, raw data, `.env`

---

## STAGE 20 — Future: Multi-City Expansion

Only after Pune works end-to-end:
- Add `city` parameter to `pipeline_config.yaml`
- Run full pipeline for Delhi, Mumbai, Bengaluru
- Abstract city-specific bounding boxes into separate config files
- Add city selector to the React frontend

---

## Summary: Task Execution Order

```
DONE  Stage 1:  Foundation
      Stage 2:  Restructure + Config           <- START HERE
      Stage 3:  Real Data Ingestion (CPCB + MODIS + TROPOMI + ERA5 + OSM)
      Stage 4:  Run Each Dataset Through Cleaners
      Stage 5:  Spatial + Temporal Matching on Real Data
      Stage 6:  Build canonical_dataset.parquet + Quality Report
      Stage 7:  EDA Notebook (18 sections)
      Stage 8:  Feature Engineering
      Stage 9:  Baseline ML (Linear + RF + XGBoost)
      Stage 10: Fusion Ablation (Weather / Weather+GIS / Full)
      Stage 11: AQI Engine
      Stage 12: Forecasting (1h, 6h, 12h, 24h)
      Stage 13: SHAP + Human Explanation
      Stage 14: Spatial Interpolation (IDW + Raster)
      Stage 15: FastAPI Backend
      Stage 16: React Frontend
      Stage 17: Docker + docker-compose
      Stage 18: Evaluation + Ablation Report
      Stage 19: Hackathon Packaging
      Stage 20: Multi-city Expansion
```

---

## Rules to Never Break

| DO NOT | INSTEAD |
|:-------|:--------|
| Train inside FastAPI | Load a pre-trained `.json` artifact at startup |
| Use `aqi_label` as an ML feature | Predict PM2.5, derive AQI afterwards |
| Use random train_test_split | Spatial K-Fold + temporal holdout |
| Impute `pm25_ground` (target) | Drop rows where target is NaN |
| Start with LSTM / CNN | Start with Linear -> RF -> XGBoost |
| Build all India first | Start with Pune only |
| Hardcode matching thresholds | Put them in `configs/pipeline_config.yaml` |
| Claim "real-time" unless data supports it | Be precise about data latency |
| Commit large model files to Git | Use model registry or cloud storage |
| Write a 2000-line notebook | One notebook per stage, max 500 lines |

