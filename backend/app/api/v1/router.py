from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    users,
    health,
    metrics,
    audit,
    corridors,
    stations,
    fires,
    weather,
    hotspots,
    forecasts,
    attribution,
    models,
    reports,
    alerts,
    sources,
    federated
)

api_router = APIRouter()

# Health & Metrics
api_router.include_router(health.router, tags=["Health & Status"])
api_router.include_router(metrics.router, tags=["Observability & Metrics"])

# Security & RBAC
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(users.router, prefix="/users", tags=["User Management & Partner Keys"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Log"])

# Data & Corridor Telemetry (Phase 1)
api_router.include_router(corridors.router, prefix="/corridors", tags=["Corridors"])
api_router.include_router(stations.router, prefix="/stations", tags=["Stations & Telemetry"])
api_router.include_router(fires.router, prefix="/fires", tags=["Active Fires (NASA FIRMS)"])
api_router.include_router(weather.router, prefix="/weather", tags=["Atmospheric Weather (Open-Meteo)"])
api_router.include_router(sources.router, prefix="/sources", tags=["Data Sources Health"])

# Intelligence & Actions (Phase 2)
api_router.include_router(hotspots.router, prefix="/hotspots", tags=["Hotspots (DBSCAN)"])
api_router.include_router(attribution.router, prefix="/attribution", tags=["Kinematic Source Attribution"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts (XGBoost)"])
api_router.include_router(models.router, prefix="/models", tags=["Model Registry & Evaluation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Citizen Reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Emergency Alerts & CAP 1.2"])
api_router.include_router(federated.router, prefix="/federated", tags=["Federated Network"])
