export interface DetectionBox {
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
  class_id: number
  class_name: string
  chinese_name: string | null
}

export interface DetectionResult {
  detection_id: string
  image_url: string
  result_image_url: string
  boxes: DetectionBox[]
  total_objects: number
  detection_time: number
  model_name: string
  created_at: string
}

export interface SingleDetectionResponse {
  success: boolean
  message: string
  data: DetectionResult | null
}

export interface HistoryItem {
  id: string
  image_url: string
  result_image_url: string
  total_objects: number
  created_at: string
  model_name: string
  filename: string
  status: string
  type: string
  time: string
  count: number
}

export interface HistoryResponse {
  success: boolean
  message: string
  data: HistoryItem[]
  total: number
}

export interface BatchDetectionItem {
  id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result?: DetectionResult
}

export interface BatchUploadResponse {
  success: boolean
  message: string
  task_id: string
  total: number
}

export interface BatchStatusResponse {
  success: boolean
  status: string
  completed: number
  failed: number
  total: number
  progress: number
}

export interface StatCountItem {
  class_name: string
  count: number
}

export interface CameraDetectRequest {
  image: string
  frame_index: number
}

export interface CameraDetectResponse {
  success: boolean
  message: string
  boxes: DetectionBox[]
  frame_index: number
  fps: number
  detection_time: number
  total_objects: number
}

export interface CameraStatusResponse {
  status: string
  message: string
}