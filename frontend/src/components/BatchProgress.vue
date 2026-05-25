<template>
  <div class="batch-progress" v-if="visible">
    <div class="batch-header">
      <span class="batch-title">批量检测进度</span>
      <span class="batch-count">{{ completedCount }} / {{ totalCount }}</span>
    </div>
    <el-progress
      :percentage="percentage"
      :stroke-width="8"
      :color="progressColor"
    />
    <div class="batch-files">
      <div
        v-for="item in items"
        :key="item.id"
        class="batch-file-item"
      >
        <span class="file-name">{{ item.filename }}</span>
        <el-tag
          :type="statusType(item.status)"
          size="small"
          effect="dark"
        >
          {{ statusLabel(item.status) }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BatchDetectionItem } from '@/api/types'

const props = defineProps<{
  visible: boolean
  items: BatchDetectionItem[]
}>()

const totalCount = computed(() => props.items.length)

const completedCount = computed(
  () => props.items.filter((i) => i.status === 'completed' || i.status === 'failed').length
)

const percentage = computed(() =>
  totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0
)

const progressColor = computed(() => {
  const colors: Record<string, string> = {
    '#409EFF': '#409EFF',
  }
  return colors
})

function statusType(status: string): 'info' | 'warning' | 'success' | 'danger' | '' {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '检测中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}
</script>

<style scoped>
.batch-progress {
  background: rgba(64, 158, 255, 0.05);
  border: 1px solid rgba(64, 158, 255, 0.12);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.batch-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8ecf4;
}

.batch-count {
  font-size: 13px;
  color: #409EFF;
}

.batch-files {
  margin-top: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.batch-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(64, 158, 255, 0.06);
}

.batch-file-item:last-child {
  border-bottom: none;
}

.batch-file-item .file-name {
  font-size: 13px;
  color: #c8d6e5;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>