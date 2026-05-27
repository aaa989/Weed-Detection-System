import os
import time
import uuid
import threading
import logging
from typing import Optional, Dict

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import settings

logger = logging.getLogger(__name__)


class VideoDetectionService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.model: Optional[YOLO] = None

        self._class_names = {
            0: "crop", 1: "weed",
        }
        self._chinese_names = {
            "crop": "作物", "weed": "杂草",
        }
        self._active_tasks: Dict[str, dict] = {}
        self._tasks_lock = threading.Lock()

    def _load_model(self):
        if self.model is None:
            self.model = YOLO(settings.yolo_model_path)
            logger.info(f"Video detection model loaded: {settings.yolo_model_path}")

    def start_detection(self, video_path: str, output_dir: str,
                        frame_interval: int = 5, model_name: str = "rsod-yolo11n") -> str:
        self._load_model()
        task_id = str(uuid.uuid4())

        with self._tasks_lock:
            self._active_tasks[task_id] = {
                "status": "processing",
                "progress": 0,
                "total_frames": 0,
                "processed_frames": 0,
                "detections": [],
                "output_video_path": "",
                "start_time": time.time(),
            }

        thread = threading.Thread(
            target=self._process_video,
            args=(task_id, video_path, output_dir, frame_interval),
            daemon=True,
        )
        thread.start()
        return task_id

    def _process_video(self, task_id: str, video_path: str,
                       output_dir: str, frame_interval: int):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self._set_task_error(task_id, "Cannot open video file")
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_path = os.path.join(output_dir, f"{task_id}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        with self._tasks_lock:
            self._active_tasks[task_id]["total_frames"] = total_frames
            self._active_tasks[task_id]["output_video_path"] = output_path

        frame_idx = 0
        detections = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                try:
                    results = self.model.predict(
                        source=frame,
                        conf=0.5,
                        iou=0.7,
                        imgsz=320,
                        save=False,
                        verbose=False,
                    )

                    frame_detections = []
                    for result in results:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            class_name = self._class_names.get(class_id, f"class_{class_id}")
                            chinese_name = self._chinese_names.get(class_name, class_name)

                            frame_detections.append({
                                "frame": frame_idx,
                                "x1": round(x1, 1), "y1": round(y1, 1),
                                "x2": round(x2, 1), "y2": round(y2, 1),
                                "confidence": round(confidence, 3),
                                "class_id": class_id,
                                "class_name": class_name,
                                "chinese_name": chinese_name,
                            })

                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (64, 158, 255), 2)
                            label = f"{chinese_name} {confidence:.1%}"
                            cv2.putText(frame, label, (int(x1), int(y1) - 5),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (64, 158, 255), 1)

                    detections.extend(frame_detections)
                    with self._tasks_lock:
                        self._active_tasks[task_id]["detections"] = detections

                except Exception as e:
                    logger.error(f"Frame {frame_idx} detection error: {e}")

            out.write(frame)
            frame_idx += 1

            with self._tasks_lock:
                self._active_tasks[task_id]["processed_frames"] = frame_idx
                if total_frames > 0:
                    self._active_tasks[task_id]["progress"] = min(
                        int(frame_idx / total_frames * 100), 99
                    )

        cap.release()
        out.release()

        with self._tasks_lock:
            self._active_tasks[task_id]["status"] = "completed"
            self._active_tasks[task_id]["progress"] = 100
            self._active_tasks[task_id]["detections"] = detections
            self._active_tasks[task_id]["elapsed"] = time.time() - self._active_tasks[task_id]["start_time"]

        logger.info(f"Video detection completed. Task: {task_id}, "
                    f"Frames: {frame_idx}, Detections: {len(detections)}")

        try:
            os.remove(video_path)
        except Exception:
            pass

    def _set_task_error(self, task_id: str, error: str):
        with self._tasks_lock:
            if task_id in self._active_tasks:
                self._active_tasks[task_id]["status"] = "failed"
                self._active_tasks[task_id]["error"] = error

    def get_status(self, task_id: str) -> Optional[dict]:
        with self._tasks_lock:
            return self._active_tasks.get(task_id)


video_detection_service = VideoDetectionService()