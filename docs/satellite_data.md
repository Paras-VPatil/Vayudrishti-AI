# Satellite Data Reference

Comprehensive documentation of all satellite and reanalysis data products used in the Vayudrishti-AI pipeline.

---

## 1. MODIS Aerosol Optical Depth (AOD)

| Property | Value |
|----------|-------|
| **Satellite** | Terra (MOD04_3K) / Aqua (MYD04_3K) |
| **Instrument** | MODIS |
| **Product version** | Collection 6.1 |
| **GEE Collection** | `MODIS/061/MOD04_3K` |
| **Temporal resolution** | Daily (~10:30 LT Terra, ~13:30 LT Aqua) |
| **Spatial resolution** | 3 km × 3 km |
| **Coverage** | Global |

### Key Bands Used

| Band | Description | Scale factor | Units |
|------|-------------|-------------|-------|
| `Optical_Depth_Land_And_Ocean` | AOD at 550 nm (best-coverage) | 0.001 | Dimensionless |
| `Optical_Depth_055` | AOD at 550 nm (deep-blue + dark-target) | 0.001 | Dimensionless |
| `AOD_QA` | Retrieval confidence flag | — | 0–3 |

### QA Flag Interpretation

| Flag | Meaning |
|------|---------|
| 0 | Poor — not recommended |
| 1 | Marginal |
| 2 | Good ✓ |
| 3 | Very good ✓ |

> [!TIP]
> We retain only QA ≥ 2 (good + very good) to minimise retrieval errors over complex terrain and coastal areas.

---

## 2. Sentinel-5P TROPOMI Trace Gases

| Property | Value |
|----------|-------|
| **Satellite** | Sentinel-5 Precursor (S5P) |
| **Instrument** | TROPOMI |
| **Level** | L2 Offline (OFFL) |
| **Temporal resolution** | Daily (~13:30 LT) |
| **Spatial resolution** | 3.5 km × 5.5 km (since August 2019) |

### Products Used

| Variable | GEE Collection | Band | QA threshold |
|----------|---------------|------|-------------|
| NO₂ tropospheric column | `COPERNICUS/S5P/OFFL/L3_NO2` | `tropospheric_NO2_column_number_density` | ≥ 0.75 |
| SO₂ total column | `COPERNICUS/S5P/OFFL/L3_SO2` | `SO2_column_number_density` | ≥ 0.5 |
| CO total column | `COPERNICUS/S5P/OFFL/L3_CO` | `CO_column_number_density` | ≥ 0.5 |
| O₃ total column | `COPERNICUS/S5P/OFFL/L3_O3` | `O3_column_number_density` | ≥ 0.5 |
| UV Aerosol Index | `COPERNICUS/S5P/OFFL/L3_AER_AI` | `absorbing_aerosol_index` | — |

---

## 3. ERA5-Land Reanalysis (Meteorology)

| Property | Value |
|----------|-------|
| **Provider** | ECMWF |
| **GEE Collection** | `ECMWF/ERA5_LAND/HOURLY` |
| **Temporal resolution** | Hourly |
| **Spatial resolution** | ~9 km (0.1°) |
| **Coverage** | Global land |

### Variables Used

| Variable | Original Band | Derived As | Units |
|----------|--------------|-----------|-------|
| Wind speed | `u_component_of_wind_10m`, `v_component_of_wind_10m` | `√(u²+v²)` | m/s |
| Wind direction | same | `atan2(u,v)` | degrees |
| Air temperature | `2m_temperature` | Subtract 273.15 | °C |
| Relative humidity | `2m_temperature`, `2m_dewpoint_temperature` | Magnus formula | % |
| Surface pressure | `surface_pressure` | Divide by 100 | hPa |
| Precipitation | `total_precipitation_hourly` | Multiply by 1000 | mm |

---

## 4. Static / Auxiliary Data

| Dataset | Variable | Resolution | Source |
|---------|---------|-----------|--------|
| ESA WorldCover 2021 | Land-use classification | 10 m | `ESA/WorldCover/v200` |
| SRTM DEM | Elevation | 30 m | `USGS/SRTMGL1_003` |
| WorldPop 2020 | Population density | 100 m | `WorldPop/GP/100m/pop` |
| OSM Roads | Distance to road | Vector | OpenStreetMap |

---

## 5. Ground Truth — CPCB AQI Stations

- **Source**: Central Pollution Control Board (CPCB), India
- **Variables**: PM2.5, PM10, NO₂, SO₂, CO, O₃, AQI
- **Coverage**: ~800+ stations across India
- **Temporal resolution**: Hourly (4-hour rolling average for AQI)
- **API**: [https://app.cpcbccr.com/ccr/](https://app.cpcbccr.com/ccr/)

> [!NOTE]
> Ground station data must be requested from CPCB or downloaded via the SAMEER portal.
> It is **not** redistributed in this repository.
