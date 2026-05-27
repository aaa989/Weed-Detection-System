import base64
import time
import threading
import logging
from typing import Optional, List, Dict, Any
from enum import Enum

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import settings

logger = logging.getLogger(__name__)


class DetectionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class CameraDetectionService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.model: Optional[YOLO] = None
        self._status = DetectionStatus.IDLE
        self._status_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._detection_thread: Optional[threading.Thread] = None
        self._semaphore = threading.Semaphore(2)

        self._class_names: Dict[int, str] = {}
        self._chinese_names: Dict[str, str] = {}
        self._init_class_names()

    def _init_class_names(self):
        self._class_names = {
            0: "crop",
            1: "weed",
        }
        self._chinese_names = {
            "crop": "作物",
            "weed": "杂草",
        }

    def _load_model(self):
        if self.model is None:
            try:
                self.model = YOLO(settings.yolo_model_path)
                logger.info(f"Camera detection model loaded: {settings.yolo_model_path}")
            except Exception as e:
                logger.error(f"Failed to load camera detection model: {e}")

    @property
    def status(self) -> DetectionStatus:
        with self._status_lock:
            return self._status

    @status.setter
    def status(self, value: DetectionStatus):
        with self._status_lock:
            self._status = value

    def start_detection(self):
        with self._status_lock:
            if self._status == DetectionStatus.RUNNING:
                logger.warning("Detection is already running")
                return
            if self._status == DetectionStatus.PAUSED:
                self._status = DetectionStatus.RUNNING
                logger.info("Detection resumed")
                return

        self._stop_event.clear()
        self._load_model()
        self.status = DetectionStatus.RUNNING
        logger.info("Camera detection started")

    def stop_detection(self):
        self._stop_event.set()
        with self._status_lock:
            self._status = DetectionStatus.STOPPED
        logger.info("Camera detection stopped")

    def pause_detection(self):
        with self._status_lock:
            if self._status == DetectionStatus.RUNNING:
                self._status = DetectionStatus.PAUSED
                logger.info("Camera detection paused")

    def resume_detection(self):
        with self._status_lock:
            if self._status == DetectionStatus.PAUSED:
                self._status = DetectionStatus.RUNNING
                logger.info("Camera detection resumed")

    def detect_image(self, image_base64: str, frame_index: int = 0) -> Dict[str, Any]:
        start_time = time.time()

        if not image_base64:
            return {
                "success": False,
                "message": "No image data provided",
                "boxes": [],
                "frame_index": frame_index,
                "fps": 0,
                "detection_time": 0,
                "total_objects": 0,
            }

        if self.model is None:
            self._load_model()

        if self.model is None:
            return {
                "success": False,
                "message": "Model not loaded",
                "boxes": [],
                "frame_index": frame_index,
                "fps": 0,
                "detection_time": 0,
                "total_objects": 0,
            }

        acquired = self._semaphore.acquire(timeout=60)
        if not acquired:
            return {
                "success": False,
                "message": "Server busy, please try again later",
                "boxes": [],
                "frame_index": frame_index,
                "fps": 0,
                "detection_time": 0,
                "total_objects": 0,
            }

        try:
            if image_base64.startswith("data:image"):
                image_base64 = image_base64.split(",", 1)[1]

            image_bytes = base64.b64decode(image_base64)
            np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image is None:
                return {
                    "success": False,
                    "message": "Image decode failed",
                    "boxes": [],
                    "frame_index": frame_index,
                    "fps": 0,
                    "detection_time": 0,
                    "total_objects": 0,
                }

            results = self.model.predict(
                source=image,
                conf=0.5,
                iou=0.7,
                imgsz=320,
                save=False,
                verbose=False,
            )

            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    if confidence < 0.5:
                        continue
                    class_id = int(box.cls[0])
                    class_name = self._class_names.get(class_id, f"class_{class_id}")
                    chinese_name = self._chinese_names.get(class_name, class_name)

                    boxes.append({
                        "x1": round(x1, 1),
                        "y1": round(y1, 1),
                        "x2": round(x2, 1),
                        "y2": round(y2, 1),
                        "confidence": round(confidence, 3),
                        "class_id": class_id,
                        "class_name": class_name,
                        "chinese_name": chinese_name,
                    })

            detection_time = time.time() - start_time
            fps = 1.0 / detection_time if detection_time > 0 else 0

            return {
                "success": True,
                "message": "Detection completed",
                "boxes": boxes,
                "frame_index": frame_index,
                "fps": round(fps, 1),
                "detection_time": round(detection_time, 4),
                "total_objects": len(boxes),
            }

        except Exception as e:
            logger.error(f"Detection error: {str(e)}")
            return {
                "success": False,
                "message": f"Detection failed: {str(e)}",
                "boxes": [],
                "frame_index": frame_index,
                "fps": 0,
                "detection_time": 0,
                "total_objects": 0,
            }
        finally:
            self._semaphore.release()


camera_detection_service = CameraDetectionService()