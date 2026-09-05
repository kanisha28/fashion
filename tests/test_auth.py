import pytest
from backend.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    raw_pass = "secure_password_123"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_token_lifecycle():
    token = create_access_token(user_id=42, username="planner_test", role="planner")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["user_id"] == 42
    assert payload["username"] == "planner_test"
    assert payload["role"] == "planner"

    # Corrupt token
    corrupted = token + "bad"
    assert decode_access_token(corrupted) is None


def test_login_api_success(client):
    response = client.post("/api/auth/login", json={"username": "test_planner", "password": "planner123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "test_planner"
    assert data["user"]["role"] == "planner"


def test_login_api_failure(client):
    response = client.post("/api/auth/login", json={"username": "test_planner", "password": "wrongpassword"})
    assert response.status_code == 401


def test_role_permission_viewer_restriction(client, viewer_auth_header):
    # Viewer should be blocked (403) from creating events
    new_event = {
        "name": "Unauthorized Event",
        "event_type": "Festival",
        "start_date": "2026-10-01",
        "end_date": "2026-10-05",
        "latitude": 13.0,
        "longitude": 80.0,
        "location_name": "Park",
        "city": "Chennai",
        "expected_attendance": 5000
    }
    res = client.post("/api/events", json=new_event, headers=viewer_auth_header)
    assert res.status_code == 403
