import math
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from backend.models import Event, Store, Sales


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points on Earth in kilometers."""
    r = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


def calculate_distance_attenuation(distance_km: float, impact_radius_km: float) -> float:
    """
    Calculates geographic uplift attenuation factor alpha(d).
    Within 3 km: full impact (1.0).
    Between 3 km and impact_radius: linear decay from 1.0 down to 0.15.
    Beyond impact_radius: exponential falloff towards 0.
    """
    if distance_km <= 3.0:
        return 1.0
    if distance_km <= impact_radius_km:
        ratio = (distance_km - 3.0) / max(1.0, (impact_radius_km - 3.0))
        return max(0.15, round(1.0 - (0.85 * ratio), 3))
    # Distant falloff
    excess = distance_km - impact_radius_km
    return max(0.02, round(0.15 * math.exp(-excess / 10.0), 3))


def get_nearby_stores(
    event_lat: float,
    event_lon: float,
    stores: List[Store],
    max_radius_km: Optional[float] = None
) -> List[Dict]:
    """Returns stores sorted by proximity with calculated distance."""
    results = []
    for store in stores:
        dist = haversine_distance_km(event_lat, event_lon, store.latitude, store.longitude)
        if max_radius_km is None or dist <= max_radius_km:
            results.append({
                "store_id": store.id,
                "store_code": store.store_code,
                "store_name": store.store_name,
                "city": store.city,
                "distance_km": dist,
                "store_type": store.store_type
            })
    results.sort(key=lambda x: x["distance_km"])
    return results


def get_historical_similar_event_uplift(
    db: Session,
    event_type: str,
    product_category: str,
    store_id: Optional[int] = None
) -> Dict[str, float]:
    """
    Finds past sales records during similar events to compute empirical uplift benchmark.
    Returns average uplift %, sample count, and standard deviation.
    """
    # Prior benchmarks by event type and category (domain heuristics when data is cold)
    PRIOR_BENCHMARKS = {
        ("Festival", "Traditional Wear"): 26.5,
        ("Festival", "Women's Wear"): 22.0,
        ("Festival", "Accessories"): 18.0,
        ("Concert", "Casual Wear"): 20.0,
        ("Concert", "Footwear"): 14.0,
        ("Sports Event", "Casual Wear"): 19.0,
        ("Sports Event", "Footwear"): 16.5,
        ("College Event", "Casual Wear"): 21.0,
        ("College Event", "Accessories"): 15.0,
        ("Exhibition", "Women's Wear"): 17.5,
        ("Shopping Event", "Women's Wear"): 25.0,
        ("Shopping Event", "Traditional Wear"): 24.0,
        ("Religious/Cultural Event", "Traditional Wear"): 28.0,
    }

    # Query historical sales where an event was associated
    query = db.query(Sales).join(Event, Sales.event_id == Event.id).filter(
        Event.event_type == event_type,
        Sales.product_category == product_category,
        Sales.baseline_expected > 0
    )
    if store_id:
        query = query.filter(Sales.store_id == store_id)

    records = query.all()

    if not records or len(records) < 3:
        # Fallback to domain prior with slight category generalisation
        prior = PRIOR_BENCHMARKS.get((event_type, product_category), 15.0)
        return {
            "historical_uplift_pct": prior,
            "sample_count": len(records),
            "is_prior_fallback": True,
            "std_dev_pct": 6.5
        }

    uplifts = [((r.actual_units - r.baseline_expected) / r.baseline_expected) * 100.0 for r in records]
    avg_uplift = sum(uplifts) / len(uplifts)
    variance = sum((u - avg_uplift) ** 2 for u in uplifts) / max(1, len(uplifts) - 1)
    std_dev = math.sqrt(variance)

    return {
        "historical_uplift_pct": round(avg_uplift, 2),
        "sample_count": len(records),
        "is_prior_fallback": False,
        "std_dev_pct": round(std_dev, 2)
    }


def detect_overlapping_events(
    db: Session,
    city: str,
    start_date: str,
    end_date: str,
    current_event_id: Optional[int] = None
) -> List[Dict]:
    """Finds other events occurring in the same city during overlapping date range."""
    events = db.query(Event).filter(
        Event.city == city,
        Event.status.in_(["active", "approved"]),
        Event.start_date <= end_date,
        Event.end_date >= start_date
    )
    if current_event_id:
        events = events.filter(Event.id != current_event_id)

    overlapping = []
    for ev in events.all():
        overlapping.append({
            "id": ev.id,
            "name": ev.name,
            "event_type": ev.event_type,
            "start_date": ev.start_date,
            "end_date": ev.end_date,
            "expected_attendance": ev.expected_attendance
        })
    return overlapping
