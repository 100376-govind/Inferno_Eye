# backend/ai/video_processor.py
"""
Background task: processes an uploaded MP4 video frame-by-frame using YOLO.
Updates VideoJob status in DB and publishes SSE progress events.
"""
import asyncio
import logging
import time

import cv2

from backend.ai.yolo_engine import get_engine, frame_to_base64
from backend.core.event_bus import event_bus
from backend.database import AsyncSessionLocal
from backend.models import VideoJob
from backend.schemas import Detection, BBox as SBBox
from backend.services.alert_service import process_detections

logger = logging.getLogger(__name__)

FRAME_SKIP = 5   # process every 5th frame (≈ 5–6 FPS from typical 25/30 FPS video)


async def process_video(job_id: int, filepath: str, lat: float, lng: float):
    """Run in asyncio background task."""
    loop = asyncio.get_event_loop()

    async with AsyncSessionLocal() as db:
        job = await _get_job(db, job_id)
        if not job:
            return

        job.status = "processing"
        await db.commit()

    cap = None
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            await _set_error(job_id, "Cannot open video file")
            return

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        engine = get_engine()

        processed = 0
        detections_total = 0
        frame_idx = 0
        all_detections = []

        while True:
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                break

            frame_idx += 1
            if frame_idx % FRAME_SKIP != 0:
                continue

            processed += 1
            if engine and engine.is_ready():
                dets, annotated = await loop.run_in_executor(None, engine.run, frame)
            else:
                dets, annotated = [], frame

            if dets:
                detections_total += len(dets)
                det_list = [
                    {"label": d.label, "confidence": round(d.confidence, 4),
                     "frame": frame_idx}
                    for d in dets
                ]
                all_detections.extend(det_list)

                # Publish annotated frame to dashboard
                await event_bus.publish("frame", {
                    "source": "upload",
                    "annotated_frame": frame_to_base64(annotated),
                    "detections": det_list,
                    "lat": lat,
                    "lng": lng,
                    "timestamp": time.time(),
                })

                # Trigger alerts
                schema_dets = [
                    Detection(
                        label=d.label,
                        confidence=d.confidence,
                        bbox=SBBox(x=d.bbox.x, y=d.bbox.y,
                                   w=d.bbox.w, h=d.bbox.h),
                    )
                    for d in dets
                ]
                async with AsyncSessionLocal() as db:
                    await process_detections(db, schema_dets, "upload",
                                             lat=lat, lng=lng)

            # Publish progress
            pct = round((frame_idx / total * 100) if total else 0, 1)
            await event_bus.publish("video_progress", {
                "job_id": job_id, "progress_pct": pct,
                "source": "upload",
                "detections_so_far": detections_total,
            })

            # Update DB every 30 processed frames
            if processed % 30 == 0:
                async with AsyncSessionLocal() as db:
                    j = await _get_job(db, job_id)
                    if j:
                        j.processed_frames = processed
                        j.detections_count = detections_total
                        await db.commit()

            await asyncio.sleep(0)   # yield to event loop

        # Finalise
        async with AsyncSessionLocal() as db:
            j = await _get_job(db, job_id)
            if j:
                j.status = "done"
                j.total_frames = total
                j.processed_frames = processed
                j.detections_count = detections_total
                j.result_data = {"detections": all_detections[:500]}
                await db.commit()

        await event_bus.publish("video_progress", {
            "job_id": job_id, "progress_pct": 100,
            "source": "upload",
            "status": "done", "detections_total": detections_total,
        })
        logger.info(f"Video job {job_id} done. Detections: {detections_total}")

    except Exception as exc:
        logger.error(f"Video job {job_id} failed: {exc}")
        await _set_error(job_id, str(exc))
    finally:
        if cap:
            await asyncio.get_event_loop().run_in_executor(None, cap.release)


async def _get_job(db, job_id: int):
    from sqlalchemy import select
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
    return result.scalar_one_or_none()


async def _set_error(job_id: int, msg: str):
    async with AsyncSessionLocal() as db:
        j = await _get_job(db, job_id)
        if j:
            j.status = "error"
            j.result_data = {"error": msg}
            await db.commit()
    await event_bus.publish("video_progress", {
        "job_id": job_id, "status": "error", "error": msg
    })
