# backend/services/alert_service.py
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import Alert, Incident
from backend.schemas import Detection
from backend.services.severity_engine import compute_severity, get_response_recommendation
from backend.services import blockchain_service
from backend.core.event_bus import event_bus
from typing import List


async def process_detections(
    db: AsyncSession,
    detections: List[Detection],
    source: str,
    lat: float,
    lng: float,
    sensor_temp: float = 0.0,
    sensor_smoke: float = 0.0,
    sensor_gas: float = 0.0,
) -> None:
    """
    Given YOLO detections from any camera source:
    1. Compute severity
    2. Save Incident + Alert to DB
    3. Log to blockchain
    4. Publish SSE events
    """
    if not detections:
        return

    best = max(detections, key=lambda d: d.confidence)
    severity = compute_severity(
        confidence=best.confidence,
        temperature=sensor_temp,
        smoke=sensor_smoke,
        gas=sensor_gas,
    )
    recommendation = get_response_recommendation(severity)

    # ── Persist incident ───────────────────────────────────────────────────
    incident = Incident(
        camera_source=source,
        confidence=best.confidence,
        severity=severity,
        label=best.label,
        lat=lat,
        lng=lng,
        response_recommendation=recommendation,
        timestamp=time.time(),
    )
    db.add(incident)

    # ── Persist alert ──────────────────────────────────────────────────────
    alert = Alert(
        alert_type=best.label,
        severity=severity,
        message=f"{best.label.upper()} detected via {source} "
                f"(confidence: {best.confidence:.0%}). {recommendation}",
        camera_source=source,
        confidence=best.confidence,
        lat=lat,
        lng=lng,
        acknowledged=False,
        timestamp=time.time(),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(incident)
    await db.refresh(alert)

    # ── Blockchain log ─────────────────────────────────────────────────────
    block = await blockchain_service.add_block(
        db,
        event_type=f"FIRE_DETECTED_{severity}",
        data={
            "source": source,
            "label": best.label,
            "confidence": round(best.confidence, 4),
            "severity": severity,
            "lat": lat,
            "lng": lng,
            "incident_id": incident.id,
            "ts": incident.timestamp,
        },
    )

    # ── SSE broadcasts ─────────────────────────────────────────────────────
    await event_bus.publish("alert", {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "camera_source": alert.camera_source,
        "confidence": alert.confidence,
        "lat": alert.lat,
        "lng": alert.lng,
        "acknowledged": alert.acknowledged,
        "timestamp": alert.timestamp,
        "recommendation": recommendation,
    })

    await event_bus.publish("incident", {
        "id": incident.id,
        "camera_source": incident.camera_source,
        "confidence": incident.confidence,
        "severity": incident.severity,
        "label": incident.label,
        "lat": incident.lat,
        "lng": incident.lng,
        "response_recommendation": incident.response_recommendation,
        "timestamp": incident.timestamp,
    })

    await event_bus.publish("blockchain", {
        "index": block.index,
        "event_type": block.event_type,
        "block_hash": block.block_hash,
        "prev_hash": block.prev_hash,
        "nonce": block.nonce,
        "timestamp": block.timestamp,
        "data": block.data,
    })


async def acknowledge_alert(db: AsyncSession, alert_id: int) -> bool:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return False
    alert.acknowledged = True
    await db.commit()
    await event_bus.publish("alert_ack", {"id": alert_id})
    return True
