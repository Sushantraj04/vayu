import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from backend.app.models.hotspot import Hotspot


EARTH_RADIUS_KM = 6371.0


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates initial compass bearing from point 1 (receptor) to point 2 (source) in degrees [0, 360).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def compass_direction_name(deg: float) -> str:
    """Converts degrees to 8-point compass name (N, NE, E, SE, S, SW, W, NW)."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int(round(deg / 45.0)) % 8
    return directions[idx]


@dataclass
class SourceAttributionResult:
    receptor_name: str
    receptor_lat: float
    receptor_lon: float
    wind_speed_kmh: float
    wind_direction_deg: float
    wind_direction_cardinal: str
    boundary_layer_height_m: float
    sources: List[Dict[str, Any]]
    local_share_pct: float
    dominant_source_name: str
    confidence_pct: int
    plain_language_reasoning: str


class KinematicSourceAttributionEngine:
    """
    Heuristic atmospheric kinematic source attribution engine for VAYU-NET.
    Computes upwind angular deviation, atmospheric dispersion distance decay,
    and boundary layer trapping to apportion pollution origins to regional
    hotspots vs. local background sources.
    """

    def __init__(self, dispersion_scale_km: float = 180.0, base_local_emission_factor: float = 2.5):
        self.dispersion_scale_km = dispersion_scale_km
        self.base_local_emission_factor = base_local_emission_factor

    def attribute(
        self,
        receptor_name: str,
        receptor_lat: float,
        receptor_lon: float,
        wind_speed_kmh: float,
        wind_direction_deg: float,
        boundary_layer_height_m: float,
        hotspots: List[Hotspot],
        max_search_radius_km: float = 350.0
    ) -> SourceAttributionResult:
        """
        Attributes pollution for a target receptor using wind field and active hotspots.
        """
        wind_cardinal = compass_direction_name(wind_direction_deg)
        # Boundary layer inversion factor (shallow BLH traps pollution)
        blh = max(100.0, boundary_layer_height_m or 400.0)
        trapping_factor = max(0.25, 1.0 - (blh / 2500.0))

        # Local background emission baseline
        local_raw_score = self.base_local_emission_factor * trapping_factor
        calm_wind_bonus = max(0.0, (10.0 - wind_speed_kmh) / 5.0) if wind_speed_kmh < 10.0 else 0.0
        local_raw_score += calm_wind_bonus

        source_candidates = []

        for h in hotspots:
            dist_km = haversine_km(receptor_lat, receptor_lon, h.centroid_lat, h.centroid_lon)
            if dist_km > max_search_radius_km:
                continue

            bearing_to_source = calculate_bearing_deg(
                receptor_lat, receptor_lon, h.centroid_lat, h.centroid_lon
            )
            # Angular deviation from upwind direction (wind is coming from wind_direction_deg)
            angle_diff = abs(bearing_to_source - wind_direction_deg)
            if angle_diff > 180.0:
                angle_diff = 360.0 - angle_diff

            # Alignment factor: if > 90 deg, source is downwind (0 alignment)
            alignment = math.cos(math.radians(angle_diff)) if angle_diff <= 90.0 else 0.0

            # Atmospheric dispersion exponential decay
            distance_decay = math.exp(-dist_km / self.dispersion_scale_km)

            # Plume transit time in hours
            effective_speed = max(3.0, wind_speed_kmh)
            transit_hours = round(dist_km / effective_speed, 1)

            # Source strength
            total_frp = (h.evidence or {}).get("total_frp_mw", 0.0) if isinstance(h.evidence, dict) else 0.0
            frp_strength = math.log1p(total_frp) * 2.2
            pm25_strength = (h.mean_pm25 / 45.0) if h.mean_pm25 else 0.5
            source_strength = frp_strength + pm25_strength

            # Raw kinematic attribution score
            raw_score = source_strength * alignment * distance_decay * trapping_factor

            source_candidates.append({
                "hotspot_id": h.id,
                "probable_source": h.probable_source,
                "centroid_lat": h.centroid_lat,
                "centroid_lon": h.centroid_lon,
                "distance_km": round(dist_km, 1),
                "bearing_deg": round(bearing_to_source, 1),
                "bearing_cardinal": compass_direction_name(bearing_to_source),
                "angular_deviation_deg": round(angle_diff, 1),
                "alignment_factor": round(alignment, 3),
                "distance_decay": round(distance_decay, 3),
                "transit_hours": transit_hours,
                "total_frp_mw": round(total_frp, 1),
                "severity": h.severity,
                "raw_score": raw_score
            })

        # Calculate percentages
        total_raw = local_raw_score + sum(s["raw_score"] for s in source_candidates)
        local_share = round((local_raw_score / total_raw) * 100.0, 1)

        for s in source_candidates:
            s["share_pct"] = round((s["raw_score"] / total_raw) * 100.0, 1)

        # Sort sources by attributed share descending
        source_candidates.sort(key=lambda x: x["share_pct"], reverse=True)
        top_candidates = [s for s in source_candidates if s["share_pct"] >= 2.0]

        # Plain language narrative generation
        dominant_source_name = "Local Urban Emissions"
        confidence_pct = 70
        reasoning = ""

        if top_candidates and top_candidates[0]["share_pct"] >= 35.0:
            top = top_candidates[0]
            dominant_source_name = top["probable_source"]
            confidence_pct = min(96, int(round(top["share_pct"] + 15)))
            
            reasoning = (
                f"{confidence_pct}% confidence: {top['probable_source']} located "
                f"{top['distance_km']} km {top['bearing_cardinal']} of {receptor_name} "
                f"(total FRP {top['total_frp_mw']} MW) transported by {round(wind_speed_kmh, 1)} km/h "
                f"{wind_cardinal} winds ({round(wind_direction_deg, 0)}°) with an estimated transit time "
                f"of {top['transit_hours']} hours under shallow {round(blh, 0)}m boundary layer. "
                f"Local urban emissions contribute remaining {local_share}%."
            )
        elif wind_speed_kmh < 6.0 and blh < 350.0:
            dominant_source_name = "Local Stagnation & Urban Trapping"
            confidence_pct = 85
            reasoning = (
                f"{confidence_pct}% confidence: Strong surface stagnation over {receptor_name}. "
                f"Calm winds ({round(wind_speed_kmh, 1)} km/h) and a compressed nocturnal boundary layer "
                f"({round(blh, 0)}m) are trapping local vehicular, industrial, and domestic emissions "
                f"near surface level (local contribution: {local_share}%)."
            )
        else:
            dominant_source_name = "Mixed Regional Dispersion"
            confidence_pct = 65
            reasoning = (
                f"{confidence_pct}% confidence: Dispersed regional pollution background. "
                f"Local sources contribute {local_share}%, with moderate advection from "
                f"{len(top_candidates)} upwind regional sectors along the {wind_cardinal} wind corridor."
            )

        return SourceAttributionResult(
            receptor_name=receptor_name,
            receptor_lat=receptor_lat,
            receptor_lon=receptor_lon,
            wind_speed_kmh=wind_speed_kmh,
            wind_direction_deg=wind_direction_deg,
            wind_direction_cardinal=wind_cardinal,
            boundary_layer_height_m=blh,
            sources=top_candidates,
            local_share_pct=local_share,
            dominant_source_name=dominant_source_name,
            confidence_pct=confidence_pct,
            plain_language_reasoning=reasoning
        )
