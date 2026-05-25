# =============================================================================
# 用户管理 API 路由模块
# =============================================================================
# 功能说明：
#   - 用户注册、登录、信息查询/更新
#   - JWT Token 签发与验证
#   - 密码加密存储与修改
#   - 精细化权限控制
#
# API 接口列表：
#   POST /api/user/register    - 用户注册
#   POST /api/user/login       - 用户登录
#   GET  /api/user/info        - 获取当前用户信息
#   PUT  /api/user/info        - 更新当前用户信息
#   PUT  /api/user/password    - 修改密码
#   GET  /api/user/list        - 获取用户列表（管理员）
#   DELETE /api/user/{id}      - 删除用户（管理员）
#   PUT  /api/user/{id}/status - 更新用户状态（管理员）
#   PUT  /api/user/{id}/role   - 更新用户角色（管理员）
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from app.models.database import get_db
from app.models.user_schema import (
    UserRegisterRequest, UserRegisterResponse,
    UserLoginRequest, UserLoginResponse,
    UserInfo, UserInfoResponse,
    UserUpdateRequest, UserPasswordUpdateRequest,
    UserListResponse, MessageResponse
)
from app.crud.user_crud import user_crud
from app.core.security import (
    get_current_user, require_role,
    create_token_response
)

# 创建 API 路由实例
router = APIRouter(prefix="/api/user", tags=["用户管理"])


# =============================================================================
# 用户注册接口
# =============================================================================

@router.post("/register", response_model=UserRegisterResponse)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册接口
    """
    try:
        user = user_crud.create_user(
            db=db,
            username=request.username,
            email=request.email,
            password=request.password,
            nickname=request.nickname,
            role="user"
        )
        
        return UserRegisterResponse(
            success=True,
            message="注册成功",
            user_id=user.id
        )
    
    except ValueError as e:
        return UserRegisterResponse(
            success=False,
            message=str(e),
            user_id=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


# =============================================================================
# 用户登录接口
# =============================================================================

@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    """
    try:
        user = user_crud.authenticate_user(
            db=db,
            username=request.username,
            password=request.password
        )
        
        if not user:
            return UserLoginResponse(
                success=False,
                message="用户名或密码错误"
            )
        
        if not user.is_active:
            return UserLoginResponse(
                success=False,
                message="账号已被禁用"
            )
        
        # 创建 Token 响应
        token_data = create_token_response(
            user_id=user.id,
            username=user.username,
            role=user.role
        )
        
        # 构建用户信息
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            role=user.role,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return UserLoginResponse(
            success=True,
            message="登录成功",
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user_info=user_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


# =============================================================================
# 获取当前用户信息接口
# =============================================================================

@router.get("/info", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户信息接口
    """
    try:
        user = user_crud.get_user_by_id(db, current_user["user_id"])
        
        if not user:
            return UserInfoResponse(
                success=False,
                message="用户不存在"
            )
        
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            role=user.role,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return UserInfoResponse(
            success=True,
            message="获取成功",
            data=user_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


# =============================================================================
# 更新当前用户信息接口
# =============================================================================

@router.put("/info", response_model=UserInfoResponse)
async def update_current_user_info(
    request: UserUpdateRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前登录用户信息接口
    """
    try:
        user = user_crud.update_user(
            db=db,
            user_id=current_user["user_id"],
            email=request.email,
            nickname=request.nickname,
            avatar_url=request.avatar_url
        )
        
        if not user:
            return UserInfoResponse(
                success=False,
                message="用户不存在"
            )
        
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            role=user.role,
            is_active=user.is_active,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return UserInfoResponse(
            success=True,
            message="更新成功",
            data=user_info
        )
    
    except ValueError as e:
        return UserInfoResponse(
            success=False,
            message=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


# =============================================================================
# 修改密码接口
# =============================================================================

@router.put("/password", response_model=MessageResponse)
async def change_password(
    request: UserPasswordUpdateRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户密码接口
    """
    try:
        user_crud.update_user_password(
            db=db,
            user_id=current_user["user_id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        return MessageResponse(
            success=True,
            message="密码修改成功"
        )
    
    except ValueError as e:
        return MessageResponse(
            success=False,
            message=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


# =============================================================================
# 获取用户列表接口（管理员）
# =============================================================================

@router.get("/list", response_model=UserListResponse)
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    获取用户列表接口（管理员专用）
    """
    try:
        skip = (page - 1) * page_size
        
        users = user_crud.get_users(
            db=db,
            skip=skip,
            limit=page_size,
            role=role,
            is_active=is_active
        )
        
        total = user_crud.count_users(
            db=db,
            role=role,
            is_active=is_active
        )
        
        user_list = [
            UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                nickname=user.nickname,
                role=user.role,
                is_active=user.is_active,
                avatar_url=user.avatar_url,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
        return UserListResponse(
            success=True,
            message="获取成功",
            data=user_list,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


# =============================================================================
# 删除用户接口（管理员）
# =============================================================================

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    删除用户接口（管理员专用）
    """
    try:
        if user_id == current_user["user_id"]:
            return MessageResponse(
                success=False,
                message="不允许删除自己"
            )
        
        success = user_crud.delete_user(db, user_id)
        
        if not success:
            return MessageResponse(
                success=False,
                message="用户不存在"
            )
        
        return MessageResponse(
            success=True,
            message="删除成功"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


# =============================================================================
# 更新用户状态接口（管理员）
# =============================================================================

@router.put("/{user_id}/status", response_model=MessageResponse)
async def update_user_status(
    user_id: str,
    is_active: bool = Query(..., description="是否激活"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    更新用户状态接口（管理员专用）
    """
    try:
        user = user_crud.update_user_status(db, user_id, is_active)
        
        if not user:
            return MessageResponse(
                success=False,
                message="用户不存在"
            )
        
        return MessageResponse(
            success=True,
            message=f"用户状态已更新为 {'激活' if is_active else '禁用'}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}"
        )


# =============================================================================
# 更新用户角色接口（管理员）
# =============================================================================

@router.put("/{user_id}/role", response_model=MessageResponse)
async def update_user_role(
    user_id: str,
    role: str = Query(..., description="用户角色（admin/user）"),
    current_user: Dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    更新用户角色接口（管理员专用）
    """
    try:
        if user_id == current_user["user_id"]:
            return MessageResponse(
                success=False,
                message="不允许修改自己的角色"
            )
        
        if role not in ["admin", "user"]:
            return MessageResponse(
                success=False,
                message="无效的角色值"
            )
        
        user = user_crud.update_user_role(db, user_id, role)
        
        if not user:
            return MessageResponse(
                success=False,
                message="用户不存在"
            )
        
        return MessageResponse(
            success=True,
            message=f"用户角色已更新为 {role}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户角色失败: {str(e)}"
        )
