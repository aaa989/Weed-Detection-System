# =============================================================================
# 用户 CRUD 操作模块
# =============================================================================
# 功能说明：
#   - 用户注册、登录、信息查询/更新、密码修改
#   - 与数据库交互的底层操作
# =============================================================================

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime

from app.models.database import User
from app.core.security import hash_password, verify_password


class UserCRUD:
    """用户 CRUD 操作类"""
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        根据用户ID获取用户信息
        
        参数：
            db: 数据库会话
            user_id: 用户ID
        
        返回：
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户信息
        
        参数：
            db: 数据库会话
            username: 用户名
        
        返回：
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.username == username.lower()).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户信息
        
        参数：
            db: 数据库会话
            email: 邮箱地址
        
        返回：
            Optional[User]: 用户对象，不存在返回 None
        """
        return db.query(User).filter(User.email == email.lower()).first()
    
    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        nickname: Optional[str] = None,
        role: str = "user"
    ) -> User:
        """
        创建新用户
        
        参数：
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 密码（明文，会自动加密）
            nickname: 昵称
            role: 用户角色
        
        返回：
            User: 创建的用户对象
        
        异常：
            ValueError: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username.lower()).first()
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == email.lower()).first()
        if existing_email:
            raise ValueError("邮箱已被注册")
        
        # 创建用户对象
        db_user = User(
            username=username.lower(),
            email=email.lower(),
            password_hash=hash_password(password),
            nickname=nickname,
            role=role,
            is_active=True
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise ValueError("用户创建失败，用户名或邮箱可能已存在")
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        参数：
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码（明文）
        
        返回：
            Optional[User]: 认证成功返回用户对象，失败返回 None
        """
        # 先尝试用户名查询
        user = db.query(User).filter(User.username == username.lower()).first()
        
        # 再尝试邮箱查询
        if not user:
            user = db.query(User).filter(User.email == username.lower()).first()
        
        # 验证密码
        if not user or not verify_password(password, user.password_hash):
            return None
        
        # 检查用户状态
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        email: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """
        更新用户信息
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            email: 新邮箱
            nickname: 新昵称
            avatar_url: 新头像URL
        
        返回：
            Optional[User]: 更新后的用户对象
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # 更新字段
        if email is not None:
            # 检查邮箱是否被其他用户使用
            existing = db.query(User).filter(
                User.email == email.lower(),
                User.id != user_id
            ).first()
            if existing:
                raise ValueError("邮箱已被其他用户使用")
            user.email = email.lower()
        
        if nickname is not None:
            user.nickname = nickname
        
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("邮箱已被其他用户使用")
    
    @staticmethod
    def update_user_password(db: Session, user_id: str, old_password: str, new_password: str) -> bool:
        """
        更新用户密码
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        返回：
            bool: 是否更新成功
        
        异常：
            ValueError: 旧密码错误
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")
        
        # 更新密码
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    @staticmethod
    def reset_password(db: Session, user_id: str, new_password: str) -> bool:
        """
        重置用户密码（管理员操作）
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            new_password: 新密码
        
        返回：
            bool: 是否更新成功
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    @staticmethod
    def update_user_status(db: Session, user_id: str, is_active: bool) -> Optional[User]:
        """
        更新用户状态
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            is_active: 是否激活
        
        返回：
            Optional[User]: 更新后的用户对象
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user_role(db: Session, user_id: str, role: str) -> Optional[User]:
        """
        更新用户角色
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            role: 新角色
        
        返回：
            Optional[User]: 更新后的用户对象
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.role = role
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """
        删除用户
        
        参数：
            db: 数据库会话
            user_id: 用户ID
        
        返回：
            bool: 是否删除成功
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        获取用户列表
        
        参数：
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            role: 按角色筛选
            is_active: 按状态筛选
        
        返回：
            List[User]: 用户列表
        """
        query = db.query(User)
        
        if role is not None:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_users(
        db: Session,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        统计用户数量
        
        参数：
            db: 数据库会话
            role: 按角色筛选
            is_active: 按状态筛选
        
        返回：
            int: 用户数量
        """
        query = db.query(User)
        
        if role is not None:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.count()


# 创建全局 CRUD 实例
user_crud = UserCRUD()
