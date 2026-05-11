# backend/routers/sensors.py
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import SensorReading
from backend.schemas import SensorPayload, SensorOut
from backend.core.event_bus import event_bus
from backend.services.severity_engine import (
    compute_severity, get_response_recommendation,
    SMOKE_WARNING, GAS_WARNING, FIRE_TEMP_WARNING,
)

router = APIRouter(prefix="/iot", tags=["Sensors"])


@router.post("/sensor", response_model=SensorOut)
async def ingest_sensor(payload: SensorPayload, db: AsyncSession = Depends(get_db)):
    """Receive real sensor data from ESP32 / Arduino / any IoT device."""
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
    )
    if (payload.temperature >= FIRE_TEMP_WARNING
            or payload.smoke >= SMOKE_WARNING
            or payload.gas >= GAS_WARNING):

        from backend.models import Alert
        rec = get_response_recommendation(severity)
        alert = Alert(
            alert_type="sensor",
            severity=severity,
            message=(
                f"Sensor threshold exceeded — "
                f"Temp:{payload.temperature}°C  Smoke:{payload.smoke}%  "
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


@router.get("/sensor/live", response_model=SensorOut)
async def get_latest_sensor(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return SensorOut(id=0, device_id="none", temperature=0, smoke=0,
                         gas=0, humidity=0, lat=22.5726, lng=88.3639, timestamp=0)
    return SensorOut.model_validate(row)


@router.get("/sensor/history")
async def sensor_history(limit: int = 60, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [SensorOut.model_validate(r) for r in reversed(rows)]
