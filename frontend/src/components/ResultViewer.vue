<template>
  <div class="result-viewer">
    <div v-if="!result" class="empty-state">
      <el-icon :size="64"><PictureFilled /></el-icon>
      <p class="empty-title">暂无检测结果</p>
      <p class="empty-desc">请先上传图片进行检测</p>
    </div>
    <template v-else>
      <div class="result-header">
        <h3 class="result-title">检测结果</h3>
        <el-tag type="success" effect="dark" size="small">
          检测到 {{ result.total_objects }} 个目标
        </el-tag>
      </div>
      <div class="image-canvas-wrapper" ref="wrapperRef">
        <img
          ref="imageRef"
          :src="getFullUrl(result.result_image_url || result.image_url)"
          alt="检测结果"
          class="result-image"
          @load="onImageLoad"
        />
        <div
          v-for="(box, index) in boxes"
          :key="index"
          class="bbox-overlay"
          :style="getBoxStyle(box)"
          @mouseenter="hoveredIndex = index"
          @mouseleave="hoveredIndex = -1"
        >
          <div class="bbox-tooltip" v-show="hoveredIndex === index">
            <span class="tooltip-class">{{ box.chinese_name || box.class_name }}</span>
            <span class="tooltip-conf">{{ (box.confidence * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ result.total_objects }}</div>
          <div class="stat-label">检测总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ result.detection_time.toFixed(2) }}s</div>
          <div class="stat-label">检测耗时</div>
        </div>
        <div class="stat-card" v-for="item in classStats" :key="item.name">
          <div class="stat-value">{{ item.count }}</div>
          <div class="stat-label">{{ item.name }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { PictureFilled } from '@element-plus/icons-vue'
import type { DetectionResult, DetectionBox } from '@/api/types'

const props = defineProps<{
  result: DetectionResult | null
}>()

const imageRef = ref<HTMLImageElement | null>(null)
const wrapperRef = ref<HTMLDivElement | null>(null)
const imageSize = ref({ width: 0, height: 0, displayWidth: 0, displayHeight: 0 })
const hoveredIndex = ref(-1)

const boxes = computed(() => props.result?.boxes || [])

const classStats = computed(() => {
  if (!props.result?.boxes) return []
  const map: Record<string, number> = {}
  props.result.boxes.forEach((box) => {
    const name = box.chinese_name || box.class_name
    map[name] = (map[name] || 0) + 1
  })
  return Object.entries(map)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 4)
})

function getFullUrl(url: string): string {
  if (url.startsWith('http')) return url
  return 'http://localhost:8000' + url
}

function onImageLoad() {
  if (!imageRef.value || !wrapperRef.value) return
  const img = imageRef.value
  const wrapper = wrapperRef.value
  imageSize.value = {
    width: img.naturalWidth,
    height: img.naturalHeight,
    displayWidth: wrapper.clientWidth,
    displayHeight: (img.naturalHeight / img.naturalWidth) * wrapper.clientWidth,
  }
}

function getBoxStyle(box: DetectionBox) {
  const { width: nw, height: nh, displayWidth: dw, displayHeight: dh } = imageSize.value
  if (!nw || !nh) return { display: 'none' }
  const scaleX = dw / nw
  const scaleY = dh / nh
  return {
    left: box.x1 * scaleX + 'px',
    top: box.y1 * scaleY + 'px',
    width: (box.x2 - box.x1) * scaleX + 'px',
    height: (box.y2 - box.y1) * scaleY + 'px',
  }
}
</script>

<style scoped>
.result-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(200, 214, 229, 0.3);
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(200, 214, 229, 0.4);
  margin-top: 16px;
}

.empty-desc {
  font-size: 13px;
  color: rgba(200, 214, 229, 0.25);
  margin-top: 8px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.result-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8ecf4;
}

.image-canvas-wrapper {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: auto;
  flex: 1;
  min-height: 0;
}

.result-image {
  width: 100%;
  display: block;
}

.bbox-overlay {
  position: absolute;
  border: 2px solid #409EFF;
  background: rgba(64, 158, 255, 0.08);
  cursor: pointer;
  transition: all 0.2s;
}

.bbox-overlay:hover {
  border-color: #36cfc9;
  background: rgba(54, 207, 201, 0.15);
  z-index: 10;
}

.bbox-tooltip {
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  background: rgba(10, 14, 39, 0.95);
  border: 1px solid #409EFF;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  color: #e8ecf4;
  pointer-events: none;
}

.tooltip-class {
  color: #36cfc9;
  font-weight: 600;
  margin-right: 6px;
}

.tooltip-conf {
  color: #409EFF;
}

.stats-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 80px;
  background: rgba(64, 158, 255, 0.06);
  border: 1px solid rgba(64, 158, 255, 0.12);
  border-radius: 8px;
  padding: 12px 16px;
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #409EFF;
}

.stat-label {
  font-size: 11px;
  color: rgba(200, 214, 229, 0.5);
  margin-top: 4px;
}
</style>