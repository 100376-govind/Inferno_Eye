# backend/models.py
import time
from sqlalchemy import String, Float, Integer, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), default="default")
    temperature: Mapped[float] = mapped_column(Float, default=0.0)
    smoke: Mapped[float] = mapped_column(Float, default=0.0)     # 0-100 %
    gas: Mapped[float] = mapped_column(Float, default=0.0)       # ppm
    humidity: Mapped[float] = mapped_column(Float, default=0.0)
    lat: Mapped[float] = mapped_column(Float, default=22.5726)
    lng: Mapped[float] = mapped_column(Float, default=88.3639)
    timestamp: Mapped[float] = mapped_column(Float, default=time.time)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_source: Mapped[str] = mapped_column(String(32))        # esp32 | mobile | upload
    confidence: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(16))             # LOW|MEDIUM|HIGH|CRITICAL
    label: Mapped[str] = mapped_column(String(32))                # fire | smoke
    lat: Mapped[float] = mapped_column(Float, default=22.5726)
    lng: Mapped[float] = mapped_column(Float, default=88.3639)
    response_recommendation: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[float] = mapped_column(Float, default=time.time)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_type: Mapped[str] = mapped_column(String(32))           # fire | smoke | sensor
    severity: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    camera_source: Mapped[str] = mapped_column(String(32), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    lat: Mapped[float] = mapped_column(Float, default=22.5726)
    lng: Mapped[float] = mapped_column(Float, default=88.3639)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[float] = mapped_column(Float, default=time.time)


class BlockchainBlock(Base):
    __tablename__ = "blockchain_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index: Mapped[int] = mapped_column(Integer, unique=True)
    event_type: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)
    prev_hash: Mapped[str] = mapped_column(String(64))
    block_hash: Mapped[str] = mapped_column(String(64))
    nonce: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[float] = mapped_column(Float)


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(256))
    filepath: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued|processing|done|error
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    processed_frames: Mapped[int] = mapped_column(Integer, default=0)
    detections_count: Mapped[int] = mapped_column(Integer, default=0)
    result_data: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[float] = mapped_column(Float, default=time.time)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16), default="admin")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

