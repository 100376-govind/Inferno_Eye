# backend/ai/external_stream_reader.py
import asyncio
import logging
import time
from typing import Optional
import cv2
import httpx

from backend.ai.yolo_engine import get_engine, frame_to_base64
from backend.core.event_bus import event_bus

logger = logging.getLogger(__name__)

_reader_task: Optional[asyncio.Task] = None
_stream_url: Optional[str] = None
_is_running = False
_high_freq = False

async def start_reader(stream_url: str):
    global _reader_task, _stream_url, _is_running
    _stream_url = stream_url
    _is_running = True

    if _reader_task and not _reader_task.done():
        _reader_task.cancel()

    _reader_task = asyncio.create_task(_reader_loop())
    logger.info(f"External phone stream reader started: {stream_url}")

async def stop_reader():
    global _is_running, _reader_task
    _is_running = False
    if _reader_task:
        _reader_task.cancel()
    await event_bus.publish("camera_status", {"source": "mobile", "status": "offline"})
    logger.info("External phone stream reader stopped")

def get_status() -> dict:
    return {
        "source": "mobile",
        "url": _stream_url,
        "running": _is_running and bool(_reader_task and not _reader_task.done()),
    }

async def toggle_torch(state: bool):
    """Specific to 'IP Webcam' app on Android."""
    if not _stream_url: return
    try:
        base = _stream_url.rsplit('/', 1)[0]
        cmd = "enabletorch" if state else "disabletorch"
        async with httpx.AsyncClient() as client:
            await client.get(f"{base}/{cmd}", timeout=2.0)
    except Exception as e:
        logger.warning(f"Failed to toggle torch: {e}")

async def switch_camera():
    """Specific to 'IP Webcam' app on Android."""
    if not _stream_url: return
    try:
        base = _stream_url.rsplit('/', 1)[0]
        # IP Webcam uses /ptz?camera=switch or similar endpoints
        async with httpx.AsyncClient() as client:
            # We'll just hit a generic switch endpoint.
            await client.get(f"{base}/settings/ffc?set=toggle", timeout=2.0)
    except Exception as e:
        logger.warning(f"Failed to switch camera: {e}")

async def toggle_high_freq(state: bool):
    global _high_freq
    _high_freq = state

async def play_audio_alert():
    """Play audio on the IP Webcam app when fire detected."""
    if not _stream_url: return
    try:
        base = _stream_url.rsplit('/', 1)[0]
        async with httpx.AsyncClient() as client:
            await client.get(f"{base}/audio/play", timeout=2.0)
    except Exception as e:
        logger.warning(f"Failed to play audio alert: {e}")

async def _reader_loop():
    retry_delay = 2
    while _is_running:
        cap = None
        try:
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(None, cv2.VideoCapture, _stream_url)

            if not await loop.run_in_executor(None, cap.isOpened):
                raise ConnectionError(f"Cannot open external stream: {_stream_url}")

            await event_bus.publish("camera_status", {"source": "mobile", "status": "online", "url": _stream_url})
            retry_delay = 2
            logger.info("External phone stream connected")

            frame_count = 0
            last_audio_alert = 0.0

            while _is_running:
                ret, frame = await loop.run_in_executor(None, cap.read)
                if not ret or frame is None:
                    raise ConnectionError("External frame read failed")

                frame_count += 1
                if not _high_freq and frame_count % 3 != 0: continue

                engine = get_engine()
                if engine and engine.is_ready():
                    detections, annotated = await loop.run_in_executor(None, engine.run, frame)
                    b64 = frame_to_base64(annotated)
                else:
                    b64 = frame_to_base64(frame)
                    detections = []

                det_list = [
                    {
                        "label": d.label,
                        "confidence": round(d.confidence, 4),
                        "bbox": {"x": d.bbox.x, "y": d.bbox.y, "w": d.bbox.w, "h": d.bbox.h},
                    }
                    for d in detections
                ]

                await event_bus.publish("frame", {
                    "source": "mobile",
                    "annotated_frame": b64,
                    "detections": det_list,
                    "lat": 22.5726,
                    "lng": 88.3639,
                    "timestamp": time.time(),
                })

                if detections:
                    if time.time() - last_audio_alert > 10:
                        asyncio.create_task(play_audio_alert())
                        last_audio_alert = time.time()

                    from backend.schemas import Detection, BBox as SBBox
                    from backend.database import AsyncSessionLocal
                    from backend.services.alert_service import process_detections
                    schema_dets = [
                        Detection(label=d.label, confidence=d.confidence,
                                  bbox=SBBox(x=d.bbox.x, y=d.bbox.y, w=d.bbox.w, h=d.bbox.h))
                        for d in detections
                    ]
                    async with AsyncSessionLocal() as db:
                        await process_detections(db, schema_dets, "mobile", lat=22.5726, lng=88.3639)

                await asyncio.sleep(0.05)

        except asyncio.CancelledError: break
        except Exception as exc:
            msg = str(exc)
            logger.warning(f"External stream error: {msg}")
            await event_bus.publish("camera_status", {"source": "mobile", "status": "reconnecting", "error": msg})
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
        finally:
            if cap: await loop.run_in_executor(None, cap.release)
