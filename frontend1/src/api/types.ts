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

export interface StatCountItem {
  class_name: string
  count: number
}