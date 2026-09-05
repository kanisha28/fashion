import json
import datetime
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from backend.models import AuditLog


def log_audit_action(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    user_id: int,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    reason: Optional[str] = None
) -> AuditLog:
    """
    Creates an immutable audit log entry for changes to events, assessments, forecasts, or sales.
    """
    def serialize(val: Any) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, str):
            return val
        try:
            return json.dumps(val, default=str)
        except Exception:
            return str(val)

    log_entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        timestamp=datetime.datetime.utcnow(),
        old_value=serialize(old_value),
        new_value=serialize(new_value),
        reason=reason or f"{action} operation performed"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def format_audit_diff(old_json_str: Optional[str], new_json_str: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """Compares old and new JSON objects and extracts altered field diffs."""
    diffs = {}
    if not old_json_str or not new_json_str:
        return diffs
    try:
        old_dict = json.loads(old_json_str) if isinstance(old_json_str, str) else old_json_str
        new_dict = json.loads(new_json_str) if isinstance(new_json_str, str) else new_json_str
        all_keys = set(old_dict.keys()).union(set(new_dict.keys()))
        for key in all_keys:
            old_val = old_dict.get(key)
            new_val = new_dict.get(key)
            if old_val != new_val:
                diffs[key] = {"old": old_val, "new": new_val}
    except Exception:
        pass
    return diffs
