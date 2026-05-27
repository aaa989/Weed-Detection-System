<template>
  <div
    class="image-uploader"
    :class="{ 'is-dragover': isDragover, 'has-image': previewUrl }"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
    @click="triggerInput"
  >
    <input
      ref="fileInputRef"
      type="file"
      accept=".jpg,.jpeg,.png"
      class="file-input"
      @change="onFileChange"
    />
    <div v-if="!previewUrl" class="upload-placeholder">
      <div class="upload-icon-wrapper">
        <el-icon :size="48"><UploadFilled /></el-icon>
      </div>
      <p class="upload-title">拖拽图片到此处，或点击上传</p>
      <p class="upload-hint">支持 JPG / PNG 格式，单张图片不超过 10MB</p>
    </div>
    <div v-else class="image-preview">
      <img :src="previewUrl" alt="预览图片" />
      <div class="preview-overlay">
        <el-button type="primary" size="small" @click="triggerInput">
          <el-icon><RefreshRight /></el-icon>重新选择
        </el-button>
      </div>
      <span class="file-name">{{ fileName }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, RefreshRight } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: File | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', file: File | null): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const previewUrl = ref<string>('')
const fileName = ref<string>('')
const isDragover = ref(false)

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    previewUrl.value = ''
    fileName.value = ''
  }
})

function onDragOver() {
  isDragover.value = true
}

function onDragLeave() {
  isDragover.value = false
}

function onDrop(e: DragEvent) {
  isDragover.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

function triggerInput() {
  fileInputRef.value?.click()
}

function handleFile(file: File) {
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    ElMessage.warning('仅支持 JPG/PNG 格式的图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }
  fileName.value = file.name
  previewUrl.value = URL.createObjectURL(file)
  emit('update:modelValue', file)
}

defineExpose({ triggerInput })
</script>

<style scoped>
.image-uploader {
  width: 100%;
  height: 300px;
  border: 2px dashed rgba(64, 158, 255, 0.35);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(64, 158, 255, 0.03);
  position: relative;
  overflow: hidden;
}

.image-uploader:hover,
.image-uploader.is-dragover {
  border-color: #409EFF;
  background: rgba(64, 158, 255, 0.08);
  box-shadow: 0 0 30px rgba(64, 158, 255, 0.1);
}

.file-input {
  display: none;
}

.upload-placeholder {
  text-align: center;
}

.upload-icon-wrapper {
  color: rgba(64, 158, 255, 0.6);
  margin-bottom: 16px;
}

.upload-title {
  font-size: 16px;
  font-weight: 600;
  color: #c8d6e5;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 12px;
  color: rgba(200, 214, 229, 0.5);
}

.image-preview {
  width: 100%;
  height: 100%;
  position: relative;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-preview:hover .preview-overlay {
  opacity: 1;
}

.file-name {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: #c8d6e5;
  font-size: 12px;
  border-radius: 4px;
}
</style>