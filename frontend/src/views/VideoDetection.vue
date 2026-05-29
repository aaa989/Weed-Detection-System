<template>
  <div class="video-detection-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><VideoPlay /></el-icon>
        视频检测
      </h2>
      <el-tag v-if="isDetecting" type="success" effect="light" class="status-tag">
        <el-icon class="el-icon--left"><Check /></el-icon>
        实时检测中
      </el-tag>
      <el-tag v-else-if="currentDetection || hasResult" type="info" effect="light" class="status-tag">
        <el-icon class="el-icon--left"><CircleCheck /></el-icon>
        检测已结束
      </el-tag>
      <el-tag v-else type="info" effect="light" class="status-tag">
        <el-icon class="el-icon--left"><Upload /></el-icon>
        等待检测
      </el-tag>
    </div>

    <div class="detection-content">
      <div class="video-panel section-card">
        <div class="card-title">视频播放</div>

        <div v-if="!hasVideo" class="video-placeholder" @click="triggerFileInput">
          <el-icon class="placeholder-icon"><Monitor /></el-icon>
          <p class="placeholder-text">点击上传视频</p>
          <p class="placeholder-desc">支持 mp4、avi、mov 等格式</p>
          <input
            type="file"
            accept="video/*"
            class="video-file-input"
            ref="fileInputRef"
            @change="handleVideoUpload"
          />
        </div>

        <div v-else class="video-content">
          <div class="video-player-wrapper">
            <video
              ref="videoRef"
              :src="originalVideoUrl"
              class="video-player"
              :controls="!realtimeMode"
              @loadedmetadata="onVideoLoaded"
              @timeupdate="onTimeUpdate"
              @ended="onVideoEnded"
            />
            <canvas
              ref="canvasRef"
              class="detection-canvas"
              :class="{ 'canvas-active': realtimeMode && currentDetection }"
            />
          </div>

          <div v-if="realtimeMode" class="realtime-stats">
            <div class="stat-item">
              <span class="stat-label">当前帧</span>
              <span class="stat-value">{{ currentFrameIndex }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测目标</span>
              <span class="stat-value highlight">{{ currentDetection?.total_objects || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测耗时</span>
              <span class="stat-value">{{ currentDetection?.detection_time ? (currentDetection.detection_time * 1000).toFixed(0) : '0' }}ms</span>
            </div>
          </div>

          <div class="video-info">
            <div class="info-row">
              <span class="info-label">视频时长</span>
              <span class="info-value">{{ formatDuration(videoDuration) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前时间</span>
              <span class="info-value">{{ formatDuration(currentTime) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="result-card section-card">
          <div class="card-title">检测结果</div>

          <div v-if="!hasVideo" class="empty-state">
            <el-icon class="empty-icon"><Upload /></el-icon>
            <p class="empty-text">请上传视频开始检测</p>
          </div>

          <div v-else-if="!currentDetection && !hasResult && !isDetecting" class="empty-state">
            <el-icon class="empty-icon"><CircleCheck /></el-icon>
            <p class="empty-text">{{ realtimeMode ? '实时检测中...' : '等待检测' }}</p>
            <p class="empty-desc">点击开始检测按钮</p>
          </div>

          <div v-else class="result-content">
            <div v-if="currentDetection && realtimeMode" class="realtime-result">
              <div class="result-summary">
                <div class="summary-item">
                  <span class="summary-value">{{ currentDetection.total_objects }}</span>
                  <span class="summary-label">当前帧目标</span>
                </div>
              </div>

              <div v-if="currentDetection.boxes && currentDetection.boxes.length > 0" class="detection-list">
                <div
                  v-for="(box, index) in currentDetection.boxes"
                  :key="index"
                  class="detection-item"
                >
                  <span class="color-dot" :style="{ background: getClassColor(box.class_name) }" />
                  <span class="detection-name">{{ box.chinese_name || box.class_name }}</span>
                  <span class="detection-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <div v-else class="no-detection">
                <span>该帧未检测到目标</span>
              </div>
            </div>

            <div v-if="hasResult && taskStatus === 'completed'" class="full-result">
              <div class="result-summary">
                <div class="summary-item">
                  <span class="summary-value">{{ detectionCount }}</span>
                  <span class="summary-label">检测目标总数</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ elapsed ? Math.round(elapsed) : '-' }}</span>
                  <span class="summary-label">耗时(s)</span>
                </div>
              </div>

              <div class="detection-stats">
                <div class="detection-stat-item">
                  <span class="detection-stat-label">已处理帧</span>
                  <span class="detection-stat-value">{{ processedFrames }} / {{ totalFrames }}</span>
                </div>
              </div>

              <div v-if="detections.length > 0" class="detection-summary-list">
                <div v-for="(summary, index) in detectionSummary" :key="index" class="detection-item">
                  <span class="color-dot" :style="{ background: classColors[index % classColors.length] }" />
                  <span class="detection-name">{{ summary.name }}</span>
                  <span class="detection-confidence">{{ summary.count }}</span>
                </div>
              </div>

              <div style="margin-top: 16px; text-align: center">
                <el-button type="success" @click="downloadVideo">
                  <el-icon><Download /></el-icon>
                  下载检测结果视频
                </el-button>
              </div>
            </div>

            <div v-if="taskStatus === 'processing'" class="full-result">
              <el-progress
                :percentage="progress"
                :status="taskStatus === 'completed' ? 'success' : undefined"
                :stroke-width="16"
              />
              <div class="progress-stats">
                <div class="stat">
                  <span class="stat-label">已处理帧</span>
                  <span class="stat-num">{{ processedFrames }} / {{ totalFrames }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="action-card section-card">
          <div class="card-title">检测设置</div>

          <div class="mode-selection">
            <div class="mode-item">
              <el-radio
                v-model="detectionMode"
                label="realtime"
                :disabled="isDetecting"
              >
                实时检测
              </el-radio>
              <span class="mode-desc">视频播放时实时检测</span>
            </div>
            <div class="mode-item">
              <el-radio
                v-model="detectionMode"
                label="full"
                :disabled="isDetecting"
              >
                完整检测
              </el-radio>
              <span class="mode-desc">处理整个视频并保存结果</span>
            </div>
          </div>

          <div class="param-section">
            <div class="param-item">
              <div class="param-label">
                <span>置信度阈值</span>
                <span class="param-value">{{ confidenceThreshold.toFixed(2) }}</span>
              </div>
              <el-slider
                v-model="confidenceThreshold"
                :min="0.01"
                :max="0.9"
                :step="0.01"
                :disabled="isDetecting"
              />
              <div class="param-tip">更低阈值检测更多目标，可能产生假阳性</div>
            </div>

            <div class="param-item" v-if="detectionMode === 'full'">
              <div class="param-label">
                <span>检测帧间隔</span>
                <span class="param-value">{{ frameInterval }}</span>
              </div>
              <el-slider
                v-model="frameInterval"
                :min="1"
                :max="30"
                :step="1"
                :disabled="isDetecting"
              />
              <div class="param-tip">每隔多少帧检测一次</div>
            </div>

            <div class="param-item" v-if="detectionMode === 'realtime'">
              <div class="param-label">
                <span>检测帧率</span>
                <span class="param-value">{{ detectionFPS }} fps</span>
              </div>
              <el-slider
                v-model="detectionFPS"
                :min="2"
                :max="15"
                :step="1"
                :disabled="isDetecting"
              />
              <div class="param-tip">每秒检测帧数（越高检测越频繁，延迟可能增加）</div>
            </div>
          </div>

          <div class="action-buttons">
            <el-button
              size="default"
              class="btn-upload"
              @click="triggerFileInput"
              :disabled="isDetecting"
            >
              <el-icon><Upload /></el-icon>
              上传视频
            </el-button>
            <el-button
              v-if="!realtimeMode || !isDetecting"
              type="primary"
              size="default"
              class="btn-detect"
              :disabled="!hasVideo || isDetecting"
              @click="performVideoDetection"
              :loading="isProcessing"
            >
              <el-icon><Search /></el-icon>
              {{ isProcessing ? '检测中...' : '开始检测' }}
            </el-button>
            <el-button
              v-else
              type="danger"
              size="default"
              class="btn-stop"
              @click="stopRealtimeDetection"
            >
              <el-icon><VideoPause /></el-icon>
              停止检测
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay, Search, Upload, UploadFilled, Download,
  Check, List, CircleCheck, Refresh, VideoPause, Monitor,
} from '@element-plus/icons-vue'
import { detectRealtimeFrame } from '@/api/detection'
import { videoUploadAndDetect, getVideoStatus } from '@/api/video'

const videoRef = ref(null)
const canvasRef = ref(null)
const fileInputRef = ref(null)
const hasVideo = ref(false)
const originalVideoUrl = ref(null)
const videoDuration = ref(0)
const currentTime = ref(0)
const currentFrameIndex = ref(0)

const isDetecting = ref(false)
const isProcessing = ref(false)
const detectionResult = ref(null)
const currentDetection = ref(null)
const detectionMode = ref('realtime')

const confidenceThreshold = ref(0.25)
const iouThreshold = ref(0.7)
const frameInterval = ref(10)
const detectionFPS = ref(5)

const taskId = ref('')
const taskStatus = ref('')
const progress = ref(0)
const processedFrames = ref(0)
const totalFrames = ref(0)
const detectionCount = ref(0)
const elapsed = ref(0)
const detections = ref([])

const classColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD93D', '#6C5CE7']
const classColorMap = {
  'crop': '#4ECDC4',
  'weed': '#FF6B6B',
}

let detectionTimer = null
let canvasContext = null
let animationFrameId = null
let lastBoxes = []
let lastVideoWidth = 0
let lastVideoHeight = 0
let isProcessingFrame = false
let pollTimer = null

const realtimeMode = computed(() => detectionMode.value === 'realtime')
const hasResult = computed(() => taskStatus.value === 'completed' || taskStatus.value === 'failed')

const detectionSummary = computed(() => {
  const stats = {}
  detections.value.forEach(d => {
    const key = d.class_name
    if (!stats[key]) stats[key] = { name: d.chinese_name || d.class_name, count: 0 }
    stats[key].count++
  })
  return Object.values(stats)
})

function getClassColor(className) {
  return classColorMap[className] || '#FF6B6B'
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleVideoUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (originalVideoUrl.value) {
    URL.revokeObjectURL(originalVideoUrl.value)
  }

  originalVideoUrl.value = URL.createObjectURL(file)
  hasVideo.value = true
  detectionResult.value = null
  currentDetection.value = null
  currentFrameIndex.value = 0
  currentTime.value = 0
  taskId.value = ''
  taskStatus.value = ''
}

function onVideoLoaded() {
  const video = videoRef.value
  if (video) {
    videoDuration.value = video.duration
    nextTick(() => initCanvas())
  }
}

function onTimeUpdate() {
  const video = videoRef.value
  if (video) {
    currentTime.value = video.currentTime
  }
}

function onVideoEnded() {
  if (realtimeMode.value && isDetecting.value) {
    stopRealtimeDetection()
    ElMessage.success('视频播放完成，检测结束')
  }
}

function initCanvas() {
  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas) return

  const displayWidth = video.clientWidth || video.offsetWidth
  const displayHeight = video.clientHeight || video.offsetHeight
  canvas.width = displayWidth
  canvas.height = displayHeight
  canvasContext = canvas.getContext('2d')
}

function clearCanvas() {
  if (!canvasContext || !canvasRef.value) return
  canvasContext.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
}

function drawDetectionBoxes(boxes, videoWidth, videoHeight, interpolate = false) {
  if (!canvasContext || !canvasRef.value || !videoRef.value) return

  const canvas = canvasRef.value
  const video = videoRef.value

  const displayWidth = video.clientWidth || video.offsetWidth
  const displayHeight = video.clientHeight || video.offsetHeight

  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth
    canvas.height = displayHeight
  }

  const scaleX = displayWidth / videoWidth
  const scaleY = displayHeight / videoHeight

  canvasContext.clearRect(0, 0, displayWidth, displayHeight)

  let boxesToDraw = boxes
  if (interpolate && lastBoxes.length > 0) {
    boxesToDraw = lastBoxes
    videoWidth = lastVideoWidth
    videoHeight = lastVideoHeight
  }

  boxesToDraw.forEach((box) => {
    const x1 = box.x1 * scaleX
    const y1 = box.y1 * scaleY
    const x2 = box.x2 * scaleX
    const y2 = box.y2 * scaleY
    const color = getClassColor(box.class_name)

    canvasContext.strokeStyle = color
    canvasContext.lineWidth = 2
    canvasContext.strokeRect(x1, y1, x2 - x1, y2 - y1)

    canvasContext.fillStyle = color
    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`
    const labelWidth = canvasContext.measureText(label).width + 10
    canvasContext.fillRect(x1, y1 - 20, labelWidth, 20)

    canvasContext.fillStyle = '#FFFFFF'
    canvasContext.font = '14px Arial'
    canvasContext.fillText(label, x1 + 5, y1 - 5)
  })

  if (!interpolate) {
    lastBoxes = boxes
    lastVideoWidth = videoWidth
    lastVideoHeight = videoHeight
  }
}

function animateCanvas() {
  if (!isDetecting.value) return

  const video = videoRef.value
  if (video && !video.paused && !video.ended && lastBoxes.length > 0 && lastVideoWidth > 0) {
    drawDetectionBoxes([], lastVideoWidth, lastVideoHeight, true)
  }

  animationFrameId = requestAnimationFrame(animateCanvas)
}

async function captureAndDetectFrame() {
  const video = videoRef.value
  if (!video || video.paused || video.ended || isProcessingFrame) return

  isProcessingFrame = true

  try {
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = video.videoWidth
    tempCanvas.height = video.videoHeight
    const ctx = tempCanvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    const blob = await new Promise((resolve) => {
      tempCanvas.toBlob((b) => resolve(b), 'image/jpeg', 0.6)
    })

    if (!blob) {
      isProcessingFrame = false
      return
    }

    const formData = new FormData()
    formData.append('file', blob, 'frame.jpg')
    formData.append('confidence_threshold', confidenceThreshold.value.toString())
    formData.append('iou_threshold', iouThreshold.value.toString())

    const response = await detectRealtimeFrame(formData)

    if (response.success && response.data) {
      currentDetection.value = response.data
      drawDetectionBoxes(response.data.boxes || [], response.data.image_width, response.data.image_height)
      currentFrameIndex.value++
    }
  } catch (error) {
    console.error('帧检测失败:', error)
  } finally {
    isProcessingFrame = false
  }
}

async function startRealtimeDetection() {
  const video = videoRef.value
  if (!video) {
    ElMessage.error('视频未加载')
    return
  }

  if (video.readyState < 2) {
    ElMessage.info('正在加载视频，请稍候...')
    await new Promise((resolve) => {
      video.onloadeddata = resolve
      setTimeout(resolve, 10000)
    })
  }

  if (video.readyState < 2) {
    ElMessage.error('视频加载失败')
    return
  }

  isDetecting.value = true
  isProcessing.value = true
  currentDetection.value = null
  currentFrameIndex.value = 0
  lastBoxes = []
  isProcessingFrame = false

  nextTick(() => {
    initCanvas()
    clearCanvas()
  })

  await nextTick()

  try {
    await video.play()
    ElMessage.success('开始实时检测')
  } catch (err) {
    console.error('播放失败:', err)
    ElMessage.warning('自动播放被阻止，请手动点击播放')
  }

  animateCanvas()

  const intervalMs = Math.floor(1000 / detectionFPS.value)
  detectionTimer = setInterval(captureAndDetectFrame, intervalMs)
}

function stopRealtimeDetection() {
  const video = videoRef.value

  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  if (video) {
    video.pause()
  }

  isDetecting.value = false
  isProcessing.value = false
  clearCanvas()
  lastBoxes = []
  isProcessingFrame = false
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const res = await getVideoStatus(taskId.value)
      if (res.success) {
        taskStatus.value = res.status
        progress.value = res.progress || 0
        processedFrames.value = res.processed_frames || 0
        totalFrames.value = res.total_frames || 0
        detectionCount.value = (res.detections || []).length
        detections.value = res.detections || []
        elapsed.value = res.elapsed ? Math.round(res.elapsed) : 0

        if (res.status === 'completed' || res.status === 'failed') {
          stopPolling()
          isProcessing.value = false
          if (res.status === 'completed') {
            ElMessage.success(`视频检测完成！检测到 ${detectionCount.value} 个目标`)
          } else {
            ElMessage.error(res.error || '视频检测失败')
          }
        }
      }
    } catch (error) {
      console.error('Poll status error:', error)
    }
  }, 3000)
}

async function performVideoDetection() {
  if (!originalVideoUrl.value) {
    ElMessage.warning('请先上传视频')
    return
  }

  if (realtimeMode.value) {
    startRealtimeDetection()
    return
  }

  try {
    isProcessing.value = true

    const videoBlob = await fetch(originalVideoUrl.value).then((res) => res.blob())

    const formData = new FormData()
    formData.append('file', videoBlob, 'video.mp4')
    formData.append('frame_interval', frameInterval.value.toString())
    formData.append('model_name', 'rsod-yolo11n')

    const res = await videoUploadAndDetect(formData)
    if (res.success) {
      taskId.value = res.task_id
      taskStatus.value = 'processing'
      ElMessage.success('视频检测任务已启动')
      startPolling()
    } else {
      ElMessage.error(res.message || '任务启动失败')
      isProcessing.value = false
    }
  } catch (error) {
    console.error('视频检测错误:', error)
    ElMessage.error('检测失败，请稍后重试')
    isProcessing.value = false
  }
}

function downloadVideo() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  window.open(`${baseUrl}/detection/video/download/${taskId.value}`, '_blank')
}

watch(detectionMode, (newMode) => {
  if (newMode === 'realtime' && isDetecting.value) {
    stopRealtimeDetection()
  }
})

onBeforeUnmount(() => {
  stopRealtimeDetection()
  stopPolling()
  if (originalVideoUrl.value) {
    URL.revokeObjectURL(originalVideoUrl.value)
  }
})
</script>

<style scoped>
.video-detection-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
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

.status-tag {
  font-size: 12px;
}

.detection-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  min-height: 0;
}

.section-card {
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #c8d6e5;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
}

.result-card {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.video-panel {
  min-height: 0;
  overflow: hidden;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 400px;
  border: 2px dashed rgba(64, 158, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.video-placeholder:hover {
  border-color: #409EFF;
  background: rgba(64, 158, 255, 0.05);
}

.placeholder-icon {
  font-size: 64px;
  color: #409EFF;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 16px;
  color: #c8d6e5;
  margin: 8px 0;
}

.placeholder-desc {
  font-size: 14px;
  color: #909399;
}

.video-file-input {
  display: none;
}

.video-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.video-player-wrapper {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-player {
  width: 100%;
  display: block;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.detection-canvas.canvas-active {
  opacity: 1;
}

.realtime-stats {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.stat-value.highlight {
  color: #ffd04b;
}

.video-info {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: #909399;
  font-size: 14px;
}

.info-value {
  color: #c8d6e5;
  font-size: 14px;
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #409EFF;
}

.empty-text {
  font-size: 16px;
  color: #c8d6e5;
  margin: 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: #909399;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-summary {
  display: flex;
  gap: 16px;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #409EFF;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.detection-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detection-stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.detection-stat-label {
  color: #909399;
  font-size: 14px;
}

.detection-stat-value {
  color: #c8d6e5;
  font-size: 14px;
}

.detection-list,
.detection-summary-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
  font-size: 14px;
}

.detection-name {
  color: #c8d6e5;
}

.detection-confidence {
  color: #409EFF;
  font-weight: 500;
}

.no-detection {
  padding: 20px;
  text-align: center;
  color: #909399;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
}

.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.progress-stats {
  display: flex;
  gap: 24px;
  margin-top: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: #409EFF;
  font-family: 'Courier New', monospace;
}

.action-card {
  flex-shrink: 0;
}

.mode-selection {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.mode-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mode-desc {
  font-size: 12px;
  color: #909399;
  margin-left: 24px;
}

.param-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #c8d6e5;
}

.param-value {
  color: #409EFF;
  font-weight: 500;
}

.param-tip {
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-upload {
  flex: 1;
}

.btn-detect,
.btn-stop {
  flex: 2;
}
</style>
