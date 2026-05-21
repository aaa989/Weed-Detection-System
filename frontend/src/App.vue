<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-icon">
          <el-icon :size="22"><Monitor /></el-icon>
        </div>
        <div class="logo-text">
          <span class="logo-title">遥感目标智能检测平台</span>
          <span class="logo-subtitle">Remote Sensing Detection</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span class="version">v1.0.0</span>
      </div>
    </aside>
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Monitor, Picture, Clock, DataAnalysis } from '@element-plus/icons-vue'
import type { Component } from 'vue'

interface MenuItem {
  path: string
  label: string
  icon: Component
}

const route = useRoute()

const menuItems: MenuItem[] = [
  { path: '/detection', label: '智能检测', icon: Picture },
  { path: '/history', label: '历史记录', icon: Clock },
  { path: '/analysis', label: '结果分析', icon: DataAnalysis },
]

const currentPath = computed(() => route.path)
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: #0a0e27;
}

.sidebar {
  width: 240px;
  min-width: 240px;
  background: linear-gradient(180deg, #0d1137 0%, #0a0e27 100%);
  border-right: 1px solid rgba(64, 158, 255, 0.15);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.sidebar-header {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.1);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #409EFF, #36cfc9);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-icon .el-icon {
  color: #fff;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 14px;
  font-weight: 700;
  color: #e8ecf4;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 10px;
  color: rgba(64, 158, 255, 0.7);
  letter-spacing: 1px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  color: rgba(232, 236, 244, 0.65);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.25s ease;
  cursor: pointer;
  position: relative;
}

.nav-item:hover {
  color: #e8ecf4;
  background: rgba(64, 158, 255, 0.08);
}

.nav-item.active {
  color: #409EFF;
  background: rgba(64, 158, 255, 0.12);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #409EFF;
  border-radius: 0 3px 3px 0;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(64, 158, 255, 0.1);
  text-align: center;
}

.version {
  font-size: 11px;
  color: rgba(232, 236, 244, 0.35);
}

.main-content {
  flex: 1;
  overflow: hidden;
  background-color: #0a0e27;
  padding: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>