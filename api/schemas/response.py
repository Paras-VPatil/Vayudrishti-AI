"""
api/schemas/response.py
-----------------------
Pydantic response models for Vayudrishti-AI REST endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "Vayudrishti-AI Hyperlocal Air Quality Intelligence"
    model_loaded: bool
    forecaster_loaded: bool
    city: str = "Pune, Maharashtra, India"


class UncertaintyBounds(BaseModel):
    margin_of_error: float
    pm25_lower_bound: float
    pm25_upper_bound: float
    confidence_level: float = 0.90
    uncertainty_percentage: float
    uncertainty_level: str


class DataReliabilityInfo(BaseModel):
    reliability_score: int
    reliability_level: str
    description: str
    inputs_verified: Dict[str, Any]


class StationComparisonInfo(BaseModel):
    nearest_station_name: str
    distance_to_station_km: float
    nearest_station_pm25: float
    hyperlocal_pm25: float
    delta_pm25: float
    delta_direction: str
    blind_spot_insight: str


class OutdoorAdvisorInfo(BaseModel):
    recommended_window: str
    lowest_predicted_pm25: float
    peak_hazard_pm25: float
    peak_hazard_horizon: str
    actionable_advice: str


class ProvenanceInfo(BaseModel):
    prediction_id: str
    model_version: str
    timestamp_utc: str
    coordinates: Dict[str, float]
    satellite_sensors: List[str]
    meteorological_model: str
    geospatial_grid: str
    target_leakage_guaranteed: bool
    cpcb_standard_version: str


class CurrentAQIResponse(BaseModel):
    latitude: float
    longitude: float
    predicted_pm25: float = Field(..., description="Surface PM2.5 in ug/m3")
    predicted_aqi: float = Field(..., description="India NAQI value (0-500)")
    category: str = Field(..., description="Good | Satisfactory | Moderate | Poor | Very Poor | Severe")
    color: str = Field(..., description="Hex color code")
    dominant_pollutant: str = Field("PM2.5", description="Primary driving pollutant")
    health_advisory: str
    timestamp: str

    # Scientific Defense & Actionability Layer
    uncertainty: Optional[UncertaintyBounds] = None
    data_reliability: Optional[DataReliabilityInfo] = None
    station_comparison: Optional[StationComparisonInfo] = None
    outdoor_advisor: Optional[OutdoorAdvisorInfo] = None
    provenance: Optional[ProvenanceInfo] = None


class CurrentPM25Response(BaseModel):
    latitude: float
    longitude: float
    pm25: float
    unit: str = "ug/m3"
    timestamp: str
    uncertainty: Optional[UncertaintyBounds] = None


class ForecastHorizonPoint(BaseModel):
    horizon_hours: int
    predicted_pm25: float
    predicted_aqi: float
    category: str
    color: str
    target_time: str


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    horizons: List[ForecastHorizonPoint]
    forecast_generated_at: str
    outdoor_advisor: Optional[OutdoorAdvisorInfo] = None


class ExplanationDriver(BaseModel):
    feature: str
    driver: str
    impact_value: float
    direction: str
    description: str


class ExplainResponse(BaseModel):
    latitude: float
    longitude: float
    predicted_pm25: float
    baseline_expected_pm25: float
    top_drivers: List[ExplanationDriver]
    narrative_explanation: str
    data_reliability: Optional[DataReliabilityInfo] = None


class HistoricalDataPoint(BaseModel):
    timestamp: str
    pm25: float
    aqi: float
    category: str


class HistoricalResponse(BaseModel):
    latitude: float
    longitude: float
    station_id: Optional[str]
    history: List[HistoricalDataPoint]
