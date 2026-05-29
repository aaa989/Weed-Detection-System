<template>
  <div class="history-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon :size="22"><Document /></el-icon>
          检测历史记录
        </h1>
        <p class="page-subtitle">查看和管理您的所有检测记录</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ totalRecords }}</span>
          <span class="stat-label">总记录</span>
        </div>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名..."
        clearable
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="filterType"
        placeholder="检测类型"
        clearable
        size="default"
        class="filter-select"
      >
        <el-option label="全部类型" value="" />
        <el-option label="单图检测" value="single" />
        <el-option label="批量检测" value="batch" />
        <el-option label="视频检测" value="video" />
      </el-select>

      <el-button
        type="primary"
        plain
        @click="fetchHistory"
        :loading="isLoading"
      >
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <div class="history-list" v-loading="isLoading">
      <transition-group name="list" tag="div">
        <div
          v-for="record in filteredRecords"
          :key="record.id"
          class="history-card"
          @click="viewRecord(record)"
        >
          <div class="record-preview">
            <img
              :src="getImageUrl(record.result_image_url || record.image_url)"
              :alt="record.filename"
              class="preview-image"
              @error="onImageError"
            />
            <div class="status-badge" :class="record.status">
              <el-icon><component :is="getStatusIcon(record.status)" /></el-icon>
              {{ getStatusText(record.status) }}
            </div>
          </div>

          <div class="record-info">
            <div class="record-header">
              <span class="record-filename">{{ record.filename }}</span>
              <el-tag size="small" :type="getTypeTagType(record.type)">
                {{ getTypeText(record.type) }}
              </el-tag>
            </div>
            <div class="record-meta">
              <span class="meta-item">
                <el-icon><Clock /></el-icon>
                {{ record.time }}
              </span>
              <span class="meta-item">
                <el-icon><Aim /></el-icon>
                {{ record.total_objects }} 个目标
              </span>
              <span class="meta-item">
                <el-icon><Cpu /></el-icon>
                {{ record.model_name }}
              </span>
            </div>
            <div class="record-tags" v-if="record.detectedTargets && record.detectedTargets.length">
              <span
                v-for="tag in record.detectedTargets"
                :key="tag"
                class="detected-tag"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="record-actions">
            <el-button size="small" @click.stop="viewRecord(record)">
              <el-icon><Monitor/></el-icon>
              查看
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click.stop="deleteRecord(record)"
            >
              <el-icon><Delete/></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </transition-group>
    </div>

    <div v-if="filteredRecords.length === 0 && !isLoading" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Document /></el-icon>
      <p class="empty-text">暂无检测记录</p>
      <el-button type="primary" @click="goToDetection">
        <el-icon><Plus /></el-icon>
        开始检测
      </el-button>
    </div>

    <div class="pagination-wrapper">
      <el-pagination
        v-if="totalRecords > pageSize"
        :total="totalRecords"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        layout="prev, pager, next, total"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="检测详情"
      width="700px"
      destroy-on-close
    >
      <div class="detail-content" v-if="selectedRecord">
        <div class="detail-images">
          <div class="detail-image-item">
            <div class="image-label">检测结果</div>
            <img
              :src="getImageUrl(selectedRecord.result_image_url || selectedRecord.image_url)"
              alt="检测结果"
              class="detail-image"
            />
          </div>
        </div>
        <div class="detail-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件名">{{ selectedRecord.filename }}</el-descriptions-item>
            <el-descriptions-item label="检测类型">{{ getTypeText(selectedRecord.type) }}</el-descriptions-item>
            <el-descriptions-item label="检测模型">{{ selectedRecord.model_name }}</el-descriptions-item>
            <el-descriptions-item label="检测状态">
              <el-tag :type="selectedRecord.status === 'completed' ? 'success' : 'danger'" size="small">
                {{ getStatusText(selectedRecord.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="检测目标数">{{ selectedRecord.total_objects }}</el-descriptions-item>
            <el-descriptions-item label="检测时间">{{ selectedRecord.time }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Clock,
  Aim,
  Monitor,
  Delete,
  Plus,
  Document,
  Refresh,
  CircleCheck,
  Loading,
  CircleClose,
  Cpu,
} from "@element-plus/icons-vue";
import { getHistoryList, deleteDetectionRecord } from "../api/history";

const router = useRouter();

const searchQuery = ref("");
const filterType = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const isLoading = ref(false);

const historyRecords = ref([]);
const totalRecords = ref(0);

const detailVisible = ref(false);
const selectedRecord = ref(null);

const fetchHistory = async () => {
  isLoading.value = true;
  try {
    const response = await getHistoryList({
      page: currentPage.value,
      page_size: pageSize.value,
    });
    if (response.success) {
      historyRecords.value = response.data || [];
      totalRecords.value = response.total || 0;
    }
  } catch (error) {
    console.error("获取历史记录失败:", error);
    historyRecords.value = [];
    totalRecords.value = 0;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchHistory();
});

const filteredRecords = computed(() => {
  return historyRecords.value.filter((record) => {
    const matchesSearch =
      !searchQuery.value ||
      record.filename.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesType = !filterType.value || record.type === filterType.value;
    return matchesSearch && matchesType;
  });
});

const getImageUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return "http://localhost:8000" + url;
};

const onImageError = (e) => {
  e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'%3E%3Crect fill='%23f0f0f0' width='120' height='80'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='12' x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle'%3E暂无图片%3C/text%3E%3C/svg%3E";
};

const getStatusIcon = (status) => {
  const icons = { completed: CircleCheck, processing: Loading, failed: CircleClose };
  return icons[status] || CircleCheck;
};

const getStatusText = (status) => {
  const texts = { completed: "检测完成", processing: "检测中", failed: "失败" };
  return texts[status] || status;
};

const getTypeText = (type) => {
  const texts = { single: "单图检测", batch: "批量检测", video: "视频检测" };
  return texts[type] || type;
};

const getTypeTagType = (type) => {
  const map = { single: "", batch: "warning", video: "success" };
  return map[type] || "info";
};

const viewRecord = (record) => {
  selectedRecord.value = record;
  detailVisible.value = true;
};

const deleteRecord = async (record) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除记录 "${record.filename}" 吗？此操作不可恢复。`,
      "删除确认",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
    );
    try {
      await deleteDetectionRecord(record.id);
      ElMessage.success("删除成功");
      fetchHistory();
    } catch (e) {
      ElMessage.error("删除失败");
    }
  } catch {
    // cancelled
  }
};

const goToDetection = () => {
  router.push("/detection");
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchHistory();
};
</script>

<style scoped lang="scss">
.history-page {
  width: 100%;

  .page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;

    .header-left {
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

    .header-stats {
      display: flex;
      gap: 16px;

      .stat-item {
        background: #fff;
        padding: 12px 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: var(--card-shadow);

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
          color: var(--primary-color);
        }

        .stat-label {
          font-size: 12px;
          color: var(--text-secondary);
        }
      }
    }
  }

  .search-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    align-items: center;

    .search-input {
      width: 280px;
    }

    .filter-select {
      width: 140px;
    }
  }

  .history-list {
    min-height: 200px;
  }

  .history-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: var(--card-shadow);
    display: flex;
    align-items: center;
    gap: 20px;
    cursor: pointer;
    transition: all 0.25s ease;
    margin-bottom: 12px;
    border: 1px solid transparent;

    &:hover {
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
      border-color: var(--primary-light);
    }

    .record-preview {
      position: relative;
      width: 120px;
      height: 80px;
      border-radius: 8px;
      overflow: hidden;
      flex-shrink: 0;
      background: #f5f5f5;

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .status-badge {
        position: absolute;
        bottom: 6px;
        left: 6px;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 11px;
        display: flex;
        align-items: center;
        gap: 3px;
        backdrop-filter: blur(4px);

        &.completed {
          background-color: rgba(34, 197, 94, 0.9);
          color: white;
        }

        &.processing {
          background-color: rgba(59, 130, 246, 0.9);
          color: white;
        }

        &.failed {
          background-color: rgba(239, 68, 68, 0.9);
          color: white;
        }
      }
    }

    .record-info {
      flex: 1;
      min-width: 0;

      .record-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;

        .record-filename {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .record-meta {
        display: flex;
        gap: 20px;
        margin-bottom: 6px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: var(--text-secondary);

          :deep(.el-icon) {
            font-size: 13px;
          }
        }
      }

      .record-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;

        .detected-tag {
          padding: 2px 8px;
          background-color: rgba(39, 174, 96, 0.1);
          color: #27ae60;
          border-radius: 4px;
          font-size: 11px;
        }
      }
    }

    .record-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 0;

    .empty-icon {
      color: #d1d5db;
      margin-bottom: 16px;
    }

    .empty-text {
      font-size: 15px;
      color: var(--text-secondary);
      margin-bottom: 24px;
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 24px;
    padding-bottom: 20px;
  }

  .list-enter-active,
  .list-leave-active {
    transition: all 0.3s ease;
  }

  .list-enter-from {
    opacity: 0;
    transform: translateX(-20px);
  }

  .list-leave-to {
    opacity: 0;
    transform: translateX(20px);
  }
}

.detail-content {
  .detail-images {
    margin-bottom: 20px;

    .detail-image-item {
      .image-label {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
      }

      .detail-image {
        width: 100%;
        max-height: 400px;
        object-fit: contain;
        border-radius: 8px;
        background: #f5f5f5;
      }
    }
  }

  .detail-info {
    :deep(.el-descriptions) {
      .el-descriptions__label {
        width: 100px;
      }
    }
  }
}
</style>
