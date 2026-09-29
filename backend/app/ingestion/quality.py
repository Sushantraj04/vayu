import math
import statistics
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List, Dict, Any


class PhysicalRangeValidator:
    """Enforces physical reality constraints on sensor telemetry."""
    RANGES = {
        "pm25": (0.0, 1500.0),       # ug/m3
        "pm10": (0.0, 2500.0),       # ug/m3
        "no2": (0.0, 1000.0),        # ug/m3
        "so2": (0.0, 1500.0),        # ug/m3
        "o3": (0.0, 1000.0),         # ug/m3
        "temperature": (-20.0, 60.0),# Celsius
        "humidity": (0.0, 100.0),    # %
        "wind_speed": (0.0, 150.0),  # km/h
        "wind_direction": (0.0, 360.0), # degrees
        "blh": (10.0, 5000.0),       # Boundary layer height in meters
    }

    @classmethod
    def validate(cls, parameter: str, value: Optional[float]) -> Tuple[bool, Optional[str]]:
        if value is None:
            return False, "Null value"
        if math.isnan(value) or math.isinf(value):
            return False, "NaN or infinite value"
        
        param_clean = parameter.lower().replace(".", "")
        if param_clean in cls.RANGES:
            min_v, max_v = cls.RANGES[param_clean]
            if not (min_v <= value <= max_v):
                return False, f"Out of physical bounds: {value} not in [{min_v}, {max_v}]"
        return True, None


def calculate_cpcb_naqi(pm25: Optional[float]) -> Tuple[Optional[int], Optional[str]]:
    """
    Computes India National Air Quality Index (NAQI) for PM2.5 per CPCB 2014 guidelines.
    Returns (aqi_value, aqi_category)
    """
    if pm25 is None or pm25 < 0.0 or math.isnan(pm25):
        return None, "Insufficient Data"

    # Breakpoints: (min_c, max_c, min_i, max_i, category)
    breakpoints = [
        (0.0, 30.0, 0, 50, "Good"),
        (31.0, 60.0, 51, 100, "Satisfactory"),
        (61.0, 90.0, 101, 200, "Moderate"),
        (91.0, 120.0, 201, 300, "Poor"),
        (121.0, 250.0, 301, 400, "Very Poor"),
        (251.0, 500.0, 401, 500, "Severe"),
    ]

    for min_c, max_c, min_i, max_i, cat in breakpoints:
        if pm25 <= max_c:
            factor = (max_i - min_i) / (max_c - min_c)
            aqi = round(min_i + factor * (pm25 - min_c))
            return max(0, min(500, aqi)), cat

    # Above 500 ug/m3 is off-scale Severe
    return 500, "Severe"


def check_sensor_staleness(
    recent_readings: List[float], 
    last_sync: Optional[datetime],
    max_lag_minutes: int = 120
) -> Tuple[bool, str]:
    """
    Flags stale sensors based on:
    1. Timestamp latency > max_lag_minutes (default 2 hours)
    2. Zero variance (flatline) across 6 or more consecutive readings
    """
    now = datetime.now(timezone.utc)
    if not last_sync:
        return True, "No sync timestamp recorded"

    if (now - last_sync) > timedelta(minutes=max_lag_minutes):
        return True, f"Telemetry lag exceeds {max_lag_minutes} minutes"

    if len(recent_readings) >= 6:
        # Variance of sample readings
        variance = statistics.pvariance(recent_readings)
        if variance == 0.0:
            return True, "Zero-variance flatline detected over 6 consecutive intervals"

    return False, "Active and responsive"


class SourceStatusTracker:
    """Tracks live availability, sync freshness, and latency across external APIs."""
    _STATUS_STORE: Dict[str, Dict[str, Any]] = {
        "openaq": {
            "name": "OpenAQ Ground Telemetry",
            "type": "MEASURED",
            "status": "LIVE",
            "last_sync": datetime.now(timezone.utc),
            "latency_ms": 280,
            "record_count_24h": 0,
            "error_message": None,
        },
        "firms": {
            "name": "NASA FIRMS VIIRS Active Fires",
            "type": "MEASURED",
            "status": "LIVE",
            "last_sync": datetime.now(timezone.utc),
            "latency_ms": 640,
            "record_count_24h": 0,
            "error_message": None,
        },
        "openmeteo": {
            "name": "Open-Meteo Meteorology & CAMS Fallback",
            "type": "MODELLED",
            "status": "LIVE",
            "last_sync": datetime.now(timezone.utc),
            "latency_ms": 190,
            "record_count_24h": 0,
            "error_message": None,
        },
        "gibs": {
            "name": "NASA GIBS Tile Services",
            "type": "SATELLITE_TILES",
            "status": "LIVE",
            "last_sync": datetime.now(timezone.utc),
            "latency_ms": 320,
            "record_count_24h": 0,
            "error_message": None,
        },
    }

    @classmethod
    def record_sync(cls, source_id: str, count: int, latency_ms: float, error: Optional[str] = None):
        if source_id in cls._STATUS_STORE:
            cls._STATUS_STORE[source_id]["last_sync"] = datetime.now(timezone.utc)
            cls._STATUS_STORE[source_id]["latency_ms"] = round(latency_ms, 1)
            cls._STATUS_STORE[source_id]["record_count_24h"] += count
            if error:
                cls._STATUS_STORE[source_id]["status"] = "UNAVAILABLE" if count == 0 else "DELAYED"
                cls._STATUS_STORE[source_id]["error_message"] = error
            else:
                cls._STATUS_STORE[source_id]["status"] = "LIVE"
                cls._STATUS_STORE[source_id]["error_message"] = None

    @classmethod
    def get_all_status(cls) -> List[Dict[str, Any]]:
        return [
            {"source_id": k, **v}
            for k, v in cls._STATUS_STORE.items()
        ]
