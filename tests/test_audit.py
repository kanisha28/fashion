import pytest
from backend.models import Forecast
from backend.audit import log_audit_action, format_audit_diff


def test_audit_log_creation(db_session):
    log = log_audit_action(
        db=db_session,
        entity_type="Event",
        entity_id=1,
        action="UPDATE",
        user_id=1,
        old_value={"status": "pending"},
        new_value={"status": "approved"},
        reason="Approved by store director"
    )
    assert log.id is not None
    assert log.action == "UPDATE"
    assert "pending" in log.old_value
    assert "approved" in log.new_value


def test_audit_diff_formatting():
    old_json = '{"uplift": 30.0, "status": "active"}'
    new_json = '{"uplift": 25.0, "status": "active"}'
    diffs = format_audit_diff(old_json, new_json)

    assert "uplift" in diffs
    assert diffs["uplift"]["old"] == 30.0
    assert diffs["uplift"]["new"] == 25.0
    assert "status" not in diffs  # Unchanged


def test_correction_workflow_versioning(client, planner_auth_header):
    # 1. Create initial forecast
    payload = {
        "event_id": 1,
        "store_id": 1,
        "product_category": "Traditional Wear",
        "forecast_date": "2026-09-20",
        "override_planner_uplift": 30.0,
        "override_confidence": 85.0,
        "reason": "Initial forecast"
    }
    create_res = client.post("/api/forecast", json=payload, headers=planner_auth_header)
    assert create_res.status_code == 200
    forecast_id = create_res.json()["id"]
    assert create_res.json()["current_version"] == 1

    # 2. Submit correction
    corr_payload = {
        "corrected_uplift_pct": 22.0,
        "corrected_confidence_pct": 80.0,
        "reason": "Reduced attendance expectation after transport strike warning"
    }
    corr_res = client.post(f"/api/forecast/{forecast_id}/correction", json=corr_payload, headers=planner_auth_header)
    assert corr_res.status_code == 200
    assert corr_res.json()["current_version"] == 2

    # 3. Fetch history and verify both versions exist
    hist_res = client.get(f"/api/forecast/{forecast_id}/history", headers=planner_auth_header)
    assert hist_res.status_code == 200
    versions = hist_res.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 1
    assert versions[1]["version_number"] == 2
    assert "transport strike" in versions[1]["reason"]
