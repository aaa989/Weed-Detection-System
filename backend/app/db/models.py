# =============================================================================
# SQLAlchemy ORM 模型
# =============================================================================
# 功能说明：
#   - 定义数据库表结构的Python对象
#   - 支持SQLAlchemy ORM操作
#   - 与现有模块完全兼容
# =============================================================================

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

# 创建基类
Base = declarative_base()


# =============================================================================
# 用户模型 (users)
# =============================================================================

class User(Base):
    """用户表模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    role = Column(String(20), default="user")
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    detection_records = relationship("DetectionRecord", back_populates="user")
    uploaded_samples = relationship("DatasetSample", back_populates="uploader")
    annotations = relationship("SampleAnnotation", back_populates="annotator")
    
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user', 'guest')", name="check_user_role"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


# =============================================================================
# 数据集样本模型 (dataset_samples)
# =============================================================================

class DatasetSample(Base):
    """数据集样本表模型"""
    __tablename__ = "dataset_samples"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_key = Column(String(500))
    class_name = Column(String(50), nullable=False, index=True)
    class_id = Column(Integer)
    split_type = Column(String(20), default="train")
    status = Column(String(20), default="pending")
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    notes = Column(Text)
    annotation_count = Column(Integer, default=0)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    uploader = relationship("User", foreign_keys=[uploader_id], back_populates="uploaded_samples")
    annotations = relationship("SampleAnnotation", back_populates="sample", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("filename", "split_type", name="uk_dataset_samples_filename_split"),
        CheckConstraint("split_type IN ('train', 'val', 'test')", name="check_split_type"),
        CheckConstraint("status IN ('pending', 'annotated', 'approved', 'rejected')", name="check_sample_status"),
    )
    
    def __repr__(self):
        return f"<DatasetSample(id={self.id}, filename='{self.filename}', class_name='{self.class_name}')>"


# =============================================================================
# 样本标注模型 (sample_annotations)
# =============================================================================

class SampleAnnotation(Base):
    """样本标注表模型"""
    __tablename__ = "sample_annotations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey("dataset_samples.id", ondelete="CASCADE"), nullable=False, index=True)
    annotator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    annotation_data = Column(JSONB, nullable=False)
    annotation_type = Column(String(20), default="bbox")
    is_valid = Column(Boolean, default=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    validated_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    sample = relationship("DatasetSample", back_populates="annotations")
    annotator = relationship("User", foreign_keys=[annotator_id])
    
    __table_args__ = (
        CheckConstraint("annotation_type IN ('bbox', 'polygon', 'mask')", name="check_annotation_type"),
    )
    
    def __repr__(self):
        return f"<SampleAnnotation(id={self.id}, sample_id={self.sample_id})>"


# =============================================================================
# 检测记录模型 (detection_records)
# =============================================================================

class DetectionRecord(Base):
    """检测记录表模型"""
    __tablename__ = "detection_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20), default="1.0.0")
    model_path = Column(String(500))
    
    # 图片信息
    original_image_url = Column(String(500))
    original_image_key = Column(String(500))
    result_image_url = Column(String(500))
    result_image_key = Column(String(500))
    
    # 统计信息
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float)
    confidence_avg = Column(Float)
    
    # 错误信息
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # 批处理信息
    batch_id = Column(String(100), index=True)
    batch_total = Column(Integer, default=0)
    batch_processed = Column(Integer, default=0)
    
    # 元数据
    metadata = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    user = relationship("User", back_populates="detection_records")
    boxes = relationship("DetectionBox", back_populates="record", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("type IN ('single', 'batch', 'folder', 'video')", name="check_detection_type"),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="check_detection_status"),
    )
    
    def __repr__(self):
        return f"<DetectionRecord(id={self.id}, type='{self.type}', status='{self.status}')>"


# =============================================================================
# 检测目标框模型 (detection_boxes)
# =============================================================================

class DetectionBox(Base):
    """检测目标框表模型"""
    __tablename__ = "detection_boxes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("detection_records.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 边界框坐标
    x_min = Column(Float, nullable=False)
    y_min = Column(Float, nullable=False)
    x_max = Column(Float, nullable=False)
    y_max = Column(Float, nullable=False)
    
    # 类别信息
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False)
    chinese_name = Column(String(50))
    
    # 置信度
    confidence = Column(Float, nullable=False)
    
    # 分割信息
    segmentation = Column(JSONB)
    area = Column(Float)
    
    # 元数据
    metadata = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    record = relationship("DetectionRecord", back_populates="boxes")
    
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
    )
    
    def __repr__(self):
        return f"<DetectionBox(id={self.id}, class_name='{self.class_name}', confidence={self.confidence})>"
    
    @property
    def width(self):
        return self.x_max - self.x_min
    
    @property
    def height(self):
        return self.y_max - self.y_min


# =============================================================================
# 系统配置模型 (system_config)
# =============================================================================

class SystemConfig(Base):
    """系统配置表模型"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text)
    value_type = Column(String(20), default="string")
    config_group = Column(String(50), default="general", index=True)
    description = Column(Text)
    is_public = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("value_type IN ('string', 'number', 'boolean', 'json')", name="check_value_type"),
    )
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key='{self.config_key}', value='{self.config_value}')>"
    
    def get_typed_value(self):
        """获取类型化后的值"""
        if self.value_type == "number":
            try:
                return float(self.config_value)
            except:
                return self.config_value
        elif self.value_type == "boolean":
            return self.config_value.lower() in ("true", "1", "yes")
        elif self.value_type == "json":
            import json
            try:
                return json.loads(self.config_value)
            except:
                return self.config_value
        return self.config_value


# =============================================================================
# API访问日志模型 (api_access_logs)
# =============================================================================

class APIAccessLog(Base):
    """API访问日志表模型"""
    __tablename__ = "api_access_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    # 请求信息
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSONB)
    request_body = Column(JSONB)
    
    # 响应信息
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)
    response_size = Column(Integer)
    
    # 客户端信息
    client_ip = Column(String(50))
    user_agent = Column(Text)
    
    # 错误信息
    error_message = Column(Text)
    error_stack = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<APIAccessLog(id={self.id}, method='{self.method}', path='{self.path}')>"


# =============================================================================
# 推理日志模型 (inference_logs)
# =============================================================================

class InferenceLog(Base):
    """推理日志表模型"""
    __tablename__ = "inference_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), ForeignKey("detection_records.id", ondelete="SET NULL"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    # 模型信息
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(20))
    
    # 输入信息
    image_url = Column(String(500))
    image_key = Column(String(500))
    
    # 输出信息
    detection_count = Column(Integer, default=0)
    confidence_avg = Column(Float)
    inference_time = Column(Float, nullable=False)
    
    # 结果摘要
    result_summary = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    record = relationship("DetectionRecord")
    user = relationship("User")
    
    def __repr__(self):
        return f"<InferenceLog(id={self.id}, request_id='{self.request_id}', model_name='{self.model_name}')>"


# =============================================================================
# 模型列表（用于批量操作）
# =============================================================================

__all__ = [
    "Base",
    "User",
    "DatasetSample",
    "SampleAnnotation",
    "DetectionRecord",
    "DetectionBox",
    "SystemConfig",
    "APIAccessLog",
    "InferenceLog"
]
