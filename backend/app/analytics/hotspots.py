import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.cluster import DBSCAN

from backend.app.core.logging import logger
from backend.app.models.hotspot import Hotspot
from backend.app.models.fire import FireEvent
from backend.app.models.reading import StationReading
from backend.app.models.station import Station
from backend.app.models.report import CitizenReport


# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


class HotspotDetectionEngine:
    """
    Spatio-temporal DBSCAN clustering engine for VAYU-NET.
    Clusters multi-modal anomaly points:
      - Active VIIRS fire radiometry (NASA FIRMS)
      - Anomalous ground monitoring stations (>1.5 standard deviations or PM2.5 >= 90 ug/m3)
      - Geocoded citizen reports (last 6h)
    """

    def __init__(self, eps_km: float = 35.0, min_samples: int = 2):
        self.eps_km = eps_km
        self.eps_radians = eps_km / EARTH_RADIUS_KM
        self.min_samples = min_samples

    def cluster_points(
        self,
        fires: List[FireEvent],
        anomalous_readings: List[Tuple[Station, StationReading]],
        citizen_reports: List[CitizenReport],
        corridors_config: Optional[List[Dict[str, Any]]] = None
    ) -> List[Hotspot]:
        """
        Runs spatio-temporal clustering over combined points and returns Hotspot models.
        """
        data_points = []
        point_metadata = []

        # 1. Collect fire detections
        for f in fires:
            data_points.append([f.latitude, f.longitude])
            point_metadata.append({
                "type": "FIRE",
                "id": f.id,
                "frp_mw": f.frp_mw,
                "lat": f.latitude,
                "lon": f.longitude,
                "weight": max(1.0, f.frp_mw / 10.0),
                "confidence": f.confidence,
                "time": f.acquisition_time.isoformat() if f.acquisition_time else None
            })

        # 2. Collect anomalous station readings
        for stn, reading in anomalous_readings:
            data_points.append([stn.latitude, stn.longitude])
            point_metadata.append({
                "type": "STATION",
                "id": stn.id,
                "name": stn.name,
                "city": stn.city,
                "pm25": reading.value,
                "lat": stn.latitude,
                "lon": stn.longitude,
                "weight": max(1.0, (reading.value or 50.0) / 30.0),
                "time": reading.timestamp.isoformat() if reading.timestamp else None
            })

        # 3. Collect citizen reports
        for rep in citizen_reports:
            lat = getattr(rep, "public_lat", getattr(rep, "raw_lat", getattr(rep, "latitude", None)))
            lon = getattr(rep, "public_lon", getattr(rep, "raw_lon", getattr(rep, "longitude", None)))
            cat = getattr(rep, "user_category", getattr(rep, "category", "smoke"))
            if lat is not None and lon is not None:
                data_points.append([lat, lon])
                point_metadata.append({
                    "type": "CITIZEN_REPORT",
                    "id": rep.id,
                    "category": cat,
                    "lat": lat,
                    "lon": lon,
                    "weight": 1.5,
                    "time": rep.created_at.isoformat() if rep.created_at else None
                })

        if not data_points:
            logger.info("No active spatial points to cluster for hotspots.")
            return []

        coords_array = np.array(data_points)
        coords_rad = np.radians(coords_array)

        # Run DBSCAN with haversine metric
        db = DBSCAN(eps=self.eps_radians, min_samples=self.min_samples, metric="haversine")
        labels = db.fit_predict(coords_rad)

        unique_labels = set(labels)
        hotspots: List[Hotspot] = []
        now = datetime.now(timezone.utc)

        for label in unique_labels:
            if label == -1:
                # Outlier points: if it's a high-power fire (FRP >= 120 MW), keep as standalone cluster
                outlier_indices = np.where(labels == -1)[0]
                for idx in outlier_indices:
                    meta = point_metadata[idx]
                    if meta["type"] == "FIRE" and meta.get("frp_mw", 0) >= 120.0:
                        single_hotspot = self._build_hotspot(
                            points=[meta],
                            corridors_config=corridors_config,
                            now=now,
                            is_isolated=True
                        )
                        hotspots.append(single_hotspot)
                continue

            cluster_indices = np.where(labels == label)[0]
            cluster_members = [point_metadata[i] for i in cluster_indices]
            hotspot = self._build_hotspot(
                points=cluster_members,
                corridors_config=corridors_config,
                now=now
            )
            hotspots.append(hotspot)

        logger.info(f"DBSCAN clustering produced {len(hotspots)} active pollution hotspots.")
        return hotspots

    def _build_hotspot(
        self,
        points: List[Dict[str, Any]],
        corridors_config: Optional[List[Dict[str, Any]]],
        now: datetime,
        is_isolated: bool = False
    ) -> Hotspot:
        """Assembles a Hotspot record from cluster member points."""
        weights = [p["weight"] for p in points]
        total_weight = sum(weights)

        # Weighted centroid
        c_lat = sum(p["lat"] * w for p, w in zip(points, weights)) / total_weight
        c_lon = sum(p["lon"] * w for p, w in zip(points, weights)) / total_weight

        # Radius: max distance to member point
        max_dist = max(haversine_km(c_lat, c_lon, p["lat"], p["lon"]) for p in points)
        radius_km = max(8.0, round(max_dist, 1))

        # Metrics aggregation
        fire_points = [p for p in points if p["type"] == "FIRE"]
        station_points = [p for p in points if p["type"] == "STATION"]
        report_points = [p for p in points if p["type"] == "CITIZEN_REPORT"]

        fire_count = len(fire_points)
        station_count = len(station_points)
        report_count = len(report_points)

        max_frp = max([p["frp_mw"] for p in fire_points], default=0.0)
        total_frp = sum([p["frp_mw"] for p in fire_points])
        pm25_vals = [p["pm25"] for p in station_points if p.get("pm25") is not None]
        mean_pm25 = round(sum(pm25_vals) / len(pm25_vals), 1) if pm25_vals else None

        # Source classification
        if fire_count >= 1 and total_frp >= 40.0:
            probable_source = "Agricultural Biomass Burning"
        elif fire_count == 0 and report_count >= 2:
            probable_source = "Local Citizen-Reported Waste/Dust Burning"
        elif fire_count == 0 and station_count >= 1:
            probable_source = "Industrial / Urban Congestion Plume"
        else:
            probable_source = "Mixed Trans-boundary Plume"

        # Severity determination
        if max_frp > 300.0 or (mean_pm25 and mean_pm25 > 250.0) or total_frp > 500.0:
            severity = "CRITICAL"
        elif max_frp > 100.0 or (mean_pm25 and mean_pm25 > 150.0) or total_frp > 150.0:
            severity = "SEVERE"
        elif max_frp > 30.0 or (mean_pm25 and mean_pm25 > 90.0) or total_frp > 50.0:
            severity = "HIGH"
        else:
            severity = "MODERATE"

        # Determine nearest corridor
        corridor_id = self._find_nearest_corridor(c_lat, c_lon, corridors_config)

        # Reasoning synthesis
        isolated_prefix = "[Isolated Point Source] " if is_isolated else ""
        if probable_source == "Agricultural Biomass Burning":
            reasoning = (
                f"{isolated_prefix}Active crop residue fires detected ({fire_count} hotspots, "
                f"total FRP {round(total_frp, 1)} MW, peak {round(max_frp, 1)} MW). "
                f"Dense smoke emission radius: ~{radius_km} km."
            )
        elif probable_source == "Local Citizen-Reported Waste/Dust Burning":
            reasoning = (
                f"{isolated_prefix}Verified cluster of {report_count} ground citizen reports "
                f"indicating open waste combustion or local construction dust."
            )
        elif probable_source == "Industrial / Urban Congestion Plume":
            reasoning = (
                f"{isolated_prefix}Ground telemetry anomaly across {station_count} monitors "
                f"with mean PM2.5 of {mean_pm25} ug/m3 without satellite fire detections."
            )
        else:
            reasoning = (
                f"{isolated_prefix}Combined plume across {len(points)} multi-modal observations "
                f"(FRP: {round(total_frp, 1)} MW, PM2.5: {mean_pm25 or 'N/A'} ug/m3)."
            )

        evidence = {
            "cluster_members_count": len(points),
            "fire_count": fire_count,
            "station_count": station_count,
            "report_count": report_count,
            "total_frp_mw": round(total_frp, 2),
            "max_frp_mw": round(max_frp, 2),
            "mean_pm25": mean_pm25,
            "sample_points": points[:10]  # Store up to 10 points for inspection
        }

        return Hotspot(
            id=str(uuid.uuid4()),
            corridor_id=corridor_id,
            centroid_lat=round(c_lat, 4),
            centroid_lon=round(c_lon, 4),
            radius_km=radius_km,
            cluster_size=len(points),
            mean_pm25=mean_pm25,
            max_frp_mw=round(max_frp, 2),
            probable_source=probable_source,
            reasoning=reasoning,
            evidence=evidence,
            severity=severity,
            detected_at=now,
            is_active=True
        )

    def _find_nearest_corridor(
        self,
        lat: float,
        lon: float,
        corridors_config: Optional[List[Dict[str, Any]]]
    ) -> Optional[str]:
        """Finds closest corridor within 120 km, else returns None."""
        if not corridors_config:
            return "indo-gangetic-main"

        best_corridor = None
        min_dist = 120.0

        for corr in corridors_config:
            nodes = corr.get("nodes", [])
            for node in nodes:
                n_lat = node.get("lat")
                n_lon = node.get("lon")
                if n_lat and n_lon:
                    d = haversine_km(lat, lon, n_lat, n_lon)
                    if d < min_dist:
                        min_dist = d
                        best_corridor = corr.get("id")

        return best_corridor or "indo-gangetic-main"
