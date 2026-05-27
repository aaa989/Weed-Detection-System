import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.detection_service import detection_service
from app.models.schemas import RealtimeDetectionResponse
from app.utils.common import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/video-detection", tags=["video-detection"])


@router.post("/realtime-frame", response_model=RealtimeDetectionResponse)
async def detect_realtime_frame(
    file: UploadFile = File(...),
    model_name: str = Form("rsod-yolo11n"),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.7)
):
    try:
        contents = await file.read()

        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")

        result = detection_service.detect_frame_realtime(
            image=image,
            model_name=model_name,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold
        )

        return RealtimeDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"[实时帧检测错误] 异常类型: {type(e).__name__}")
        logger.error(f"[实时帧检测错误] 异常信息: {str(e)}")
        logger.error(f"[实时帧检测错误] 堆栈信息: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"实时帧检测失败: {str(e)}"
        )
