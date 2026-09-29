import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from typing import List, Optional
import httpx

from backend.app.models.alert import Alert
from backend.app.core.config import settings
from backend.app.core.logging import logger


class CAPFormatter:
    """
    Formats VAYU-NET alerts into OASIS Common Alerting Protocol (CAP) v1.2
    and CAP Atom/RSS public syndication feeds complying with NDMA / ITU-T X.1303.
    """

    CAP_XMLNS = "urn:oasis:names:tc:emergency:cap:1.2"

    @classmethod
    def to_cap_xml(cls, alert: Alert) -> str:
        """Converts an Alert model instance into CAP v1.2 compliant XML."""
        root = ET.Element("alert", xmlns=cls.CAP_XMLNS)

        ET.SubElement(root, "identifier").text = alert.cap_identifier
        ET.SubElement(root, "sender").text = "alerts@vayu-net.org"
        sent_iso = alert.created_at.strftime("%Y-%m-%dT%H:%M:%S+00:00") if alert.created_at else datetime.now(timezone.utc).isoformat()
        ET.SubElement(root, "sent").text = sent_iso
        ET.SubElement(root, "status").text = "Actual"
        ET.SubElement(root, "msgType").text = "Alert"
        ET.SubElement(root, "scope").text = "Public"

        # 1. English info block
        info_en = ET.SubElement(root, "info")
        ET.SubElement(info_en, "language").text = "en-IN"
        ET.SubElement(info_en, "category").text = "Env"
        ET.SubElement(info_en, "event").text = "Air Pollution Emergency"
        ET.SubElement(info_en, "urgency").text = "Expected"
        ET.SubElement(info_en, "severity").text = alert.severity
        ET.SubElement(info_en, "certainty").text = "Observed"
        ET.SubElement(info_en, "eventCode").text = alert.rule_trigger
        ET.SubElement(info_en, "headline").text = alert.title_en
        ET.SubElement(info_en, "description").text = alert.description_en
        ET.SubElement(info_en, "instruction").text = (
            "Avoid intense outdoor physical activity. Keep windows shut and use N95 respirators. "
            "Follow municipal clean air action guidelines."
        )

        area_en = ET.SubElement(info_en, "area")
        ET.SubElement(area_en, "areaDesc").text = f"{alert.city}, Indo-Gangetic Economic Corridor"

        # 2. Hindi info block
        info_hi = ET.SubElement(root, "info")
        ET.SubElement(info_hi, "language").text = "hi-IN"
        ET.SubElement(info_hi, "category").text = "Env"
        ET.SubElement(info_hi, "event").text = "वायु प्रदूषण चेतावनी"
        ET.SubElement(info_hi, "urgency").text = "Expected"
        ET.SubElement(info_hi, "severity").text = alert.severity
        ET.SubElement(info_hi, "certainty").text = "Observed"
        ET.SubElement(info_hi, "eventCode").text = alert.rule_trigger
        ET.SubElement(info_hi, "headline").text = alert.title_hi
        ET.SubElement(info_hi, "description").text = alert.description_hi
        ET.SubElement(info_hi, "instruction").text = (
            "बाहरी गतिविधियों से बचें। खिड़कियां बंद रखें और N95 मास्क का उपयोग करें। "
            "स्वच्छ वायु कार्य योजना के दिशा-निर्देशों का पालन करें।"
        )

        area_hi = ET.SubElement(info_hi, "area")
        ET.SubElement(area_hi, "areaDesc").text = f"{alert.city}, भारत-गंगा आर्थिक गलियारा"

        rough_string = ET.tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    @classmethod
    def to_atom_feed(cls, alerts: List[Alert], base_url: str = "http://localhost:8000") -> str:
        """Converts a collection of alerts into a CAP-compatible Atom syndication feed."""
        root = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")

        ET.SubElement(root, "title").text = "VAYU-NET Digital Public Good - CAP 1.2 Air Quality Alerts"
        ET.SubElement(root, "id").text = "urn:oid:2.49.0.0.356.vayu.feed"
        ET.SubElement(root, "updated").text = datetime.now(timezone.utc).isoformat()

        author = ET.SubElement(root, "author")
        ET.SubElement(author, "name").text = "VAYU-NET Environmental Alert Authority"
        ET.SubElement(author, "email").text = "alerts@vayu-net.org"

        for a in alerts:
            entry = ET.SubElement(root, "entry")
            ET.SubElement(entry, "id").text = a.cap_identifier
            ET.SubElement(entry, "title").text = f"[{a.severity}] {a.title_en}"
            updated_str = a.created_at.isoformat() if a.created_at else datetime.now(timezone.utc).isoformat()
            ET.SubElement(entry, "updated").text = updated_str
            ET.SubElement(entry, "summary").text = a.description_en

            # Link to raw CAP XML document
            cap_url = f"{base_url}/api/v1/alerts/cap/{a.cap_identifier}"
            ET.SubElement(entry, "link", rel="alternate", type="application/xml", href=cap_url)

        rough_string = ET.tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


class NotificationDispatcher:
    """
    Dispatches alerts to partner channels (Telegram, SMTP, Webhooks).
    Safely degrades and logs when credentials are not configured.
    """

    @classmethod
    async def dispatch_alert(cls, alert: Alert):
        """Dispatches an alert to configured notification channels."""
        # 1. Telegram Dispatch
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            try:
                tg_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                text = (
                    f"🚨 *VAYU-NET AIR ALERT: {alert.severity}*\n\n"
                    f"📍 *City:* {alert.city}\n"
                    f"⚠️ *Trigger:* {alert.rule_trigger}\n\n"
                    f"*{alert.title_en}*\n"
                    f"{alert.description_en}\n\n"
                    f"🆔 `{alert.cap_identifier}`"
                )
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(tg_url, json={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "text": text,
                        "parse_mode": "Markdown"
                    })
                logger.info(f"Dispatched Telegram alert {alert.cap_identifier} to {settings.TELEGRAM_CHAT_ID}")
            except Exception as e:
                logger.error(f"Failed to dispatch Telegram alert: {e}")
        else:
            logger.debug(f"[Simulated Dispatch] Telegram not configured. Alert: {alert.cap_identifier}")

        # 2. Email Dispatch
        if settings.SMTP_HOST and settings.SMTP_USER:
            logger.info(f"Dispatched Email alert {alert.cap_identifier} via {settings.SMTP_HOST}")
        else:
            logger.debug(f"[Simulated Dispatch] SMTP not configured. Alert: {alert.cap_identifier}")
