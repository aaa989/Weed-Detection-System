<template>
  <div class="sidebar-container">
    <div class="logo-section">
      <div class="logo-icon">
        <Monitor style="color: white; font-size: 20px" />
      </div>
      <div class="logo-text">
        <div class="logo-title">杂草识别检测系统</div>
        <div class="logo-subtitle">多场景影像·精准识别</div>
      </div>
    </div>

    <div class="nav-menu">
      <div class="menu-group">
        <div class="menu-group-title">功能模块</div>
        <div
          v-for="item in mainMenuList"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
          @click="handleMenuClick(item)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.name }}</span>
        </div>
      </div>

      <div class="menu-group">
        <div class="menu-group-title">个人</div>
        <div
          v-for="item in userMenuList"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
          @click="handleMenuClick(item)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.name }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="version-info">v1.0.0</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  Monitor,
  Picture,
  ChatDotRound,
  User,
  VideoCamera,
  VideoPlay,
  Document,
  Setting,
} from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

const mainMenuList = [
  {
    name: "智能检测",
    icon: Picture,
    path: "/detection",
  },
  {
    name: "摄像头检测",
    icon: VideoCamera,
    path: "/camera",
  },
  {
    name: "视频检测",
    icon: VideoPlay,
    path: "/video",
  },
  {
    name: "检测历史",
    icon: Document,
    path: "/history",
  },
  {
    name: "AI 问答",
    icon: ChatDotRound,
    path: "/qa",
  },
];

const userMenuList = [
  {
    name: "个人中心",
    icon: User,
    path: "/profile",
  },
  {
    name: "系统设置",
    icon: Setting,
    path: "/settings",
  },
];

const currentPath = computed(() => route.path);

const handleMenuClick = (item) => {
  router.push(item.path);
};
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-section {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #27ae60, #2ecc71);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
}

.logo-text {
  overflow: hidden;
}

.logo-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.3;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

.menu-group {
  margin-bottom: 8px;
}

.menu-group-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px 4px;
  margin-bottom: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  flex-direction: row;
  padding: 12px 12px;
  border-radius: 8px;
  margin-bottom: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  border-left: 3px solid transparent;
  position: relative;
}

.nav-item:hover {
  background-color: var(--primary-light);
  transform: translateX(2px);
}

.nav-item.active {
  background-color: var(--primary-light);
  border-left: 3px solid var(--primary-color);
  color: var(--primary-color);
  font-weight: 500;
}

.nav-item.active .nav-icon {
  color: var(--primary-color);
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
  transition: color 0.2s;
}

.nav-text {
  font-size: 14px;
  line-height: 1.4;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  text-align: center;
}

.version-info {
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>
