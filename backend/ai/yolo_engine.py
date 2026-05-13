# backend/ai/yolo_engine.py
"""
YOLOv8 fire/smoke detection engine.
Primary model: keremberke/yolov8n-fire-detection (HuggingFace, ~6 MB).
Fallback:      HSV color-based fire detector (no model download required).
"""
import os
import base64
import logging
from typing import List, Optional

import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", 0.30))
MODEL_REPO = os.getenv("MODEL_REPO", "keremberke/yolov8n-fire-detection")
MODEL_FILE = os.getenv("MODEL_FILE", "best.pt")


class BBox:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x, self.y, self.w, self.h = x, y, w, h


class DetectionItem:
    def __init__(self, label: str, confidence: float, bbox: BBox):
        self.label = label
        self.confidence = confidence
        self.bbox = bbox


class YOLOEngine:
    def __init__(self):
        self._model = None
        self._using_fallback = False

    async def load(self):
        """Load YOLOv8 model or fall back to HSV detector."""
        try:
            from huggingface_hub import hf_hub_download
            from ultralytics import YOLO

            logger.info(f"Downloading model {MODEL_REPO}/{MODEL_FILE} …")
            model_path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
            self._model = YOLO(model_path)
            logger.info("✅ YOLOv8 fire model loaded successfully")
        except Exception as exc:
            logger.warning(f"YOLOv8 load failed ({exc}). Using HSV fallback detector.")
            self._model = None
            self._using_fallback = True

    def is_ready(self) -> bool:
        return self._model is not None or self._using_fallback

    def run(self, frame: np.ndarray) -> tuple[List[DetectionItem], np.ndarray]:
        """
        Run inference on a BGR OpenCV frame.
        Returns (detections, annotated_frame).
        """
        if self._model is not None:
            return self._run_yolo(frame)
        return self._run_hsv(frame)

    def _run_yolo(self, frame: np.ndarray):
        results = self._model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        detections: List[DetectionItem] = []
        annotated = frame.copy()

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = r.names.get(cls_id, "fire")
                
                # Filter: Only allow fire detections
                if label != "fire":
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1

                detections.append(DetectionItem(label, conf, BBox(x1, y1, w, h)))

                color = (0, 0, 255)  # Always red for fire
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                text = f"{label.upper()} {conf:.0%}"
                cv2.putText(annotated, text, (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return detections, annotated

    def _run_hsv(self, frame: np.ndarray):
        """HSV color-based fire/smoke detection fallback."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detections: List[DetectionItem] = []
        annotated = frame.copy()

        # Fire: orange-red hues
        lower_fire = np.array([0, 120, 150])
        upper_fire = np.array([30, 255, 255])
        mask_fire = cv2.inRange(hsv, lower_fire, upper_fire)

        for mask, label, color in [
            (mask_fire,  "fire",  (0, 0, 255)),
        ]:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 1500:
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                conf = min(0.95, area / (frame.shape[0] * frame.shape[1]) * 20)
                if conf < CONFIDENCE_THRESHOLD:
                    continue
                detections.append(DetectionItem(label, conf, BBox(x, y, w, h)))
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                cv2.putText(annotated, f"{label.upper()} {conf:.0%}",
                            (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return detections, annotated


def frame_to_base64(frame: np.ndarray) -> str:
    """Encode OpenCV BGR frame to base64 JPEG string."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def base64_to_frame(b64: str) -> Optional[np.ndarray]:
    """Decode base64 JPEG string to OpenCV BGR frame."""
    try:
        data = base64.b64decode(b64)
        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


# ── Module-level singleton ──────────────────────────────────────────────────
_engine: Optional[YOLOEngine] = None


def get_engine() -> YOLOEngine:
    return _engine


def set_engine(engine: YOLOEngine):
    global _engine
    _engine = engine
