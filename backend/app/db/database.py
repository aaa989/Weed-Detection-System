# =============================================================================
# 数据库连接配置
# =============================================================================
# 功能说明：
#   - 数据库引擎配置
#   - 会话管理
#   - 依赖注入
#   - 连接池配置
# =============================================================================

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager

from app.config import settings

# =============================================================================
# 数据库URL配置
# =============================================================================

# 构建PostgreSQL数据库连接URL
DATABASE_URL = (
    f"postgresql+psycopg2://{settings.database.username}:{settings.database.password}"
    f"@{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

# =============================================================================
# 引擎配置
# =============================================================================

# 根据环境选择连接池类型
if os.getenv("ENVIRONMENT", "development") == "production":
    # 生产环境：使用连接池
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,              # 连接池大小
        max_overflow=30,           # 最大溢出连接数
        pool_pre_ping=True,        # 连接前ping检测
        pool_recycle=3600,         # 连接回收时间（秒）
        echo=False,                # 是否打印SQL语句
        logging_name="DatabaseEngine"
    )
else:
    # 开发环境：使用NullPool（方便调试）
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,                # 开发环境可设为True查看SQL
        logging_name="DatabaseEngine"
    )

# =============================================================================
# 会话工厂配置
# =============================================================================

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 提交后不使对象过期
)

# =============================================================================
# 依赖注入函数
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入函数
    
    用法：在FastAPI路由中使用 Depends(get_db) 注入数据库会话
    
    示例：
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    上下文管理器方式的数据库会话
    
    用法：
        with get_db_context() as db:
            user = db.query(User).first()
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# 数据库操作函数
# =============================================================================

def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    删除所有表结构
    危险操作，请谨慎使用！
    """
    from app.db.models import Base
    Base.metadata.drop_all(bind=engine)


def recreate_db():
    """
    重建数据库
    删除所有表并重新创建
    """
    drop_db()
    init_db()


# =============================================================================
# 事件监听器
# =============================================================================

@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """
    数据库连接事件
    设置默认的search_path
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()
    except Exception:
        pass


@event.listens_for(engine, "checkout")
def check_connection(dbapi_connection, connection_record, connection_proxy):
    """
    连接检出事件
    检测连接是否有效
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception:
        raise Exception("Database connection is invalid")


# =============================================================================
# 会话中间件（可选）
# =============================================================================

class DatabaseMiddleware:
    """
    数据库会话中间件
    用于在请求开始时创建会话，结束时关闭
    """
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type is not None:
                self.db.rollback()
            self.db.close()


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_context",
    "init_db",
    "drop_db",
    "recreate_db",
    "DatabaseMiddleware"
]
