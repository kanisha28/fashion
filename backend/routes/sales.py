from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Sales
from backend.schemas import SalesCreate, SalesResponse
from backend.auth import get_current_user, require_role
from backend.crud import record_sales, list_sales

router = APIRouter(prefix="/sales", tags=["Sales Actuals"])


@router.post("", response_model=SalesResponse)
def add_sales_record(
    sales_in: SalesCreate,
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """Record actual sales after an event has concluded."""
    saved = record_sales(db, sales_in.model_dump(), user_id=current_user.id)
    observed_uplift = None
    if saved.baseline_expected > 0:
        observed_uplift = round(((saved.actual_units - saved.baseline_expected) / saved.baseline_expected) * 100.0, 2)

    resp = {c.name: getattr(saved, c.name) for c in saved.__table__.columns}
    resp["observed_uplift_pct"] = observed_uplift
    return resp


@router.get("", response_model=List[SalesResponse])
def get_sales_records(
    store_id: Optional[int] = Query(None),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db)
):
    """Retrieve historical sales records with calculated observed uplift."""
    records = list_sales(db, store_id=store_id, limit=limit)
    out = []
    for r in records:
        uplift = None
        if r.baseline_expected > 0:
            uplift = round(((r.actual_units - r.baseline_expected) / r.baseline_expected) * 100.0, 2)
        item = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        item["observed_uplift_pct"] = uplift
        out.append(item)
    return out
