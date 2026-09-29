from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

# Metrics definitions
REQUEST_COUNT = Counter(
    "vayunet_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "vayunet_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"]
)
ACTIVE_HOTSPOTS_GAUGE = Gauge(
    "vayunet_active_hotspots_count",
    "Number of active spatial pollution hotspots"
)
ACTIVE_ALERTS_GAUGE = Gauge(
    "vayunet_active_alerts_count",
    "Number of currently open emergency alerts"
)
CORRIDOR_RISK_GAUGE = Gauge(
    "vayunet_corridor_risk_index",
    "Current Corridor Risk Index (0-100)",
    ["corridor_id"]
)


@router.get("/metrics")
async def prometheus_metrics():
    """Exposes Prometheus formatted telemetry metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
