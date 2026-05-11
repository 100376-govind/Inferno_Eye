# backend/routers/video.py
import os
import time
import asyncio
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import VideoJob
from backend.schemas import VideoJobOut
from backend.ai.video_processor import process_video

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
router = APIRouter(prefix="/video", tags=["Video"])


@router.post("/upload", response_model=VideoJobOut)
async def upload_video(
    file: UploadFile = File(...),
    lat: float = Form(default=22.5726),
    lng: float = Form(default=88.3639),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(400, "Only video files (mp4/avi/mov/mkv) are accepted")

    safe_name = f"{int(time.time())}_{file.filename.replace(' ', '_')}"
    filepath = os.path.join(UPLOAD_DIR, safe_name)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):   # 1 MB chunks
            await f.write(chunk)

    # Create job record
    job = VideoJob(filename=file.filename, filepath=filepath, status="queued",
                   timestamp=time.time())
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch background task
    asyncio.create_task(process_video(job.id, filepath, lat, lng))

    return job


@router.get("/status/{job_id}", response_model=VideoJobOut)
async def video_status(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Video job not found")
    return job


@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VideoJob).order_by(VideoJob.timestamp.desc()).limit(20)
    )
    return [VideoJobOut.model_validate(j) for j in result.scalars().all()]
