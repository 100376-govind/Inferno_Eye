# backend/routers/alerts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Alert
from backend.schemas import AlertOut
from backend.services.alert_service import acknowledge_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/live", response_model=AlertOut)
async def latest_alert(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).order_by(Alert.timestamp.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "No alerts yet")
    return AlertOut.model_validate(row)


@router.get("/history")
async def alert_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).order_by(Alert.timestamp.desc()).limit(limit)
    )
    return [AlertOut.model_validate(a) for a in result.scalars().all()]


@router.post("/acknowledge/{alert_id}")
async def ack_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    ok = await acknowledge_alert(db, alert_id)
    if not ok:
        raise HTTPException(404, "Alert not found")
    return {"acknowledged": True, "id": alert_id}
