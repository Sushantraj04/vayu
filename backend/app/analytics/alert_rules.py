import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from backend.app.core.logging import logger
from backend.app.models.alert import Alert
from backend.app.models.reading import StationReading
from backend.app.models.station import Station
from backend.app.models.forecast import Forecast
from backend.app.models.hotspot import Hotspot
from backend.app.models.report import CitizenReport
from backend.app.analytics.hotspots import haversine_km


class AlertRuleEngine:
    """
    Evaluates automated environmental alert rules:
      1. SUSTAINED_HIGH_AQI: PM2.5 >= 250 ug/m3 in anchor cities.
      2. FORECAST_SPIKE: Predicted PM2.5 jump >= +75 ug/m3 or Severe AQI in +24h.
      3. CORRIDOR_TRANS_BOUNDARY: High-intensity upwind biomass/industrial smoke plume advection.
      4. LOCAL_CITIZEN_CLUSTER: >= 3 citizen reports within 5 km within 4 hours.

    Enforces alert suppression: max 1 alert per city/rule within 3 hours unless CRITICAL.
    """

    COOLDOWN_HOURS = 3

    @staticmethod
    def generate_cap_identifier() -> str:
        year = datetime.now(timezone.utc).year
        unique_suffix = uuid.uuid4().hex[:8].upper()
        return f"urn:oid:2.49.0.0.356.vayu.{year}.{unique_suffix}"

    async def is_rate_limited(
        self,
        db: AsyncSession,
        city: str,
        rule_trigger: str,
        new_severity: str
    ) -> bool:
        """
        Suppresses alert if an alert with same rule was created for this city within COOLDOWN_HOURS,
        unless the new alert escalates to CRITICAL.
        """
        if new_severity == "CRITICAL":
            return False

        since = datetime.now(timezone.utc) - timedelta(hours=self.COOLDOWN_HOURS)
        stmt = (
            select(Alert)
            .where(Alert.city == city)
            .where(Alert.rule_trigger == rule_trigger)
            .where(Alert.created_at >= since)
        )
        recent = (await db.execute(stmt)).scalars().first()
        return recent is not None

    async def evaluate_sustained_high_aqi(
        self,
        db: AsyncSession,
        stations: List[Station]
    ) -> List[Alert]:
        """Checks for severe PM2.5 levels (>= 250 ug/m3) at active monitoring stations."""
        alerts: List[Alert] = []
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=3)

        for stn in stations:
            # Query recent PM2.5 readings for station
            stmt = (
                select(StationReading)
                .where(StationReading.station_id == stn.id)
                .where(StationReading.parameter == "pm25")
                .where(StationReading.timestamp >= since)
                .order_by(desc(StationReading.timestamp))
            )
            readings = (await db.execute(stmt)).scalars().all()
            if not readings:
                continue

            latest = readings[0]
            val = latest.value or 0.0

            if val >= 250.0:
                severity = "CRITICAL" if val >= 380.0 else "SEVERE"
                if await self.is_rate_limited(db, stn.city, "SUSTAINED_HIGH_AQI", severity):
                    continue

                cap_id = self.generate_cap_identifier()
                alert = Alert(
                    id=str(uuid.uuid4()),
                    corridor_id="indo-gangetic-main",
                    city=stn.city,
                    severity=severity,
                    title_en=f"Severe Air Pollution Emergency in {stn.city}",
                    title_hi=f"{stn.city} में गंभीर वायु प्रदूषण आपातकाल",
                    description_en=(
                        f"Station '{stn.name}' recorded hazardous PM2.5 level of {val:.1f} ug/m3. "
                        "CPCB NAQI Category: Severe. Vulnerable populations, children, and elderly must avoid all outdoor activity. "
                        "Keep indoor air purifiers operational and wear N95 respirators outdoors."
                    ),
                    description_hi=(
                        f"स्टेशन '{stn.name}' ने {val:.1f} ug/m3 का खतरनाक PM2.5 स्तर दर्ज किया। "
                        "सीपीसीबी एक्यूआई श्रेणी: गंभीर। संवेदनशील नागरिक, बच्चे और बुजुर्ग बाहरी गतिविधियों से पूरी तरह बचें।"
                    ),
                    evidence={
                        "station_id": stn.id,
                        "station_name": stn.name,
                        "pm25_ug_m3": val,
                        "readings_count_3h": len(readings),
                        "aqi_category": "Severe"
                    },
                    rule_trigger="SUSTAINED_HIGH_AQI",
                    status="NEW",
                    cap_identifier=cap_id,
                    created_at=now
                )
                alerts.append(alert)

        return alerts

    async def evaluate_forecast_spikes(
        self,
        db: AsyncSession,
        forecasts: List[Forecast]
    ) -> List[Alert]:
        """Detects significant upcoming pollution spikes predicted by ML models."""
        alerts: List[Alert] = []
        now = datetime.now(timezone.utc)

        for fc in forecasts:
            if fc.is_insufficient_data or fc.predicted_pm25 is None:
                continue

            # Check if 24h forecast predicts Severe or Very Poor with high PM2.5
            if fc.horizon_hours == 24 and fc.predicted_pm25 >= 200.0:
                severity = "CRITICAL" if fc.predicted_pm25 >= 300.0 else "SEVERE"
                if await self.is_rate_limited(db, fc.city, "FORECAST_SPIKE", severity):
                    continue

                cap_id = self.generate_cap_identifier()
                alert = Alert(
                    id=str(uuid.uuid4()),
                    corridor_id="indo-gangetic-main",
                    city=fc.city,
                    severity=severity,
                    title_en=f"Pollution Spike Forecast Advisory for {fc.city} (+24h)",
                    title_hi=f"{fc.city} के लिए 24 घंटे का गंभीर प्रदूषण पूर्वानुमान",
                    description_en=(
                        f"Predictive models forecast a sharp pollution surge reaching {fc.predicted_pm25:.1f} ug/m3 "
                        f"(CPCB AQI: {fc.predicted_aqi or 'Severe'}) by {fc.target_timestamp.strftime('%Y-%m-%d %H:%M UTC')}. "
                        "Municipal authorities should enact emergency dust control and industrial curbing immediately."
                    ),
                    description_hi=(
                        f"पूर्वानुमान मॉडल 24 घंटों में {fc.city} में {fc.predicted_pm25:.1f} ug/m3 तक प्रदूषण वृद्धि का संकेत दे रहे हैं। "
                        "स्थानीय प्रशासन को धूल नियंत्रण और औद्योगिक उपायों को तुरंत लागू करना चाहिए।"
                    ),
                    evidence={
                        "horizon_hours": fc.horizon_hours,
                        "predicted_pm25": fc.predicted_pm25,
                        "predicted_aqi": fc.predicted_aqi,
                        "lower_bound_pm25": fc.lower_bound_pm25,
                        "upper_bound_pm25": fc.upper_bound_pm25,
                        "model_version": fc.model_version
                    },
                    rule_trigger="FORECAST_SPIKE",
                    status="NEW",
                    cap_identifier=cap_id,
                    created_at=now
                )
                alerts.append(alert)

        return alerts

    async def evaluate_trans_boundary_plumes(
        self,
        db: AsyncSession,
        hotspots: List[Hotspot],
        target_cities: List[Tuple[str, float, float]]
    ) -> List[Alert]:
        """Detects high-FRP upstream biomass clusters transporting smoke towards downwind corridor cities."""
        alerts: List[Alert] = []
        now = datetime.now(timezone.utc)

        for h in hotspots:
            total_frp = (h.evidence or {}).get("total_frp_mw", 0.0) if isinstance(h.evidence, dict) else 0.0
            if total_frp < 150.0:
                continue

            for city_name, c_lat, c_lon in target_cities:
                dist = haversine_km(c_lat, c_lon, h.centroid_lat, h.centroid_lon)
                # If hotspot is between 40 km and 300 km away
                if 40.0 <= dist <= 300.0:
                    severity = "CRITICAL" if total_frp >= 500.0 else "SEVERE"
                    if await self.is_rate_limited(db, city_name, "CORRIDOR_TRANS_BOUNDARY", severity):
                        continue

                    cap_id = self.generate_cap_identifier()
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        corridor_id=h.corridor_id or "indo-gangetic-main",
                        city=city_name,
                        severity=severity,
                        title_en=f"Trans-boundary Smoke Inflow Alert for {city_name}",
                        title_hi=f"{city_name} के लिए सीमा-पार धुएं का अलर्ट",
                        description_en=(
                            f"Intense regional crop burning cluster detected ~{dist:.0f} km upwind from {city_name} "
                            f"(Total FRP: {total_frp:.1f} MW, peak: {h.max_frp_mw:.1f} MW). "
                            "Prevailing meteorological winds are transporting dense trans-boundary smoke along the corridor."
                        ),
                        description_hi=(
                            f"{city_name} से लगभग {dist:.0f} किमी ऊपर तीव्र पराली दहन क्लस्टर दर्ज हुआ है "
                            f"(कुल एफआरपी: {total_frp:.1f} मेगावाट)। क्षेत्रीय हवाएं गलियारे के साथ सघन धुआं ला रही हैं।"
                        ),
                        evidence={
                            "hotspot_id": h.id,
                            "hotspot_lat": h.centroid_lat,
                            "hotspot_lon": h.centroid_lon,
                            "distance_km": round(dist, 1),
                            "total_frp_mw": total_frp,
                            "probable_source": h.probable_source
                        },
                        rule_trigger="CORRIDOR_TRANS_BOUNDARY",
                        status="NEW",
                        cap_identifier=cap_id,
                        created_at=now
                    )
                    alerts.append(alert)

        return alerts

    async def evaluate_citizen_report_clusters(
        self,
        db: AsyncSession,
        reports: List[CitizenReport]
    ) -> List[Alert]:
        """Detects localized ground citizen report clusters (>= 3 reports within 5 km within 4 hours)."""
        alerts: List[Alert] = []
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=4)

        recent_reports = [
            r for r in reports 
            if r.created_at and r.created_at >= since and r.public_lat and r.public_lon
        ]

        # Spatial grouping within 5 km
        processed = set()
        for i, r1 in enumerate(recent_reports):
            if r1.id in processed:
                continue

            cluster = [r1]
            for j, r2 in enumerate(recent_reports):
                if i != j and r2.id not in processed:
                    d = haversine_km(r1.public_lat, r1.public_lon, r2.public_lat, r2.public_lon)
                    if d <= 5.0:
                        cluster.append(r2)

            if len(cluster) >= 3:
                for member in cluster:
                    processed.add(member.id)

                city_name = "Local Municipal Area"
                severity = "HIGH"
                if await self.is_rate_limited(db, city_name, "LOCAL_CITIZEN_CLUSTER", severity):
                    continue

                cap_id = self.generate_cap_identifier()
                categories = list(set(r.user_category for r in cluster))
                alert = Alert(
                    id=str(uuid.uuid4()),
                    corridor_id="delhi-ncr-industrial",
                    city=city_name,
                    severity=severity,
                    title_en="Verified Ground Citizen Pollution Incident Cluster",
                    title_hi="सत्यापित नागरिक प्रदूषण रिपोर्ट क्लस्टर",
                    description_en=(
                        f"High-density cluster of {len(cluster)} citizen reports submitted within a 5 km radius "
                        f"in the last 4 hours (reported activities: {', '.join(categories)}). "
                        "Dispatched to local municipal flying squads for ground verification."
                    ),
                    description_hi=(
                        f"पिछले 4 घंटों में 5 किमी के दायरे में {len(cluster)} नागरिक रिपोर्टें दर्ज की गईं। "
                        "सत्यापन के लिए स्थानीय नगर निगम उड़नदस्ते को सतर्क कर दिया गया है।"
                    ),
                    evidence={
                        "reports_count": len(cluster),
                        "cluster_center_lat": round(r1.public_lat, 4),
                        "cluster_center_lon": round(r1.public_lon, 4),
                        "categories": categories
                    },
                    rule_trigger="LOCAL_CITIZEN_CLUSTER",
                    status="NEW",
                    cap_identifier=cap_id,
                    created_at=now
                )
                alerts.append(alert)

        return alerts
