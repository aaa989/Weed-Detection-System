# =============================================================================
# 数据集 CRUD 操作模块
# =============================================================================
# 功能说明：
#   - 样本列表、类别统计、样本上传、标注管理
#   - 与数据库交互的底层操作
# =============================================================================

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from app.models.database import Base
from enum import Enum


class WeedClass(str, Enum):
    """杂草类别枚举"""
    BROADLEAF = "broadleaf"
    GRASS = "grass"
    SEDGE = "sedge"
    OTHER = "other"


class SplitType(str, Enum):
    """数据集划分类型"""
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class SampleStatus(str, Enum):
    """样本状态"""
    PENDING = "pending"
    ANNOTATED = "annotated"
    APPROVED = "approved"
    REJECTED = "rejected"


class DatasetSample(Base):
    """数据集样本表"""
    __tablename__ = "dataset_samples"
    
    id = Base.metadata.tables["dataset_samples"].columns["id"] if "dataset_samples" in Base.metadata.tables else None
    # 由于无法直接访问列，使用原始方式
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS dataset_samples (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            image_url VARCHAR(500) NOT NULL,
            class_name VARCHAR(50) NOT NULL,
            split_type VARCHAR(20) DEFAULT 'train',
            status VARCHAR(20) DEFAULT 'pending',
            width INTEGER,
            height INTEGER,
            file_size INTEGER,
            notes TEXT,
            annotation_count INTEGER DEFAULT 0,
            uploader_id VARCHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """


class SampleAnnotation(Base):
    """样本标注表"""
    __tablename__ = "sample_annotations"
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS sample_annotations (
            id SERIAL PRIMARY KEY,
            sample_id INTEGER NOT NULL,
            annotator VARCHAR(100) NOT NULL,
            annotation_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """


class DatasetStatistics(Base):
    """数据集统计表"""
    __tablename__ = "dataset_statistics"
    
    @staticmethod
    def create_table_sql():
        return """
        CREATE TABLE IF NOT EXISTS dataset_statistics (
            id SERIAL PRIMARY KEY,
            stat_date DATE UNIQUE,
            total_samples INTEGER DEFAULT 0,
            total_annotations INTEGER DEFAULT 0,
            train_count INTEGER DEFAULT 0,
            val_count INTEGER DEFAULT 0,
            test_count INTEGER DEFAULT 0,
            broadleaf_count INTEGER DEFAULT 0,
            grass_count INTEGER DEFAULT 0,
            sedge_count INTEGER DEFAULT 0,
            other_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """


class DatasetCRUD:
    """数据集 CRUD 操作类"""
    
    # =============================================================================
    # 样本管理
    # =============================================================================
    
    @staticmethod
    def get_sample_by_id(db: Session, sample_id: int) -> Optional[Dict]:
        """
        根据ID获取样本
        
        参数：
            db: 数据库会话
            sample_id: 样本ID
        
        返回：
            Optional[Dict]: 样本对象字典
        """
        result = db.execute(
            f"SELECT * FROM dataset_samples WHERE id = {sample_id}"
        ).fetchone()
        return dict(result._mapping) if result else None
    
    @staticmethod
    def create_sample(
        db: Session,
        filename: str,
        image_url: str,
        class_name: str,
        width: int,
        height: int,
        file_size: int,
        split_type: str = "train",
        uploader_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        创建新样本
        
        参数：
            db: 数据库会话
            filename: 文件名
            image_url: 图片URL
            class_name: 杂草类别
            width: 图片宽度
            height: 图片高度
            file_size: 文件大小
            split_type: 数据集划分
            uploader_id: 上传者ID
            notes: 备注
        
        返回：
            Dict: 创建的样本对象
        """
        result = db.execute(
            """
            INSERT INTO dataset_samples 
            (filename, image_url, class_name, width, height, file_size, split_type, uploader_id, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (filename, image_url, class_name, width, height, file_size, split_type, uploader_id, notes)
        )
        db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None
    
    @staticmethod
    def update_sample(
        db: Session,
        sample_id: int,
        class_name: Optional[str] = None,
        split_type: Optional[str] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict]:
        """
        更新样本信息
        
        参数：
            db: 数据库会话
            sample_id: 样本ID
            class_name: 新类别
            split_type: 新划分
            status: 新状态
            notes: 新备注
        
        返回：
            Optional[Dict]: 更新后的样本
        """
        updates = []
        params = []
        
        if class_name is not None:
            updates.append("class_name = %s")
            params.append(class_name)
        if split_type is not None:
            updates.append("split_type = %s")
            params.append(split_type)
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        
        if not updates:
            return DatasetCRUD.get_sample_by_id(db, sample_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(sample_id)
        
        result = db.execute(
            f"UPDATE dataset_samples SET {', '.join(updates)} WHERE id = %s RETURNING *",
            params
        )
        db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None
    
    @staticmethod
    def delete_sample(db: Session, sample_id: int) -> bool:
        """
        删除样本
        
        参数：
            db: 数据库会话
            sample_id: 样本ID
        
        返回：
            bool: 是否删除成功
        """
        db.execute("DELETE FROM dataset_samples WHERE id = %s", (sample_id,))
        db.commit()
        return True
    
    @staticmethod
    def get_samples(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        class_name: Optional[str] = None,
        split_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        获取样本列表
        
        参数：
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            class_name: 按类别筛选
            split_type: 按划分筛选
            status: 按状态筛选
            search: 搜索文件名
        
        返回：
            List[Dict]: 样本列表
        """
        conditions = []
        params = []
        
        if class_name is not None:
            conditions.append("class_name = %s")
            params.append(class_name)
        if split_type is not None:
            conditions.append("split_type = %s")
            params.append(split_type)
        if status is not None:
            conditions.append("status = %s")
            params.append(status)
        if search:
            conditions.append("filename LIKE %s")
            params.append(f"%{search}%")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        result = db.execute(
            f"""
            SELECT * FROM dataset_samples 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
            """,
            params + [limit, skip]
        )
        return [dict(row._mapping) for row in result.fetchall()]
    
    @staticmethod
    def count_samples(
        db: Session,
        class_name: Optional[str] = None,
        split_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        统计样本数量
        
        参数：
            db: 数据库会话
            class_name: 按类别筛选
            split_type: 按划分筛选
            status: 按状态筛选
        
        返回：
            int: 样本数量
        """
        conditions = []
        params = []
        
        if class_name is not None:
            conditions.append("class_name = %s")
            params.append(class_name)
        if split_type is not None:
            conditions.append("split_type = %s")
            params.append(split_type)
        if status is not None:
            conditions.append("status = %s")
            params.append(status)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        result = db.execute(
            f"SELECT COUNT(*) as count FROM dataset_samples {where_clause}",
            params
        )
        return result.fetchone()[0]
    
    # =============================================================================
    # 标注管理
    # =============================================================================
    
    @staticmethod
    def create_annotation(
        db: Session,
        sample_id: int,
        annotator: str,
        boxes: List[Dict[str, Any]]
    ) -> Dict:
        """
        创建标注
        
        参数：
            db: 数据库会话
            sample_id: 样本ID
            annotator: 标注人
            boxes: 标注框列表
        
        返回：
            Dict: 创建的标注对象
        """
        # 更新样本状态
        db.execute(
            "UPDATE dataset_samples SET status = 'annotated', annotation_count = %s WHERE id = %s",
            (len(boxes), sample_id)
        )
        
        # 创建标注
        result = db.execute(
            """
            INSERT INTO sample_annotations (sample_id, annotator, annotation_data)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (sample_id, annotator, json.dumps(boxes, ensure_ascii=False))
        )
        db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None
    
    @staticmethod
    def get_annotations_by_sample(db: Session, sample_id: int) -> List[Dict]:
        """
        获取样本的所有标注
        
        参数：
            db: 数据库会话
            sample_id: 样本ID
        
        返回：
            List[Dict]: 标注列表
        """
        result = db.execute(
            "SELECT * FROM sample_annotations WHERE sample_id = %s ORDER BY created_at DESC",
            (sample_id,)
        )
        return [dict(row._mapping) for row in result.fetchall()]
    
    @staticmethod
    def delete_annotation(db: Session, annotation_id: int) -> bool:
        """
        删除标注
        
        参数：
            db: 数据库会话
            annotation_id: 标注ID
        
        返回：
            bool: 是否删除成功
        """
        db.execute("DELETE FROM sample_annotations WHERE id = %s", (annotation_id,))
        db.commit()
        return True
    
    # =============================================================================
    # 统计功能
    # =============================================================================
    
    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        参数：
            db: 数据库会话
        
        返回：
            Dict: 统计信息字典
        """
        # 基础统计
        total_samples = db.execute("SELECT COUNT(*) FROM dataset_samples").fetchone()[0]
        total_annotations = db.execute("SELECT COUNT(*) FROM sample_annotations").fetchone()[0]
        
        # 按划分统计
        train_count = DatasetCRUD.count_samples(db, split_type="train")
        val_count = DatasetCRUD.count_samples(db, split_type="val")
        test_count = DatasetCRUD.count_samples(db, split_type="test")
        
        # 按类别统计
        class_stats = []
        for class_name in ["broadleaf", "grass", "sedge", "other"]:
            count = DatasetCRUD.count_samples(db, class_name=class_name)
            percentage = (count / total_samples * 100) if total_samples > 0 else 0
            
            class_stats.append({
                "class_name": class_name,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        return {
            "total_samples": total_samples,
            "total_annotations": total_annotations,
            "train_count": train_count,
            "val_count": val_count,
            "test_count": test_count,
            "class_statistics": class_stats
        }


# 创建全局 CRUD 实例
dataset_crud = DatasetCRUD()
