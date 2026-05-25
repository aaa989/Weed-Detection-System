# =============================================================================
# 数据集管理 API 路由模块
# =============================================================================
# 功能说明：
#   - 样本列表、类别统计、样本上传、标注管理
#
# API 接口列表：
#   GET  /api/dataset/samples           - 获取样本列表
#   POST /api/dataset/samples          - 创建样本
#   GET  /api/dataset/samples/{id}      - 获取单个样本
#   PUT  /api/dataset/samples/{id}      - 更新样本
#   DELETE /api/dataset/samples/{id}    - 删除样本
#   POST /api/dataset/upload            - 上传图片
#   POST /api/dataset/batch-upload      - 批量上传
#   GET  /api/dataset/statistics        - 获取统计信息
#   GET  /api/dataset/classes           - 获取类别列表
#   GET  /api/dataset/annotations/{id}  - 获取样本标注
#   POST /api/dataset/annotations       - 创建标注
#   DELETE /api/dataset/annotations/{id} - 删除标注
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import os
import uuid
import json

from app.models.database import get_db
from app.models.dataset_schema import (
    SampleCreate, SampleUpdate, SampleResponse, SampleListResponse,
    AnnotationCreate, AnnotationBox,
    ClassStatistics, DatasetStatisticsResponse,
    FileUploadResponse, BatchUploadResponse
)
from app.crud.dataset_crud import dataset_crud
from app.core.security import get_current_user, require_role

# 创建 API 路由实例
router = APIRouter(prefix="/api/dataset", tags=["数据集管理"])

# 上传目录配置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/dataset")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


# =============================================================================
# 辅助函数
# =============================================================================

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def save_uploaded_file(file: UploadFile) -> tuple:
    """保存上传的文件"""
    if not allowed_file(file.filename):
        raise ValueError(f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")
    
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)
    
    file_size = len(content)
    
    return unique_filename, file_path, file_size


# =============================================================================
# 样本管理接口
# =============================================================================

@router.get("/samples", response_model=SampleListResponse)
async def get_samples(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    class_name: Optional[str] = Query(None, description="按类别筛选"),
    split_type: Optional[str] = Query(None, description="按划分筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    search: Optional[str] = Query(None, description="搜索文件名"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取样本列表
    """
    try:
        skip = (page - 1) * page_size
        
        samples = dataset_crud.get_samples(
            db=db,
            skip=skip,
            limit=page_size,
            class_name=class_name,
            split_type=split_type,
            status=status,
            search=search
        )
        
        total = dataset_crud.count_samples(
            db=db,
            class_name=class_name,
            split_type=split_type,
            status=status
        )
        
        sample_list = [
            SampleResponse(
                id=s["id"],
                filename=s["filename"],
                image_url=s["image_url"],
                class_name=s["class_name"],
                split_type=s["split_type"],
                status=s["status"],
                width=s.get("width") or 0,
                height=s.get("height") or 0,
                file_size=s.get("file_size") or 0,
                annotation_count=s.get("annotation_count") or 0,
                created_at=s.get("created_at"),
                updated_at=s.get("updated_at")
            )
            for s in samples
        ]
        
        return SampleListResponse(
            success=True,
            message="获取成功",
            data=sample_list,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取样本列表失败: {str(e)}"
        )


@router.post("/samples", response_model=SampleResponse)
async def create_sample(
    request: SampleCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建样本记录
    """
    try:
        sample = dataset_crud.create_sample(
            db=db,
            filename=request.filename,
            image_url=request.image_url,
            class_name=request.class_name.value,
            width=request.width,
            height=request.height,
            file_size=request.file_size,
            split_type=request.split_type.value,
            uploader_id=current_user.get("user_id"),
            notes=request.notes
        )
        
        return SampleResponse(
            id=sample["id"],
            filename=sample["filename"],
            image_url=sample["image_url"],
            class_name=sample["class_name"],
            split_type=sample["split_type"],
            status=sample["status"],
            width=sample.get("width") or 0,
            height=sample.get("height") or 0,
            file_size=sample.get("file_size") or 0,
            annotation_count=sample.get("annotation_count") or 0,
            created_at=sample.get("created_at"),
            updated_at=sample.get("updated_at")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建样本失败: {str(e)}"
        )


@router.get("/samples/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个样本详情
    """
    sample = dataset_crud.get_sample_by_id(db, sample_id)
    
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="样本不存在"
        )
    
    return SampleResponse(
        id=sample["id"],
        filename=sample["filename"],
        image_url=sample["image_url"],
        class_name=sample["class_name"],
        split_type=sample["split_type"],
        status=sample["status"],
        width=sample.get("width") or 0,
        height=sample.get("height") or 0,
        file_size=sample.get("file_size") or 0,
        annotation_count=sample.get("annotation_count") or 0,
        created_at=sample.get("created_at"),
        updated_at=sample.get("updated_at")
    )


@router.put("/samples/{sample_id}", response_model=SampleResponse)
async def update_sample(
    sample_id: int,
    request: SampleUpdate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新样本信息
    """
    try:
        sample = dataset_crud.update_sample(
            db=db,
            sample_id=sample_id,
            class_name=request.class_name.value if request.class_name else None,
            split_type=request.split_type.value if request.split_type else None,
            status=request.status.value if request.status else None,
            notes=request.notes
        )
        
        if not sample:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="样本不存在"
            )
        
        return SampleResponse(
            id=sample["id"],
            filename=sample["filename"],
            image_url=sample["image_url"],
            class_name=sample["class_name"],
            split_type=sample["split_type"],
            status=sample["status"],
            width=sample.get("width") or 0,
            height=sample.get("height") or 0,
            file_size=sample.get("file_size") or 0,
            annotation_count=sample.get("annotation_count") or 0,
            created_at=sample.get("created_at"),
            updated_at=sample.get("updated_at")
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新样本失败: {str(e)}"
        )


@router.delete("/samples/{sample_id}")
async def delete_sample(
    sample_id: int,
    current_user: Dict = Depends(require_role(["admin", "user"])),
    db: Session = Depends(get_db)
):
    """
    删除样本
    """
    success = dataset_crud.delete_sample(db, sample_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="样本不存在"
        )
    
    return {"success": True, "message": "删除成功"}


# =============================================================================
# 文件上传接口
# =============================================================================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    class_name: str = Query(..., description="杂草类别"),
    split_type: str = Query("train", description="数据集划分"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传单个图片文件
    """
    try:
        unique_filename, file_path, file_size = save_uploaded_file(file)
        
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
        except:
            width, height = 0, 0
        
        sample = dataset_crud.create_sample(
            db=db,
            filename=file.filename,
            image_url=f"/api/dataset/files/{unique_filename}",
            class_name=class_name,
            width=width,
            height=height,
            file_size=file_size,
            split_type=split_type,
            uploader_id=current_user.get("user_id")
        )
        
        return FileUploadResponse(
            success=True,
            message="上传成功",
            filename=unique_filename,
            file_url=sample["image_url"],
            file_size=file_size
        )
    
    except ValueError as e:
        return FileUploadResponse(
            success=False,
            message=str(e),
            filename="",
            file_url="",
            file_size=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    class_name: str = Query(..., description="杂草类别"),
    split_type: str = Query("train", description="数据集划分"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量上传图片文件
    """
    uploaded = []
    failed = 0
    
    for file in files:
        try:
            unique_filename, file_path, file_size = save_uploaded_file(file)
            
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    width, height = img.size
            except:
                width, height = 0, 0
            
            sample = dataset_crud.create_sample(
                db=db,
                filename=file.filename,
                image_url=f"/api/dataset/files/{unique_filename}",
                class_name=class_name,
                width=width,
                height=height,
                file_size=file_size,
                split_type=split_type,
                uploader_id=current_user.get("user_id")
            )
            
            uploaded.append(FileUploadResponse(
                success=True,
                message="上传成功",
                filename=unique_filename,
                file_url=sample["image_url"],
                file_size=file_size
            ))
        
        except Exception as e:
            failed += 1
            uploaded.append(FileUploadResponse(
                success=False,
                message=str(e),
                filename=file.filename,
                file_url="",
                file_size=0
            ))
    
    return BatchUploadResponse(
        success=True,
        message=f"上传完成，成功 {len(uploaded) - failed} 个，失败 {failed} 个",
        uploaded_count=len(uploaded) - failed,
        failed_count=failed,
        files=uploaded
    )


# =============================================================================
# 统计和类别接口
# =============================================================================

@router.get("/statistics", response_model=DatasetStatisticsResponse)
async def get_statistics(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据集统计信息
    """
    try:
        stats = dataset_crud.get_statistics(db)
        
        class_stats = [
            ClassStatistics(
                class_name=c["class_name"],
                count=c["count"],
                percentage=c["percentage"]
            )
            for c in stats["class_statistics"]
        ]
        
        return DatasetStatisticsResponse(
            success=True,
            message="获取成功",
            total_samples=stats["total_samples"],
            total_annotations=stats["total_annotations"],
            train_count=stats["train_count"],
            val_count=stats["val_count"],
            test_count=stats["test_count"],
            class_statistics=class_stats
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/classes")
async def get_classes():
    """
    获取杂草类别列表
    """
    return {
        "success": True,
        "data": [
            {"id": "broadleaf", "name": "阔叶杂草", "description": "双子叶杂草"},
            {"id": "grass", "name": "禾本科杂草", "description": "单子叶杂草"},
            {"id": "sedge", "name": "莎草科杂草", "description": "莎草科杂草"},
            {"id": "other", "name": "其他杂草", "description": "其他类型杂草"}
        ]
    }


# =============================================================================
# 标注管理接口
# =============================================================================

@router.get("/annotations/{sample_id}")
async def get_sample_annotations(
    sample_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取样本的所有标注
    """
    annotations = dataset_crud.get_annotations_by_sample(db, sample_id)
    
    result = []
    for ann in annotations:
        boxes = json.loads(ann["annotation_data"])
        result.append({
            "id": ann["id"],
            "sample_id": ann["sample_id"],
            "boxes": boxes,
            "annotator": ann["annotator"],
            "created_at": str(ann["created_at"]) if ann.get("created_at") else None,
            "updated_at": str(ann["updated_at"]) if ann.get("updated_at") else None
        })
    
    return {
        "success": True,
        "message": "获取成功",
        "data": result
    }


@router.post("/annotations")
async def create_annotation(
    request: AnnotationCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建标注
    """
    try:
        boxes = [box.dict() for box in request.boxes]
        
        annotation = dataset_crud.create_annotation(
            db=db,
            sample_id=request.sample_id,
            annotator=request.annotator,
            boxes=boxes
        )
        
        return {
            "success": True,
            "message": "标注创建成功",
            "annotation_id": annotation["id"]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建标注失败: {str(e)}"
        )


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除标注
    """
    success = dataset_crud.delete_annotation(db, annotation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    return {"success": True, "message": "删除成功"}
