<template>
  <div class="camera-detection-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><VideoCamera /></el-icon>
        摄像头实时检测
      </h2>
      <div class="header-actions">
        <div class="stats-bar">
          <span class="stat-item">
            <span class="stat-label">帧率</span>
            <span class="stat-value">{{ currentFps }} FPS</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">总帧数</span>
            <span class="stat-value">{{ totalFrames }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">目标数</span>
            <span class="stat-value">{{ totalObjects }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">检测耗时</span>
            <span class="stat-value">{{ detectionTime }}ms</span>
          </span>
        </div>
      </div>
    </div>

    <div class="detection-content">
      <div class="video-section">
        <div class="section-card video-card">
          <div class="card-title">实时画面</div>
          <div class="video-wrapper">
            <video
              ref="videoRef"
              autoplay
              playsinline
              muted
              class="camera-video"
            />
            <canvas
              ref="canvasRef"
              class="detection-canvas"
            />
            <div v-if="!isCameraActive" class="camera-placeholder">
              <el-icon :size="48"><VideoCamera /></el-icon>
              <p>点击下方按钮开启摄像头</p>
            </div>
            <div v-if="cameraError" class="camera-error-overlay">
              <el-icon :size="36"><WarningFilled /></el-icon>
              <p>{{ cameraError }}</p>
            </div>
          </div>
        </div>

        <div class="control-bar">
          <el-button
            type="primary"
            :icon="isCameraActive ? SwitchButton : VideoPlay"
            :loading="isStarting"
            @click="toggleCamera"
            size="large"
          >
            {{ isCameraActive ? '关闭摄像头' : '开启摄像头' }}
          </el-button>

          <template v-if="isCameraActive">
            <el-button
              :type="isDetecting ? 'warning' : 'success'"
              @click="isDetecting ? pauseDetection() : startDetection()"
              :disabled="!isCameraActive"
              size="large"
            >
              {{ isDetecting ? '暂停检测' : '开始检测' }}
            </el-button>
            <el-button
              type="danger"
              @click="resetAll"
              size="large"
            >
              重置
            </el-button>
          </template>

          <div class="control-options">
            <span class="option-label">推理间隔：</span>
            <el-slider
              v-model="inferenceInterval"
              :min="1"
              :max="10"
              :step="1"
              style="width: 140px"
              show-stops
            />
            <span class="option-value">{{ inferenceInterval }}帧</span>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="section-card detection-list-card">
          <div class="card-title">
            检测目标列表
            <span class="badge">{{ detectionBoxes.length }}</span>
          </div>
          <div class="detection-list" v-if="detectionBoxes.length > 0">
            <div
              v-for="(box, index) in detectionBoxes"
              :key="index"
              class="detection-item"
            >
              <span
                class="color-dot"
                :style="{ background: getClassColor(box.class_id) }"
              />
              <span class="item-name">{{ box.chinese_name || box.class_name }}</span>
              <span class="item-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div class="empty-list" v-else>
            <el-icon :size="32"><Picture /></el-icon>
            <p>暂无检测目标</p>
          </div>
        </div>

        <div class="section-card stats-card">
          <div class="card-title">类别统计</div>
          <div class="stats-grid" v-if="classStats.length > 0">
            <div
              v-for="stat in classStats"
              :key="stat.class_name"
              class="stat-card"
            >
              <span
                class="color-dot large"
                :style="{ background: stat.color }"
              />
              <span class="stat-name">{{ stat.chinese_name }}</span>
              <span class="stat-count">{{ stat.count }}</span>
            </div>
          </div>
          <div class="empty-list" v-else>
            <el-icon :size="32"><DataLine /></el-icon>
            <p>暂无统计数据</p>
          </div>
        </div>

        <div class="section-card log-card">
          <div class="card-title">操作日志</div>
          <div class="log-list">
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-item"
              :class="log.level"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-msg">{{ log.message }}</span>
            </div>
            <div v-if="logs.length === 0" class="empty-list">
              <p>暂无日志</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, VideoPlay, SwitchButton, WarningFilled, Picture, DataLine } from '@element-plus/icons-vue'
import { detectCameraFrame } from '@/api/detection'

const videoRef = ref(null)
const canvasRef = ref(null)

const isCameraActive = ref(false)
const isStarting = ref(false)
const isDetecting = ref(false)
const cameraError = ref('')

const currentFps = ref(0)
const totalFrames = ref(0)
const totalObjects = ref(0)
const detectionTime = ref(0)
const inferenceInterval = ref(3)

const detectionBoxes = ref([])
const logs = ref([])

let stream = null
let animationFrameId = null
let frameIndex = 0
let lastInferenceIndex = 0

const classColors = [
  '#409EFF',
  '#67C23A',
  '#E6A23C',
  '#F56C6C',
  '#909399',
  '#B37FEB',
  '#FF85C0',
  '#36CFC9',
]

const classChineseNames = {
  crop: '作物',
  weed: '杂草',
}

function getClassColor(classId) {
  return classColors[classId % classColors.length]
}

const classStats = computed(() => {
  const stats = {}
  detectionBoxes.value.forEach((box) => {
    const key = box.class_name
    if (!stats[key]) {
      stats[key] = {
        class_name: box.class_name,
        chinese_name: box.chinese_name || box.class_name,
        color: getClassColor(box.class_id),
        count: 0,
      }
    }
    stats[key].count++
  })
  return Object.values(stats)
})

function addLog(message, level = 'info') {
  const now = new Date()
  const time = now.toLocaleTimeString()
  logs.value.unshift({ time, message, level })
  if (logs.value.length > 50) {
    logs.value.pop()
  }
}

async function toggleCamera() {
  if (isCameraActive.value) {
    stopCamera()
  } else {
    await startCamera()
  }
}

async function startCamera() {
  isStarting.value = true
  cameraError.value = ''

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 },
      },
      audio: false,
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream
      await videoRef.value.play()
    }

    await nextTick()
    initCanvas()

    isCameraActive.value = true
    frameIndex = 0
    lastInferenceIndex = 0
    detectionBoxes.value = []
    totalFrames.value = 0
    totalObjects.value = 0
    currentFps.value = 0
    detectionTime.value = 0

    startDrawLoop()
    addLog('摄像头已开启', 'success')
  } catch (error) {
    handleCameraError(error)
    resetResources()
  } finally {
    isStarting.value = false
  }
}

function handleCameraError(error) {
  switch (error.name) {
    case 'NotAllowedError':
      cameraError.value = '摄像头权限被拒绝，请在浏览器设置中允许访问'
      break
    case 'NotFoundError':
      cameraError.value = '未找到摄像头设备，请确认设备已连接'
      break
    case 'NotReadableError':
      cameraError.value = '摄像头被其他应用占用，请关闭后重试'
      break
    default:
      cameraError.value = `摄像头访问失败：${error.message || '未知错误'}`
  }
  addLog(cameraError.value, 'error')
}

function initCanvas() {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value

  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

function startDrawLoop() {
  const draw = () => {
    if (!isCameraActive.value) return

    drawDetectionBoxes()

    if (isDetecting.value && videoRef.value && canvasRef.value) {
      totalFrames.value++
      frameIndex++

      if (frameIndex - lastInferenceIndex >= inferenceInterval.value) {
        lastInferenceIndex = frameIndex
        captureAndDetect()
      }
    }

    animationFrameId = requestAnimationFrame(draw)
  }
  animationFrameId = requestAnimationFrame(draw)
}

function drawDetectionBoxes() {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  if (video.videoWidth && video.videoHeight) {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const scaleX = canvas.width / (video.videoWidth || 640)
  const scaleY = canvas.height / (video.videoHeight || 480)

  detectionBoxes.value.forEach((box) => {
    const x = box.x1 * scaleX
    const y = box.y1 * scaleY
    const w = (box.x2 - box.x1) * scaleX
    const h = (box.y2 - box.y1) * scaleY
    const color = getClassColor(box.class_id)

    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, w, h)

    ctx.fillStyle = color + '33'
    ctx.fillRect(x, y, w, h)

    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`
    ctx.font = '12px sans-serif'
    const textWidth = ctx.measureText(label).width
    const textHeight = 16
    let labelY = y - textHeight - 2
    if (labelY < 0) labelY = y + h + 2

    ctx.fillStyle = color
    ctx.fillRect(x, labelY, textWidth + 6, textHeight + 2)

    ctx.fillStyle = '#ffffff'
    ctx.fillText(label, x + 3, labelY + textHeight - 2)
  })
}

let isCapturing = false

async function captureAndDetect() {
  if (!videoRef.value || !canvasRef.value || isCapturing) return
  isCapturing = true

  try {
    const video = videoRef.value
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = video.videoWidth || 640
    tempCanvas.height = video.videoHeight || 480
    const tempCtx = tempCanvas.getContext('2d')
    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height)

    const imageData = tempCanvas.toDataURL('image/jpeg', 0.7)

    const res = await detectCameraFrame(imageData, frameIndex)
    if (res.success) {
      detectionBoxes.value = res.boxes || []
      totalObjects.value = res.total_objects || 0
      currentFps.value = res.fps || 0
      detectionTime.value = Math.round((res.detection_time || 0) * 1000)
    }
  } catch (error) {
    console.error('Frame detection failed:', error)
  } finally {
    isCapturing = false
  }
}

function startDetection() {
  if (!isCameraActive.value) {
    ElMessage.warning('请先开启摄像头')
    return
  }
  isDetecting.value = true
  lastInferenceIndex = frameIndex
  addLog('实时检测已开始', 'success')
  ElMessage.success('实时检测已开始')
}

function pauseDetection() {
  isDetecting.value = false
  addLog('检测已暂停', 'info')
  ElMessage.info('检测已暂停')
}

function stopCamera() {
  isDetecting.value = false

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }

  resetResources()

  isCameraActive.value = false
  detectionBoxes.value = []

  if (canvasRef.value) {
    const ctx = canvasRef.value.getContext('2d')
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  }

  addLog('摄像头已关闭', 'info')
}

function resetResources() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
    stream = null
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
}

function resetAll() {
  stopCamera()
  frameIndex = 0
  lastInferenceIndex = 0
  totalFrames.value = 0
  totalObjects.value = 0
  currentFps.value = 0
  detectionTime.value = 0
  detectionBoxes.value = []
  logs.value = []
  cameraError.value = ''
  ElMessage.info('已重置所有状态')
}

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
.camera-detection-page {
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
  flex-shrink: 0;
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
}

.stats-bar {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 11px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #409EFF;
  font-family: 'Courier New', monospace;
}

.detection-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  min-height: 0;
}

.video-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  background: rgba(64, 158, 255, 0.2);
  color: #409EFF;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.video-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.video-wrapper {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.camera-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  gap: 12px;
}

.camera-placeholder .el-icon {
  opacity: 0.5;
}

.camera-placeholder p {
  font-size: 14px;
}

.camera-error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  color: #F56C6C;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.camera-error-overlay p {
  font-size: 14px;
  max-width: 300px;
}

.control-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.control-options {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.option-label {
  font-size: 13px;
  color: #909399;
}

.option-value {
  font-size: 13px;
  color: #c8d6e5;
  font-weight: 600;
  min-width: 40px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
}

.detection-list-card {
  flex-shrink: 0;
  max-height: 260px;
  overflow-y: auto;
}

.detection-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detection-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 6px;
}

.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.color-dot.large {
  width: 12px;
  height: 12px;
}

.item-name {
  flex: 1;
  font-size: 13px;
  color: #c8d6e5;
}

.item-confidence {
  font-size: 12px;
  color: #67C23A;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.stats-card {
  flex-shrink: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 6px;
}

.stat-name {
  flex: 1;
  font-size: 13px;
  color: #c8d6e5;
}

.stat-count {
  font-size: 14px;
  font-weight: 700;
  color: #409EFF;
  font-family: 'Courier New', monospace;
}

.log-card {
  flex: 1;
  min-height: 120px;
  max-height: 200px;
  overflow-y: auto;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-item {
  display: flex;
  gap: 10px;
  font-size: 12px;
  padding: 4px 0;
  border-bottom: 1px solid rgba(64, 158, 255, 0.05);
}

.log-item.success .log-msg {
  color: #67C23A;
}

.log-item.error .log-msg {
  color: #F56C6C;
}

.log-item.info .log-msg {
  color: #c8d6e5;
}

.log-time {
  color: #909399;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
}

.log-msg {
  color: #c8d6e5;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #909399;
  gap: 8px;
}

.empty-list .el-icon {
  opacity: 0.4;
}

.empty-list p {
  font-size: 13px;
}
</style>