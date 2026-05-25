# =============================================================================
# 数据集管理 Schema 模块
# =============================================================================
# 功能说明：
#   - 定义数据集相关的 Pydantic 数据模型
#   - 用于样本列表、类别统计、样本上传、标注管理
# =============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# 类别和数据集划分枚举
# =============================================================================

class WeedClass(str, Enum):
    """杂草类别枚举"""
    BROADLEAF = "broadleaf"
    GRASS = "grass"
    SEDGE = "sedge"
    OTHER = "other"


class SplitType(str, Enum):
    """数据集划分类型"""
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class SampleStatus(str, Enum):
    """样本状态"""
    PENDING = "pending"
    ANNOTATED = "annotated"
    APPROVED = "approved"
    REJECTED = "rejected"


# =============================================================================
# 样本相关 Schema
# =============================================================================

class SampleBase(BaseModel):
    """样本基础模型"""
    filename: str = Field(..., description="文件名")
    class_name: WeedClass = Field(..., description="杂草类别")
    split_type: SplitType = Field(SplitType.TRAIN, description="数据集划分")
    notes: Optional[str] = Field(None, description="备注")


class SampleCreate(SampleBase):
    """样本创建请求模型"""
    image_url: str = Field(..., description="图片URL")
    width: int = Field(..., description="图片宽度")
    height: int = Field(..., description="图片高度")
    file_size: int = Field(..., description="文件大小（字节）")


class SampleUpdate(BaseModel):
    """样本更新请求模型"""
    class_name: Optional[WeedClass] = Field(None, description="杂草类别")
    split_type: Optional[SplitType] = Field(None, description="数据集划分")
    status: Optional[SampleStatus] = Field(None, description="样本状态")
    notes: Optional[str] = Field(None, description="备注")


class AnnotationBox(BaseModel):
    """标注框模型"""
    x_min: float = Field(..., description="左上角X坐标")
    y_min: float = Field(..., description="左上角Y坐标")
    x_max: float = Field(..., description="右下角X坐标")
    y_max: float = Field(..., description="右下角Y坐标")
    class_name: WeedClass = Field(..., description="杂草类别")
    confidence: Optional[float] = Field(None, description="置信度")


class AnnotationCreate(BaseModel):
    """标注创建请求模型"""
    sample_id: int = Field(..., description="样本ID")
    boxes: List[AnnotationBox] = Field(..., description="标注框列表")
    annotator: str = Field(..., description="标注人")


class SampleResponse(BaseModel):
    """样本响应模型"""
    id: int
    filename: str
    image_url: str
    class_name: str
    split_type: str
    status: str
    width: int
    height: int
    file_size: int
    annotation_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SampleListResponse(BaseModel):
    """样本列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[SampleResponse] = Field(default_factory=list, description="样本列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")


# =============================================================================
# 类别统计 Schema
# =============================================================================

class ClassStatistics(BaseModel):
    """类别统计模型"""
    class_name: str = Field(..., description="杂草类别")
    count: int = Field(..., description="样本数量")
    percentage: float = Field(..., description="占比")


class DatasetStatisticsResponse(BaseModel):
    """数据集统计响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    total_samples: int = Field(0, description="总样本数")
    total_annotations: int = Field(0, description="总标注数")
    train_count: int = Field(0, description="训练集数量")
    val_count: int = Field(0, description="验证集数量")
    test_count: int = Field(0, description="测试集数量")
    class_statistics: List[ClassStatistics] = Field(default_factory=list, description="类别统计")


# =============================================================================
# 文件上传 Schema
# =============================================================================

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    filename: str = Field(..., description="保存的文件名")
    file_url: str = Field(..., description="文件访问URL")
    file_size: int = Field(..., description="文件大小")


class BatchUploadResponse(BaseModel):
    """批量上传响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    uploaded_count: int = Field(0, description="成功上传数量")
    failed_count: int = Field(0, description="失败数量")
    files: List[FileUploadResponse] = Field(default_factory=list, description="上传结果列表")
