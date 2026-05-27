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
def get_me(current_user: dict = Depends(get_current_user)):
    return {"success": True, "user": current_user}