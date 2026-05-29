import request from '@/utils/request'

export function getUserInfo() {
  return request({
    url: '/auth/me',
    method: 'get',
  })
}

export function updateProfile(data: {
  nickname?: string
  email?: string
}) {
  return request({
    url: '/auth/profile',
    method: 'put',
    data,
  })
}

export function changePassword(data: {
  old_password: string
  new_password: string
}) {
  return request({
    url: '/auth/password',
    method: 'put',
    data,
  })
}

export function getUserStats() {
  return request({
    url: '/auth/stats',
    method: 'get',
  })
}
