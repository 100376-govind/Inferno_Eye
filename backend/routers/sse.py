# backend/routers/sse.py
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.core.event_bus import event_bus

router = APIRouter(tags=["SSE"])


@router.get("/events/live")
async def live_events(request: Request):
    """
    Server-Sent Events stream.
    Clients subscribe and receive ALL real-time events:
      frame | sensor | alert | incident | blockchain | camera_status |
      video_progress | alert_ack | gps
    """
    q = event_bus.subscribe()

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # SSE keep-alive comment (not parsed by EventSource)
                    yield ": keepalive\n\n"
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )
