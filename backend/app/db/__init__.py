# =============================================================================
# 数据库模块
# =============================================================================
# 功能说明：
#   - 数据库连接管理
#   - ORM模型定义
#   - 数据库初始化
# =============================================================================

from app.db.models import (
    Base,
    User,
    DatasetSample,
    SampleAnnotation,
    DetectionRecord,
    DetectionBox,
    SystemConfig,
    APIAccessLog,
    InferenceLog
)

from app.db.database import (
    engine,
    SessionLocal,
    get_db,
    get_db_context,
    init_db,
    drop_db,
    recreate_db,
    DatabaseMiddleware
)

__all__ = [
    # 模型
    "Base",
    "User",
    "DatasetSample",
    "SampleAnnotation",
    "DetectionRecord",
    "DetectionBox",
    "SystemConfig",
    "APIAccessLog",
    "InferenceLog",
    # 数据库
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_context",
    "init_db",
    "drop_db",
    "recreate_db",
    "DatabaseMiddleware"
]
