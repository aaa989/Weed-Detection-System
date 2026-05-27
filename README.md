
# 杂草智能识别平台

> 基于 YOLO11 的杂草智能识别平台，支持单图检测、批量检测、视频检测、实时摄像头检测和 AI 智能问答

***

## 项目简介

**杂草智能识别平台** 是一个基于深度学习的杂草识别系统，利用计算机视觉技术实现对农田中杂草的快速、准确识别，为精准农业提供智能化解决方案。

### 核心功能

- **单图检测**：上传单张农田图片进行杂草检测与分类
- **批量检测**：批量上传多张图片进行杂草识别
- **视频检测**：上传视频文件进行逐帧杂草检测
- **摄像头实时检测**：使用摄像头进行实时杂草识别
- **AI 智能问答**：集成 DeepSeek AI，提供杂草识别相关知识问答服务
- **用户认证**：支持用户注册、登录和个人信息管理
- **历史记录**：查看和管理检测历史记录

### 技术特点

- **高精度检测**：基于 YOLO11 目标检测算法，支持多种杂草类别识别
- **实时处理**：优化的模型推理速度，满足实时检测需求
- **双阶段 AI 流水线**：YOLO11 目标定位 + EfficientNet 细粒度分类
- **可视化展示**：检测结果可视化标注，支持置信度展示
- **容器化部署**：Docker 一键部署，环境配置简单

***

## 技术栈

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.34 | 前端框架 |
| Vue Router | 4.6.4 | 路由管理 |
| Pinia | 3.0.4 | 状态管理 |
| Element Plus | 2.7.6 | UI 组件库 |
| Axios | 1.7.2 | HTTP 客户端 |
| ECharts | 5.5.1 | 数据可视化 |
| Vite | 8.0.12 | 构建工具 |

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.104.0+ | Web 框架 |
| PostgreSQL | 16 | 关系型数据库 |
| Redis | latest | 缓存服务 |
| MinIO | latest | 对象存储 |
| SQLAlchemy | 2.0.0+ | ORM 框架 |
| Ultralytics | 8.0.0+ | YOLO 目标检测库 |
| OpenCV | 4.8.0+ | 计算机视觉库 |

### 基础设施

| 技术 | 说明 |
|------|------|
| Docker | 容器化部署 |
| Docker Compose | 多容器编排 |

***

## 项目结构

```
Weed-Detection-System-main/
├── backend/                              # 后端代码目录
│   ├── app/                              # 应用核心模块
│   │   ├── api/                          # API 路由层
│   │   │   ├── auth.py                  # 用户认证 API
│   │   │   ├── batch.py                 # 批量检测 API
│   │   │   ├── camera.py                # 摄像头实时检测 API
│   │   │   ├── detection.py             # 单图检测 API
│   │   │   ├── model.py                 # 模型管理 API
│   │   │   ├── qa.py                    # AI 问答 API
│   │   │   ├── video.py                 # 视频检测 API
│   │   │   └── video_detection.py       # 视频实时帧检测 API
│   │   ├── models/                       # 数据模型层
│   │   │   ├── database.py              # 数据库连接配置
│   │   │   └── schemas.py               # Pydantic 数据模型
│   │   ├── services/                     # 业务逻辑层
│   │   ├── utils/                        # 工具函数层
│   │   ├── __init__.py
│   │   ├── config.py                    # 配置管理
│   │   └── database.py                  # 数据库初始化
│   ├── models/                           # 模型文件目录
│   │   ├── yolo11_best.pt              # YOLO11 训练好的最佳模型
│   │   └── model_info.json              # 模型信息
│   ├── data/                             # 数据存储目录
│   ├── uploads/                          # 上传文件临时目录
│   ├── results/                          # 检测结果存储目录
│   ├── train_model.py                    # 模型训练脚本
│   ├── convert_rsod.py                   # 数据集格式转换脚本
│   ├── requirements.txt                  # Python 依赖列表
│   ├── main.py                           # FastAPI 应用入口
│   └── .env                              # 环境变量配置
│
├── frontend/                             # 前端代码目录
│   ├── src/
│   │   ├── api/                         # API 接口层
│   │   ├── components/                  # Vue 组件
│   │   ├── layouts/                     # 布局组件
│   │   ├── router/                      # 路由配置
│   │   ├── store/                       # 状态管理
│   │   ├── utils/                       # 工具函数
│   │   ├── views/                       # 页面视图
│   │   ├── App.vue                      # 根组件
│   │   └── main.js                      # 前端入口文件
│   ├── public/                          # 静态公共资源
│   ├── package.json                     # 前端依赖配置
│   └── vite.config.js                   # Vite 配置
│
├── storage/                              # 持久化存储目录
│   ├── minio/                           # MinIO 对象存储数据
│   ├── postgres/                        # PostgreSQL 数据库
│   └── redis/                           # Redis 缓存数据
│
├── docs/                                 # 项目文档
│   ├── Day1-环境搭建教程.md
│   ├── Day2-单图检测全流程教程.md
│   ├── Day3-模型训练与微调教程.md
│   └── 遥感目标检测-项目介绍.md
│
├── docker-compose.yml                    # Docker Compose 配置
└── README.md                             # 项目说明文档
```

***

## 快速开始

### 方式一：Docker Compose 启动（推荐）

```bash
# 克隆项目
git clone https://github.com/aaa989/Weed-Detection-System.git
cd Weed-Detection-System-main

# 启动所有服务
docker-compose up -d
```

服务访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- 后端 API 文档：http://localhost:8000/docs
- MinIO 控制台：http://localhost:9001（用户名：admin，密码：minio_password）

### 方式二：本地开发

#### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate
# 激活虚拟环境（Linux/Mac）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

***

## API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/profile | 获取用户信息 |

### 检测接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/detection/single | 单图检测 |
| POST | /api/batch/upload | 批量上传并检测 |
| POST | /api/video/upload | 上传视频进行检测 |
| POST | /api/camera/realtime | 摄像头实时帧检测 |
| GET | /api/detection/history | 获取检测历史 |

### 模型管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/model/list | 获取模型列表 |
| POST | /api/model/upload | 上传模型 |

### AI 问答接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/qa/ask | 发送问题并获取 AI 回答 |

***

## 配置说明

### 后端环境变量（backend/.env）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | Weed Detection Platform | 应用名称 |
| APP_VERSION | 1.0.0 | 应用版本 |
| DEBUG | true | 调试模式 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8000 | 监听端口 |
| DB_HOST | localhost | PostgreSQL 主机 |
| DB_PORT | 5432 | PostgreSQL 端口 |
| DB_USERNAME | rsod_user | PostgreSQL 用户名 |
| DB_PASSWORD | rsod_password | PostgreSQL 密码 |
| DB_DATABASE | rsod_platform | PostgreSQL 数据库名 |
| MINIO_HOST | localhost | MinIO 主机 |
| MINIO_PORT | 9000 | MinIO 端口 |
| MINIO_ACCESS_KEY | admin | MinIO 访问密钥 |
| MINIO_SECRET_KEY | minio_password | MinIO 密钥 |
| REDIS_HOST | localhost | Redis 主机 |
| REDIS_PORT | 6379 | Redis 端口 |
| REDIS_PASSWORD | redis_password | Redis 密码 |
| YOLO_MODEL_PATH | models/yolo11_best.pt | YOLO 模型路径 |
| CONFIDENCE_THRESHOLD | 0.5 | 置信度阈值 |
| IOU_THRESHOLD | 0.45 | IOU 阈值 |
| DEEPSEEK_API_KEY | | DeepSeek API 密钥 |
| DEEPSEEK_API_URL | https://api.deepseek.com/v1/chat/completions | DeepSeek API 地址 |

***

## 开发进度

### 已完成

- [x] 环境搭建
- [x] 用户认证系统（注册、登录）
- [x] 单图检测功能
- [x] 批量检测功能
- [x] 视频检测功能
- [x] 摄像头实时检测功能
- [x] 历史记录管理
- [x] AI 智能问答功能
- [x] 模型训练

***

**最后更新**: 2026-05-27

