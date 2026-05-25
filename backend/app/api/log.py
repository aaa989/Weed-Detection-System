# =============================================================================
# 日志与监控 API 路由模块
# =============================================================================
# 功能说明：
#   - API 访问日志、模型推理日志、错误日志、接口耗时统计
#
# API 接口列表：
#   GET  /api/logs/access              - 获取访问日志
#   GET  /api/logs/inference          - 获取推理日志
#   GET  /api/logs/error              - 获取错误日志
#   GET  /api/logs/stats/endpoint     - 获取接口统计
#   GET  /api/logs/stats/daily        - 获取日统计
#   GET  /api/logs/stats/inference    - 获取推理统计
#   GET  /api/logs/files/{filename}   - 下载日志文件
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
import json

from app.models.database import get_db
from app.models.log_schema import (
    AccessLogResponse, AccessLogCreate,
    InferenceLogResponse, InferenceLogCreate,
    ErrorLogResponse, ErrorLogCreate,
    EndpointStats, DailyStats, InferenceStats,
    LogListResponse, StatsResponse
)
from app.core.security import get_current_user, require_role
from app.core.log_config import access_logger, error_logger, inference_logger

# 创建 API 路由实例
router = APIRouter(prefix="/api/logs", tags=["日志与监控"])

# 日志目录
LOG_DIR = os.getenv("LOG_DIR", "logs")


# =============================================================================
# 日志记录函数
# =============================================================================

def log_access(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_id: Optional[str] = None,
    request_body: Optional[str] = None,
    response_body: Optional[str] = None
):
    """记录访问日志"""
    access_logger.info(
        f"{method} {path} | {status_code} | {response_time:.2f}ms | "
        f"IP: {client_ip} | User: {user_id}"
    )


def log_error(
    level: str,
    message: str,
    exception_type: Optional[str] = None,
    stack_trace: Optional[str] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    path: Optional[str] = None
):
    """记录错误日志"""
    error_logger.error(
        f"{level} | {message} | Type: {exception_type} | "
        f"Path: {path} | User: {user_id}"
    )


def log_inference(
    request_id: str,
    model_name: str,
    model_version: Optional[str],
    image_url: str,
    detection_count: int,
    confidence_avg: Optional[float],
    inference_time: float,
    user_id: Optional[str] = None
):
    """记录推理日志"""
    inference_logger.info(
        f"[{request_id}] {model_name} v{model_version} | "
        f"Image: {image_url} | Detections: {detection_count} | "
        f"Avg Conf: {confidence_avg:.4f} | Time: {inference_time:.2f}ms | "
        f"User: {user_id}"
    )


# =============================================================================
# 辅助函数
# =============================================================================

def parse_log_line(line: str) -> Optional[Dict]:
    """解析日志行"""
    try:
        parts = line.split(" | ")
        if len(parts) >= 3:
            return {
                "time": parts[0],
                "level": parts[1] if len(parts) > 2 else "INFO",
                "message": " | ".join(parts[2:])
            }
    except:
        pass
    return None


def read_log_file(filepath: str, lines: int = 100) -> List[str]:
    """读取日志文件最后N行"""
    try:
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return [l.strip() for l in all_lines[-lines:]]
    except:
        return []


# =============================================================================
# 访问日志接口
# =============================================================================

@router.get("/access", response_model=LogListResponse)
async def get_access_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    method: Optional[str] = Query(None, description="请求方法"),
    path: Optional[str] = Query(None, description="请求路径"),
    status_code: Optional[int] = Query(None, description="状态码"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    获取访问日志
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"access_{today}.log")
        
        all_logs = read_log_file(log_file, lines=1000)
        
        filtered_logs = []
        for log in all_logs:
            parsed = parse_log_line(log)
            if parsed:
                if method and method.upper() not in parsed["message"]:
                    continue
                if path and path not in parsed["message"]:
                    continue
                if status_code and str(status_code) not in parsed["message"]:
                    continue
                filtered_logs.append(parsed)
        
        total = len(filtered_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = filtered_logs[start:end]
        
        return LogListResponse(
            success=True,
            message="获取成功",
            data=paginated_logs,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志失败: {str(e)}"
        )


# =============================================================================
# 推理日志接口
# =============================================================================

@router.get("/inference", response_model=LogListResponse)
async def get_inference_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    model_name: Optional[str] = Query(None, description="模型名称"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取推理日志
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"inference_{today}.log")
        
        all_logs = read_log_file(log_file, lines=1000)
        
        filtered_logs = []
        for log in all_logs:
            if model_name and model_name not in log:
                continue
            parsed = parse_log_line(log)
            if parsed:
                filtered_logs.append(parsed)
        
        total = len(filtered_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = filtered_logs[start:end]
        
        return LogListResponse(
            success=True,
            message="获取成功",
            data=paginated_logs,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推理日志失败: {str(e)}"
        )


# =============================================================================
# 错误日志接口
# =============================================================================

@router.get("/error", response_model=LogListResponse)
async def get_error_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="日志级别"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    获取错误日志
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"error_{today}.log")
        
        all_logs = read_log_file(log_file, lines=1000)
        
        filtered_logs = []
        for log in all_logs:
            if level and level.upper() not in log:
                continue
            parsed = parse_log_line(log)
            if parsed:
                filtered_logs.append(parsed)
        
        total = len(filtered_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = filtered_logs[start:end]
        
        return LogListResponse(
            success=True,
            message="获取成功",
            data=paginated_logs,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误日志失败: {str(e)}"
        )


# =============================================================================
# 接口统计接口
# =============================================================================

@router.get("/stats/endpoint", response_model=StatsResponse)
async def get_endpoint_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    获取接口统计信息
    """
    try:
        stats = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = os.path.join(LOG_DIR, f"access_{date}.log")
            
            log_lines = read_log_file(log_file, lines=10000)
            
            endpoint_data = {}
            for line in log_lines:
                parsed = parse_log_line(line)
                if parsed and " | " in parsed["message"]:
                    parts = parsed["message"].split(" | ")
                    if len(parts) >= 2:
                        method_path = parts[0].strip()
                        status_time = parts[1].strip()
                        
                        if " " in method_path:
                            method = method_path.split()[0]
                            path = method_path.split()[1] if len(method_path.split()) > 1 else ""
                            
                            status_code = 0
                            response_time = 0.0
                            
                            try:
                                status_code = int(status_time.split()[0])
                                response_time = float(status_time.split()[2].replace("ms", "")) if len(status_time.split()) > 2 else 0
                            except:
                                pass
                            
                            key = f"{method} {path}"
                            if key not in endpoint_data:
                                endpoint_data[key] = {
                                    "total_calls": 0,
                                    "total_time": 0.0,
                                    "min_time": float("inf"),
                                    "max_time": 0.0,
                                    "success_count": 0
                                }
                            
                            endpoint_data[key]["total_calls"] += 1
                            endpoint_data[key]["total_time"] += response_time
                            endpoint_data[key]["min_time"] = min(endpoint_data[key]["min_time"], response_time)
                            endpoint_data[key]["max_time"] = max(endpoint_data[key]["max_time"], response_time)
                            if 200 <= status_code < 400:
                                endpoint_data[key]["success_count"] += 1
            
            for endpoint, data in endpoint_data.items():
                if data["total_calls"] > 0:
                    parts = endpoint.split()
                    method = parts[0] if parts else ""
                    path = parts[1] if len(parts) > 1 else ""
                    
                    stats.append(EndpointStats(
                        path=path,
                        method=method,
                        total_calls=data["total_calls"],
                        avg_response_time=data["total_time"] / data["total_calls"],
                        min_response_time=data["min_time"] if data["min_time"] != float("inf") else 0,
                        max_response_time=data["max_time"],
                        success_rate=(data["success_count"] / data["total_calls"] * 100) if data["total_calls"] > 0 else 0
                    ))
        
        return StatsResponse(
            success=True,
            message="获取成功",
            data={"endpoints": [s.model_dump() for s in stats]}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口统计失败: {str(e)}"
        )


# =============================================================================
# 日统计接口
# =============================================================================

@router.get("/stats/daily", response_model=StatsResponse)
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    获取日统计信息
    """
    try:
        daily_stats = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            access_log = os.path.join(LOG_DIR, f"access_{date}.log")
            error_log = os.path.join(LOG_DIR, f"error_{date}.log")
            
            access_lines = read_log_file(access_log, lines=10000)
            error_lines = read_log_file(error_log, lines=10000)
            
            total_requests = len(access_lines)
            total_errors = len(error_lines)
            total_time = 0.0
            
            for line in access_lines:
                parsed = parse_log_line(line)
                if parsed and " | " in parsed["message"]:
                    parts = parsed["message"].split(" | ")
                    if len(parts) >= 2:
                        try:
                            status_time = parts[1].strip()
                            response_time = float(status_time.split()[2].replace("ms", "")) if len(status_time.split()) > 2 else 0
                            total_time += response_time
                        except:
                            pass
            
            avg_time = total_time / total_requests if total_requests > 0 else 0
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            daily_stats.append(DailyStats(
                date=date,
                total_requests=total_requests,
                total_errors=total_errors,
                avg_response_time=avg_time,
                error_rate=error_rate
            ))
        
        return StatsResponse(
            success=True,
            message="获取成功",
            data={"daily": [s.model_dump() for s in daily_stats]}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日统计失败: {str(e)}"
        )


# =============================================================================
# 推理统计接口
# =============================================================================

@router.get("/stats/inference", response_model=StatsResponse)
async def get_inference_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取推理统计信息
    """
    try:
        total_inferences = 0
        total_detections = 0
        total_time = 0.0
        total_confidence = 0.0
        count_with_confidence = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = os.path.join(LOG_DIR, f"inference_{date}.log")
            
            log_lines = read_log_file(log_file, lines=10000)
            
            for line in log_lines:
                total_inferences += 1
                
                if "Detections:" in line:
                    try:
                        detections = int(line.split("Detections:")[1].split("|")[0].strip())
                        total_detections += detections
                    except:
                        pass
                
                if "Time:" in line:
                    try:
                        time_str = line.split("Time:")[1].split("ms")[0].strip()
                        total_time += float(time_str)
                    except:
                        pass
                
                if "Avg Conf:" in line:
                    try:
                        conf_str = line.split("Avg Conf:")[1].split("|")[0].strip()
                        total_confidence += float(conf_str)
                        count_with_confidence += 1
                    except:
                        pass
        
        avg_time = total_time / total_inferences if total_inferences > 0 else 0
        avg_confidence = total_confidence / count_with_confidence if count_with_confidence > 0 else 0
        
        return StatsResponse(
            success=True,
            message="获取成功",
            data=InferenceStats(
                total_inferences=total_inferences,
                total_detections=total_detections,
                avg_inference_time=avg_time,
                avg_confidence=avg_confidence
            ).model_dump()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推理统计失败: {str(e)}"
        )


# =============================================================================
# 日志文件下载接口
# =============================================================================

@router.get("/files/{filename}")
async def download_log_file(
    filename: str,
    current_user: Dict = Depends(require_role(["admin"]))
):
    """
    下载日志文件
    """
    if ".." in filename or "/" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文件名"
        )
    
    filepath = os.path.join(LOG_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/plain"
    )


# =============================================================================
# 导出日志记录函数
# =============================================================================

__all__ = ["log_access", "log_error", "log_inference"]
