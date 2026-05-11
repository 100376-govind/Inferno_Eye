# backend/ai/mobile_frame_processor.py
"""
Processes a single base64-encoded frame from the mobile/drone camera.
Called by POST /camera/mobile/start.
"""
import time
import logging
from typing import Optional

from backend.ai.yolo_engine import get_engine, base64_to_frame, frame_to_base64
from backend.core.event_bus import event_bus

logger = logging.getLogger(__name__)


async def process_mobile_frame(
    b64_frame: str,
    lat: float,
    lng: float,
    db=None,
) -> dict:
    """
    Decode frame → YOLO → publish SSE → (optionally) trigger alert pipeline.
    Returns annotated frame as base64 + detections list.
    """
    frame = base64_to_frame(b64_frame)
    if frame is None:
        return {"error": "Invalid frame data", "detections": [], "annotated_frame": None}

    engine = get_engine()
    if engine and engine.is_ready():
        detections, annotated = engine.run(frame)
    else:
        detections, annotated = [], frame

    b64_out = frame_to_base64(annotated)
    det_list = [
        {
            "label": d.label,
            "confidence": round(d.confidence, 4),
            "bbox": {"x": d.bbox.x, "y": d.bbox.y, "w": d.bbox.w, "h": d.bbox.h},
        }
        for d in detections
    ]

    # Publish frame SSE event (dashboard displays it)
    await event_bus.publish("frame", {
        "source": "mobile",
        "annotated_frame": b64_out,
        "detections": det_list,
        "lat": lat,
        "lng": lng,
        "timestamp": time.time(),
    })

    # Trigger alert pipeline when fire/smoke detected
    if detections and db is not None:
        from backend.schemas import Detection, BBox as SBBox
        from backend.services.alert_service import process_detections

        schema_dets = [
            Detection(
                label=d.label,
                confidence=d.confidence,
                bbox=SBBox(x=d.bbox.x, y=d.bbox.y, w=d.bbox.w, h=d.bbox.h),
            )
            for d in detections
        ]
        await process_detections(db, schema_dets, "mobile", lat=lat, lng=lng)

    return {
        "detections": det_list,
        "annotated_frame": b64_out,
        "timestamp": time.time(),
    }
