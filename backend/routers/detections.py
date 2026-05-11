# backend/routers/detections.py
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Incident
from backend.schemas import IncidentOut

router = APIRouter(prefix="/detections", tags=["Detections"])


@router.get("/live")
async def latest_detection(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).order_by(Incident.timestamp.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return {"status": "SAFE", "message": "No detections yet", "timestamp": time.time()}
    return {
        "status": row.severity,
        "label": row.label,
        "confidence": row.confidence,
        "camera_source": row.camera_source,
        "lat": row.lat,
        "lng": row.lng,
        "timestamp": row.timestamp,
    }


@router.get("/history")
async def detection_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).order_by(Incident.timestamp.desc()).limit(limit)
    )
    return [IncidentOut.model_validate(r) for r in result.scalars().all()]
