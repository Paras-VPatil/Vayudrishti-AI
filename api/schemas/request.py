"""
api/schemas/request.py
----------------------
Pydantic input validation models for Vayudrishti-AI REST endpoints.
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field


class CoordinatesQuery(BaseModel):
    lat: float = Field(..., ge=18.0, le=19.5, description="Latitude in Pune metropolitan region")
    lon: float = Field(..., ge=73.0, le=75.0, description="Longitude in Pune metropolitan region")


class FeaturePredictionRequest(BaseModel):
    latitude: float = Field(18.5204, ge=18.0, le=19.5)
    longitude: float = Field(73.8567, ge=73.0, le=75.0)
    temperature_2m: Optional[float] = Field(28.5, description="Temperature in Celsius")
    relative_humidity_2m: Optional[float] = Field(55.0, description="Relative humidity in %")
    wind_speed_10m: Optional[float] = Field(3.2, description="Wind speed in m/s")
    wind_direction_10m: Optional[float] = Field(240.0, description="Wind direction in degrees")
    boundary_layer_height: Optional[float] = Field(850.0, description="PBLH in meters")
    surface_pressure: Optional[float] = Field(955.0, description="Pressure in hPa")
    precipitation_1h: Optional[float] = Field(0.0, description="Precipitation in mm")
    aod_550nm: Optional[float] = Field(0.45, description="MODIS AOD 550nm")
    satellite_no2: Optional[float] = Field(1.5e-4, description="TROPOMI NO2 column in mol/m2")
    satellite_so2: Optional[float] = Field(2.0e-5, description="TROPOMI SO2 column in mol/m2")
    satellite_co: Optional[float] = Field(0.035, description="TROPOMI CO column in mol/m2")
    satellite_o3: Optional[float] = Field(0.12, description="TROPOMI O3 column in mol/m2")
    road_density: Optional[float] = Field(12.5, description="OSM Road Density")
    building_density: Optional[float] = Field(42.0, description="OSM Building Density")
    elevation_m: Optional[float] = Field(560.0, description="SRTM Elevation in meters")
    population_density: Optional[float] = Field(4500.0, description="WorldPop population/km2")
    distance_to_road_km: Optional[float] = Field(0.15, description="Distance to major arterial road in km")
    distance_to_industry_km: Optional[float] = Field(4.5, description="Distance to nearest industrial area in km")
