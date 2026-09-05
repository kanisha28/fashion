from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import EventResponse, EventCreate, EventUpdate
from backend.auth import get_current_user, require_role
from backend.crud import list_events, get_event, create_event, update_event_status, list_stores
from backend.event_engine import get_nearby_stores, haversine_distance_km

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse])
def get_events(
    city: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    store_id: Optional[int] = Query(None, description="Compute distance to specific store"),
    db: Session = Depends(get_db)
):
    """List events matching optional filters."""
    events = list_events(db, city=city, event_type=event_type, status=status, search_query=search)

    target_store = None
    if store_id:
        from backend.crud import get_store
        target_store = get_store(db, store_id)

    response_list = []
    for ev in events:
        ev_dict = {c.name: getattr(ev, c.name) for c in ev.__table__.columns}
        if target_store:
            ev_dict["distance_to_store_km"] = haversine_distance_km(
                ev.latitude, ev.longitude, target_store.latitude, target_store.longitude
            )
        else:
            ev_dict["distance_to_store_km"] = None
        response_list.append(ev_dict)

    return response_list


@router.get("/{event_id}")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """Retrieve full event detail with nearby stores ranked by distance."""
    event = get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    stores = list_stores(db)
    nearby_stores = get_nearby_stores(event.latitude, event.longitude, stores)

    ev_dict = {c.name: getattr(event, c.name) for c in event.__table__.columns}
    ev_dict["nearby_stores"] = nearby_stores
    ev_dict["nearest_store"] = nearby_stores[0] if nearby_stores else None
    return ev_dict


@router.post("", response_model=EventResponse)
def add_event(
    event_in: EventCreate,
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """Create a new event record (requires Planner or Admin)."""
    return create_event(db, event_in.model_dump(), user_id=current_user.id)


@router.put("/{event_id}/status")
def change_event_status(
    event_id: int,
    new_status: str = Query(..., description="active, pending, approved, completed, cancelled"),
    reason: str = Query("Status change requested"),
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """Update event status (e.g. approve or mark cancelled for failure case demonstration)."""
    updated = update_event_status(db, event_id, new_status, current_user.id, reason)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": f"Event status updated to {new_status}", "event_id": event_id, "status": new_status}
