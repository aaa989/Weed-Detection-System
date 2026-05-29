import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    nickname: Optional[str] = None


class TokenResponse(BaseModel):
    success: bool
    message: str
    access_token: str = ""
    token_type: str = "bearer"
    user: Optional[dict] = None


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = auth_service.get_current_user_from_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return TokenResponse(
        success=True,
        message="登录成功",
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
        },
    )


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if len(request.username) < 3 or len(request.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度应在3-20个字符之间")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6个字符")

    existing = auth_service.get_user_by_username(db, request.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    existing = auth_service.get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = auth_service.create_user(
        db, request.username, request.email, request.password, request.nickname
    )
    if not user:
        raise HTTPException(status_code=500, detail="注册失败")

    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return TokenResponse(
        success=True,
        message="注册成功",
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
        },
    )


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = auth_service.get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@router.put("/profile")
def update_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = auth_service.get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.nickname is not None:
        user.nickname = request.nickname
    if request.email is not None:
        existing = auth_service.get_user_by_email(db, request.email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = request.email

    try:
        db.commit()
        db.refresh(user)
        return {
            "success": True,
            "message": "个人信息更新成功",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="更新失败")


@router.put("/password")
def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = auth_service.get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not auth_service.verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6个字符")

    user.password_hash = auth_service.hash_password(request.new_password)
    try:
        db.commit()
        return {"success": True, "message": "密码修改成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="密码修改失败")


@router.get("/stats")
def get_user_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.database import DetectionRecord
    from sqlalchemy import func
    from datetime import datetime, timedelta

    user_id = current_user["user_id"]

    total_detections = (
        db.query(func.count(DetectionRecord.id))
        .filter(DetectionRecord.user_id == user_id)
        .scalar()
        or 0
    )

    total_objects = (
        db.query(func.coalesce(func.sum(DetectionRecord.total_objects), 0))
        .filter(DetectionRecord.user_id == user_id)
        .scalar()
        or 0
    )

    success_count = (
        db.query(func.count(DetectionRecord.id))
        .filter(DetectionRecord.user_id == user_id, DetectionRecord.status == "completed")
        .scalar()
        or 0
    )

    success_rate = round((success_count / total_detections * 100), 1) if total_detections > 0 else 0

    first_record = (
        db.query(func.min(DetectionRecord.created_at))
        .filter(DetectionRecord.user_id == user_id)
        .scalar()
    )
    if first_record:
        days_used = (datetime.now() - first_record).days + 1
    else:
        days_used = 0

    week_ago = datetime.now() - timedelta(days=7)
    weekly_detections = (
        db.query(func.count(DetectionRecord.id))
        .filter(DetectionRecord.user_id == user_id, DetectionRecord.created_at >= week_ago)
        .scalar()
        or 0
    )

    monthly_detections = []
    for i in range(5, -1, -1):
        month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        count = (
            db.query(func.count(DetectionRecord.id))
            .filter(
                DetectionRecord.user_id == user_id,
                DetectionRecord.created_at >= month_start,
                DetectionRecord.created_at < month_end,
            )
            .scalar()
            or 0
        )
        monthly_detections.append({
            "month": month_start.strftime("%Y-%m"),
            "count": count,
        })

    class_stats = (
        db.query(
            DetectionRecord.model_name,
            func.count(DetectionRecord.id).label("count"),
        )
        .filter(DetectionRecord.user_id == user_id)
        .group_by(DetectionRecord.model_name)
        .all()
    )

    return {
        "success": True,
        "data": {
            "total_detections": total_detections,
            "total_objects": total_objects,
            "success_rate": success_rate,
            "days_used": days_used,
            "weekly_detections": weekly_detections,
            "monthly_detections": monthly_detections,
            "model_stats": [{"model": m, "count": c} for m, c in class_stats],
        },
    }