import json
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models import (
    User, Store, Product, Event, PlannerAssessment, Forecast, ForecastVersion, Sales, AuditLog
)
from backend.audit import log_audit_action


# --- USERS ---
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, hashed_pw: str, full_name: str, role: str = "planner", city: Optional[str] = None) -> User:
    user = User(
        username=username,
        hashed_password=hashed_pw,
        full_name=full_name,
        role=role,
        city=city
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> List[User]:
    return db.query(User).all()


# --- STORES ---
def list_stores(db: Session, city: Optional[str] = None, active_only: bool = True) -> List[Store]:
    q = db.query(Store)
    if active_only:
        q = q.filter(Store.active == True)
    if city and city != "All":
        q = q.filter(Store.city == city)
    return q.all()


def get_store(db: Session, store_id: int) -> Optional[Store]:
    return db.query(Store).filter(Store.id == store_id).first()


def create_store(db: Session, store_code: str, store_name: str, city: str, lat: float, lon: float, store_type: str = "High Street", size_sqft: int = 5000) -> Store:
    store = Store(
        store_code=store_code,
        store_name=store_name,
        city=city,
        latitude=lat,
        longitude=lon,
        store_type=store_type,
        size_sqft=size_sqft
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


# --- PRODUCTS ---
def list_products(db: Session) -> List[Product]:
    return db.query(Product).all()


# --- EVENTS ---
def list_events(
    db: Session,
    city: Optional[str] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Event]:
    q = db.query(Event)
    if city and city != "All":
        q = q.filter(Event.city == city)
    if event_type and event_type != "All":
        q = q.filter(Event.event_type == event_type)
    if status and status != "All":
        q = q.filter(Event.status == status)
    if search_query:
        q = q.filter(Event.name.ilike(f"%{search_query}%"))
    return q.order_by(Event.start_date.asc()).all()


def get_event(db: Session, event_id: int) -> Optional[Event]:
    return db.query(Event).filter(Event.id == event_id).first()


def create_event(db: Session, event_data: Dict[str, Any], user_id: int) -> Event:
    event = Event(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)

    log_audit_action(
        db=db,
        entity_type="Event",
        entity_id=event.id,
        action="CREATE",
        user_id=user_id,
        old_value=None,
        new_value=event_data,
        reason=f"Created new event: {event.name}"
    )
    return event


def update_event_status(db: Session, event_id: int, new_status: str, user_id: int, reason: str) -> Optional[Event]:
    event = get_event(db, event_id)
    if not event:
        return None
    old_status = event.status
    event.status = new_status
    event.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(event)

    log_audit_action(
        db=db,
        entity_type="Event",
        entity_id=event.id,
        action="UPDATE_STATUS",
        user_id=user_id,
        old_value={"status": old_status},
        new_value={"status": new_status},
        reason=reason
    )
    return event


# --- PLANNER ASSESSMENTS ---
def get_planner_assessment(db: Session, event_id: int) -> Optional[PlannerAssessment]:
    return db.query(PlannerAssessment).filter(
        PlannerAssessment.event_id == event_id
    ).order_by(desc(PlannerAssessment.updated_at)).first()


def save_planner_assessment(
    db: Session,
    event_id: int,
    user_id: int,
    affected_store_ids: List[int],
    affected_categories: List[str],
    expected_uplift_pct: float,
    confidence_pct: float,
    demand_duration_days: int = 3,
    planner_notes: Optional[str] = None,
    reason: Optional[str] = None
) -> PlannerAssessment:
    existing = get_planner_assessment(db, event_id)
    new_data = {
        "affected_store_ids": json.dumps(affected_store_ids),
        "affected_categories": json.dumps(affected_categories),
        "expected_uplift_pct": expected_uplift_pct,
        "confidence_pct": confidence_pct,
        "demand_duration_days": demand_duration_days,
        "planner_notes": planner_notes,
        "reason": reason
    }

    if existing:
        old_data = {
            "affected_store_ids": existing.affected_store_ids,
            "affected_categories": existing.affected_categories,
            "expected_uplift_pct": existing.expected_uplift_pct,
            "confidence_pct": existing.confidence_pct,
            "demand_duration_days": existing.demand_duration_days,
            "planner_notes": existing.planner_notes,
            "reason": existing.reason
        }
        for k, v in new_data.items():
            setattr(existing, k, v)
        existing.user_id = user_id
        existing.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)

        log_audit_action(
            db=db,
            entity_type="PlannerAssessment",
            entity_id=existing.id,
            action="UPDATE",
            user_id=user_id,
            old_value=old_data,
            new_value=new_data,
            reason=reason or "Planner updated event assessment"
        )
        return existing
    else:
        assessment = PlannerAssessment(
            event_id=event_id,
            user_id=user_id,
            **new_data
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        log_audit_action(
            db=db,
            entity_type="PlannerAssessment",
            entity_id=assessment.id,
            action="CREATE",
            user_id=user_id,
            old_value=None,
            new_value=new_data,
            reason=reason or "Initial planner event assessment submitted"
        )
        return assessment


# --- FORECASTS & VERSIONING ---
def create_or_save_forecast(
    db: Session,
    user_id: int,
    forecast_data: Dict[str, Any],
    reason: str = "Initial event-aware forecast generated"
) -> Forecast:
    # Check if a forecast record for this event, store, and category already exists
    existing = db.query(Forecast).filter(
        Forecast.event_id == forecast_data["event_id"],
        Forecast.store_id == forecast_data["store_id"],
        Forecast.product_category == forecast_data["product_category"]
    ).first()

    if existing:
        # Increment version and update
        old_dict = {
            "version": existing.current_version,
            "event_aware_forecast": existing.event_aware_forecast,
            "effective_uplift_pct": existing.effective_uplift_pct,
            "confidence_pct": existing.heuristic_confidence_pct
        }
        existing.current_version += 1
        for k, v in forecast_data.items():
            if hasattr(existing, k) and k not in ["id", "created_at"]:
                setattr(existing, k, v)
        existing.updated_at = datetime.datetime.utcnow()

        version_record = ForecastVersion(
            forecast_id=existing.id,
            version_number=existing.current_version,
            user_id=user_id,
            baseline_forecast=existing.baseline_forecast,
            event_aware_forecast=existing.event_aware_forecast,
            effective_uplift_pct=existing.effective_uplift_pct,
            confidence_pct=existing.heuristic_confidence_pct,
            reason=reason
        )
        db.add(version_record)
        db.commit()
        db.refresh(existing)

        log_audit_action(
            db=db,
            entity_type="Forecast",
            entity_id=existing.id,
            action="CORRECT",
            user_id=user_id,
            old_value=old_dict,
            new_value={
                "version": existing.current_version,
                "event_aware_forecast": existing.event_aware_forecast,
                "effective_uplift_pct": existing.effective_uplift_pct,
                "confidence_pct": existing.heuristic_confidence_pct
            },
            reason=reason
        )
        return existing
    else:
        forecast = Forecast(
            event_id=forecast_data["event_id"],
            store_id=forecast_data["store_id"],
            product_category=forecast_data["product_category"],
            forecast_date=forecast_data["forecast_date"],
            baseline_forecast=forecast_data["baseline_forecast"],
            planner_expected_uplift_pct=forecast_data["planner_expected_uplift_pct"],
            historical_similar_event_uplift_pct=forecast_data.get("historical_similar_event_uplift_pct", 0.0),
            effective_uplift_pct=forecast_data["effective_uplift_pct"],
            event_aware_forecast=forecast_data["event_aware_forecast"],
            ml_forecast=forecast_data.get("ml_forecast"),
            prediction_interval_lower=forecast_data["prediction_interval_lower"],
            prediction_interval_upper=forecast_data["prediction_interval_upper"],
            heuristic_confidence_pct=forecast_data["heuristic_confidence_pct"],
            current_version=1,
            status="active"
        )
        db.add(forecast)
        db.commit()
        db.refresh(forecast)

        # Create version 1 record
        v1 = ForecastVersion(
            forecast_id=forecast.id,
            version_number=1,
            user_id=user_id,
            baseline_forecast=forecast.baseline_forecast,
            event_aware_forecast=forecast.event_aware_forecast,
            effective_uplift_pct=forecast.effective_uplift_pct,
            confidence_pct=forecast.heuristic_confidence_pct,
            reason=reason
        )
        db.add(v1)
        db.commit()
        db.refresh(forecast)

        log_audit_action(
            db=db,
            entity_type="Forecast",
            entity_id=forecast.id,
            action="CREATE",
            user_id=user_id,
            old_value=None,
            new_value={"version": 1, "forecast": forecast.event_aware_forecast},
            reason=reason
        )
        return forecast


def get_forecast(db: Session, forecast_id: int) -> Optional[Forecast]:
    return db.query(Forecast).filter(Forecast.id == forecast_id).first()


def list_forecasts(db: Session, store_id: Optional[int] = None, event_id: Optional[int] = None) -> List[Forecast]:
    q = db.query(Forecast)
    if store_id:
        q = q.filter(Forecast.store_id == store_id)
    if event_id:
        q = q.filter(Forecast.event_id == event_id)
    return q.order_by(desc(Forecast.updated_at)).all()


def get_forecast_versions(db: Session, forecast_id: int) -> List[ForecastVersion]:
    return db.query(ForecastVersion).filter(
        ForecastVersion.forecast_id == forecast_id
    ).order_by(ForecastVersion.version_number.asc()).all()


# --- SALES ---
def record_sales(db: Session, sales_data: Dict[str, Any], user_id: int) -> Sales:
    sales = Sales(**sales_data)
    db.add(sales)
    db.commit()
    db.refresh(sales)

    log_audit_action(
        db=db,
        entity_type="Sales",
        entity_id=sales.id,
        action="RECORD_ACTUALS",
        user_id=user_id,
        old_value=None,
        new_value={"actual_units": sales.actual_units, "baseline": sales.baseline_expected},
        reason=f"Recorded actual sales for date {sales.date}"
    )
    return sales


def list_sales(db: Session, store_id: Optional[int] = None, limit: int = 500) -> List[Sales]:
    q = db.query(Sales)
    if store_id:
        q = q.filter(Sales.store_id == store_id)
    return q.order_by(desc(Sales.date)).limit(limit).all()


# --- AUDIT LOGS ---
def list_audit_logs(db: Session, entity_type: Optional[str] = None, entity_id: Optional[int] = None, limit: int = 100) -> List[AuditLog]:
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.order_by(desc(AuditLog.timestamp)).limit(limit).all()
