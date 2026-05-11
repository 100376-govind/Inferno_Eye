# backend/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ── Sensor ─────────────────────────────────────────────────────────────────
class SensorPayload(BaseModel):
    device_id: str = "default"
    temperature: float = Field(..., ge=0, le=1500)
    smoke: float = Field(..., ge=0, le=100)
    gas: float = Field(..., ge=0, le=10000)
    humidity: float = Field(default=0.0, ge=0, le=100)
    lat: float = Field(default=22.5726)
    lng: float = Field(default=88.3639)


class SensorOut(BaseModel):
    id: int
    device_id: str
    temperature: float
    smoke: float
    gas: float
    humidity: float
    lat: float
    lng: float
    timestamp: float

    model_config = {"from_attributes": True}


# ── Camera ─────────────────────────────────────────────────────────────────
class ESP32ConnectRequest(BaseModel):
    stream_url: str


class MobileFrameRequest(BaseModel):
    frame: str            # base64-encoded JPEG
    lat: float = 22.5726
    lng: float = 88.3639


# ── Detection ──────────────────────────────────────────────────────────────
class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class Detection(BaseModel):
    label: str            # fire | smoke
    confidence: float
    bbox: BBox


class DetectionResult(BaseModel):
    source: str           # esp32 | mobile | upload
    detections: List[Detection]
    annotated_frame: Optional[str] = None   # base64 JPEG
    lat: float = 22.5726
    lng: float = 88.3639
    timestamp: float = 0.0


# ── Alert ──────────────────────────────────────────────────────────────────
class AlertOut(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    camera_source: str
    confidence: float
    lat: float
    lng: float
    acknowledged: bool
    timestamp: float

    model_config = {"from_attributes": True}


# ── Incident ───────────────────────────────────────────────────────────────
class IncidentOut(BaseModel):
    id: int
    camera_source: str
    confidence: float
    severity: str
    label: str
    lat: float
    lng: float
    response_recommendation: str
    timestamp: float

    model_config = {"from_attributes": True}


# ── Blockchain ─────────────────────────────────────────────────────────────
class BlockOut(BaseModel):
    id: int
    index: int
    event_type: str
    data: Any
    prev_hash: str
    block_hash: str
    nonce: int
    timestamp: float

    model_config = {"from_attributes": True}


# ── Video Job ──────────────────────────────────────────────────────────────
class VideoJobOut(BaseModel):
    id: int
    filename: str
    status: str
    total_frames: int
    processed_frames: int
    detections_count: int
    result_data: Any
    timestamp: float

    model_config = {"from_attributes": True}
