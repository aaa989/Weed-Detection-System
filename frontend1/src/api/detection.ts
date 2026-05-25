import request from '@/utils/request'
import type { SingleDetectionResponse } from './types'

export function detectSingleImage(file: File, modelName = 'rsod-yolo11n'): Promise<SingleDetectionResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_name', modelName)
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