<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon :size="22"><Setting /></el-icon>
        系统设置
      </h1>
      <p class="page-subtitle">管理系统配置和偏好设置</p>
    </div>

    <div class="settings-content">
      <div class="settings-section">
        <div class="section-title">
          <el-icon><Monitor /></el-icon>
          检测设置
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="label-text">默认置信度阈值</div>
            <div class="label-desc">检测结果的最低置信度要求，值越高越严格</div>
          </div>
          <div class="setting-control">
            <el-slider
              v-model="settings.confidence"
              :min="0.05"
              :max="0.95"
              :step="0.05"
              show-input
              :format-tooltip="(val) => (val * 100).toFixed(0) + '%'"
            />
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="label-text">默认检测模型</div>
            <div class="label-desc">选择默认使用的YOLO检测模型</div>
          </div>
          <div class="setting-control">
            <el-select v-model="settings.model" style="width: 200px">
              <el-option label="YOLO11n (推荐)" value="rsod-yolo11n" />
              <el-option label="YOLO11s (高精度)" value="rsod-yolo11s" />
            </el-select>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-title">
          <el-icon><View /></el-icon>
          界面设置
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="label-text">检测结果自动保存</div>
            <div class="label-desc">检测完成后自动保存结果到历史记录</div>
          </div>
          <div class="setting-control">
            <el-switch v-model="settings.autoSave" />
          </div>
        </div>
        <div class="setting-item">
          <div class="setting-label">
            <div class="label-text">显示检测框详情</div>
            <div class="label-desc">在结果图片上显示检测框的置信度和类别信息</div>
          </div>
          <div class="setting-control">
            <el-switch v-model="settings.showBoxDetails" />
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          系统信息
        </div>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">系统版本</div>
            <div class="info-value">v1.0.0</div>
          </div>
          <div class="info-item">
            <div class="info-label">前端框架</div>
            <div class="info-value">Vue 3 + Element Plus</div>
          </div>
          <div class="info-item">
            <div class="info-label">后端框架</div>
            <div class="info-value">FastAPI + SQLAlchemy</div>
          </div>
          <div class="info-item">
            <div class="info-label">检测模型</div>
            <div class="info-value">YOLO11</div>
          </div>
          <div class="info-item">
            <div class="info-label">数据库</div>
            <div class="info-value">PostgreSQL</div>
          </div>
          <div class="info-item">
            <div class="info-label">对象存储</div>
            <div class="info-value">MinIO</div>
          </div>
        </div>
      </div>

      <div class="settings-actions">
        <el-button type="primary" @click="saveSettings">
          <el-icon><Check /></el-icon>
          保存设置
        </el-button>
        <el-button plain @click="resetSettings">
          <el-icon><RefreshRight /></el-icon>
          恢复默认
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Setting,
  Monitor,
  View,
  InfoFilled,
  Check,
  RefreshRight,
} from "@element-plus/icons-vue";

const defaultSettings = {
  confidence: 0.25,
  model: "rsod-yolo11n",
  autoSave: true,
  showBoxDetails: true,
};

const settings = reactive({ ...defaultSettings });

const SETTINGS_KEY = "app_settings";

onMounted(() => {
  try {
    const saved = localStorage.getItem(SETTINGS_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      Object.assign(settings, parsed);
    }
  } catch {}
});

const saveSettings = () => {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  ElMessage.success("设置已保存");
};

const resetSettings = () => {
  Object.assign(settings, defaultSettings);
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(defaultSettings));
  ElMessage.success("已恢复默认设置");
};
</script>

<style scoped lang="scss">
.settings-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 22px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;

      .el-icon {
        color: var(--primary-color);
      }
    }

    .page-subtitle {
      font-size: 13px;
      color: var(--text-secondary);
    }
  }

  .settings-content {
    display: flex;
    flex-direction: column;
    gap: 24px;

    .settings-section {
      background-color: #ffffff;
      border-radius: 12px;
      padding: 24px;
      box-shadow: var(--card-shadow);

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-color);

        .el-icon {
          color: var(--primary-color);
        }
      }

      .setting-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        border-bottom: 1px solid #f3f4f6;

        &:last-child {
          border-bottom: none;
          padding-bottom: 0;
        }

        .setting-label {
          flex: 1;

          .label-text {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .label-desc {
            font-size: 12px;
            color: var(--text-secondary);
          }
        }

        .setting-control {
          width: 300px;
          flex-shrink: 0;
          display: flex;
          justify-content: flex-end;
        }
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;

        .info-item {
          background: #f9fafb;
          border-radius: 8px;
          padding: 14px 16px;

          .info-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 6px;
          }

          .info-value {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
          }
        }
      }
    }

    .settings-actions {
      display: flex;
      gap: 12px;
    }
  }
}
</style>
