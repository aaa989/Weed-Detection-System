# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All" 
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session


get_ipython().getoutput("pip install ultralytics -q")


import os
import time
import copy
import shutil
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
from ultralytics import YOLO
from sklearn.utils.class_weight import compute_class_weight

# ==========================================
# 辅助函数：自动寻找有效路径
# ==========================================
def find_valid_path(paths_to_try):
    for path in paths_to_try:
        if os.path.exists(path):
            return path
    return None

def debug_kaggle_paths():
    """打印 /kaggle/input/ 下的所有真实路径，帮助排查挂载问题"""
    print("\n[调试信息] 当前 /kaggle/input/ 目录下实际存在的文件和文件夹：")
    if os.path.exists('/kaggle/input'):
        for root, dirs, files in os.walk('/kaggle/input'):
            # 为了避免打印太多，只打印前两层目录
            level = root.replace('/kaggle/input', '').count(os.sep)
            if level < 3:
                indent = ' ' * 4 * (level)
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 1)
                for f in files[:3]: # 每个目录最多打印3个文件示意
                    print(f"{subindent}{f}")
                if len(files) > 3:
                    print(f"{subindent}...")
    print("-" * 50)

# ==========================================
# 辅助函数：地毯式自动搜索 DeepWeeds
# ==========================================
def auto_find_deepweeds():
    """全自动遍历 /kaggle/input 寻找 DeepWeeds 的核心文件，告别手动猜路径"""
    print("\n正在全局搜索 DeepWeeds 数据集...")
    csv_path = None
    img_dir = None
    for root, dirs, files in os.walk('/kaggle/input'):
        if 'labels.csv' in files and not csv_path:
            csv_path = os.path.join(root, 'labels.csv')
        if 'images' in dirs and not img_dir:
            img_dir = os.path.join(root, 'images')
            
    if csv_path and img_dir:
        return csv_path, img_dir
    return None, None

# ==========================================
# 核心模块 1：DeepWeeds 数据集专属处理 (用于分类)
# ==========================================
def prepare_deepweeds_data(csv_path, img_dir, output_dir, train_ratio=0.8):
    """
    处理 Kaggle 上的原生 DeepWeeds 数据集，转换为 PyTorch 需要的分类格式。
    """
    print(f"--- [准备 1/2] 开始处理 DeepWeeds (来自: {csv_path}) ---")
    if not os.path.exists(csv_path) or not os.path.exists(img_dir):
        print(f"❌ 未找到 DeepWeeds 路径。")
        return False
        
    df = pd.read_csv(csv_path)
    # DeepWeeds 标准的 9 个类别
    classes = ['Chinee apple', 'Lantana', 'Parkinsonia', 'Parthenium', 
               'Prickly acacia', 'Rubber vine', 'Siam weed', 'Snake weed', 'Negative']
               
    os.makedirs(os.path.join(output_dir, 'train'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'val'), exist_ok=True)
    for c in classes:
        os.makedirs(os.path.join(output_dir, 'train', c), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'val', c), exist_ok=True)

    images = df['Filename'].tolist()
    labels = df['Label'].tolist()
    combined = list(zip(images, labels))
    random.shuffle(combined)
    split_idx = int(len(combined) * train_ratio)
    
    print(f"开始分配分类图像... 总计 {len(combined)} 张图片。")
    for img_name, label_idx in combined[:split_idx]:
        src = os.path.join(img_dir, img_name)
        dst = os.path.join(output_dir, 'train', classes[label_idx], img_name)
        if os.path.exists(src): shutil.copy(src, dst)
        
    for img_name, label_idx in combined[split_idx:]:
        src = os.path.join(img_dir, img_name)
        dst = os.path.join(output_dir, 'val', classes[label_idx], img_name)
        if os.path.exists(src): shutil.copy(src, dst)
        
    print(f"✅ DeepWeeds 分类数据准备完成！已保存至: {output_dir}")
    return True

# ==========================================
# 核心模块 2：Target-Weed 数据集专属处理 (用于 YOLO 目标检测)
# ==========================================
def prepare_target_weed_yolo_data(source_dir, output_dir, train_ratio=0.8):
    """
    专门处理 Kaggle 上的 `target-and-eliminate-weed` 数据集，
    将其按 8:2 拆分，并生成 YOLO11 官方支持的目录结构和 data.yaml。
    """
    print(f"\n--- [准备 2/2] 开始处理 YOLO 目标定位数据集 (来自: {source_dir}) ---")
    if not os.path.exists(source_dir):
        print(f"❌ 未找到检测数据集路径。")
        return None
        
    # YOLO 官方目录规范
    img_train_dir = os.path.join(output_dir, 'images', 'train')
    img_val_dir = os.path.join(output_dir, 'images', 'val')
    lbl_train_dir = os.path.join(output_dir, 'labels', 'train')
    lbl_val_dir = os.path.join(output_dir, 'labels', 'val')
    
    for d in [img_train_dir, img_val_dir, lbl_train_dir, lbl_val_dir]:
        os.makedirs(d, exist_ok=True)
        
    # 获取所有图片 (过滤掉非图片文件)
    all_images = [f for f in os.listdir(source_dir) if f.endswith('.jpeg') or f.endswith('.jpg')]
    random.shuffle(all_images)
    split_idx = int(len(all_images) * train_ratio)
    
    train_images = all_images[:split_idx]
    val_images = all_images[split_idx:]
    
    print(f"开始分配 YOLO 数据... 训练集 {len(train_images)} 张，验证集 {len(val_images)} 张。")
    
    # 辅助函数：拷贝图片和对应的txt标签
    def copy_data(img_list, split_type):
        dest_img_dir = img_train_dir if split_type == 'train' else img_val_dir
        dest_lbl_dir = lbl_train_dir if split_type == 'train' else lbl_val_dir
        
        for img_name in img_list:
            base_name = os.path.splitext(img_name)[0]
            txt_name = base_name + '.txt'
            
            src_img = os.path.join(source_dir, img_name)
            src_txt = os.path.join(source_dir, txt_name)
            
            if os.path.exists(src_img) and os.path.exists(src_txt):
                shutil.copy(src_img, os.path.join(dest_img_dir, img_name))
                shutil.copy(src_txt, os.path.join(dest_lbl_dir, txt_name))

    copy_data(train_images, 'train')
    copy_data(val_images, 'val')
    
    # 生成 YOLO11 需要的 yaml 配置文件
    yaml_path = os.path.join(output_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(f"train: {img_train_dir}\n")
        f.write(f"val: {img_val_dir}\n")
        f.write("nc: 2\n")
        f.write("names: ['crop', 'weed']\n") # 对应原数据集 0:crop, 1:weed
        
    print(f"✅ YOLO 检测数据准备完成！已生成配置: {yaml_path}")
    return yaml_path

# ==========================================
# 训练模块 1：EfficientNet (分类)
# ==========================================
def train_efficientnet_classifier(data_dir, epochs=25, batch_size=32, save_path='./best_efficientnet.pth'):
    print("\n===========================================")
    print("🚀 启动阶段: EfficientNet 高精度分类训练 (基于 DeepWeeds)")
    print("===========================================")
    
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
    dataloaders = {x: DataLoader(image_datasets[x], batch_size=batch_size, shuffle=True, num_workers=4) for x in ['train', 'val']}
    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
    
    num_classes = len(image_datasets['train'].classes)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"检测到 {num_classes} 个分类类别。使用设备: {device}")

    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, num_classes)
    model = model.to(device)

    # 解决 DeepWeeds 类别不平衡问题
    train_targets = image_datasets['train'].targets
    class_weights_val = compute_class_weight('balanced', classes=np.unique(train_targets), y=train_targets)
    class_weights_tensor = torch.tensor(class_weights_val, dtype=torch.float).to(device)
    
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    optimizer = optim.AdamW(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(epochs):
        for phase in ['train', 'val']:
            if phase == 'train': model.train()
            else: model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            if phase == 'train': scheduler.step()

            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            
            # 简化的进度输出
            if phase == 'val':
                print(f'Epoch {epoch+1}/{epochs} - Val Acc: {epoch_acc:.4f}')
                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_model_wts)
    torch.save(model.state_dict(), save_path)
    print(f"✅ EfficientNet 训练完成！最高准确率: {best_acc:4f}，模型保存在: {save_path}")
    return model

# ==========================================
# 训练模块 2：YOLO11 (目标检测)
# ==========================================
def train_yolo_detector(data_yaml_path, epochs=30, project_path='./yolo_output'):
    print("\n===========================================")
    print("🎯 启动阶段: YOLO11 目标检测训练 (区分作物与杂草)")
    print("===========================================")
    model = YOLO('yolo11n.pt') # 使用最新的 YOLO11 架构
    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=640,
        batch=16,
        device=0 if torch.cuda.is_available() else 'cpu',
        project=project_path,
        name='yolo11_weed_detector',
        exist_ok=True
    )
    print(f"✅ YOLO11 训练完成。模型保存在: {project_path}/yolo11_weed_detector/weights/best.pt")

if __name__ == '__main__':
    print("🌟 启动农业双阶段 AI 流水线 (YOLO11 + EfficientNet) 🌟")
    
    # ---------------------------------------------------------
    # 0. 打印真实的挂载目录 (排查路径薛定谔问题)
    # ---------------------------------------------------------
    debug_kaggle_paths()

    # ---------------------------------------------------------
    # 阶段 1: 训练 EfficientNet (使用 DeepWeeds 数据集)
    # ---------------------------------------------------------
    # 自动探测真实的 Kaggle DeepWeeds 路径 (覆盖截图中的 labels 文件夹情况)
    DEEPWEEDS_CSV_PATHS = [
        '/kaggle/input/deepweeds/labels.csv',
        '/kaggle/input/deepweeds/labels/labels.csv',
        '/kaggle/input/datasets/imsparsh/deepweeds/labels.csv',
        '/kaggle/input/datasets/imsparsh/deepweeds/labels/labels.csv',
    ]
    DEEPWEEDS_IMG_PATHS = [
        '/kaggle/input/deepweeds/images',
        '/kaggle/input/datasets/imsparsh/deepweeds/images',
    ]
    
    csv_target = find_valid_path(DEEPWEEDS_CSV_PATHS)
    img_target = find_valid_path(DEEPWEEDS_IMG_PATHS)
    
    if not (csv_target and img_target):
        print("⚠️ 常见路径未命中，启动全局地毯式搜索...")
        csv_target, img_target = auto_find_deepweeds()
    else:
        print(f"▶️ 成功命中 DeepWeeds 路径！\nCSV: {csv_target}\nIMG: {img_target}")
        
    PROCESSED_DEEPWEEDS_DIR = '/kaggle/working/processed_deepweeds/'
    
    if csv_target and img_target:
        if not os.path.exists(PROCESSED_DEEPWEEDS_DIR):
            prepare_deepweeds_data(csv_target, img_target, PROCESSED_DEEPWEEDS_DIR)
        
        # 执行 EfficientNet 训练
        train_efficientnet_classifier(
            data_dir=PROCESSED_DEEPWEEDS_DIR,
            epochs=20,       
            batch_size=32,
            save_path='/kaggle/working/best_efficientnet.pth'
        )
    else:
        print("\n⚠️ 依旧未检测到 DeepWeeds 数据集。请确保已挂载名为 'DeepWeeds' 的数据集。")

    # ---------------------------------------------------------
    # 阶段 2: 训练 YOLO11 (使用 target-and-eliminate-weed 数据集)
    # ---------------------------------------------------------
    # 自动探测真实的 YOLO 农田检测数据集路径 (YOLO上次没问题，保留原样)
    TARGET_WEED_DATA_PATHS = [
        '/kaggle/input/datasets/jirayia/target-and-eliminate-weed/data',
        '/kaggle/input/datasets/jirayia/target-and-eliminate-weed',
        '/kaggle/input/target-and-eliminate-weed/data',
        '/kaggle/input/target-and-eliminate-weed'
    ]
    
    yolo_data_target = find_valid_path(TARGET_WEED_DATA_PATHS)
    PROCESSED_YOLO_DIR = '/kaggle/working/yolo_dataset_ready'
    
    if yolo_data_target:
        print("\n▶️ 成功探测到目标检测数据集路径！")
        yaml_path = prepare_target_weed_yolo_data(yolo_data_target, PROCESSED_YOLO_DIR)
        
        if yaml_path:
            train_yolo_detector(
                data_yaml_path=yaml_path, 
                epochs=30,
                project_path='/kaggle/working/'
            )
    else:
        print(f"\n⚠️ 未检测到目标检测数据集。请确认挂载状态！")
