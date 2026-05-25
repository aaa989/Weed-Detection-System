# -*- coding: utf-8 -*-
"""
杂草识别系统功能测试脚本
用于验证数据库连接、模型、CRUD操作是否正常
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("1. 测试模块导入")
    print("=" * 60)
    
    try:
        from app.db.models import (
            User, DatasetSample, SampleAnnotation,
            DetectionRecord, DetectionBox, SystemConfig,
            APIAccessLog, InferenceLog, Base
        )
        print("[OK] 所有模型导入成功")
        print(f"    - User: {User.__tablename__}")
        print(f"    - DatasetSample: {DatasetSample.__tablename__}")
        print(f"    - SampleAnnotation: {SampleAnnotation.__tablename__}")
        print(f"    - DetectionRecord: {DetectionRecord.__tablename__}")
        print(f"    - DetectionBox: {DetectionBox.__tablename__}")
        print(f"    - SystemConfig: {SystemConfig.__tablename__}")
        print(f"    - APIAccessLog: {APIAccessLog.__tablename__}")
        print(f"    - InferenceLog: {InferenceLog.__tablename__}")
        return True
    except ImportError as e:
        print(f"[FAIL] 导入失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("2. 测试数据库连接")
    print("=" * 60)
    
    try:
        from app.db.database import engine, SessionLocal
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"[OK] 数据库连接成功")
            print(f"    - PostgreSQL版本: {version[:50]}...")
            return True
    except SQLAlchemyError as e:
        print(f"[FAIL] 数据库连接失败: {e}")
        print("\n请确保：")
        print("  1. PostgreSQL服务已启动")
        print("  2. 数据库已创建")
        print("  3. .env配置正确")
        return False
    except Exception as e:
        print(f"[FAIL] 连接错误: {e}")
        return False


def test_table_creation():
    """测试表创建"""
    print("\n" + "=" * 60)
    print("3. 测试表创建")
    print("=" * 60)
    
    try:
        from app.db.database import engine
        from app.db.models import Base
        
        # 检查表是否存在
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'users', 'dataset_samples', 'sample_annotations',
                'detection_records', 'detection_boxes', 'system_config',
                'api_access_logs', 'inference_logs'
            ]
            
            print(f"[OK] 发现 {len(tables)} 张表:")
            for table in tables:
                print(f"    - {table}")
            
            missing = set(expected_tables) - set(tables)
            if missing:
                print(f"\n[WARNING] 缺少以下表:")
                for t in missing:
                    print(f"    - {t}")
                print(f"\n请运行 SQL 脚本创建表:")
                print(f"    psql -U weed_user -d weed_db -f app/sql/init.sql")
                return False
            
            print("[OK] 所有表已创建")
            return True
            
    except SQLAlchemyError as e:
        print(f"[FAIL] 检查表失败: {e}")
        return False


def test_user_crud():
    """测试用户CRUD操作"""
    print("\n" + "=" * 60)
    print("4. 测试用户CRUD操作")
    print("=" * 60)
    
    try:
        from app.db.database import SessionLocal
        from app.db.models import User
        from app.core.security import hash_password, verify_password
        import uuid
        
        db = SessionLocal()
        
        # 测试创建用户
        test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        test_email = f"{test_username}@example.com"
        test_password = "test123456"
        
        new_user = User(
            username=test_username,
            email=test_email,
            password_hash=hash_password(test_password),
            role="user",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"[OK] 创建用户成功: {new_user.username} (ID: {new_user.id})")
        
        # 测试查询用户
        found_user = db.query(User).filter(User.username == test_username).first()
        if found_user and found_user.email == test_email:
            print(f"[OK] 查询用户成功")
        
        # 测试密码验证
        if verify_password(test_password, found_user.password_hash):
            print(f"[OK] 密码验证成功")
        else:
            print(f"[FAIL] 密码验证失败")
        
        # 测试更新用户
        found_user.nickname = "测试用户"
        db.commit()
        print(f"[OK] 更新用户成功")
        
        # 测试删除用户
        db.delete(found_user)
        db.commit()
        print(f"[OK] 删除用户成功")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] CRUD测试失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def test_dataset_crud():
    """测试数据集CRUD操作"""
    print("\n" + "=" * 60)
    print("5. 测试数据集CRUD操作")
    print("=" * 60)
    
    try:
        from app.db.database import SessionLocal
        from app.db.models import DatasetSample
        import uuid
        
        db = SessionLocal()
        
        # 测试创建样本
        test_filename = f"test_image_{uuid.uuid4().hex[:8]}.jpg"
        new_sample = DatasetSample(
            filename=test_filename,
            image_url=f"http://localhost:9000/images/{test_filename}",
            class_name="broadleaf",
            split_type="train",
            status="pending",
            width=640,
            height=480,
            file_size=123456
        )
        db.add(new_sample)
        db.commit()
        db.refresh(new_sample)
        print(f"[OK] 创建样本成功: {new_sample.filename} (ID: {new_sample.id})")
        
        # 测试查询样本
        found_sample = db.query(DatasetSample).filter(
            DatasetSample.filename == test_filename
        ).first()
        if found_sample:
            print(f"[OK] 查询样本成功")
        
        # 测试更新样本
        found_sample.status = "annotated"
        found_sample.annotation_count = 5
        db.commit()
        print(f"[OK] 更新样本成功")
        
        # 测试删除样本
        db.delete(found_sample)
        db.commit()
        print(f"[OK] 删除样本成功")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 数据集CRUD测试失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def test_system_config():
    """测试系统配置"""
    print("\n" + "=" * 60)
    print("6. 测试系统配置")
    print("=" * 60)
    
    try:
        from app.db.database import SessionLocal
        from app.db.models import SystemConfig
        
        db = SessionLocal()
        
        # 查询配置
        configs = db.query(SystemConfig).all()
        print(f"[OK] 系统配置数量: {len(configs)}")
        
        # 显示关键配置
        for config in configs[:5]:
            print(f"    - {config.config_key} = {config.config_value}")
        
        if len(configs) > 5:
            print(f"    ... 还有 {len(configs) - 5} 条配置")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 系统配置测试失败: {e}")
        if 'db' in locals():
            db.close()
        return False


def test_api_modules():
    """测试API模块导入"""
    print("\n" + "=" * 60)
    print("7. 测试API模块导入")
    print("=" * 60)
    
    try:
        from app.api import user, dataset, log
        print(f"[OK] 用户管理API: {user.router.prefix}")
        print(f"[OK] 数据集管理API: {dataset.router.prefix}")
        print(f"[OK] 日志监控API: {log.router.prefix}")
        return True
    except ImportError as e:
        print(f"[FAIL] API模块导入失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("  杂草识别系统 - 功能测试")
    print("*" * 60)
    
    results = []
    
    # 执行所有测试
    results.append(("模块导入", test_imports()))
    results.append(("数据库连接", test_database_connection()))
    results.append(("数据表检查", test_table_creation()))
    results.append(("用户CRUD", test_user_crud()))
    results.append(("数据集CRUD", test_dataset_crud()))
    results.append(("系统配置", test_system_config()))
    results.append(("API模块", test_api_modules()))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("  测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  通过: {passed}/{total}")
    
    if passed == total:
        print("\n  所有测试通过！系统已就绪。")
    else:
        print("\n  部分测试失败，请检查配置和依赖。")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
