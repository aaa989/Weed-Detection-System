<template>
  <div class="video-detection-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><VideoPlay /></el-icon>
        视频检测
      </h2>
    </div>

    <div class="detection-content">
      <div class="video-panel">
        <div class="panel-header">
          <span class="panel-title">视频检测</span>
          <el-tag :type="getTagType()" effect="light" class="result-tag">
            <el-icon class="el-icon--left" v-if="isRealtimeDetecting"><Check /></el-icon>
            <el-icon class="el-icon--left" v-else-if="currentDetection"><CircleCheck /></el-icon>
            <el-icon class="el-icon--left" v-else><Upload /></el-icon>
            {{ getTagText() }}
          </el-tag>
        </div>

        <div class="video-container">
          <div v-if="!hasVideo" class="video-placeholder" @click="triggerFileInput">
            <el-icon class="placeholder-icon"><Monitor /></el-icon>
            <p class="placeholder-text">点击上传视频</p>
            <p class="placeholder-desc">支持 mp4、avi、mov 等格式</p>
            <input
              type="file"
              accept="video/*"
              class="video-file-input"
              @change="handleVideoUpload"
            />
          </div>

          <div v-else class="video-content">
            <div class="video-player-wrapper">
              <video
                ref="videoRef"
                :src="originalVideoUrl"
                class="video-player"
                :controls="!isRealtimeDetecting"
                @loadedmetadata="onVideoLoaded"
                @timeupdate="onTimeUpdate"
                @ended="onVideoEnded"
              />
              <canvas
                ref="canvasRef"
                class="detection-canvas"
                :class="{ 'canvas-active': isRealtimeDetecting && currentDetection }"
              />
            </div>

            <div v-if="isRealtimeDetecting" class="realtime-stats">
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
                <span class="stat-value">{{ currentDetection?.detection_time?.toFixed(2) || '0' }}ms</span>
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
      </div>

      <div class="result-panel">
        <div class="result-card">
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span class="card-title">检测结果</span>
          </div>

          <div v-if="!hasVideo" class="empty-state">
            <el-icon class="empty-icon"><Upload /></el-icon>
            <p class="empty-text">请上传视频开始检测</p>
            <p class="empty-desc">上传遥感影像视频以识别目标</p>
          </div>

          <div v-else-if="!currentDetection && !hasFullResult" class="empty-state">
            <el-icon class="empty-icon"><CircleCheck /></el-icon>
            <p class="empty-text">{{ isRealtimeDetecting ? '实时检测中...' : '等待检测' }}</p>
            <p class="empty-desc">{{ isRealtimeDetecting ? '视频正在播放并实时检测' : '点击开始检测按钮' }}</p>
          </div>

          <div v-else class="result-content">
            <div v-if="currentDetection && isRealtimeDetecting" class="realtime-result">
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
                  <span class="detection-name">{{ box.chinese_name || box.class_name }}</span>
                  <span class="detection-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <div v-else class="no-detection">
                <span>该帧未检测到目标</span>
              </div>
            </div>

            <div v-if="hasFullResult" class="full-result">
              <div class="result-summary">
                <div class="summary-item">
                  <span class="summary-value">{{ detectionCount }}</span>
                  <span class="summary-label">检测目标总数</span>
                </div>
                <div class="summary-item">
                  <span class="summary-value">{{ elapsed || '-' }}</span>
                  <span class="summary-label">检测耗时(s)</span>
                </div>
              </div>

              <div v-if="detectionSummary.length > 0" class="detection-stats">
                <div v-for="(det, index) in detectionSummary" :key="index" class="summary-item-row">
                  <span class="color-dot" :style="{ background: classColors[index % classColors.length] }" />
                  <span class="summary-name">{{ det.name }}</span>
                  <span class="summary-count">{{ det.count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="action-card">
          <div class="action-header">
            <span class="action-title">检测设置</span>
          </div>

          <div class="mode-selection">
            <div class="mode-item">
              <el-radio v-model="detectionMode" label="realtime" :disabled="isProcessing">
                实时检测
              </el-radio>
              <span class="mode-desc">视频播放时实时检测</span>
            </div>
            <div class="mode-item">
              <el-radio v-model="detectionMode" label="full" :disabled="isProcessing">
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
                :disabled="isProcessing"
              />
            </div>

            <div class="param-item" v-if="detectionMode === 'full'">
              <div class="param-label">
                <span>检测帧间隔</span>
                <span class="param-value">{{ frameInterval }}</span>
              </div>
              <el-slider
                v-model="frameInterval"
                :min="1"
                :max="10"
                :step="1"
                :disabled="isProcessing"
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
                :disabled="isProcessing"
              />
              <div class="param-tip">每秒检测帧数（越高检测越频繁，但延迟可能增加）</div>
            </div>

            <div class="param-item" v-if="detectionMode === 'realtime'">
              <div class="param-tip">
                <ul style="margin: 8px 0 0 16px; padding: 0; font-size: 12px;">
                  <li>降低检测帧率可减少延迟</li>
                  <li>已启用图片压缩加速传输</li>
                  <li>检测框在检测间隔持续显示</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <el-button
              size="default"
              class="btn-upload"
              @click="triggerFileInput"
              :disabled="isProcessing"
            >
              <el-icon><Upload /></el-icon>
              上传视频
            </el-button>
            <el-button
              v-if="!isRealtimeDetecting"
              type="primary"
              size="default"
              class="btn-detect"
              :disabled="!hasVideo || isProcessing"
              @click="performDetection"
            >
              <el-icon><Refresh /></el-icon>
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

          <div v-if="fullTaskStatus === 'completed'" class="result-download-section">
            <el-button type="success" @click="downloadVideo" style="width: 100%; margin-top: 16px">
              <el-icon><Download /></el-icon>
              下载检测结果视频
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  Upload,
  Check,
  List,
  CircleCheck,
  Refresh,
  VideoPause,
  VideoPlay,
  Download,
} from '@element-plus/icons-vue'
import { detectRealtimeFrame } from '@/api/detection'
import { videoUploadAndDetect, getVideoStatus } from '@/api/video'

const videoRef = ref(null)
const canvasRef = ref(null)
const hasVideo = ref(false)
const originalVideoUrl = ref(null)
const videoDuration = ref(0)
const currentTime = ref(0)
const currentFrameIndex = ref(0)

const isRealtimeDetecting = ref(false)
const isProcessing = ref(false)
const currentDetection = ref(null)
const detectionMode = ref('realtime')

const confidenceThreshold = ref(0.25)
const frameInterval = ref(5)
const detectionFPS = ref(5)

const fullTaskId = ref('')
const fullTaskStatus = ref('')
const fullProgress = ref(0)
const processedFrames = ref(0)
const totalFrames = ref(0)
const detectionCount = ref(0)
const elapsed = ref(0)
const detectionsList = ref([])

let detectionTimer = null
let animationFrameId = null
let canvasContext = null
let pollTimer = null

let lastBoxes = []
let lastVideoWidth = 0
let lastVideoHeight = 0
let isProcessingFrame = false

const classColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#B37FEB']

const hasFullResult = computed(() => fullTaskStatus.value === 'completed')

const detectionSummary = computed(() => {
  const stats = {}
  detectionsList.value.forEach(d => {
    const key = d.class_name
    if (!stats[key]) stats[key] = { name: d.chinese_name || d.class_name, count: 0 }
    stats[key].count++
  })
  return Object.values(stats)
})

const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const getTagType = () => {
  if (isRealtimeDetecting.value) return 'success'
  if (currentDetection.value) return 'info'
  return 'info'
}

const getTagText = () => {
  if (isRealtimeDetecting.value) return '实时检测中'
  if (currentDetection.value) return '检测已结束'
  return '等待检测'
}

const triggerFileInput = () => {
  const input = document.querySelector('.video-file-input')
  if (input) input.click()
}

const handleVideoUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    if (originalVideoUrl.value) {
      URL.revokeObjectURL(originalVideoUrl.value)
    }

    originalVideoUrl.value = URL.createObjectURL(file)
    hasVideo.value = true
    currentDetection.value = null
    currentFrameIndex.value = 0
    currentTime.value = 0
    fullTaskStatus.value = ''
    detectionsList.value = []

    await nextTick()
    const video = videoRef.value
    if (video) {
      video.onloadedmetadata = () => {
        videoDuration.value = video.duration
      }
      video.onerror = () => {
        ElMessage.error('视频加载失败')
        hasVideo.value = false
      }
    }
  } catch (error) {
    console.error('视频加载失败:', error)
    ElMessage.error('视频加载失败')
  }
}

const onVideoLoaded = () => {
  const video = videoRef.value
  if (video) {
    videoDuration.value = video.duration
    nextTick(() => initCanvas())
  }
}

const onTimeUpdate = () => {
  const video = videoRef.value
  if (video) currentTime.value = video.currentTime
}

const onVideoEnded = () => {
  if (detectionMode.value === 'realtime' && isRealtimeDetecting.value) {
    stopRealtimeDetection()
    ElMessage.success('视频播放完成，检测结束')
  }
}

const initCanvas = () => {
  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas) return

  const displayWidth = video.clientWidth || video.offsetWidth
  const displayHeight = video.clientHeight || video.offsetHeight
  canvas.width = displayWidth
  canvas.height = displayHeight
  canvasContext = canvas.getContext('2d')
  canvasContext.clearRect(0, 0, canvas.width, canvas.height)
}

const clearCanvas = () => {
  if (!canvasContext || !canvasRef.value) return
  canvasContext.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
}

const drawDetectionBoxes = (boxes, videoWidth, videoHeight, interpolate = false) => {
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

  const colorMap = {
    'crop': '#67C23A',
    'weed': '#F56C6C',
    'aircraft': '#FF6B6B',
    'oiltank': '#4ECDC4',
    'overpass': '#45B7D1',
    'playground': '#96CEB4',
  }

  boxesToDraw.forEach((box) => {
    const x1 = box.x1 * scaleX
    const y1 = box.y1 * scaleY
    const x2 = box.x2 * scaleX
    const y2 = box.y2 * scaleY
    const color = colorMap[box.class_name] || '#FF6B6B'

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

const captureAndDetectFrame = async () => {
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
    formData.append('iou_threshold', '0.7')

    const response = await detectRealtimeFrame(formData)

    if (response.success && response.data) {
      currentDetection.value = response.data
      const boxes = response.data.boxes || []
      drawDetectionBoxes(boxes, response.data.image_width, response.data.image_height)
      currentFrameIndex.value++
    }
  } catch (error) {
    console.error('帧检测失败:', error)
  } finally {
    isProcessingFrame = false
  }
}

const animateCanvas = () => {
  if (!isRealtimeDetecting.value) return

  const video = videoRef.value
  if (video && !video.paused && !video.ended && lastBoxes.length > 0 && lastVideoWidth > 0) {
    drawDetectionBoxes([], lastVideoWidth, lastVideoHeight, true)
  }

  animationFrameId = requestAnimationFrame(animateCanvas)
}

const startRealtimeDetection = async () => {
  const video = videoRef.value
  if (!video) {
    ElMessage.error('视频未加载')
    return
  }

  if (video.readyState < 2) {
    ElMessage.info('正在加载视频，请稍候...')
    await new Promise((resolve) => {
      video.onloadeddata = resolve
      video.onerror = () => {
        ElMessage.error('视频加载失败')
        resolve()
      }
      setTimeout(resolve, 10000)
    })
  }

  if (video.readyState < 2) {
    ElMessage.error('视频加载失败')
    return
  }

  isRealtimeDetecting.value = true
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

const stopRealtimeDetection = () => {
  const video = videoRef.value

  if (detectionTimer) {
    clearInterval(detectionTimer)
    detectionTimer = null
  }

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  if (video) video.pause()

  isRealtimeDetecting.value = false
  isProcessing.value = false

  clearCanvas()
  lastBoxes = []
  isProcessingFrame = false
}

const startFullDetection = async () => {
  if (!originalVideoUrl.value) {
    ElMessage.warning('请先上传视频')
    return
  }

  try {
    isProcessing.value = true

    const videoFile = await fetch(originalVideoUrl.value).then((res) => res.blob())

    const formData = new FormData()
    formData.append('file', videoFile, 'video.mp4')
    formData.append('model_name', 'rsod-yolo11n')
    formData.append('frame_interval', String(frameInterval.value))

    const res = await videoUploadAndDetect(formData)
    if (res.success) {
      fullTaskId.value = res.task_id
      fullTaskStatus.value = 'processing'
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

const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const res = await getVideoStatus(fullTaskId.value)
      if (res.success) {
        fullTaskStatus.value = res.status
        fullProgress.value = res.progress || 0
        processedFrames.value = res.processed_frames || 0
        totalFrames.value = res.total_frames || 0
        detectionCount.value = (res.detections || []).length
        detectionsList.value = res.detections || []
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

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const performDetection = () => {
  if (!hasVideo.value) {
    ElMessage.warning('请先上传视频')
    return
  }

  if (detectionMode.value === 'realtime') {
    startRealtimeDetection()
  } else {
    startFullDetection()
  }
}

const downloadVideo = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  window.open(`${baseUrl}/detection/video/download/${fullTaskId.value}`, '_blank')
}

watch(detectionMode, (newMode) => {
  if (newMode === 'realtime' && isRealtimeDetecting.value) {
    stopRealtimeDetection()
  }
  if (newMode === 'full') {
    stopRealtimeDetection()
  }
})

onUnmounted(() => {
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

.detection-content {
  flex: 1;
  display: flex;
  gap: 24px;
  min-height: 0;
}

.video-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8ecf4;
}

.result-tag {
  font-size: 12px;
}

.video-container {
  flex: 1;
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  border: 2px dashed rgba(64, 158, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 300px;
}

.video-placeholder:hover {
  border-color: #409EFF;
  background: rgba(64, 158, 255, 0.05);
}

.placeholder-icon {
  font-size: 64px;
  color: #5a6d8a;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 16px;
  color: #c8d6e5;
  margin: 8px 0;
}

.placeholder-desc {
  font-size: 14px;
  color: #5a6d8a;
}

.video-file-input {
  display: none;
}

.video-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
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
  background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
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
  color: #5a6d8a;
  font-size: 14px;
}

.info-value {
  color: #c8d6e5;
  font-size: 14px;
  font-weight: 500;
}

.result-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
}

.result-card {
  flex: 1;
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  overflow-y: auto;
  min-height: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #c8d6e5;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #5a6d8a;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #909399;
  margin: 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: #5a6d8a;
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
  color: #5a6d8a;
  margin-top: 4px;
}

.detection-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 6px;
}

.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.summary-name {
  flex: 1;
  color: #c8d6e5;
  font-size: 14px;
}

.summary-count {
  color: #409EFF;
  font-weight: 600;
}

.realtime-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detection-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(64, 158, 255, 0.08);
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
  color: #5a6d8a;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 8px;
}

.action-card {
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
}

.action-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: #c8d6e5;
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
  color: #5a6d8a;
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
  color: #909399;
}

.param-value {
  color: #409EFF;
  font-weight: 500;
}

.param-tip {
  font-size: 12px;
  color: #5a6d8a;
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

.result-download-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(64, 158, 255, 0.1);
}
</style>
