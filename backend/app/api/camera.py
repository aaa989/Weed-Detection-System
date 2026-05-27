import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.camera_detection_service import camera_detection_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection/camera", tags=["camera-detection"])


class CameraDetectRequest(BaseModel):
    image: str
    frame_index: int = 0


class DetectionBoxResult(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    chinese_name: str


class CameraDetectResponse(BaseModel):
    success: bool
    message: str
    boxes: list[DetectionBoxResult] = []
    frame_index: int = 0
    fps: float = 0
    detection_time: float = 0
    total_objects: int = 0


class StatusResponse(BaseModel):
    status: str
    message: str


@router.post("/detect", response_model=CameraDetectResponse)
async def detect_frame(request: CameraDetectRequest):
    result = camera_detection_service.detect_image(
        image_base64=request.image,
        frame_index=request.frame_index,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/status", response_model=StatusResponse)
async def get_status():
    status = camera_detection_service.status
    return StatusResponse(
        status=status.value,
        message=f"Camera detection service is {status.value}",
    )


@router.post("/start")
async def start_detection():
    camera_detection_service.start_detection()
    return {"success": True, "message": "Detection started"}


@router.post("/stop")
async def stop_detection():
    camera_detection_service.stop_detection()
    return {"success": True, "message": "Detection stopped"}


@router.post("/pause")
async def pause_detection():
    camera_detection_service.pause_detection()
    return {"success": True, "message": "Detection paused"}


@router.post("/resume")
async def resume_detection():
    camera_detection_service.resume_detection()
    return {"success": True, "message": "Detection resumed"}