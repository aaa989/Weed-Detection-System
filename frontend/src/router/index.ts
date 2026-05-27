import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/detection',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: { title: '注册' },
  }, 
  {
    path: '/detection',
    name: 'Detection',
    component: () => import('@/views/Detection.vue'),
    meta: { title: '智能检测', icon: 'Picture' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录', icon: 'Clock' },
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/Analysis.vue'),
    meta: { title: '结果分析', icon: 'DataAnalysis' },
  },
  {
    path: '/camera',
    name: 'CameraDetection',
    component: () => import('@/views/CameraDetection.vue'),
    meta: { title: '摄像头实时检测', icon: 'VideoCamera' },
  },
  {
    path: '/video',
    name: 'VideoDetection',
    component: () => import('@/views/VideoDetection.vue'),
    meta: { title: '视频检测', icon: 'VideoPlay' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router