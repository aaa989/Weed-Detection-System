<template>
  <div class="detection-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><Picture /></el-icon>
        智能检测
      </h2>
      <div class="header-actions">
        <el-radio-group v-model="detectMode" size="small" @change="onModeChange">
          <el-radio-button value="single">单图检测</el-radio-button>
          <el-radio-button value="batch">批量检测</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="detection-content" :class="{ 'is-single': detectMode === 'single' }">
      <div class="upload-section">
        <div class="section-card">
          <div class="card-title">
            {{ detectMode === 'single' ? '上传图片' : '批量上传（最多50张）' }}
          </div>

          <template v-if="detectMode === 'single'">
            <ImageUploader v-model="uploadFile" />
          </template>

          <template v-else>
            <el-upload
              ref="batchUploadRef"
              :auto-upload="false"
              :limit="50"
              multiple
              accept="image/*"
              list-type="picture-card"
              v-model:file-list="batchFileList"
              :on-exceed="onExceed"
              :on-change="onBatchFileChange"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </template>

          <div v-if="detectMode === 'single'" class="threshold-section">
            <div class="threshold-label">
              <span>置信度阈值</span>
              <span class="threshold-value">{{ confidenceThreshold.toFixed(2) }}</span>
            </div>
            <el-slider
              v-model="confidenceThreshold"
              :min="0.05"
              :max="0.9"
              :step="0.05"
              :disabled="isDetecting"
            />
            <div class="threshold-tip">越低检出越多目标，越高越精准</div>
          </div>

          <div class="upload-actions">
            <el-button
              type="primary"
              :loading="isDetecting"
              :disabled="detectMode === 'single' ? !uploadFile : batchFileList.length === 0"
              @click="handleDetect"
              size="large"
              class="detect-btn"
            >
              <el-icon v-if="!isDetecting"><Search /></el-icon>
              {{ isDetecting ? '检测中...' : '开始检测' }}
            </el-button>
          </div>
        </div>

        <div v-if="detectMode === 'batch' && batchTaskId" class="section-card batch-progress-card">
          <div class="card-title">
            批量检测进度
            <el-tag :type="batchStatus === 'completed' ? 'success' : batchStatus === 'failed' ? 'danger' : 'warning'" size="small">
              {{ batchStatusText }}
            </el-tag>
          </div>
          <el-progress
            :percentage="batchProgress"
            :status="batchStatus === 'completed' ? 'success' : batchStatus === 'failed' ? 'exception' : undefined"
          />
          <div class="batch-stats">
            <span>已完成: {{ batchCompleted }}/{{ batchTotal }}</span>
            <span v-if="batchFailed > 0" class="failed-count">失败: {{ batchFailed }}</span>
          </div>
          <div v-if="batchCompletedResults.length > 0" class="batch-results-summary">
            <div class="summary-title">检测结果汇总</div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-label">总目标数</span>
                <span class="summary-value">{{ batchTotalObjects }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">平均耗时</span>
                <span class="summary-value">{{ batchAvgTime }}s</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">成功/总数</span>
                <span class="summary-value">{{ batchCompleted }}/{{ batchTotal }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="result-section">
        <div class="section-card result-card">
          <div v-if="detectMode === 'batch' && batchCompletedResults.length > 0" class="batch-result-header">
            <div class="result-tabs">
              <span
                v-for="(item, index) in batchCompletedResults"
                :key="index"
                class="result-tab"
                :class="{ active: currentBatchIndex === index }"
                @click="switchBatchResult(index)"
              >
                {{ index + 1 }}
              </span>
            </div>
            <span class="current-file-name">{{ currentBatchFileName }}</span>
          </div>
          <ResultViewer :result="currentDisplayResult" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElLoading, ElMessage } from 'element-plus'
import { Picture, Search, Plus } from '@element-plus/icons-vue'
import ImageUploader from '@/components/ImageUploader.vue'
import ResultViewer from '@/components/ResultViewer.vue'
import { detectSingleImage, batchUpload, getBatchStatus } from '@/api/detection'
import type { DetectionResult } from '@/api/types'

const detectMode = ref<'single' | 'batch'>('single')
const uploadFile = ref<File | null>(null)
const isDetecting = ref(false)
const detectionResult = ref<DetectionResult | null>(null)
const confidenceThreshold = ref(0.25)

const batchFileList = ref<any[]>([])
const batchTaskId = ref('')
const batchStatus = ref('')
const batchProgress = ref(0)
const batchTotal = ref(0)
const batchCompleted = ref(0)
const batchFailed = ref(0)
const batchResults = ref<any[]>([])
const currentBatchIndex = ref(0)

let batchPollTimer: ReturnType<typeof setInterval> | null = null

const batchStatusText = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[batchStatus.value] || batchStatus.value
})

const batchCompletedResults = computed(() => {
  return batchResults.value.filter((r: any) => r.status === 'completed' && r.result)
})

const currentBatchFileName = computed(() => {
  if (batchCompletedResults.value.length > 0 && currentBatchIndex.value < batchCompletedResults.value.length) {
    return batchCompletedResults.value[currentBatchIndex.value].filename || `图片 ${currentBatchIndex.value + 1}`
  }
  return ''
})

const currentDisplayResult = computed(() => {
  if (detectMode.value === 'batch' && batchCompletedResults.value.length > 0) {
    const item = batchCompletedResults.value[currentBatchIndex.value]
    if (item && item.result) {
      return {
        detection_id: item.result.detection_id,
        image_url: item.result.image_url || '',
        result_image_url: item.result.result_image_url || '',
        boxes: item.result.boxes || [],
        total_objects: item.result.total_objects || 0,
        detection_time: item.result.detection_time || 0,
        model_name: 'rsod-yolo11n',
        created_at: new Date().toISOString(),
      }
    }
  }
  return detectionResult.value
})

function switchBatchResult(index: number) {
  currentBatchIndex.value = index
}

const batchTotalObjects = computed(() => {
  return batchCompletedResults.value.reduce((sum: number, r: any) => sum + (r.result?.total_objects || 0), 0)
})

const batchAvgTime = computed(() => {
  if (batchCompletedResults.value.length === 0) return '0.00'
  const total = batchCompletedResults.value.reduce((sum: number, r: any) => sum + (r.result?.detection_time || 0), 0)
  return (total / batchCompletedResults.value.length).toFixed(2)
})

function getCurrentUserId(): string | null {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.id || null
  } catch {
    return null
  }
}

function onModeChange() {
  detectionResult.value = null
  batchFileList.value = []
  batchResults.value = []
  currentBatchIndex.value = 0
  stopBatchPolling()
  batchTaskId.value = ''
}

function onExceed() {
  ElMessage.warning('最多只能上传50张图片')
}

function onBatchFileChange(file: any) {
  if (!file.raw?.type?.startsWith('image/')) {
    batchFileList.value = batchFileList.value.filter(f => f.uid !== file.uid)
    ElMessage.warning('只支持图片文件')
  }
}

async function handleDetect() {
  if (detectMode.value === 'single') {
    await handleSingleDetect()
  } else {
    await handleBatchDetect()
  }
}

async function handleSingleDetect() {
  if (!uploadFile.value) return
  isDetecting.value = true
  const loading = ElLoading.service({
    lock: true,
    text: '正在检测中...',
    background: 'rgba(0, 0, 0, 0.7)',
  })
  const startTime = performance.now()

  try {
    const userId = getCurrentUserId()
    const res = await detectSingleImage(uploadFile.value, 'rsod-yolo11n', confidenceThreshold.value, userId)
    if (res.success && res.data) {
      detectionResult.value = {
        ...res.data,
        detection_time: (performance.now() - startTime) / 1000,
      }
    } else {
      ElMessage.error(res.message || '检测失败')
    }
  } catch (error) {
    ElMessage.error('检测请求失败，请检查后端服务')
    console.error(error)
  } finally {
    isDetecting.value = false
    loading.close()
  }
}

async function handleBatchDetect() {
  if (batchFileList.value.length === 0) return
  isDetecting.value = true

  try {
    const userId = getCurrentUserId()
    const formData = new FormData()
    batchFileList.value.forEach((file: any) => {
      if (file.raw) {
        formData.append('files', file.raw)
      }
    })
    if (userId) {
      formData.append('user_id', userId)
    }

    const res = await batchUpload(formData)
    if (res.success) {
      batchTaskId.value = res.task_id
      batchTotal.value = res.total
      batchStatus.value = 'pending'
      batchProgress.value = 0
      batchCompleted.value = 0
      batchFailed.value = 0
      batchResults.value = []
      ElMessage.success(`批量任务已创建，共 ${res.total} 张图片`)
      startBatchPolling()
    } else {
      ElMessage.error(res.message || '批量任务创建失败')
      isDetecting.value = false
    }
  } catch (error) {
    ElMessage.error('批量上传失败，请检查后端服务')
    console.error(error)
    isDetecting.value = false
  }
}

function startBatchPolling() {
  if (batchPollTimer) return
  batchPollTimer = setInterval(async () => {
    try {
      const res = await getBatchStatus(batchTaskId.value)
      if (res.success) {
        batchStatus.value = res.status
        batchCompleted.value = res.completed || 0
        batchFailed.value = res.failed || 0
        batchTotal.value = res.total || 0
        if (res.total > 0) {
          batchProgress.value = Math.round(((res.completed + res.failed) / res.total) * 100)
        }

        if (res.results && res.results.length > 0) {
          batchResults.value = res.results
        }

        if (res.status === 'completed' || res.status === 'failed') {
          stopBatchPolling()
          isDetecting.value = false
          if (res.status === 'completed') {
            ElMessage.success(`批量检测完成！成功: ${res.completed}, 失败: ${res.failed}`)
          }
        }
      }
    } catch (error) {
      console.error('Poll batch status error:', error)
    }
  }, 2000)
}

function stopBatchPolling() {
  if (batchPollTimer) {
    clearInterval(batchPollTimer)
    batchPollTimer = null
  }
}
</script>

<style scoped>
.detection-page {
  height: 100%;
  display: flex;
  flex-direction: column;
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

.header-actions :deep(.el-radio-button__inner) {
  background: rgba(64, 158, 255, 0.05);
  border-color: rgba(64, 158, 255, 0.15);
  color: #c8d6e5;
}

.header-actions :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(64, 158, 255, 0.2);
  border-color: #409EFF;
  color: #409EFF;
  box-shadow: none;
}

.detection-content {
  flex: 1;
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  min-height: 0;
}

.detection-content.is-single {
  grid-template-columns: 480px 1fr;
}

.section-card {
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #c8d6e5;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.upload-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.detect-btn {
  min-width: 140px;
}

.threshold-section {
  margin-top: 16px;
  padding: 12px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #c8d6e5;
  margin-bottom: 8px;
}

.threshold-value {
  color: #409EFF;
  font-weight: 600;
}

.threshold-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.batch-progress-card {
  margin-top: 16px;
}

.batch-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 13px;
  color: #c8d6e5;
}

.failed-count {
  color: #F56C6C;
}

.batch-results-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(64, 158, 255, 0.1);
}

.summary-title {
  font-size: 13px;
  font-weight: 600;
  color: #c8d6e5;
  margin-bottom: 12px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-item {
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.summary-label {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #409EFF;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-actions {
  margin-top: 16px;
}

.detect-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #409EFF, #36cfc9);
  border: none;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
}

.detect-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #529bff, #4fdad5);
}

.detect-btn:disabled {
  background: rgba(64, 158, 255, 0.2);
  color: rgba(200, 214, 229, 0.4);
}

.result-section {
  min-height: 0;
}

.result-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.batch-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.result-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.result-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.2);
  color: #c8d6e5;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-tab:hover {
  background: rgba(64, 158, 255, 0.2);
  border-color: #409EFF;
}

.result-tab.active {
  background: #409EFF;
  border-color: #409EFF;
  color: #fff;
  font-weight: 600;
}

.current-file-name {
  font-size: 12px;
  color: #909399;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>