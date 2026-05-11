# backend/routers/camera.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import ESP32ConnectRequest, MobileFrameRequest
from backend.ai import esp32_stream_reader, external_stream_reader
from backend.ai.mobile_frame_processor import process_mobile_frame

router = APIRouter(prefix="/camera", tags=["Camera"])


@router.post("/esp32/connect")
async def connect_esp32(req: ESP32ConnectRequest):
    """Register an ESP32-CAM stream URL and start reading frames."""
    await esp32_stream_reader.start_reader(req.stream_url)
    return {"status": "started", "stream_url": req.stream_url}


@router.post("/esp32/disconnect")
async def disconnect_esp32():
    await esp32_stream_reader.stop_reader()
    return {"status": "stopped"}


@router.get("/esp32/status")
async def esp32_status():
    return esp32_stream_reader.get_status()


@router.post("/external/connect")
async def connect_external(req: ESP32ConnectRequest):
    """Register a phone IP camera stream URL (MJPEG)."""
    await external_stream_reader.start_reader(req.stream_url)
    return {"status": "started", "stream_url": req.stream_url}


@router.post("/external/disconnect")
async def disconnect_external():
    await external_stream_reader.stop_reader()
    return {"status": "stopped"}


@router.post("/external/torch")
async def control_torch(enabled: bool):
    await external_stream_reader.toggle_torch(enabled)
    return {"ok": True, "enabled": enabled}


@router.post("/external/camera/switch")
async def switch_external_camera():
    await external_stream_reader.switch_camera()
    return {"ok": True}


@router.post("/external/high_freq")
async def toggle_external_high_freq(enabled: bool):
    await external_stream_reader.toggle_high_freq(enabled)
    return {"ok": True, "enabled": enabled}


@router.post("/mobile/frame")
async def receive_mobile_frame(
    req: MobileFrameRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a single base64-encoded frame from the mobile camera page.
    Runs YOLO, publishes SSE frame event, triggers alert pipeline.
    """
    result = await process_mobile_frame(req.frame, req.lat, req.lng, db=db)
    return result
