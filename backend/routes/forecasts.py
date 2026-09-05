from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    ForecastGenerateRequest,
    ForecastCorrectionRequest,
    ForecastResponse,
    ForecastVersionResponse
)
from backend.auth import get_current_user, require_role
from backend.crud import (
    create_or_save_forecast,
    get_forecast,
    list_forecasts,
    get_forecast_versions
)
from backend.forecasting import generate_event_aware_forecast

router = APIRouter(prefix="/forecast", tags=["Forecasting Engine"])


@router.post("", response_model=ForecastResponse)
def generate_forecast(
    req: ForecastGenerateRequest,
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """
    Generate event-aware forecast combining baseline moving average + planner uplift + historical benchmarks.
    Persists Forecast Version 1 (or increments version if rerun) and logs audit entry.
    """
    try:
        forecast_result = generate_event_aware_forecast(
            db=db,
            event_id=req.event_id,
            store_id=req.store_id,
            product_category=req.product_category,
            forecast_date=req.forecast_date,
            baseline_window_days=req.baseline_window_days,
            override_planner_uplift=req.override_planner_uplift,
            override_confidence=req.override_confidence
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved_forecast = create_or_save_forecast(
        db=db,
        user_id=current_user.id,
        forecast_data=forecast_result,
        reason=req.reason or "Generated event-aware forecast"
    )
    return saved_forecast


@router.get("s", response_model=List[ForecastResponse])
def get_all_forecasts(
    store_id: Optional[int] = Query(None),
    event_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """List forecasts filtered by store or event."""
    return list_forecasts(db, store_id=store_id, event_id=event_id)


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast_by_id(forecast_id: int, db: Session = Depends(get_db)):
    """Retrieve forecast details including current version and prediction intervals."""
    forecast = get_forecast(db, forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.get("/{forecast_id}/history", response_model=List[ForecastVersionResponse])
def get_forecast_history(forecast_id: int, db: Session = Depends(get_db)):
    """Retrieve full audit history of previous and current versions of this forecast."""
    forecast = get_forecast(db, forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return get_forecast_versions(db, forecast_id)


@router.post("/{forecast_id}/correction", response_model=ForecastResponse)
def correct_forecast(
    forecast_id: int,
    req: ForecastCorrectionRequest,
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """
    Submit a human planner correction to an existing forecast:
    - Never deletes previous versions.
    - Generates new ForecastVersion.
    - Updates active forecast with auditable rationale.
    """
    forecast = get_forecast(db, forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    # Re-run event forecast with overridden corrected values
    forecast_result = generate_event_aware_forecast(
        db=db,
        event_id=forecast.event_id,
        store_id=forecast.store_id,
        product_category=forecast.product_category,
        forecast_date=forecast.forecast_date,
        override_planner_uplift=req.corrected_uplift_pct,
        override_confidence=req.corrected_confidence_pct
    )

    updated_forecast = create_or_save_forecast(
        db=db,
        user_id=current_user.id,
        forecast_data=forecast_result,
        reason=f"Planner correction: {req.reason}"
    )
    return updated_forecast
