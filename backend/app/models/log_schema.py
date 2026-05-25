# =============================================================================
# 日志与监控 Schema 模块
# =============================================================================
# 功能说明：
#   - 定义日志相关的 Pydantic 数据模型
#   - 用于 API 访问日志、模型推理日志、错误日志、接口耗时统计
# =============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# 日志级别枚举
# =============================================================================

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogType(str, Enum):
    """日志类型"""
    ACCESS = "access"
    INFERENCE = "inference"
    ERROR = "error"
    SYSTEM = "system"


# =============================================================================
# API 访问日志 Schema
# =============================================================================

class AccessLogBase(BaseModel):
    """访问日志基础模型"""
    method: str = Field(..., description="请求方法")
    path: str = Field(..., description="请求路径")
    status_code: int = Field(..., description="响应状态码")
    response_time: float = Field(..., description="响应时间（毫秒）")
    client_ip: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")
    user_id: Optional[str] = Field(None, description="用户ID")


class AccessLogCreate(AccessLogBase):
    """访问日志创建模型"""
    request_body: Optional[str] = Field(None, description="请求体")
    response_body: Optional[str] = Field(None, description="响应体")


class AccessLogResponse(BaseModel):
    """访问日志响应模型"""
    id: int
    method: str
    path: str
    status_code: int
    response_time: float
    client_ip: Optional[str]
    user_agent: Optional[str]
    user_id: Optional[str]
    request_body: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# 模型推理日志 Schema
# =============================================================================

class InferenceLogBase(BaseModel):
    """推理日志基础模型"""
    model_name: str = Field(..., description="模型名称")
    model_version: Optional[str] = Field(None, description="模型版本")
    image_url: str = Field(..., description="图片URL")
    detection_count: int = Field(0, description="检测到的目标数")
    confidence_avg: Optional[float] = Field(None, description="平均置信度")


class InferenceLogCreate(InferenceLogBase):
    """推理日志创建模型"""
    request_id: str = Field(..., description="请求ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    boxes: Optional[str] = Field(None, description="检测框JSON")


class InferenceLogResponse(BaseModel):
    """推理日志响应模型"""
    id: int
    request_id: str
    model_name: str
    model_version: Optional[str]
    image_url: str
    detection_count: int
    confidence_avg: Optional[float]
    inference_time: float
    user_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# 错误日志 Schema
# =============================================================================

class ErrorLogBase(BaseModel):
    """错误日志基础模型"""
    level: LogLevel = Field(..., description="错误级别")
    message: str = Field(..., description="错误消息")
    exception_type: Optional[str] = Field(None, description="异常类型")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")


class ErrorLogCreate(ErrorLogBase):
    """错误日志创建模型"""
    request_id: Optional[str] = Field(None, description="请求ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    path: Optional[str] = Field(None, description="请求路径")


class ErrorLogResponse(BaseModel):
    """错误日志响应模型"""
    id: int
    level: str
    message: str
    exception_type: Optional[str]
    stack_trace: Optional[str]
    request_id: Optional[str]
    user_id: Optional[str]
    path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# 统计 Schema
# =============================================================================

class EndpointStats(BaseModel):
    """接口统计模型"""
    path: str = Field(..., description="接口路径")
    method: str = Field(..., description="请求方法")
    total_calls: int = Field(0, description="总调用次数")
    avg_response_time: float = Field(0, description="平均响应时间（毫秒）")
    min_response_time: float = Field(0, description="最小响应时间")
    max_response_time: float = Field(0, description="最大响应时间")
    success_rate: float = Field(0, description="成功率（%）")


class DailyStats(BaseModel):
    """日统计模型"""
    date: str = Field(..., description="日期")
    total_requests: int = Field(0, description="总请求数")
    total_errors: int = Field(0, description="总错误数")
    avg_response_time: float = Field(0, description="平均响应时间")
    error_rate: float = Field(0, description="错误率（%）")


class InferenceStats(BaseModel):
    """推理统计模型"""
    total_inferences: int = Field(0, description="总推理次数")
    total_detections: int = Field(0, description="总检测数")
    avg_inference_time: float = Field(0, description="平均推理时间（毫秒）")
    avg_confidence: float = Field(0, description="平均置信度")


# =============================================================================
# 日志列表响应
# =============================================================================

class LogListResponse(BaseModel):
    """日志列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List = Field(default_factory=list, description="日志列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")


class StatsResponse(BaseModel):
    """统计响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: dict = Field(default_factory=dict, description="统计数据")
