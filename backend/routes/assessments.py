import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import PlannerAssessmentCreate, PlannerAssessmentResponse
from backend.auth import get_current_user, require_role
from backend.crud import get_event, get_planner_assessment, save_planner_assessment

router = APIRouter(prefix="/events", tags=["Planner Assessments"])


@router.get("/{event_id}/assessment", response_model=Optional[PlannerAssessmentResponse])
def get_assessment(event_id: int, db: Session = Depends(get_db)):
    """Retrieve the latest structured planner assessment for an event."""
    assessment = get_planner_assessment(db, event_id)
    return assessment


@router.post("/{event_id}/assessment", response_model=PlannerAssessmentResponse)
def create_or_update_assessment(
    event_id: int,
    assessment_in: PlannerAssessmentCreate,
    current_user: User = Depends(require_role(["admin", "planner"])),
    db: Session = Depends(get_db)
):
    """
    Submit or update human planner knowledge about an event:
    Affected stores, affected categories, expected uplift %, confidence %, and qualitative reason.
    """
    event = get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    assessment = save_planner_assessment(
        db=db,
        event_id=event_id,
        user_id=current_user.id,
        affected_store_ids=assessment_in.affected_store_ids,
        affected_categories=assessment_in.affected_categories,
        expected_uplift_pct=assessment_in.expected_uplift_pct,
        confidence_pct=assessment_in.confidence_pct,
        demand_duration_days=assessment_in.demand_duration_days,
        planner_notes=assessment_in.planner_notes,
        reason=assessment_in.reason
    )
    return assessment
