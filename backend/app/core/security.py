# =============================================================================
# JWT 认证工具模块
# =============================================================================
# 功能说明：
#   - JWT Token 的生成和验证
#   - 密码加密和验证（bcrypt）
#   - Token 过期时间管理
#   - 用户权限验证
# =============================================================================

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# =============================================================================
# 配置常量
# =============================================================================

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer Token 安全方案
security = HTTPBearer(auto_error=False)


# =============================================================================
# JWT Token 管理函数
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    
    参数：
        data: 需要编码到 token 中的数据字典
        expires_delta: token 过期时间增量
    
    返回：
        str: 编码后的 JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 JWT token
    
    参数：
        token: JWT token 字符串
    
    返回：
        Optional[Dict]: 解码后的数据字典，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码 JWT token（不验证有效性）
    
    参数：
        token: JWT token 字符串
    
    返回：
        Dict: 解码后的数据字典
    
    异常：
        HTTPException: token 无效或已过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# 密码管理函数
# =============================================================================

def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    
    参数：
        password: 明文密码
    
    返回：
        str: 加密后的密码哈希
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    参数：
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希
    
    返回：
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# 认证依赖函数
# =============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前登录用户（强制认证）
    
    参数：
        credentials: HTTP Bearer 认证凭证
    
    返回：
        Dict: 当前用户信息字典
    
    异常：
        HTTPException: 未提供有效的认证凭证
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "username": username,
        "user_id": user_id,
        "role": payload.get("role", "user")
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户（可选，不强制认证）
    
    参数：
        credentials: HTTP Bearer 认证凭证
    
    返回：
        Optional[Dict]: 当前用户信息字典，未登录返回 None
    """
    if credentials is None:
        return None
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        return None
    
    return {
        "username": payload.get("sub"),
        "user_id": payload.get("user_id"),
        "role": payload.get("role", "user")
    }


def require_role(required_roles: List[str]):
    """
    创建角色验证依赖
    
    参数：
        required_roles: 需要的角色列表
    
    返回：
        依赖函数
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，需要以下角色之一: " + ", ".join(required_roles)
            )
        return current_user
    return role_checker


# =============================================================================
# Token 响应模型
# =============================================================================

def create_token_response(user_id: int, username: str, role: str = "user") -> Dict[str, Any]:
    """
    创建 Token 响应数据
    
    参数：
        user_id: 用户ID
        username: 用户名
        role: 用户角色
    
    返回：
        Dict: 包含 token 信息的字典
    """
    access_token = create_access_token(
        data={
            "sub": username,
            "user_id": user_id,
            "role": role
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
