from typing import List, Optional
from pydantic import BaseModel


class CorridorNode(BaseModel):
    city: str
    state: str
    lat: float
    lon: float
    order: int
    is_hub: bool
    fl_node_id: Optional[str] = None
    fl_port: Optional[int] = None
    elevation_m: Optional[float] = None
    current_pm25: Optional[float] = None
    current_aqi: Optional[int] = None
    aqi_category: Optional[str] = None


class BoundingBox(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class Corridor(BaseModel):
    id: str
    name: str
    code: str
    description: str
    bounding_box: BoundingBox
    nodes: List[CorridorNode]


class CorridorSummary(BaseModel):
    id: str
    name: str
    code: str
    risk_index: float # 0 to 100
    risk_level: str # LOW, MODERATE, HIGH, SEVERE
    active_alerts_count: int
    active_fires_count: int
    worst_city_now: Optional[str] = None
    worst_aqi_now: Optional[int] = None
    worst_city_forecast: Optional[str] = None
    worst_aqi_forecast: Optional[int] = None
    nodes: List[CorridorNode]
