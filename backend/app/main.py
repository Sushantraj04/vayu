import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import async_engine, Base
from backend.app.api.v1.router import api_router
from backend.app.api.v1.endpoints.metrics import REQUEST_COUNT, REQUEST_LATENCY


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    logger.info("Initializing VAYU-NET database schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("VAYU-NET platform startup complete.")
    yield
    # Shutdown
    logger.info("Shutting down VAYU-NET database connections...")
    await async_engine.dispose()
    logger.info("VAYU-NET platform shutdown complete.")


app = FastAPI(
    title="VAYU-NET API",
    description=(
        "Digital Public Good: Federated, AI-Powered Air Quality and Pollution-Source "
        "Intelligence Platform for the Indo-Gangetic Economic Corridor (Punjab-Haryana-Delhi-UP)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Configure to strict domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_and_telemetry_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    duration = time.time() - start_time
    duration_ms = round(duration * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"

    # Prometheus metric update
    endpoint = request.url.path
    status_code = str(response.status_code)
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    # Structured JSON log for non-metrics requests
    if "/metrics" not in endpoint:
        logger.info(
            f"{request.method} {endpoint} {response.status_code} in {duration_ms}ms",
            extra={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else "unknown",
                "duration_ms": duration_ms
            }
        )

    return response


# Mount API V1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": "VAYU-NET",
        "description": "Federated AI Air Quality & Pollution-Source Intelligence Platform",
        "corridor": "Indo-Gangetic & Delhi-NCR Belts",
        "brics_track": "Clean Air & Climate Resilience (Sustainability)",
        "dpg_status": "Digital Public Good Standard Compliant",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }
