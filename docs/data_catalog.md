# Vayudrishti-AI 🛰️🌫️ Comprehensive Data Catalog

> **Document Version**: 1.0.0  
> **Target Scope**: Multi-modal Environmental & Satellite-to-Ground AQI Estimation  
> **Target Region**: India (National Grid + Metropolitan Focus Areas: Delhi-NCR, Mumbai, Bengaluru, Indo-Gangetic Plain)

---

## 📑 Table of Contents
1. [Overview & Fusion Architecture](#1-overview--fusion-architecture)
2. [Data Source Catalog](#2-data-source-catalog)
   - [2.1 Ground Truth: CPCB CAAQMS Network](#21-ground-truth-cpcb-caaqms-network)
   - [2.2 Satellite: Sentinel-5P TROPOMI (Trace Gases)](#22-satellite-sentinel-5p-tropomi-trace-gases)
   - [2.3 Satellite: MODIS Terra/Aqua (Aerosol Optical Depth - AOD)](#23-satellite-modis-terraaqua-aerosol-optical-depth---aod)
   - [2.4 Reanalysis & Weather: ECMWF ERA5-Land](#24-reanalysis--weather-ecmwf-era5-land)
   - [2.5 Static Geography & Built Environment: OSM, WorldCover, SRTM, WorldPop](#25-static-geography--built-environment-osm-worldcover-srtm-worldpop)
3. [Spatio-Temporal Alignment & Overlapping Strategy](#3-spatio-temporal-alignment--overlapping-strategy)
4. [Dataset Cross-Reference & Lineage Matrix](#4-dataset-cross-reference--lineage-matrix)

---

## 1. Overview & Fusion Architecture

Vayudrishti-AI combines real-time continuous ground station observations with spaceborne spectrometer/radiometer observations, meteorological reanalysis, and topographical features into a unified multi-modal feature matrix for 1 km × 1 km continuous ground AQI and PM2.5 estimation.

```
┌────────────────────────┐    ┌───────────────────────────┐    ┌─────────────────────────┐
│  CPCB Ground Stations  │    │ Sentinel-5P & MODIS Space │    │  ERA5-Land Meteorology  │
│  (Point In-Situ Data)  │    │  (Raster Column Densities)│    │  (Gridded Hourly Met)   │
└───────────┬────────────┘    └─────────────┬─────────────┘    └────────────┬────────────┘
            │                               │                               │
            └───────────────────────┐       │       ┌───────────────────────┘
                                    ▼       ▼       ▼
                          ┌───────────────────────────────────┐
                          │    Spatio-Temporal Fusion Engine  │
                          │   (Spatial Matcher + Collocation) │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │   Auxiliary Spatial Features      │
                          │  (OSM Road/Building, WorldCover)  │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │  Canonical Feature Matrix Parquet │
                          │ (schemas/aqi_feature_schema.json) │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │ Baseline & Deep ST-GNN Models     │
                          │ (Continuous PM2.5 + NAQI Classes) │
                          └───────────────────────────────────┘
```

---

## 2. Data Source Catalog

### 2.1 Ground Truth: CPCB CAAQMS Network

| Attribute | Specification |
|:---|:---|
| **Dataset Name** | Continuous Ambient Air Quality Monitoring Stations (CAAQMS) |
| **Provider / Source** | Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change (MoEFCC), India |
| **Portal / API** | [CPCB CCR Portal](https://app.cpcbccr.com/ccr/) & [OpenAQ Platform](https://openaq.org/) |
| **Measured Variables** | `PM2.5` (µg/m³), `PM10` (µg/m³), `NO2` (µg/m³), `SO2` (µg/m³), `CO` (mg/m³), `O3` (µg/m³), Ambient Temp, RH, Wind Speed |
| **Spatial Coverage** | ~800+ Fixed Monitoring Stations across Urban & Semi-Urban India |
| **Spatial Resolution** | Point observations (WGS-84 coordinate points per station) |
| **Temporal Resolution** | 15-minute / 1-hour / 24-hour rolling averages |
| **Data Latency** | Near Real-Time (~15 to 60 mins delay) |
| **Quality Control (QC)** | Negative value removal, sensor freeze/flatline filter (stuck values > 4 consecutive hours), range validation (`0 <= PM2.5 <= 1000 µg/m³`), spike filtering |
| **Purpose** | **Ground Truth Target (`y`)**: Satellite-to-ground supervised regression & classification training pairs, ground validation benchmark |
| **Used By** | Data Ingestion (`ingestion/cpcb/`), Fusion Engine (`ingestion/fusion/`), Baseline & Spatial Cross-Validation Models |

```json
// Example CPCB Station Data Record
{
  "station_id": "DEL_001_ANAND_VIHAR",
  "station_name": "Anand Vihar, Delhi - DPCC",
  "latitude": 28.6468,
  "longitude": 77.3160,
  "timestamp_utc": "2024-06-01T08:00:00Z",
  "pm25": 142.5,
  "pm10": 268.0,
  "no2": 45.2,
  "so2": 14.1,
  "co": 1.8,
  "o3": 38.6,
  "aqi_calculated": 318
}
```

---

### 2.2 Satellite: Sentinel-5P TROPOMI (Trace Gases)

| Attribute | Specification |
|:---|:---|
| **Dataset Name** | Sentinel-5 Precursor (S5P) TROPOMI Level 2 / Level 3 Offline (OFFL) |
| **Provider / Source** | European Space Agency (ESA) / Copernicus Open Access Hub / Google Earth Engine |
| **GEE Collections** | - `COPERNICUS/S5P/OFFL/L3_NO2`<br>- `COPERNICUS/S5P/OFFL/L3_SO2`<br>- `COPERNICUS/S5P/OFFL/L3_CO`<br>- `COPERNICUS/S5P/OFFL/L3_O3`<br>- `COPERNICUS/S5P/OFFL/L3_AER_AI` |
| **Variables Extracted** | - `tropospheric_NO2_column_number_density` [mol/m²]<br>- `SO2_column_number_density` [mol/m²]<br>- `CO_column_number_density` [mol/m²]<br>- `O3_column_number_density` [mol/m²]<br>- `absorbing_aerosol_index` (UV Aerosol Index, dimensionless) |
| **Spatial Resolution** | 3.5 km × 5.5 km (along × across track, resampled to 0.01° / ~1 km grid) |
| **Temporal Resolution** | Daily overpass (Ascending node, ~13:30 Local Solar Time) |
| **Data Latency** | Offline (OFFL): ~24–48 hours post-orbit; Near Real-Time (NRTI): ~3 hours |
| **Quality Control (QC)** | Filter by QA flag: `qa_value >= 0.75` for NO2 (removes cloud fraction > 0.3 and snow/ice); `qa_value >= 0.50` for SO2, CO, O3 |
| **Purpose** | Gaseous precursor and chemical indicator features for photochemical pollution, secondary aerosol formation, and traffic/industrial emissions |
| **Used By** | Feature Extraction, Tabular Models, Graph Neural Networks, Inference Service |

---

### 2.3 Satellite: MODIS Terra/Aqua (Aerosol Optical Depth - AOD)

| Attribute | Specification |
|:---|:---|
| **Dataset Name** | MODIS Multi-angle Implementation of Atmospheric Correction (MAIAC) / MOD04_3K & MYD04_3K Collection 6.1 |
| **Provider / Source** | NASA Goddard Space Flight Center / Land Processes DAAC / Google Earth Engine |
| **GEE Collections** | `MODIS/061/MOD04_3K` (Terra) & `MODIS/061/MYD04_3K` (Aqua) or `MODIS/061/MCD19A2_GRANULES` (1 km MAIAC) |
| **Variables Extracted** | - `Optical_Depth_Land_And_Ocean` (AOD at 550 nm, dimensionless)<br>- `Optical_Depth_047` / `Optical_Depth_055` (AOD at 470 nm & 550 nm)<br>- `AOD_QA` / `QA_flags` (Quality confidence) |
| **Spatial Resolution** | 1 km × 1 km (MCD19A2) / 3 km × 3 km (MOD04_3K) |
| **Temporal Resolution** | Twice Daily: Terra (~10:30 Local Solar Time morning) & Aqua (~13:30 Local Solar Time afternoon) |
| **Data Latency** | Standard product: 1–2 days; LANCE Rapid Response: ~3 hours |
| **Quality Control (QC)** | Keep only Quality Assurance (QA) flags >= 2 (Good & Very Good retrievals); Cloud and high surface reflectance masking |
| **Purpose** | Core physical feature measuring atmospheric total aerosol column extinction; primary spaceborne proxy for ground-level particulate matter (`PM2.5`, `PM10`) |
| **Used By** | Satellite Ingestion Pipeline, Spatial Interpolator, Model Feature Matrix |

---

### 2.4 Reanalysis & Weather: ECMWF ERA5-Land

| Attribute | Specification |
|:---|:---|
| **Dataset Name** | ECMWF ERA5-Land Hourly Reanalysis |
| **Provider / Source** | European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Climate Change Service (C3S) |
| **GEE Collection** | `ECMWF/ERA5_LAND/HOURLY` & `ECMWF/ERA5/HOURLY` |
| **Variables Extracted** | - `temperature_2m` [°C] (converted from Kelvin: $T - 273.15$)<br>- `relative_humidity_2m` [%] (computed via Magnus formula using 2m temperature & dewpoint)<br>- `u_component_of_wind_10m`, `v_component_of_wind_10m` [m/s]<br>- `wind_speed_10m` [m/s] ($=\sqrt{u^2 + v^2}$)<br>- `wind_direction_10m` [°] ($=\text{atan2}(u, v) \times \frac{180}{\pi} \pmod{360}$)<br>- `boundary_layer_height` ($PBLH$) [m] (critical for thermal inversion & pollutant trapping)<br>- `surface_pressure` [hPa]<br>- `total_precipitation_hourly` [mm] |
| **Spatial Resolution** | ~9 km (0.1° × 0.1°), bilinearly interpolated to standard 1 km grid |
| **Temporal Resolution** | Hourly |
| **Data Latency** | ERA5T (preliminary): 5 days; Final: ~2–3 months |
| **Quality Control (QC)** | Continuous physical consistency checks; boundary layer height clipping ($PBLH \ge 50\text{ m}$) |
| **Purpose** | Meteorological conditioning (dispersion, deposition, boundary layer trapping, gas-to-particle conversion thermodynamics) |
| **Used By** | Meteorological Preprocessor, ML Feature Engine, Forecast Ingestion |

---

### 2.5 Static Geography & Built Environment: OSM, WorldCover, SRTM, WorldPop

| Attribute | Specification |
|:---|:---|
| **Datasets Included** | 1. **OpenStreetMap (OSM)**: Road networks (highways, primary, secondary), industrial zones, building footprints<br>2. **ESA WorldCover 2021**: 10 m global land cover (11 classification categories)<br>3. **NASA SRTM DEM**: 30 m Digital Elevation Model (`USGS/SRTMGL1_003`)<br>4. **WorldPop 2020**: 100 m Gridded Population Density (`WorldPop/GP/100m/pop`) |
| **Provider / Source** | ESA, NASA/USGS, WorldPop Hub, Geofabrik / Overpass API (OSM) |
| **Variables Extracted** | - `road_density`: Total road length per unit grid area ($\text{km}/\text{km}^2$)<br>- `building_density`: Percentage built-up footprint area per grid cell (%)<br>- `landuse_class`: Categorical class (Built-up, Cropland, Tree cover, Water, Bare, etc.)<br>- `distance_to_road_km`: Euclidean distance to closest major roadway (km)<br>- `distance_to_industry_km`: Distance to closest designated industrial polygon (km)<br>- `elevation_m`: Elevation above sea level (m)<br>- `population_density`: Persons per $\text{km}^2$ |
| **Spatial Resolution** | Native 10 m – 100 m; aggregated/rasterized to canonical 1 km × 1 km target grid |
| **Temporal Resolution** | Static baseline (annual / decadal updates) |
| **Quality Control (QC)** | Projection standardization to EPSG:4326 (WGS-84), spatial filling of void elevation pixels via spline interpolation |
| **Purpose** | Spatial prior representing local anthropogenic emission sources, micro-urban canyons, terrain trapping, and human exposure |
| **Used By** | Static Feature Cache, Spatial Matcher, Graph Edge Weighting |

---

## 3. Spatio-Temporal Alignment & Overlapping Strategy

### 3.1 Temporal Overlap Strategy for Model Training

Because satellite instruments pass over India at specific daylight windows while ground stations measure continuously, we establish a strict **collocation time window**:

```
00:00               10:30 (Terra)        13:30 (Aqua/TROPOMI)               24:00
  │                       │                       │                           │
  ▼                       ▼                       ▼                           ▼
──┼───────────────────────●───────────────────────●───────────────────────────┼──
                          ▲                       ▲
                          │                       │
                 [±60 min Overpass Window]   [±60 min Overpass Window]
                  Ground: 09:30 - 11:30 LT    Ground: 12:30 - 14:30 LT
                  ERA5: Closest 10:00/11:00   ERA5: Closest 13:00/14:00
```

1. **Daily Overpass Pairs**:
   - **Morning Window (Terra MODIS)**: Ground and ERA5 variables averaged over **09:30–11:30 Local Time** (centered on 10:30 LT).
   - **Afternoon Window (Aqua MODIS + S5P TROPOMI)**: Ground and ERA5 variables averaged over **12:30–14:30 Local Time** (centered on 13:30 LT).
2. **24-Hour Daily Aggregation Split**:
   - When training daily average AQI models, daytime satellite features are paired with the 24-hour mean CPCB ground values, adjusted by ERA5 diurnal dispersion indices.

### 3.2 Spatial Overlap & Resampling Grid Strategy

| Parameter | Standard Value | Rationale |
|:---|:---|:---|
| **Target Coordinate System** | EPSG:4326 (WGS-84) | Standard global geo-referencing format |
| **Target Grid Cell Size** | $0.01^\circ \times 0.01^\circ$ (~1.1 km × 1.1 km) | Matches Sentinel-5P/MODIS effective resolving capacity while preserving neighborhood-scale variations |
| **Ground Station Buffer Radius** | $r = 1.0\text{ km}$ (for pixel assignment) | Assigns ground station observation to the intersecting 1 km grid cell |
| **Maximum Ground Search Radius** | $25.0\text{ km}$ (for spatial interpolation/validation) | Stations beyond 25 km are treated as out-of-range to avoid unrepresentative spatial association |
| **Resampling Method** | Bilinear for continuous met/AOD; Nearest-neighbor for discrete landuse classes | Preserves smooth meteorological gradients and valid discrete classifications |

---

## 4. Dataset Cross-Reference & Lineage Matrix

| Feature Name | Source | Sensor / Model | Native Res | Target Res | Schema Field Name |
|:---|:---|:---|:---|:---|:---|
| Target PM2.5 | CPCB | BAM / TEOM | Point | Point / 1km | `ground_pm25` / `pm25_ground` |
| Target PM10 | CPCB | BAM / TEOM | Point | Point / 1km | `ground_pm10` / `pm10_ground` |
| Target NAQI | CPCB | NAQI Formula | Point | Integer [0–500] | `aqi_label` |
| AOD 550nm | NASA | MODIS (Terra/Aqua) | 1–3 km | 1 km | `aod_550nm` |
| Tropospheric NO₂ | ESA | Sentinel-5P TROPOMI | 3.5×5.5 km | 1 km | `no2_tropospheric_column` |
| Total SO₂ Column | ESA | Sentinel-5P TROPOMI | 3.5×5.5 km | 1 km | `so2_column` |
| Total CO Column | ESA | Sentinel-5P TROPOMI | 5.5×7 km | 1 km | `co_column` |
| Total O₃ Column | ESA | Sentinel-5P TROPOMI | 3.5×5.5 km | 1 km | `o3_column` |
| UV Aerosol Index | ESA | Sentinel-5P TROPOMI | 3.5×5.5 km | 1 km | `uv_aerosol_index` |
| 2m Temperature | ECMWF | ERA5-Land | 9 km | 1 km | `temperature_2m` |
| 2m Relative Humidity | ECMWF | ERA5-Land | 9 km | 1 km | `relative_humidity_2m` |
| 10m Wind Speed | ECMWF | ERA5-Land | 9 km | 1 km | `wind_speed_10m` |
| 10m Wind Direction | ECMWF | ERA5-Land | 9 km | 1 km | `wind_direction_10m` |
| Boundary Layer Height | ECMWF | ERA5 | 30 km | 1 km | `boundary_layer_height` |
| Surface Pressure | ECMWF | ERA5-Land | 9 km | 1 km | `surface_pressure` |
| Precipitation | ECMWF | ERA5-Land | 9 km | 1 km | `precipitation_1h` |
| Road Density | OSM | Overpass API | Vector | 1 km | `road_density` |
| Building Density | OSM / WorldCover | Overpass / ESA | Vector/10m | 1 km | `building_density` |
| Land Use Class | ESA | WorldCover 2021 | 10 m | 1 km | `land_use_class` |
| Distance to Road | OSM | Overpass API | Vector | 1 km | `distance_to_road_km` |
| Distance to Industry | OSM | Overpass API | Vector | 1 km | `distance_to_industry_km` |
| Elevation | NASA/USGS | SRTM DEM | 30 m | 1 km | `elevation_m` |
| Population Density | WorldPop | GP 100m | 100 m | 1 km | `population_density` |
