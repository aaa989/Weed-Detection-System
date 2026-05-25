-- =============================================================================
-- 杂草识别系统数据库建表SQL脚本
-- PostgreSQL 15+
-- =============================================================================
-- 功能说明：
--   - 用户管理表
--   - 数据集样本表
--   - 检测记录表
--   - 检测目标框表
--   - 系统配置表
-- =============================================================================

-- 1. 用户表 (users)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'guest')),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);


-- 2. 数据集样本表 (dataset_samples)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dataset_samples (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    image_key VARCHAR(500),                          -- MinIO存储Key
    class_name VARCHAR(50) NOT NULL,                 -- 杂草类别
    class_id INTEGER,                               -- 类别ID
    split_type VARCHAR(20) DEFAULT 'train' CHECK (split_type IN ('train', 'val', 'test')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'annotated', 'approved', 'rejected')),
    width INTEGER,
    height INTEGER,
    file_size INTEGER,                              -- 文件大小（字节）
    notes TEXT,
    annotation_count INTEGER DEFAULT 0,
    uploader_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_dataset_samples_filename_split UNIQUE (filename, split_type)
);

-- 数据集样本表索引
CREATE INDEX IF NOT EXISTS idx_dataset_samples_filename ON dataset_samples(filename);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_class_name ON dataset_samples(class_name);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_split_type ON dataset_samples(split_type);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_status ON dataset_samples(status);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_uploader_id ON dataset_samples(uploader_id);
CREATE INDEX IF NOT EXISTS idx_dataset_samples_created_at ON dataset_samples(created_at DESC);


-- 3. 样本标注表 (sample_annotations)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sample_annotations (
    id SERIAL PRIMARY KEY,
    sample_id INTEGER NOT NULL REFERENCES dataset_samples(id) ON DELETE CASCADE,
    annotator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    annotation_data JSONB NOT NULL,                  -- 标注框数据JSON
    annotation_type VARCHAR(20) DEFAULT 'bbox' CHECK (annotation_type IN ('bbox', 'polygon', 'mask')),
    is_valid BOOLEAN DEFAULT true,
    validated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    validated_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 样本标注表索引
CREATE INDEX IF NOT EXISTS idx_sample_annotations_sample_id ON sample_annotations(sample_id);
CREATE INDEX IF NOT EXISTS idx_sample_annotations_annotator_id ON sample_annotations(annotator_id);
CREATE INDEX IF NOT EXISTS idx_sample_annotations_created_at ON sample_annotations(created_at DESC);


-- 4. 检测记录表 (detection_records)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('single', 'batch', 'folder', 'video')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) DEFAULT '1.0.0',
    model_path VARCHAR(500),                        -- 模型文件路径
    
    -- 图片信息
    original_image_url VARCHAR(500),
    original_image_key VARCHAR(500),               -- MinIO存储Key
    result_image_url VARCHAR(500),
    result_image_key VARCHAR(500),                 -- MinIO存储Key
    
    -- 统计信息
    total_objects INTEGER DEFAULT 0,               -- 检测到的目标总数
    detection_time FLOAT,                           -- 检测耗时（秒）
    confidence_avg FLOAT,                          -- 平均置信度
    
    -- 错误信息
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- 批处理信息
    batch_id VARCHAR(100),                         -- 批处理ID
    batch_total INTEGER DEFAULT 0,                 -- 批处理总数
    batch_processed INTEGER DEFAULT 0,             -- 已处理数
    
    -- 元数据
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 检测记录表索引
CREATE INDEX IF NOT EXISTS idx_detection_records_user_id ON detection_records(user_id);
CREATE INDEX IF NOT EXISTS idx_detection_records_type ON detection_records(type);
CREATE INDEX IF NOT EXISTS idx_detection_records_status ON detection_records(status);
CREATE INDEX IF NOT EXISTS idx_detection_records_model_name ON detection_records(model_name);
CREATE INDEX IF NOT EXISTS idx_detection_records_batch_id ON detection_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_detection_records_created_at ON detection_records(created_at DESC);


-- 5. 检测目标框表 (detection_boxes)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_boxes (
    id SERIAL PRIMARY KEY,
    record_id UUID NOT NULL REFERENCES detection_records(id) ON DELETE CASCADE,
    
    -- 边界框坐标
    x_min FLOAT NOT NULL,
    y_min FLOAT NOT NULL,
    x_max FLOAT NOT NULL,
    y_max FLOAT NOT NULL,
    
    -- 类别信息
    class_id INTEGER NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    chinese_name VARCHAR(50),
    
    -- 置信度
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    
    -- 分割信息（可选）
    segmentation JSONB,                            -- 分割多边形坐标
    area FLOAT,                                    -- 目标面积
    
    -- 元数据
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 检测目标框表索引
CREATE INDEX IF NOT EXISTS idx_detection_boxes_record_id ON detection_boxes(record_id);
CREATE INDEX IF NOT EXISTS idx_detection_boxes_class_name ON detection_boxes(class_name);
CREATE INDEX IF NOT EXISTS idx_detection_boxes_confidence ON detection_boxes(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_detection_boxes_created_at ON detection_boxes(created_at DESC);


-- 6. 系统配置表 (system_config)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    value_type VARCHAR(20) DEFAULT 'string' CHECK (value_type IN ('string', 'number', 'boolean', 'json')),
    config_group VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_public BOOLEAN DEFAULT true,               -- 是否公开配置（前端可读）
    is_system BOOLEAN DEFAULT false,               -- 是否系统配置（不可删除）
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 系统配置表索引
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_group ON system_config(config_group);
CREATE INDEX IF NOT EXISTS idx_system_config_is_public ON system_config(is_public);


-- 7. API访问日志表 (api_access_logs)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_access_logs (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 请求信息
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    query_params JSONB,
    request_body JSONB,
    
    -- 响应信息
    status_code INTEGER NOT NULL,
    response_time FLOAT NOT NULL,                  -- 响应时间（毫秒）
    response_size INTEGER,                          -- 响应大小（字节）
    
    -- 客户端信息
    client_ip VARCHAR(50),
    user_agent TEXT,
    
    -- 错误信息
    error_message TEXT,
    error_stack TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API访问日志表索引
CREATE INDEX IF NOT EXISTS idx_api_access_logs_user_id ON api_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_request_id ON api_access_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_method_path ON api_access_logs(method, path);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_status_code ON api_access_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_api_access_logs_created_at ON api_access_logs(created_at DESC);


-- 8. 推理日志表 (inference_logs)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inference_logs (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    record_id UUID REFERENCES detection_records(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 模型信息
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),
    
    -- 输入信息
    image_url VARCHAR(500),
    image_key VARCHAR(500),
    
    -- 输出信息
    detection_count INTEGER DEFAULT 0,
    confidence_avg FLOAT,
    inference_time FLOAT NOT NULL,                -- 推理时间（毫秒）
    
    -- 结果摘要
    result_summary JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 推理日志表索引
CREATE INDEX IF NOT EXISTS idx_inference_logs_request_id ON inference_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_inference_logs_record_id ON inference_logs(record_id);
CREATE INDEX IF NOT EXISTS idx_inference_logs_user_id ON inference_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_inference_logs_model_name ON inference_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_inference_logs_created_at ON inference_logs(created_at DESC);


-- =============================================================================
-- 初始化数据
-- =============================================================================

-- 插入默认系统配置
INSERT INTO system_config (config_key, config_value, value_type, config_group, description, is_public, is_system) VALUES
('system_name', '杂草识别系统', 'string', 'general', '系统名称', true, true),
('system_version', '1.0.0', 'string', 'general', '系统版本号', true, true),
('system_description', '基于YOLO11的杂草识别检测系统', 'string', 'general', '系统描述', true, true),
('upload_max_size', '10485760', 'number', 'upload', '文件上传最大大小（字节）', true, false),
('upload_allowed_extensions', '["jpg","jpeg","png","bmp"]', 'json', 'upload', '允许的文件扩展名', true, false),
('detection_default_confidence', '0.5', 'number', 'detection', '检测默认置信度阈值', true, false),
('detection_default_iou', '0.45', 'number', 'detection', '检测默认IOU阈值', true, false),
('minio_bucket_name', 'weed-images', 'string', 'storage', 'MinIO存储桶名称', true, false),
('minio_endpoint', 'localhost:9000', 'string', 'storage', 'MinIO服务端点', true, false),
('jwt_secret_key', 'your-secret-key-change-in-production', 'string', 'security', 'JWT密钥', false, true),
('jwt_access_token_expire_minutes', '1440', 'number', 'security', 'JWT访问令牌过期时间（分钟）', false, true),
('redis_host', 'localhost', 'string', 'cache', 'Redis主机地址', true, false),
('redis_port', '6379', 'number', 'cache', 'Redis端口', true, false),
('log_level', 'INFO', 'string', 'logging', '日志级别', true, false),
('log_retention_days', '30', 'number', 'logging', '日志保留天数', true, false)
ON CONFLICT (config_key) DO NOTHING;


-- =============================================================================
-- 创建更新时间的触发器函数
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要自动更新updated_at的表创建触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dataset_samples_updated_at ON dataset_samples;
CREATE TRIGGER update_dataset_samples_updated_at BEFORE UPDATE ON dataset_samples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sample_annotations_updated_at ON sample_annotations;
CREATE TRIGGER update_sample_annotations_updated_at BEFORE UPDATE ON sample_annotations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_detection_records_updated_at ON detection_records;
CREATE TRIGGER update_detection_records_updated_at BEFORE UPDATE ON detection_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 授予权限（如果需要）
-- =============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO weed_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO weed_user;


-- =============================================================================
-- 完成
-- =============================================================================

-- SELECT 'Database schema created successfully!' AS status;
