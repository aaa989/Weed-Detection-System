import os
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.services.video_service import video_detection_service
from app.utils.file_utils import save_upload_file, ensure_directories

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection/video", tags=["video-detection"])


class VideoTaskResponse(BaseModel):
    success: bool
    message: str
    task_id: str = ""


@router.post("/upload", response_model=VideoTaskResponse)
async def video_upload_and_detect(
    file: UploadFile = File(...),
    frame_interval: int = Form(10),
    model_name: str = Form("rsod-yolo11n"),
):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Please upload a valid video file")

    ensure_directories()

    video_dir = os.path.join(settings.upload_dir, "videos")
    os.makedirs(video_dir, exist_ok=True)

    result_dir = os.path.join(settings.upload_dir, "video_results")
    os.makedirs(result_dir, exist_ok=True)

    filename = await save_upload_file(file, video_dir)
    video_path = os.path.join(video_dir, filename)

    task_id = video_detection_service.start_detection(
        video_path=video_path,
        output_dir=result_dir,
        frame_interval=frame_interval,
        model_name=model_name,
    )

    return VideoTaskResponse(
        success=True,
        message="Video detection task started",
        task_id=task_id,
    )


@router.get("/status/{task_id}")
def get_video_status(task_id: str):
    task = video_detection_service.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, **task}


@router.get("/download/{task_id}")
def download_video(task_id: str):
    task = video_detection_service.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")

    output_path = task.get("output_video_path", "")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output video not found")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"detection_result_{task_id}.mp4",
    )