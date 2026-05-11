# backend/routers/incidents.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Incident
from backend.schemas import IncidentOut

router = APIRouter(prefix="/incident", tags=["Incidents"])


@router.get("/history")
async def incident_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).order_by(Incident.timestamp.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [IncidentOut.model_validate(r) for r in rows]
