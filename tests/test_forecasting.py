import pytest
from backend.forecasting import compute_baseline_forecast, generate_event_aware_forecast
from backend.models import Event


def test_baseline_calculation(db_session):
    # Baseline for store 1 and Traditional Wear
    baseline = compute_baseline_forecast(
        db=db_session,
        store_id=1,
        product_category="Traditional Wear",
        target_date="2026-09-20",
        window_days=14
    )
    assert baseline > 0.0
    assert isinstance(baseline, float)


def test_event_aware_forecast_engine(db_session):
    result = generate_event_aware_forecast(
        db=db_session,
        event_id=1,
        store_id=1,
        product_category="Traditional Wear",
        forecast_date="2026-09-20",
        override_planner_uplift=30.0,
        override_confidence=85.0
    )
    assert result["baseline_forecast"] > 0
    assert result["effective_uplift_pct"] > 0
    assert result["event_aware_forecast"] > result["baseline_forecast"]
    assert result["prediction_interval_lower"] < result["event_aware_forecast"]
    assert result["prediction_interval_upper"] > result["event_aware_forecast"]
    assert 0.0 <= result["heuristic_confidence_pct"] <= 100.0


def test_cancelled_event_edge_case(db_session):
    # Set event status to cancelled
    ev = db_session.query(Event).filter(Event.id == 1).first()
    ev.status = "cancelled"
    db_session.commit()

    result = generate_event_aware_forecast(
        db=db_session,
        event_id=1,
        store_id=1,
        product_category="Traditional Wear",
        forecast_date="2026-09-20",
        override_planner_uplift=30.0
    )
    # Effective uplift should be neutralized to 0
    assert result["effective_uplift_pct"] == 0.0
    assert result["event_aware_forecast"] == result["baseline_forecast"]


def test_forecast_api_endpoints(client, planner_auth_header):
    payload = {
        "event_id": 1,
        "store_id": 1,
        "product_category": "Traditional Wear",
        "forecast_date": "2026-09-20",
        "override_planner_uplift": 30.0,
        "override_confidence": 85.0,
        "reason": "Test forecast creation"
    }
    res = client.post("/api/forecast", json=payload, headers=planner_auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["event_aware_forecast"] > 0
    assert data["current_version"] == 1
