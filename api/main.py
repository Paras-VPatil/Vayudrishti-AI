"""
api/main.py
-----------
Main FastAPI application entry point for Vayudrishti-AI Maharashtra-Wide Platform.

Provides:
- High-performance asynchronous API endpoints
- Dynamic CORS middleware configurable via environment
- Pre-loaded machine learning models at server startup
- Interactive Swagger documentation at /docs
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.routers import health, prediction, forecast, explain, map, districts, research
from api.services.model_service import load_artifacts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML models & feature pipelines once
    load_artifacts()
    yield


app = FastAPI(
    title="Vayudrishti-AI — Maharashtra Air Quality Intelligence API",
    description="""
    ## Multimodal Environmental Intelligence Platform (Maharashtra Statewide v2.0)
    
    Combines satellite Earth observations (MODIS MAIAC AOD, Sentinel-5P TROPOMI),
    meteorological reanalysis (Copernicus ERA5 / Open-Meteo with Planetary Boundary Layer Height),
    and OpenStreetMap geospatial density features across all 36 districts of Maharashtra.
    
    ### Core Capabilities:
    * **Real-time Surface PM2.5 & India NAQI**: Sub-kilometer fused estimates.
    * **Statewide Spatial Raster Overlays**: 1 km resolution regression-kriging color-mapped surfaces.
    * **Ground Station Network**: Live observations across 28 CAAQMS stations in 13 cities.
    * **Multi-Horizon Forecasting**: Direct LightGBM/XGBoost projections (+1h to +72h).
    * **Conformal Prediction Intervals**: Calibrated 90% uncertainty bounds.
    * **SHAP Atmospheric Explainability**: Plain-language translation of atmospheric physics and emission drivers.
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Configurable CORS
cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,*")
allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(health.router)
app.include_router(prediction.router)
app.include_router(forecast.router)
app.include_router(explain.router)
app.include_router(map.router)
app.include_router(districts.router)
app.include_router(research.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
