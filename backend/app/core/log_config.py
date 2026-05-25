# =============================================================================
# Loguru 日志配置模块
# =============================================================================
# 功能说明：
#   - 配置 Loguru 日志系统
#   - 支持控制台和文件输出
#   - 自动日志轮转
#   - 请求日志拦截
# =============================================================================

import sys
import os
from datetime import datetime
from loguru import logger
from pathlib import Path

# =============================================================================
# 日志目录配置
# =============================================================================

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 确保日志目录存在
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# =============================================================================
# 移除默认的 handler
# =============================================================================

logger.remove()

# =============================================================================
# 配置控制台输出
# =============================================================================

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True
)

# =============================================================================
# 配置文件输出 - 访问日志
# =============================================================================

logger.add(
    os.path.join(LOG_DIR, "access_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    encoding="utf-8"
)

# =============================================================================
# 配置文件输出 - 错误日志
# =============================================================================

logger.add(
    os.path.join(LOG_DIR, "error_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="00:00",
    retention="90 days",
    compression="zip",
    encoding="utf-8"
)

# =============================================================================
# 配置文件输出 - 模型推理日志
# =============================================================================

logger.add(
    os.path.join(LOG_DIR, "inference_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    level="INFO",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)

# =============================================================================
# 配置通用日志
# =============================================================================

logger.add(
    os.path.join(LOG_DIR, "app_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)


# =============================================================================
# 预配置的日志记录器
# =============================================================================

# API 访问日志记录器
access_logger = logger.bind(name="access")

# 错误日志记录器
error_logger = logger.bind(name="error")

# 模型推理日志记录器
inference_logger = logger.bind(name="inference")

# 应用日志记录器
app_logger = logger.bind(name="app")


# =============================================================================
# 日志装饰器
# =============================================================================

def log_api_call(func):
    """
    API 调用日志装饰器
    
    用法：
        @log_api_call
        async def my_endpoint():
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # 获取函数信息
        func_name = func.__name__
        module_name = func.__module__
        
        access_logger.info(f"API调用开始: {module_name}.{func_name}")
        
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000  # 毫秒
            
            access_logger.info(
                f"API调用完成: {module_name}.{func_name} | "
                f"耗时: {elapsed:.2f}ms | 状态: 成功"
            )
            
            return result
        
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            
            error_logger.error(
                f"API调用失败: {module_name}.{func_name} | "
                f"耗时: {elapsed:.2f}ms | 错误: {str(e)}"
            )
            
            raise
    
    return wrapper


def log_inference(func):
    """
    模型推理日志装饰器
    
    用法：
        @log_inference
        async def detect_weeds(image):
            pass
    """
    import functools
    import time
    import uuid
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        inference_logger.info(
            f"[{request_id}] 推理开始 | "
            f"函数: {func.__name__} | "
            f"参数: {list(kwargs.keys())}"
        )
        
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            
            # 提取检测数量
            detections = len(result.get("boxes", [])) if isinstance(result, dict) else 0
            
            inference_logger.info(
                f"[{request_id}] 推理完成 | "
                f"函数: {func.__name__} | "
                f"耗时: {elapsed:.2f}ms | "
                f"检测数: {detections}"
            )
            
            return result
        
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            
            inference_logger.error(
                f"[{request_id}] 推理失败 | "
                f"函数: {func.__name__} | "
                f"耗时: {elapsed:.2f}ms | "
                f"错误: {str(e)}"
            )
            
            raise
    
    return wrapper


# =============================================================================
# 导出 logger
# =============================================================================

__all__ = ["logger", "access_logger", "error_logger", "inference_logger", "app_logger"]
