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
    meta: { title: '登录', requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: { title: '注册', requiresAuth: false },
  },
  {
    path: '/detection',
    name: 'Detection',
    component: () => import('@/views/Detection.vue'),
    meta: { title: '智能检测', icon: 'Picture' },
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
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryPage.vue'),
    meta: { title: '检测历史', icon: 'Document' },
  },
  {
    path: '/qa',
    name: 'QAPage',
    component: () => import('@/views/QAPage.vue'),
    meta: { title: 'AI 问答', icon: 'ChatDotRound' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfilePage.vue'),
    meta: { title: '个人中心', icon: 'User' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置', icon: 'Setting' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const isAuthPage = ['/login', '/register'].includes(to.path)
  if (!token && !isAuthPage) {
    next('/login')
  } else if (token && isAuthPage) {
    next('/detection')
  } else {
    next()
  }
})

export default router