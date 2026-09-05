import os
import sys
import time
import subprocess
import signal

# Ensure root directory is on python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)


def initialize_environment():
    """Ensures database is initialized and seeded with representative demo records."""
    print("==================================================================")
    print("👗 LOCAL EVENT INTELLIGENCE & DEMAND FORECASTING PLATFORM")
    print("==================================================================")
    print("[1/3] Checking and initializing database & seed data...")
    from data.seed_data import seed_database
    seed_database()

    print("[2/3] Checking Scikit-Learn Model C...")
    model_path = os.path.join(BASE_DIR, "models", "saved_models", "rf_event_model.joblib")
    if not os.path.exists(model_path):
        print("Training baseline RandomForest predictive model...")
        import joblib
        import math
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        from backend.database import SessionLocal
        from backend.models import Sales, Event

        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        db = SessionLocal()
        sales = db.query(Sales).all()
        X, y = [], []
        for s in sales:
            base = s.baseline_expected
            act = s.actual_units
            attendance = 10000
            dist = 5.0
            ev_type_len = 8
            cat_len = len(s.product_category)
            planner_uplift = 25.0
            planner_conf = 80.0
            hist_uplift = 24.0
            if s.event_id:
                ev = db.query(Event).filter(Event.id == s.event_id).first()
                if ev:
                    attendance = max(100, ev.expected_attendance)
                    ev_type_len = len(ev.event_type)
            X.append([base, planner_uplift, planner_conf, hist_uplift, dist, math.log1p(attendance), ev_type_len, cat_len])
            y.append(act)
        db.close()
        rf = RandomForestRegressor(n_estimators=40, random_state=42)
        rf.fit(np.array(X), np.array(y))
        joblib.dump(rf, model_path)
        print("RandomForest model saved.")
    else:
        print("RandomForest model ready.")


def launch_services():
    """Starts FastAPI backend and Streamlit frontend concurrently."""
    print("[3/3] Starting Backend API and Streamlit UI services...")

    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR

    # Launch FastAPI
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    print(f"-> Launching FastAPI backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(backend_cmd, env=env)

    # Allow backend 2 seconds to bind port
    time.sleep(2)

    # Launch Streamlit
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(BASE_DIR, "frontend", "app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    print(f"-> Launching Streamlit frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(frontend_cmd, env=env)

    print("\n" + "=" * 66)
    print("🚀 PLATFORM SERVICES RUNNING SUCCESSFULLY!")
    print("=" * 66)
    print("📍 Frontend Web UI:        http://localhost:8501")
    print("📡 Backend REST API:       http://127.0.0.1:8000/api")
    print("📖 Interactive Swagger:    http://127.0.0.1:8000/docs")
    print("\n🔑 DEMO CREDENTIALS:")
    print("  • Admin:    username: admin    | password: admin123")
    print("  • Planner:  username: planner1 | password: planner123")
    print("  • Viewer:   username: viewer   | password: viewer123")
    print("=" * 66)
    print("Press Ctrl+C in this terminal to stop both services gracefully.\n")

    try:
        while True:
            time.sleep(1)
            # Check if any process terminated unexpectedly
            if backend_proc.poll() is not None:
                print(f"Backend process terminated with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"Frontend process terminated with code {frontend_proc.returncode}")
                break
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for proc, name in [(backend_proc, "Backend"), (frontend_proc, "Frontend")]:
            if proc.poll() is None:
                print(f"Terminating {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("All services stopped.")


if __name__ == "__main__":
    initialize_environment()
    launch_services()
