import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DetectionResult, HistoryItem } from '@/api/types'

export const useDetectionStore = defineStore('detection', () => {
  const currentResult = ref<DetectionResult | null>(null)
  const isDetecting = ref(false)
  const detectionTime = ref(0)
  const historyList = ref<HistoryItem[]>([])
  const totalRecords = ref(0)

  function setResult(result: DetectionResult) {
    currentResult.value = result
  }

  function clearResult() {
    currentResult.value = null
  }

  function setDetecting(val: boolean) {
    isDetecting.value = val
  }

  function setDetectionTime(time: number) {
    detectionTime.value = time
  }

  function setHistoryList(list: HistoryItem[], total: number) {
    historyList.value = list
    totalRecords.value = total
  }

  return {
    currentResult,
    isDetecting,
    detectionTime,
    historyList,
    totalRecords,
    setResult,
    clearResult,
    setDetecting,
    setDetectionTime,
    setHistoryList,
  }
})