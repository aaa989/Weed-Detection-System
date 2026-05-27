import os
import uuid
import logging
import threading
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.detection_service import detection_service
from app.services.minio_service import minio_service
from app.utils.file_utils import save_upload_file, ensure_directories

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection/batch", tags=["batch-detection"])

batch_tasks: dict = {}
_task_lock = threading.Lock()


class BatchTaskStatus(BaseModel):
    task_id: str
    status: str
    total: int
    completed: int
    failed: int
    results: list = []


@router.post("/upload")
async def batch_upload(
    files: List[UploadFile] = File(...),
    model_name: str = Form("rsod-yolo11n"),
    user_id: str = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per batch")

    ensure_directories()
    task_id = str(uuid.uuid4())

    saved_files = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            continue
        filename = await save_upload_file(file, settings.upload_dir)
        saved_files.append({
            "filename": file.filename or filename,
            "path": os.path.join(settings.upload_dir, filename),
            "status": "pending",
        })

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid image files")

    with _task_lock:
        batch_tasks[task_id] = {
            "status": "pending",
            "total": len(saved_files),
            "completed": 0,
            "failed": 0,
            "files": saved_files,
            "results": [],
        }

    thread = threading.Thread(
        target=_process_batch,
        args=(task_id, model_name, user_id),
        daemon=True,
    )
    thread.start()

    return {
        "success": True,
        "message": f"Batch task created, {len(saved_files)} files queued",
        "task_id": task_id,
        "total": len(saved_files),
    }


def _process_batch(task_id: str, model_name: str, user_id: str):
    with _task_lock:
        if task_id not in batch_tasks:
            return
        batch_tasks[task_id]["status"] = "processing"

    task_data = batch_tasks[task_id]
    files = task_data["files"]

    for i, file_info in enumerate(files):
        try:
            result = detection_service.detect_single_image(
                image_path=file_info["path"],
                user_id=user_id,
                model_name=model_name,
                minio_svc=minio_service,
            )
            file_info["status"] = "completed"
            file_info["result"] = {
                "detection_id": result.detection_id,
                "total_objects": result.total_objects,
                "detection_time": result.detection_time,
                "boxes": [
                    {
                        "class_name": b.class_name,
                        "chinese_name": b.chinese_name,
                        "confidence": b.confidence,
                    }
                    for b in result.boxes
                ],
            }
            with _task_lock:
                batch_tasks[task_id]["completed"] += 1
                batch_tasks[task_id]["results"].append(file_info)
        except Exception as e:
            logger.error(f"Batch detection failed for {file_info['filename']}: {e}")
            file_info["status"] = "failed"
            file_info["error"] = str(e)
            with _task_lock:
                batch_tasks[task_id]["failed"] += 1
                batch_tasks[task_id]["results"].append(file_info)
        finally:
            try:
                os.remove(file_info["path"])
            except Exception:
                pass

    with _task_lock:
        batch_tasks[task_id]["status"] = "completed"


@router.get("/status/{task_id}")
def get_batch_status(task_id: str):
    with _task_lock:
        task = batch_tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "success": True,
        "task_id": task_id,
        "status": task["status"],
        "total": task["total"],
        "completed": task["completed"],
        "failed": task["failed"],
        "results": task.get("results", []),
    }