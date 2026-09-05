from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import AuditLogResponse
from backend.crud import list_audit_logs
from backend.audit import format_audit_diff

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit logs across system actions."""
    logs = list_audit_logs(db, entity_type=entity_type, entity_id=entity_id, limit=limit)
    out = []
    for l in logs:
        item = {c.name: getattr(l, c.name) for c in l.__table__.columns}
        item["user_name"] = l.user.full_name if l.user else "System"
        out.append(item)
    return out


@router.get("/{entity_type}/{entity_id}")
def get_entity_history(entity_type: str, entity_id: int, db: Session = Depends(get_db)):
    """Retrieve chronologically ordered history and field diffs for a specific entity."""
    logs = list_audit_logs(db, entity_type=entity_type, entity_id=entity_id, limit=100)
    timeline = []
    for l in reversed(logs):
        diffs = format_audit_diff(l.old_value, l.new_value)
        timeline.append({
            "id": l.id,
            "action": l.action,
            "user_id": l.user_id,
            "user_name": l.user.full_name if l.user else "System",
            "timestamp": l.timestamp.isoformat(),
            "reason": l.reason,
            "diffs": diffs,
            "old_value": l.old_value,
            "new_value": l.new_value
        })
    return {"entity_type": entity_type, "entity_id": entity_id, "timeline": timeline}
