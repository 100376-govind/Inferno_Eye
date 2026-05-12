# backend/ai/esp32_stream_reader.py
"""
Async MJPEG stream reader for ESP32-CAM.
- Reads frames in a thread-pool executor (cv2 is blocking)
- Runs YOLO on each frame
- Publishes annotated frames + detections via SSE event bus
- Auto-reconnects on disconnect
"""
import asyncio
import logging
import time
from typing import Optional

import cv2

from backend.ai.yolo_engine import get_engine, frame_to_base64
from backend.core.event_bus import event_bus

logger = logging.getLogger(__name__)

_reader_task: Optional[asyncio.Task] = None
_stream_url: Optional[str] = None
_is_running = False


async def start_reader(stream_url: str):
    global _reader_task, _stream_url, _is_running
    _stream_url = stream_url
    _is_running = True

    if _reader_task and not _reader_task.done():
        _reader_task.cancel()

    _reader_task = asyncio.create_task(_reader_loop())
    logger.info(f"ESP32 stream reader started: {stream_url}")


async def stop_reader():
    global _is_running, _reader_task
    _is_running = False
    if _reader_task:
        _reader_task.cancel()
    await event_bus.publish("camera_status", {"source": "esp32", "status": "offline"})
    logger.info("ESP32 stream reader stopped")


def get_status() -> dict:
    return {
        "source": "esp32",
        "url": _stream_url,
        "running": _is_running and bool(_reader_task and not _reader_task.done()),
    }


async def _reader_loop():
    retry_delay = 2
    while _is_running:
        cap = None
        try:
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(None, cv2.VideoCapture, _stream_url)

            if not await loop.run_in_executor(None, cap.isOpened):
                raise ConnectionError(f"Cannot open stream: {_stream_url}")

            await event_bus.publish("camera_status", {"source": "esp32", "status": "online", "url": _stream_url})
            retry_delay = 2  # reset on success
            logger.info("ESP32 stream connected")

            frame_count = 0
            while _is_running:
                ret, frame = await loop.run_in_executor(None, cap.read)
                if not ret or frame is None:
                    raise ConnectionError("Frame read failed — stream dropped")

                frame_count += 1
                # Process every 3rd frame (~10 FPS → ~3-4 inference FPS)
                if frame_count % 3 != 0:
                    continue

                engine = get_engine()
                if engine and engine.is_ready():
                    detections, annotated = await loop.run_in_executor(
                        None, engine.run, frame
                    )
                    b64 = frame_to_base64(annotated)
                else:
                    b64 = frame_to_base64(frame)
                    detections = []

                det_list = [
                    {
                        "label": d.label,
                        "confidence": round(d.confidence, 4),
                        "bbox": {"x": d.bbox.x, "y": d.bbox.y,
                                 "w": d.bbox.w, "h": d.bbox.h},
                    }
                    for d in detections
                ]

                await event_bus.publish("frame", {
                    "source": "esp32",
                    "annotated_frame": b64,
                    "detections": det_list,
                    "lat": 22.5726,
                    "lng": 88.3639,
                    "timestamp": time.time(),
                })

                # Trigger alert pipeline if fire detected
                if detections:
                    from backend.schemas import Detection, BBox as SBBox
                    from backend.database import AsyncSessionLocal
                    from backend.services.alert_service import process_detections

                    schema_dets = [
                        Detection(
                            label=d.label,
                            confidence=d.confidence,
                            bbox=SBBox(x=d.bbox.x, y=d.bbox.y,
                                       w=d.bbox.w, h=d.bbox.h),
                        )
                        for d in detections
                    ]
                    async with AsyncSessionLocal() as db:
                        await process_detections(
                            db, schema_dets, "esp32",
                            lat=float(22.5726), lng=float(88.3639)
                        )

                await asyncio.sleep(0.05)   # small yield to event loop

        except asyncio.CancelledError:
            break
        except Exception as exc:
            msg = str(exc)
            logger.warning(f"ESP32 stream error: {msg}. Reconnecting in {retry_delay}s …")
            await event_bus.publish("camera_status",
                                    {"source": "esp32", "status": "reconnecting", "error": msg})
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
        finally:
            if cap:
                await asyncio.get_event_loop().run_in_executor(None, cap.release)
