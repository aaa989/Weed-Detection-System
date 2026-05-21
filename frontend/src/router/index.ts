import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/detection',
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
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router