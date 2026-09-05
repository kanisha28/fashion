import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="planner")  # admin, planner, viewer
    city = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    assessments = relationship("PlannerAssessment", back_populates="user")
    forecast_versions = relationship("ForecastVersion", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    store_code = Column(String(20), unique=True, index=True, nullable=False)
    store_name = Column(String(100), nullable=False)
    city = Column(String(50), index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    store_type = Column(String(50), default="High Street")  # Flagship, High Street, Mall
    size_sqft = Column(Integer, default=5000)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sales = relationship("Sales", back_populates="store")
    forecasts = relationship("Forecast", back_populates="store")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(50), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    unit_cost = Column(Float, default=500.0)
    retail_price = Column(Float, default=1499.0)
    holding_cost_rate = Column(Float, default=0.20)  # 20% annual holding rate
    carbon_kg_per_unit = Column(Float, default=3.2)  # Proxy kg CO2e per unit apparel
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), index=True, nullable=False)  # Festival, Concert, Sports, Exhibition, College, Cultural, Weather, Shopping, Other
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(150), nullable=False)
    city = Column(String(50), index=True, nullable=False)
    expected_attendance = Column(Integer, default=5000)
    source = Column(String(100), default="Local Cultural Board")
    source_url = Column(String(255), default="internal://curated/events")
    status = Column(String(30), default="active")  # pending, approved, active, completed, cancelled
    impact_radius_km = Column(Float, default=15.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    assessments = relationship("PlannerAssessment", back_populates="event", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="event")
    sales = relationship("Sales", back_populates="event")


class PlannerAssessment(Base):
    __tablename__ = "planner_assessments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    affected_store_ids = Column(Text, nullable=False)  # JSON array string: "[1, 4]"
    affected_categories = Column(Text, nullable=False) # JSON array string: "[\"Traditional Wear\"]"
    expected_uplift_pct = Column(Float, nullable=False) # e.g. 30.0 for +30%
    confidence_pct = Column(Float, nullable=False)      # 0 to 100
    demand_duration_days = Column(Integer, default=3)
    planner_notes = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    event = relationship("Event", back_populates="assessments")
    user = relationship("User", back_populates="assessments")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    product_category = Column(String(50), nullable=False, index=True)
    forecast_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    baseline_forecast = Column(Float, nullable=False)
    planner_expected_uplift_pct = Column(Float, nullable=False)
    historical_similar_event_uplift_pct = Column(Float, default=0.0)
    effective_uplift_pct = Column(Float, nullable=False)
    event_aware_forecast = Column(Float, nullable=False)
    ml_forecast = Column(Float, nullable=True)
    prediction_interval_lower = Column(Float, nullable=False)
    prediction_interval_upper = Column(Float, nullable=False)
    heuristic_confidence_pct = Column(Float, nullable=False)
    current_version = Column(Integer, default=1)
    status = Column(String(20), default="active")  # active, revised, archived
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    event = relationship("Event", back_populates="forecasts")
    store = relationship("Store", back_populates="forecasts")
    versions = relationship("ForecastVersion", back_populates="forecast", cascade="all, delete-orphan", order_by="ForecastVersion.version_number")


class ForecastVersion(Base):
    __tablename__ = "forecast_versions"

    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey("forecasts.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    baseline_forecast = Column(Float, nullable=False)
    event_aware_forecast = Column(Float, nullable=False)
    effective_uplift_pct = Column(Float, nullable=False)
    confidence_pct = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    forecast = relationship("Forecast", back_populates="versions")
    user = relationship("User", back_populates="forecast_versions")


class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    product_category = Column(String(50), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    baseline_expected = Column(Float, nullable=False)
    actual_units = Column(Float, nullable=False)
    revenue = Column(Float, default=0.0)
    returns_units = Column(Float, default=0.0)
    stock_available = Column(Float, default=0.0)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    store = relationship("Store", back_populates="sales")
    event = relationship("Event", back_populates="sales")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # Event, PlannerAssessment, Forecast, Store, Sales
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, CORRECT, APPROVE, CANCEL
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    old_value = Column(Text, nullable=True)  # JSON representation
    new_value = Column(Text, nullable=True)  # JSON representation
    reason = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")
