from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import StoreResponse, StoreCreate
from backend.models import User
from backend.auth import get_current_user, require_role
from backend.crud import list_stores, get_store, create_store

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model=List[StoreResponse])
def get_stores(
    city: Optional[str] = Query(None, description="Filter by city"),
    active_only: bool = Query(True, description="Only active stores"),
    db: Session = Depends(get_db)
):
    """List all retail stores, optionally filtered by city."""
    return list_stores(db, city=city, active_only=active_only)


@router.get("/{store_id}", response_model=StoreResponse)
def get_store_detail(store_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific store."""
    store = get_store(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.post("", response_model=StoreResponse)
def add_store(
    store_in: StoreCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Admin endpoint to create a new retail store."""
    return create_store(
        db=db,
        store_code=store_in.store_code,
        store_name=store_in.store_name,
        city=store_in.city,
        lat=store_in.latitude,
        lon=store_in.longitude,
        store_type=store_in.store_type,
        size_sqft=store_in.size_sqft
    )
