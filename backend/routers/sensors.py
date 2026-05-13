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
    SMOKE_WARNING, GAS_WARNING, FIRE_TEMP_WARNING,
)
from backend.services.sensor_ingestion import ingest_sensor_internal

from backend.services.iot_service import start_iot_polling, stop_iot_polling

router = APIRouter(prefix="/iot", tags=["Sensors"])


@router.post("/connect")
async def connect_iot(ip: str):
    """Start polling an external IoT sensor node."""
    await start_iot_polling(ip)
    return {"status": "polling started", "ip": ip}


@router.post("/disconnect")
async def disconnect_iot():
    """Stop polling the external IoT sensor node."""
    await stop_iot_polling()
    return {"status": "polling stopped"}


@router.post("/sensor", response_model=SensorOut)
async def ingest_sensor(payload: SensorPayload, db: AsyncSession = Depends(get_db)):
    """Receive real sensor data from ESP32 / Arduino / any IoT device."""
    return await ingest_sensor_internal(payload, db)


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
