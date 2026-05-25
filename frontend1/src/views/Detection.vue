<template>
  <div class="detection-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><Picture /></el-icon>
        智能检测
      </h2>
      <div class="header-actions">
        <el-radio-group v-model="detectMode" size="small">
          <el-radio-button value="single">单图检测</el-radio-button>
          <el-radio-button value="batch">批量检测</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="detection-content" :class="{ 'is-single': detectMode === 'single' }">
      <!-- 左侧上传区 -->
      <div class="upload-section">
        <div class="section-card">
          <div class="card-title">上传图片</div>
          <ImageUploader v-model="uploadFile" />
          <div class="upload-actions">
            <el-button
              type="primary"
              :loading="isDetecting"
              :disabled="!uploadFile"
              @click="handleDetect"
              size="large"
              class="detect-btn"
            >
              <el-icon v-if="!isDetecting"><Search /></el-icon>
              {{ isDetecting ? '检测中...' : '开始检测' }}
            </el-button>
          </div>
        </div>

        <BatchProgress
          :visible="detectMode === 'batch' && batchItems.length > 0"
          :items="batchItems"
        />
      </div>

      <!-- 右侧结果区 -->
      <div class="result-section">
        <div class="section-card result-card">
          <ResultViewer :result="detectionResult" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElLoading, ElMessage } from 'element-plus'
import { Picture, Search } from '@element-plus/icons-vue'
import ImageUploader from '@/components/ImageUploader.vue'
import ResultViewer from '@/components/ResultViewer.vue'
import BatchProgress from '@/components/BatchProgress.vue'
import { detectSingleImage } from '@/api/detection'
import type { DetectionResult, BatchDetectionItem } from '@/api/types'

const detectMode = ref<'single' | 'batch'>('single')
const uploadFile = ref<File | null>(null)
const isDetecting = ref(false)
const detectionResult = ref<DetectionResult | null>(null)
const batchItems = ref<BatchDetectionItem[]>([])

async function handleDetect() {
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
      const detectionTime = (performance.now() - startTime) / 1000
      detectionResult.value = {
        ...res.data,
        detection_time: detectionTime,
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

// Mock 数据演示
async function mockDetect() {
  if (!uploadFile.value) return
  isDetecting.value = true
  const loading = ElLoading.service({ lock: true, text: '正在检测中...', background: 'rgba(0, 0, 0, 0.7)' })
  const startTime = performance.now()

  setTimeout(() => {
    detectionResult.value = {
      detection_id: 'mock-' + Date.now(),
      image_url: URL.createObjectURL(uploadFile.value!),
      result_image_url: URL.createObjectURL(uploadFile.value!),
      boxes: [
        { x1: 50, y1: 30, x2: 150, y2: 130, confidence: 0.95, class_id: 0, class_name: 'aircraft', chinese_name: '飞机' },
        { x1: 200, y1: 60, x2: 320, y2: 180, confidence: 0.88, class_id: 0, class_name: 'aircraft', chinese_name: '飞机' },
        { x1: 350, y1: 100, x2: 450, y2: 200, confidence: 0.91, class_id: 1, class_name: 'oiltank', chinese_name: '油罐' },
        { x1: 100, y1: 200, x2: 220, y2: 320, confidence: 0.82, class_id: 2, class_name: 'overpass', chinese_name: '立交桥' },
        { x1: 300, y1: 250, x2: 400, y2: 350, confidence: 0.79, class_id: 3, class_name: 'playground', chinese_name: '操场' },
      ],
      total_objects: 5,
      detection_time: 0.52,
      model_name: 'rsod-yolo11n',
      created_at: new Date().toISOString(),
    }
    isDetecting.value = false
    loading.close()
  }, 2000)
}

// 取消注释下面这行，替换 handleDetect 中的 try 块以使用 mock 数据
// 如果后端未启动，可以在开发时使用 mockDetect
// handleDetect 已经实现真实调用，如需 Mock 请将下面函数绑定到按钮
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