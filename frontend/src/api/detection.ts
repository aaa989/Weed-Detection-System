import request from '@/utils/request'
import type { SingleDetectionResponse, BatchUploadResponse, BatchStatusResponse } from './types'

export function detectSingleImage(file: File, modelName = 'rsod-yolo11n', confidenceThreshold?: number, userId?: string | null): Promise<SingleDetectionResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_name', modelName)
  if (confidenceThreshold !== undefined) {
    formData.append('confidence_threshold', String(confidenceThreshold))
  }
  if (userId) {
    formData.append('user_id', userId)
  }
  return request({
    url: '/detection/single',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function detectBatchImages(files: File[], modelName = 'rsod-yolo11n'): Promise<SingleDetectionResponse[]> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  formData.append('model_name', modelName)
  return request({
    url: '/detection/batch',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function batchUpload(formData: FormData, modelName = 'rsod-yolo11n'): Promise<BatchUploadResponse> {
  formData.append('model_name', modelName)
  return request({
    url: '/detection/batch/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function getBatchStatus(taskId: string): Promise<BatchStatusResponse> {
  return request({
    url: `/detection/batch/status/${taskId}`,
    method: 'get',
  })
}

export function detectCameraFrame(image: string, frameIndex = 0) {
  return request({
    url: '/detection/camera/detect',
    method: 'post',
    data: {
      image,
      frame_index: frameIndex,
    },
    timeout: 60000,
  })
}

export function getCameraStatus() {
  return request({
    url: '/detection/camera/status',
    method: 'get',
  })
}

export function startCameraDetection() {
  return request({
    url: '/detection/camera/start',
    method: 'post',
  })
}

export function stopCameraDetection() {
  return request({
    url: '/detection/camera/stop',
    method: 'post',
  })
}

export function pauseCameraDetection() {
  return request({
    url: '/detection/camera/pause',
    method: 'post',
  })
}

export function detectRealtimeFrame(data: FormData) {
  return request({
    url: '/video-detection/realtime-frame',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 10000,
  })
}