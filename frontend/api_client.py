import os
import requests
from typing import Optional, Dict, Any, List

API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")


class APIClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check_health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        r = requests.post(url, json={"username": username, "password": password}, timeout=5.0)
        if r.status_code == 200:
            data = r.json()
            self.token = data["access_token"]
            return data
        raise ValueError(r.json().get("detail", "Login failed"))

    def get_users(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/auth/users"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_stores(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/stores"
        params = {}
        if city and city != "All":
            params["city"] = city
        r = requests.get(url, params=params, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_events(
        self,
        city: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
        r = requests.get(url, params=params, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_event_detail(self, event_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/events/{event_id}"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError("Failed to fetch event detail")

    def update_event_status(self, event_id: int, new_status: str, reason: str) -> Dict[str, Any]:
        url = f"{self.base_url}/events/{event_id}/status"
        params = {"new_status": new_status, "reason": reason}
        r = requests.put(url, params=params, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError(r.json().get("detail", "Failed to update event status"))

    def get_planner_assessment(self, event_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/events/{event_id}/assessment"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else None

    def save_planner_assessment(self, event_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/events/{event_id}/assessment"
        r = requests.post(url, json=payload, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError(r.json().get("detail", "Failed to save planner assessment"))

    def generate_forecast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/forecast"
        r = requests.post(url, json=payload, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError(r.json().get("detail", "Failed to generate forecast"))

    def get_forecasts(self, store_id: Optional[int] = None, event_id: Optional[int] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/forecasts"
        params = {}
        if store_id:
            params["store_id"] = store_id
        if event_id:
            params["event_id"] = event_id
        r = requests.get(url, params=params, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_forecast(self, forecast_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/forecast/{forecast_id}"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError("Forecast not found")

    def get_forecast_history(self, forecast_id: int) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/forecast/{forecast_id}/history"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def correct_forecast(self, forecast_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/forecast/{forecast_id}/correction"
        r = requests.post(url, json=payload, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError(r.json().get("detail", "Failed to submit forecast correction"))

    def record_sales(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/sales"
        r = requests.post(url, json=payload, headers=self._headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
        raise ValueError(r.json().get("detail", "Failed to record sales"))

    def get_sales(self, store_id: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/sales"
        params = {"limit": limit}
        if store_id:
            params["store_id"] = store_id
        r = requests.get(url, params=params, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_metrics(self) -> Dict[str, Any]:
        url = f"{self.base_url}/metrics"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else {}

    def get_backtest(self) -> Dict[str, Any]:
        url = f"{self.base_url}/backtest"
        r = requests.get(url, headers=self._headers(), timeout=10.0)
        return r.json() if r.status_code == 200 else {}

    def get_audit_trail(self, entity_type: Optional[str] = None, entity_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/audit"
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id
        r = requests.get(url, params=params, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else []

    def get_entity_history(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/audit/{entity_type}/{entity_id}"
        r = requests.get(url, headers=self._headers(), timeout=5.0)
        return r.json() if r.status_code == 200 else {"timeline": []}
