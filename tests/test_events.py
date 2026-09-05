import pytest
from backend.event_engine import haversine_distance_km, calculate_distance_attenuation


def test_haversine_distance():
    # Chennai Central to T Nagar (~6.5 km)
    dist = haversine_distance_km(13.0827, 80.2707, 13.0400, 80.2330)
    assert 5.0 <= dist <= 8.0

    # Same location
    dist_zero = haversine_distance_km(13.0, 80.0, 13.0, 80.0)
    assert dist_zero == 0.0


def test_distance_attenuation():
    # Near event (<3 km) -> full impact 1.0
    assert calculate_distance_attenuation(2.0, 15.0) == 1.0

    # Intermediate distance (9 km with 15 km radius) -> attenuated
    att = calculate_distance_attenuation(9.0, 15.0)
    assert 0.15 < att < 1.0

    # Far away (> 15 km) -> low attenuation factor
    far_att = calculate_distance_attenuation(35.0, 15.0)
    assert far_att < 0.10


def test_list_and_filter_events(client):
    res = client.get("/api/events?city=Chennai")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 1
    assert all(e["city"] == "Chennai" for e in events)


def test_event_detail_with_proximity(client):
    res = client.get("/api/events/1")
    assert res.status_code == 200
    data = res.json()
    assert "nearby_stores" in data
    assert len(data["nearby_stores"]) >= 1
    assert "distance_km" in data["nearby_stores"][0]
