"""
api/main.py
-----------
Main FastAPI application entry point for Vayudrishti-AI.

Provides:
- High-performance asynchronous API endpoints
- CORS middleware for frontend connection
- Pre-loaded machine learning models at server startup
- Interactive Swagger documentation at /docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.routers import health, prediction, forecast, explain, map
from api.services.model_service import load_artifacts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML models & feature pipelines once
    load_artifacts()
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title="Vayudrishti-AI — Hyperlocal Air Quality Intelligence API",
    description="""
    ## Multimodal Environmental Intelligence Platform (Pune v1)
    
    Combines satellite Earth observations (MODIS AOD, Sentinel-5P TROPOMI),
    meteorological reanalysis (ECMWF ERA5-Land), and OpenStreetMap geospatial features
    to deliver hyperlocal, explainable, and multi-horizon forecasted air quality intelligence.
    
    ### Capabilities:
    * **Real-time Surface PM2.5 & India NAQI**: Sub-kilometer resolution estimates.
    * **Multi-Horizon Forecasting**: +1h, +6h, +12h, and +24h lead projections.
    * **SHAP Explainability**: Natural language attribution of meteorological and emission drivers.
    * **Spatial Heatmaps**: GeoJSON FeatureCollection grids for interactive mapping.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
