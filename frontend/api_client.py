import os
import requests
from typing import Optional, Dict, Any, List

API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")

# Try importing backend modules for local in-process fallback when running standalone
try:
    from backend.database import SessionLocal, init_db
    from backend.models import User, Store, Event, Forecast, Sales, PlannerAssessment, AuditLog
    from backend.auth import verify_password, create_access_token
    from backend.crud import (
        get_user_by_username, list_stores, list_events, get_event, get_planner_assessment,
        save_planner_assessment, list_forecasts, get_forecast, get_forecast_versions,
        record_sales, list_sales, list_audit_logs, create_or_save_forecast, update_event_status
    )
    from backend.forecasting import generate_event_aware_forecast
    from backend.event_engine import get_nearby_stores, haversine_distance_km
    from backend.routes.analytics import get_metrics_summary, run_backtest_evaluation

    init_db()
    HAS_BACKEND_DIRECT = True
except Exception:
    HAS_BACKEND_DIRECT = False


class APIClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check_health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return HAS_BACKEND_DIRECT

    def login(self, username: str, password: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/auth/login"
            r = requests.post(url, json={"username": username, "password": password}, timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                self.token = data["access_token"]
                self.current_user = data["user"]
                return data
        except Exception:
            pass

        # In-process fallback if backend API is not responding
        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                user = get_user_by_username(db, username)
                if user and verify_password(password, user.hashed_password):
                    token = create_access_token(user.id, user.username, user.role)
                    u_dict = {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role, "city": user.city, "created_at": str(user.created_at)}
                    self.token = token
                    self.current_user = u_dict
                    return {"access_token": token, "token_type": "bearer", "user": u_dict}
            finally:
                db.close()
        raise ValueError("Login failed. Check credentials or backend status.")

    def get_users(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/auth/users"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                users = db.query(User).all()
                return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role, "city": u.city, "created_at": str(u.created_at)} for u in users]
            finally:
                db.close()
        return []

    def get_stores(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/stores"
            params = {}
            if city and city != "All":
                params["city"] = city
            r = requests.get(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                stores = list_stores(db, city=city)
                return [{c.name: getattr(s, c.name) for c in s.__table__.columns} for s in stores]
            finally:
                db.close()
        return []

    def get_events(
        self,
        city: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/events"
            params = {}
            if city and city != "All":
                params["city"] = city
            if event_type and event_type != "All":
                params["event_type"] = event_type
            if status and status != "All":
                params["status"] = status
            if search:
                params["search"] = search
            if store_id:
                params["store_id"] = store_id
            r = requests.get(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                events = list_events(db, city=city, event_type=event_type, status=status, search_query=search)
                out = []
                for ev in events:
                    ev_dict = {c.name: getattr(ev, c.name) for c in ev.__table__.columns}
                    out.append(ev_dict)
                return out
            finally:
                db.close()
        return []

    def get_event_detail(self, event_id: int) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/events/{event_id}"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                event = get_event(db, event_id)
                if event:
                    stores = list_stores(db)
                    nearby = get_nearby_stores(event.latitude, event.longitude, stores)
                    ev_dict = {c.name: getattr(event, c.name) for c in event.__table__.columns}
                    ev_dict["nearby_stores"] = nearby
                    ev_dict["nearest_store"] = nearby[0] if nearby else None
                    return ev_dict
            finally:
                db.close()
        raise ValueError("Failed to fetch event detail")

    def update_event_status(self, event_id: int, new_status: str, reason: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/events/{event_id}/status"
            params = {"new_status": new_status, "reason": reason}
            r = requests.put(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                uid = self.current_user["id"] if self.current_user else 1
                updated = update_event_status(db, event_id, new_status, uid, reason)
                if updated:
                    return {"message": f"Updated to {new_status}", "event_id": event_id, "status": new_status}
            finally:
                db.close()
        raise ValueError("Failed to update event status")

    def get_planner_assessment(self, event_id: int) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/events/{event_id}/assessment"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                ass = get_planner_assessment(db, event_id)
                if ass:
                    return {c.name: getattr(ass, c.name) for c in ass.__table__.columns}
            finally:
                db.close()
        return None

    def save_planner_assessment(self, event_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/events/{event_id}/assessment"
            r = requests.post(url, json=payload, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                uid = self.current_user["id"] if self.current_user else 1
                ass = save_planner_assessment(
                    db=db,
                    event_id=event_id,
                    user_id=uid,
                    affected_store_ids=payload["affected_store_ids"],
                    affected_categories=payload["affected_categories"],
                    expected_uplift_pct=payload["expected_uplift_pct"],
                    confidence_pct=payload["confidence_pct"],
                    demand_duration_days=payload.get("demand_duration_days", 3),
                    planner_notes=payload.get("planner_notes"),
                    reason=payload.get("reason")
                )
                return {c.name: getattr(ass, c.name) for c in ass.__table__.columns}
            finally:
                db.close()
        raise ValueError("Failed to save planner assessment")

    def generate_forecast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/forecast"
            r = requests.post(url, json=payload, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                uid = self.current_user["id"] if self.current_user else 1
                fc_res = generate_event_aware_forecast(
                    db=db,
                    event_id=payload["event_id"],
                    store_id=payload["store_id"],
                    product_category=payload["product_category"],
                    forecast_date=payload["forecast_date"],
                    baseline_window_days=payload.get("baseline_window_days", 14),
                    override_planner_uplift=payload.get("override_planner_uplift"),
                    override_confidence=payload.get("override_confidence")
                )
                saved = create_or_save_forecast(
                    db=db,
                    user_id=uid,
                    forecast_data=fc_res,
                    reason=payload.get("reason", "Generated event-aware forecast")
                )
                return {c.name: getattr(saved, c.name) for c in saved.__table__.columns}
            finally:
                db.close()
        raise ValueError("Failed to generate forecast")

    def get_forecasts(self, store_id: Optional[int] = None, event_id: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/forecasts"
            params = {}
            if store_id:
                params["store_id"] = store_id
            if event_id:
                params["event_id"] = event_id
            r = requests.get(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                fcs = list_forecasts(db, store_id=store_id, event_id=event_id)
                return [{c.name: getattr(f, c.name) for c in f.__table__.columns} for f in fcs]
            finally:
                db.close()
        return []

    def get_forecast(self, forecast_id: int) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/forecast/{forecast_id}"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                fc = get_forecast(db, forecast_id)
                if fc:
                    return {c.name: getattr(fc, c.name) for c in fc.__table__.columns}
            finally:
                db.close()
        raise ValueError("Forecast not found")

    def get_forecast_history(self, forecast_id: int) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/forecast/{forecast_id}/history"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                versions = get_forecast_versions(db, forecast_id)
                return [{c.name: getattr(v, c.name) for c in v.__table__.columns} for v in versions]
            finally:
                db.close()
        return []

    def correct_forecast(self, forecast_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/forecast/{forecast_id}/correction"
            r = requests.post(url, json=payload, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                uid = self.current_user["id"] if self.current_user else 1
                fc = get_forecast(db, forecast_id)
                if fc:
                    fc_res = generate_event_aware_forecast(
                        db=db,
                        event_id=fc.event_id,
                        store_id=fc.store_id,
                        product_category=fc.product_category,
                        forecast_date=fc.forecast_date,
                        override_planner_uplift=payload["corrected_uplift_pct"],
                        override_confidence=payload["corrected_confidence_pct"]
                    )
                    updated = create_or_save_forecast(
                        db=db,
                        user_id=uid,
                        forecast_data=fc_res,
                        reason=f"Planner correction: {payload['reason']}"
                    )
                    return {c.name: getattr(updated, c.name) for c in updated.__table__.columns}
            finally:
                db.close()
        raise ValueError("Failed to submit forecast correction")

    def record_sales(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/sales"
            r = requests.post(url, json=payload, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                uid = self.current_user["id"] if self.current_user else 1
                s = record_sales(db, payload, uid)
                uplift = round(((s.actual_units - s.baseline_expected) / s.baseline_expected) * 100.0, 2) if s.baseline_expected > 0 else None
                s_dict = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                s_dict["observed_uplift_pct"] = uplift
                return s_dict
            finally:
                db.close()
        raise ValueError("Failed to record sales")

    def get_sales(self, store_id: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/sales"
            params = {"limit": limit}
            if store_id:
                params["store_id"] = store_id
            r = requests.get(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                records = list_sales(db, store_id=store_id, limit=limit)
                out = []
                for r in records:
                    uplift = round(((r.actual_units - r.baseline_expected) / r.baseline_expected) * 100.0, 2) if r.baseline_expected > 0 else None
                    item = {c.name: getattr(r, c.name) for c in r.__table__.columns}
                    item["observed_uplift_pct"] = uplift
                    out.append(item)
                return out
            finally:
                db.close()
        return []

    def get_metrics(self) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/metrics"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                return get_metrics_summary(db)
            finally:
                db.close()
        return {}

    def get_backtest(self) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/backtest"
            r = requests.get(url, headers=self._headers(), timeout=3.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                return run_backtest_evaluation(db)
            finally:
                db.close()
        return {}

    def get_audit_trail(self, entity_type: Optional[str] = None, entity_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/audit"
            params = {"limit": limit}
            if entity_type:
                params["entity_type"] = entity_type
            if entity_id:
                params["entity_id"] = entity_id
            r = requests.get(url, params=params, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                logs = list_audit_logs(db, entity_type=entity_type, entity_id=entity_id, limit=limit)
                out = []
                for l in logs:
                    item = {c.name: getattr(l, c.name) for c in l.__table__.columns}
                    item["user_name"] = l.user.full_name if l.user else "System"
                    out.append(item)
                return out
            finally:
                db.close()
        return []

    def get_entity_history(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/audit/{entity_type}/{entity_id}"
            r = requests.get(url, headers=self._headers(), timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        if HAS_BACKEND_DIRECT:
            db = SessionLocal()
            try:
                from backend.audit import format_audit_diff
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
            finally:
                db.close()
        return {"timeline": []}
