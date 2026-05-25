# =============================================================================
# 用户管理 Schema 模块
# =============================================================================
# 功能说明：
#   - 定义用户相关的 Pydantic 数据模型
#   - 用于请求参数验证和响应数据格式化
#   - 支持用户注册、登录、信息更新等场景
# =============================================================================

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# 用户角色枚举
# =============================================================================

class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


# =============================================================================
# 用户注册相关 Schema
# =============================================================================

class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v


class UserRegisterResponse(BaseModel):
    """用户注册响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    user_id: Optional[str] = Field(None, description="用户ID")


# =============================================================================
# 用户登录相关 Schema
# =============================================================================

class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserLoginResponse(BaseModel):
    """用户登录响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    access_token: Optional[str] = Field(None, description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(7200, description="过期时间（秒）")
    user_info: Optional["UserInfo"] = Field(None, description="用户信息")


# =============================================================================
# 用户信息相关 Schema
# =============================================================================

class UserInfo(BaseModel):
    """用户基本信息模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    nickname: Optional[str] = Field(None, description="昵称")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """用户信息更新请求模型"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")


class UserPasswordUpdateRequest(BaseModel):
    """密码更新请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('新密码长度至少6位')
        return v


class UserInfoResponse(BaseModel):
    """用户信息响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[UserInfo] = Field(None, description="用户信息")


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[UserInfo] = Field(default_factory=list, description="用户列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")


# =============================================================================
# 通用响应模型
# =============================================================================

class MessageResponse(BaseModel):
    """通用消息响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    detail: Optional[str] = Field(None, description="详细信息")


# 前向引用
UserLoginResponse.model_rebuild()
