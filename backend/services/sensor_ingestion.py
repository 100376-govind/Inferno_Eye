# backend/services/sensor_ingestion.py
import time
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import SensorReading, Alert
from backend.schemas import SensorOut, SensorPayload
from backend.core.event_bus import event_bus
from backend.services.severity_engine import (
    compute_severity, get_response_recommendation,
    SMOKE_WARNING, GAS_WARNING, FIRE_TEMP_WARNING,
)

async def ingest_sensor_internal(payload: SensorPayload, db: AsyncSession) -> SensorOut:
    """Core logic for ingesting sensor data, used by both endpoint and background poller."""
    reading = SensorReading(**payload.model_dump(), timestamp=time.time())
    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    out = SensorOut.model_validate(reading)

    # Publish sensor SSE event
    await event_bus.publish("sensor", out.model_dump())

    # Check if sensor alone triggers alert
    severity = compute_severity(
        confidence=0.0,
        temperature=payload.temperature,
        smoke=payload.smoke,
        gas=payload.gas,
        ds18b20_temp=payload.ds18b20_temp,
    )
    if (payload.temperature >= FIRE_TEMP_WARNING
            or payload.ds18b20_temp >= FIRE_TEMP_WARNING
            or payload.smoke >= SMOKE_WARNING
            or payload.gas >= GAS_WARNING):

        rec = get_response_recommendation(severity)
        alert = Alert(
            alert_type="sensor",
            severity=severity,
            message=(
                f"Sensor threshold exceeded — "
                f"DHT:{payload.temperature}°C  DS:{payload.ds18b20_temp}°C  "
                f"Smoke:{payload.smoke}  "
                f"Gas:{payload.gas}ppm. {rec}"
            ),
            camera_source="sensor",
            confidence=0.0,
            lat=payload.lat,
            lng=payload.lng,
            acknowledged=False,
            timestamp=time.time(),
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        await event_bus.publish("alert", {
            "id": alert.id,
            "alert_type": "sensor",
            "severity": severity,
            "message": alert.message,
            "camera_source": "sensor",
            "confidence": 0.0,
            "lat": payload.lat,
            "lng": payload.lng,
            "acknowledged": False,
            "timestamp": alert.timestamp,
            "recommendation": rec,
        })

        # GPS event
        await event_bus.publish("gps", {
            "lat": payload.lat,
            "lng": payload.lng,
            "source": "sensor",
            "severity": severity,
        })

    return out
