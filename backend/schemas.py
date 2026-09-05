from __future__ import annotations
import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- USER SCHEMAS ---
class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    city: Optional[str] = None
    created_at: datetime.datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# --- STORE SCHEMAS ---
class StoreBase(BaseModel):
    store_code: str
    store_name: str
    city: str
    latitude: float
    longitude: float
    store_type: str = "High Street"
    size_sqft: int = 5000
    active: bool = True


class StoreCreate(StoreBase):
    pass


class StoreResponse(StoreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime


# --- PRODUCT SCHEMAS ---
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    category: str
    name: str
    unit_cost: float
    retail_price: float
    holding_cost_rate: float
    carbon_kg_per_unit: float


# --- EVENT SCHEMAS ---
class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    event_type: str
    start_date: str
    end_date: str
    latitude: float
    longitude: float
    location_name: str
    city: str
    expected_attendance: int = 5000
    source: str = "Local Event System"
    source_url: str = "internal://events"
    status: str = "active"
    impact_radius_km: float = 15.0


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    city: Optional[str] = None
    expected_attendance: Optional[int] = None
    status: Optional[str] = None
    impact_radius_km: Optional[float] = None


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    distance_to_store_km: Optional[float] = None


# --- PLANNER ASSESSMENT SCHEMAS ---
class PlannerAssessmentCreate(BaseModel):
    affected_store_ids: List[int]
    affected_categories: List[str]
    expected_uplift_pct: float = Field(..., ge=-50.0, le=300.0, description="Percentage uplift e.g. 30.0 for +30%")
    confidence_pct: float = Field(..., ge=0.0, le=100.0, description="Planner confidence 0 to 100%")
    demand_duration_days: int = Field(3, ge=1, le=30)
    planner_notes: Optional[str] = None
    reason: Optional[str] = None


class PlannerAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    user_id: int
    affected_store_ids: str
    affected_categories: str
    expected_uplift_pct: float
    confidence_pct: float
    demand_duration_days: int
    planner_notes: Optional[str]
    reason: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


# --- FORECAST SCHEMAS ---
class ForecastGenerateRequest(BaseModel):
    event_id: int
    store_id: int
    product_category: str
    forecast_date: str
    baseline_window_days: int = 14
    override_planner_uplift: Optional[float] = None
    override_confidence: Optional[float] = None
    reason: Optional[str] = "Initial event-aware forecast generation"


class ForecastCorrectionRequest(BaseModel):
    corrected_uplift_pct: float = Field(..., ge=-50.0, le=300.0)
    corrected_confidence_pct: float = Field(..., ge=0.0, le=100.0)
    reason: str = Field(..., min_length=5, description="Auditable justification for the forecast modification")


class ForecastVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    forecast_id: int
    version_number: int
    user_id: int
    baseline_forecast: float
    event_aware_forecast: float
    effective_uplift_pct: float
    confidence_pct: float
    reason: str
    created_at: datetime.datetime


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    store_id: int
    product_category: str
    forecast_date: str
    baseline_forecast: float
    planner_expected_uplift_pct: float
    historical_similar_event_uplift_pct: float
    effective_uplift_pct: float
    event_aware_forecast: float
    ml_forecast: Optional[float]
    prediction_interval_lower: float
    prediction_interval_upper: float
    heuristic_confidence_pct: float
    current_version: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    versions: List[ForecastVersionResponse] = []


# --- SALES SCHEMAS ---
class SalesCreate(BaseModel):
    store_id: int
    product_category: str
    date: str
    baseline_expected: float
    actual_units: float
    revenue: float = 0.0
    returns_units: float = 0.0
    stock_available: float = 0.0
    event_id: Optional[int] = None


class SalesResponse(SalesCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
    observed_uplift_pct: Optional[float] = None


# --- AUDIT SCHEMAS ---
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entity_type: str
    entity_id: int
    action: str
    user_id: int
    timestamp: datetime.datetime
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    user_name: Optional[str] = None


# --- ANALYTICS & BACKTEST SCHEMAS ---
class MetricsSummaryResponse(BaseModel):
    total_events: int
    reviewed_events: int
    forecasts_generated: int
    baseline_wape: float
    event_aware_wape: float
    ml_wape: float
    wape_improvement_pct: float
    baseline_mae: float
    event_aware_mae: float
    mae_improvement_pct: float
    baseline_rmse: float
    event_aware_rmse: float
    bias_baseline: float
    bias_event_aware: float
    stockout_rate_baseline: float
    stockout_rate_event_aware: float
    excess_units_baseline: float
    excess_units_event_aware: float
    estimated_excess_cost_savings: float
    estimated_carbon_saved_kg: float
    prediction_interval_coverage_pct: float
