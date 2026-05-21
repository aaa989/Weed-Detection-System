import request from '@/utils/request'
import type { HistoryResponse } from './types'

export function getHistoryList(params?: {
  page?: number
  page_size?: number
  user_id?: string
}): Promise<HistoryResponse> {
  return request({
    url: '/detection/history',
    method: 'get',
    params,
  })
}

export function getDetectionDetail(id: string) {
  return request({
    url: `/detection/${id}`,
    method: 'get',
  })
}

export function deleteDetectionRecord(id: string) {
  return request({
    url: `/detection/${id}`,
    method: 'delete',
  })
}