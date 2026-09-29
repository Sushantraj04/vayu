from typing import List, Dict, Any
from fastapi import APIRouter
from backend.app.ingestion.quality import SourceStatusTracker

router = APIRouter()


@router.get("/status", response_model=List[Dict[str, Any]])
async def get_sources_status():
    """
    Returns real-time operational status, latency, sync freshness, and data provenance
    for all real-world data pipelines (OpenAQ, NASA FIRMS, Open-Meteo, NASA GIBS).
    """
    return SourceStatusTracker.get_all_status()
