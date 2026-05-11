# backend/core/event_bus.py
import asyncio
import json
import time
from typing import Set


class EventBus:
    """Async SSE fan-out bus. Producers publish events; SSE endpoints subscribe."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def publish(self, event_type: str, payload: dict) -> None:
        """Broadcast to all connected SSE clients."""
        event = {"type": event_type, "payload": payload, "ts": time.time()}
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.discard(q)

    def subscriber_count(self) -> int:
        return len(self._subscribers)


# Singleton — imported everywhere
event_bus = EventBus()
