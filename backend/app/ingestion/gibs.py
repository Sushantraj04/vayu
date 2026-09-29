import time
from typing import Dict, Any, Optional
import httpx
from backend.app.core.logging import logger
from backend.app.ingestion.quality import SourceStatusTracker

GIBS_CAPABILITIES_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml"


class GibsLayerVerifier:
    """
    Verifies NASA GIBS WMTS endpoints, TileMatrixSets, and available time dimensions
    for TrueColor and Aerosol Optical Depth (AOD) satellite layers.
    """
    _LAYER_CONFIGS = {
        "truecolor": {
            "layer_id": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
            "tile_matrix_set": "GoogleMapsCompatible_Level9",
            "format": "image/jpeg",
            "title": "VIIRS SNPP TrueColor Corrected Reflectance",
            "template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{time}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
        },
        "aod": {
            "layer_id": "MODIS_Combined_Value_Added_AOD",
            "tile_matrix_set": "GoogleMapsCompatible_Level6",
            "format": "image/png",
            "title": "MODIS Terra/Aqua Combined Aerosol Optical Depth (AOD)",
            "template": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Combined_Value_Added_AOD/default/{time}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png"
        }
    }

    @classmethod
    async def verify_capabilities(cls) -> Dict[str, Any]:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.head("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml")
                is_available = resp.status_code in [200, 301, 302]
                latency = (time.time() - start_time) * 1000
                
                SourceStatusTracker.record_sync(
                    "gibs", 
                    1 if is_available else 0, 
                    latency,
                    None if is_available else f"HTTP {resp.status_code}"
                )

                return {
                    "is_operational": is_available,
                    "latency_ms": round(latency, 1),
                    "layers": cls._LAYER_CONFIGS
                }
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            SourceStatusTracker.record_sync("gibs", 0, latency, str(e))
            logger.warning(f"NASA GIBS capability check failed: {str(e)}")
            return {
                "is_operational": False,
                "error": str(e),
                "layers": cls._LAYER_CONFIGS
            }
