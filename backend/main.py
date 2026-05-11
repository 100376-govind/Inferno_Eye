# backend/main.py
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("inferno_eye")

# ── Routers ────────────────────────────────────────────────────────────────
from backend.routers import camera, video, sensors, detections, alerts, blockchain, incidents, sse, auth

# ── Services ───────────────────────────────────────────────────────────────
from backend.database import init_db
from backend.ai.yolo_engine import YOLOEngine, set_engine
from backend.services.blockchain_service import get_all_blocks, add_block
from backend.database import AsyncSessionLocal

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("🔥 Inferno Eye starting …")

    # 0. Wipe existing DB (Ephemeral mode)
    db_path = "./inferno_eye.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.info(f"🗑️ Wiped existing database: {db_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not wipe database: {e}")

    # 1. Init database
    await init_db()
    logger.info("✅ Database initialised")

    # 2. Load YOLO engine
    engine = YOLOEngine()
    await engine.load()
    set_engine(engine)
    logger.info("✅ YOLO engine ready")

    # 3. Mine genesis block if chain is empty
    async with AsyncSessionLocal() as db:
        blocks = await get_all_blocks(db)
        if not blocks:
            await add_block(db, "GENESIS", {"message": "Inferno Eye blockchain genesis"})
            logger.info("✅ Blockchain genesis block mined")

    logger.info("🚀 Inferno Eye ready — http://localhost:8000")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    from backend.ai.esp32_stream_reader import stop_reader
    await stop_reader()
    logger.info("👋 Inferno Eye shutdown complete")


app = FastAPI(
    title="Inferno Eye API",
    description="Hardware-integrated fire detection & emergency response system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files statically
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Register routers ───────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(sse.router)
app.include_router(camera.router)
app.include_router(video.router)
app.include_router(sensors.router)
app.include_router(detections.router)
app.include_router(alerts.router)
app.include_router(blockchain.router)
app.include_router(incidents.router)


@app.get("/health")
async def health():
    from backend.ai.yolo_engine import get_engine
    from backend.ai.esp32_stream_reader import get_status as esp32_status
    from backend.core.event_bus import event_bus

    eng = get_engine()
    return {
        "status": "ok",
        "yolo": "ready" if (eng and eng.is_ready()) else "loading",
        "esp32": esp32_status(),
        "sse_subscribers": event_bus.subscriber_count(),
    }
