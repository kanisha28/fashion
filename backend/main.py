import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import (
    auth,
    stores,
    events,
    assessments,
    forecasts,
    sales,
    analytics,
    audit
)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database schema is created on application startup."""
    init_db()
    yield


app = FastAPI(
    title="Fashion Local Event Intelligence & Demand Forecasting API",
    description=(
        "Production-ready backend capturing local human knowledge regarding cultural/sports/shopping events, "
        "generating event-aware demand forecasts, tracking versioned immutable audit histories, "
        "and evaluating forecast accuracy attribution against simple baselines."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for local Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route modules
app.include_router(auth.router, prefix="/api")
app.include_router(stores.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(forecasts.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint for orchestration."""
    return {"status": "healthy", "service": "Fashion Event Forecasting Backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
