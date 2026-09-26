"""
api/routers/health.py
---------------------
Health and readiness diagnostics endpoint.
"""

from fastapi import APIRouter
from api.schemas.response import HealthResponse
from api.services.model_service import get_primary_model, get_forecast_models

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Returns system status, active version, and model initialization state."""
    model = get_primary_model()
    forecasts = get_forecast_models()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="Vayudrishti-AI Hyperlocal Air Quality Intelligence",
        model_loaded=model is not None,
        forecaster_loaded=len(forecasts) > 0,
        city="Pune, Maharashtra, India"
    )
