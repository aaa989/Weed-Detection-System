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
        </div>
      </div>

      <div class="result-section">
        <div class="section-card result-card">
          <ResultViewer :result="detectionResult" />
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

const batchFileList = ref<any[]>([])
const batchTaskId = ref('')
const batchStatus = ref('')
const batchProgress = ref(0)
const batchTotal = ref(0)
const batchCompleted = ref(0)
const batchFailed = ref(0)

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

function onModeChange() {
  detectionResult.value = null
  batchFileList.value = []
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
    const res = await detectSingleImage(uploadFile.value)
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
    const formData = new FormData()
    batchFileList.value.forEach((file: any) => {
      if (file.raw) {
        formData.append('files', file.raw)
      }
    })

    const res = await batchUpload(formData)
    if (res.success) {
      batchTaskId.value = res.task_id
      batchTotal.value = res.total
      batchStatus.value = 'pending'
      batchProgress.value = 0
      batchCompleted.value = 0
      batchFailed.value = 0
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
</style>