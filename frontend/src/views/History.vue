<template>
  <div class="history-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><Clock /></el-icon>
        历史记录
      </h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="fetchHistory"
          class="date-picker"
        />
        <el-button size="small" @click="fetchHistory">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <div class="history-content" v-loading="loading">
      <div v-if="historyList.length === 0" class="empty-state">
        <el-icon :size="64"><FolderOpened /></el-icon>
        <p>暂无检测记录</p>
      </div>
      <div v-else class="history-grid">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-card"
          @click="showDetail(item)"
        >
          <div class="card-image">
            <img :src="getFullUrl(item.image_url)" :alt="item.filename" />
            <div class="image-overlay">
              <el-icon :size="28"><ZoomIn /></el-icon>
              <span>查看详情</span>
            </div>
          </div>
          <div class="card-info">
            <div class="card-filename" :title="item.filename || item.id">
              {{ item.filename || item.id }}
            </div>
            <div class="card-meta">
              <el-tag size="small" effect="dark" type="success">
                {{ item.total_objects }} 个目标
              </el-tag>
              <span class="card-date">{{ formatDate(item.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="totalRecords > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalRecords"
          layout="prev, pager, next"
          background
          @current-change="fetchHistory"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="检测详情"
      width="720px"
      :close-on-click-modal="true"
      class="detail-dialog"
    >
      <div class="detail-content" v-if="detailItem">
        <div class="detail-image-wrapper">
          <img
            :src="getFullUrl(detailItem.result_image_url || detailItem.image_url)"
            alt="检测结果"
            class="detail-image"
          />
        </div>
        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">检测目标数</span>
            <span class="meta-value">{{ detailItem.total_objects }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">模型</span>
            <span class="meta-value">{{ detailItem.model_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">时间</span>
            <span class="meta-value">{{ formatDate(detailItem.created_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">文件名</span>
            <span class="meta-value">{{ detailItem.filename || '-' }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Clock, Refresh, FolderOpened, ZoomIn } from '@element-plus/icons-vue'
import { getHistoryList } from '@/api/history'
import type { HistoryItem } from '@/api/types'
import type { HistoryResponse } from '@/api/types'

const historyList = ref<HistoryItem[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 12
const totalRecords = ref(0)
const dateRange = ref<[string, string] | null>(null)

const detailVisible = ref(false)
const detailItem = ref<HistoryItem | null>(null)

onMounted(() => {
  fetchHistory()
})

async function fetchHistory() {
  loading.value = true
  try {
    const res: HistoryResponse = await getHistoryList({
      page: currentPage.value,
      page_size: pageSize,
    })
    if (res.success || res.data) {
      historyList.value = res.data
      totalRecords.value = res.total || 0
    }
  } catch (error) {
    console.error('获取历史记录失败:', error)
    // Mock 数据
    historyList.value = getMockHistory()
    totalRecords.value = 10
  } finally {
    loading.value = false
  }
}

function getFullUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return 'http://localhost:8000' + url
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${min}`
}

function showDetail(item: HistoryItem) {
  detailItem.value = item
  detailVisible.value = true
}

function getMockHistory(): HistoryItem[] {
  const items: HistoryItem[] = []
  for (let i = 1; i <= 10; i++) {
    items.push({
      id: `mock-${i}`,
      image_url: '',
      result_image_url: '',
      total_objects: Math.floor(Math.random() * 8) + 1,
      created_at: new Date(Date.now() - i * 86400000).toISOString(),
      model_name: 'rsod-yolo11n',
      filename: `remote_sensing_${i}.jpg`,
      status: 'completed',
      type: 'single',
      time: `${Math.floor(Math.random() * 3) + 1}小时前`,
      count: Math.floor(Math.random() * 5) + 1,
    })
  }
  return items
}
</script>

<style scoped>
.history-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #e8ecf4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title .el-icon {
  color: #409EFF;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-picker {
  width: 260px;
}

.history-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: rgba(200, 214, 229, 0.3);
}

.empty-state p {
  margin-top: 12px;
  color: rgba(200, 214, 229, 0.4);
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.history-card {
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-card:hover {
  border-color: rgba(64, 158, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.1);
}

.card-image {
  width: 100%;
  height: 160px;
  background: rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #e8ecf4;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.3s;
}

.history-card:hover .image-overlay {
  opacity: 1;
}

.card-info {
  padding: 12px 14px;
}

.card-filename {
  font-size: 13px;
  color: #c8d6e5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-date {
  font-size: 11px;
  color: rgba(200, 214, 229, 0.4);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.detail-image-wrapper {
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: rgba(0, 0, 0, 0.2);
}

.detail-image {
  width: 100%;
  display: block;
}

.detail-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.meta-item {
  background: rgba(64, 158, 255, 0.05);
  border: 1px solid rgba(64, 158, 255, 0.08);
  border-radius: 8px;
  padding: 12px;
}

.meta-label {
  display: block;
  font-size: 11px;
  color: rgba(200, 214, 229, 0.5);
  margin-bottom: 4px;
}

.meta-value {
  font-size: 15px;
  font-weight: 600;
  color: #e8ecf4;
}
</style>

<style>
.detail-dialog .el-dialog {
  background: #0d1137 !important;
  border: 1px solid rgba(64, 158, 255, 0.2) !important;
  border-radius: 12px !important;
}

.detail-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.detail-dialog .el-dialog__title {
  color: #e8ecf4 !important;
}

.detail-dialog .el-dialog__close {
  color: rgba(200, 214, 229, 0.5) !important;
}
</style>