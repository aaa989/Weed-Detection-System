<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon :size="22"><User /></el-icon>
        个人中心
      </h1>
      <p class="page-subtitle">管理你的账户信息和使用统计</p>
    </div>

    <div class="profile-content">
      <div class="top-section">
        <div class="user-info-card">
          <div class="user-avatar-section">
            <el-avatar :size="80" class="user-avatar">
              <img
                src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
                alt="用户头像"
              />
            </el-avatar>
            <div class="user-basic-info">
              <div class="user-name">{{ userInfo.nickname || userInfo.username }}</div>
              <div class="user-role">
                <el-tag :type="userInfo.role === 'admin' ? 'danger' : 'success'" size="small">
                  {{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </div>
              <div class="user-meta">
                <span class="meta-item">
                  <el-icon><Message /></el-icon>
                  {{ userInfo.email || '未设置邮箱' }}
                </span>
                <span class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  注册于 {{ formatDate(userInfo.created_at) }}
                </span>
              </div>
            </div>
            <div class="user-actions">
              <el-button type="primary" plain @click="showEditDialog = true">
                <el-icon><Edit /></el-icon>
                编辑资料
              </el-button>
              <el-button plain @click="showPasswordDialog = true">
                <el-icon><Lock /></el-icon>
                修改密码
              </el-button>
            </div>
          </div>
        </div>

        <div class="stats-cards">
          <div class="stat-card" v-for="stat in statsCards" :key="stat.label">
            <div class="stat-icon" :style="{ background: stat.bgColor }">
              <el-icon :size="24" :color="stat.color"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">检测趋势</h3>
            <span class="chart-subtitle">近6个月检测次数统计</span>
          </div>
          <div class="chart-body">
            <div ref="trendChartRef" class="chart-container"></div>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">模型使用分布</h3>
            <span class="chart-subtitle">各检测模型使用次数</span>
          </div>
          <div class="chart-body">
            <div ref="pieChartRef" class="chart-container"></div>
          </div>
        </div>
      </div>

      <div class="recent-section">
        <div class="section-header">
          <h3 class="section-title">最近检测</h3>
          <el-button text type="primary" @click="router.push('/history')">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="recent-list">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="recent-item"
            @click="router.push('/history')"
          >
            <div class="recent-preview">
              <img
                :src="getImageUrl(record.result_image_url || record.image_url)"
                :alt="record.filename"
                @error="onImageError"
              />
            </div>
            <div class="recent-info">
              <div class="recent-name">{{ record.filename }}</div>
              <div class="recent-meta">
                <span>{{ record.time }}</span>
                <span>{{ record.total_objects }} 个目标</span>
              </div>
            </div>
            <el-icon class="recent-arrow"><ArrowRight /></el-icon>
          </div>
          <div v-if="recentRecords.length === 0" class="empty-recent">
            <el-icon :size="32" color="#d1d5db"><Document /></el-icon>
            <span>暂无检测记录</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showEditDialog"
      title="编辑个人资料"
      width="480px"
      destroy-on-close
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input :value="userInfo.username" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProfile" :loading="isUpdating">
          保存修改
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="480px"
      destroy-on-close
    >
      <el-form :model="passwordForm" label-width="80px" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="isChangingPwd">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  User,
  Edit,
  Lock,
  Message,
  Calendar,
  Picture,
  Aim,
  Check,
  Clock,
  ArrowRight,
  Document,
  DataAnalysis,
} from "@element-plus/icons-vue";
import * as echarts from "echarts";
import { getUserInfo, updateProfile, changePassword, getUserStats } from "../api/user";
import { getHistoryList } from "../api/history";

const router = useRouter();

const userInfo = ref({
  username: "",
  nickname: "",
  email: "",
  role: "user",
  avatar_url: "",
  created_at: "",
});

const stats = ref({
  total_detections: 0,
  total_objects: 0,
  success_rate: 0,
  days_used: 0,
  weekly_detections: 0,
  monthly_detections: [],
  model_stats: [],
});

const recentRecords = ref([]);
const isLoading = ref(false);

const showEditDialog = ref(false);
const editForm = reactive({ nickname: "", email: "" });
const isUpdating = ref(false);

const showPasswordDialog = ref(false);
const passwordForm = reactive({ old_password: "", new_password: "", confirm_password: "" });
const isChangingPwd = ref(false);
const passwordFormRef = ref(null);

const trendChartRef = ref(null);
const pieChartRef = ref(null);
let trendChart = null;
let pieChart = null;

const passwordRules = {
  old_password: [{ required: true, message: "请输入原密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "密码长度至少6位", trigger: "blur" },
  ],
  confirm_password: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

const statsCards = computed(() => [
  {
    label: "总检测次数",
    value: stats.value.total_detections,
    icon: Picture,
    color: "#409EFF",
    bgColor: "rgba(64,158,255,0.1)",
  },
  {
    label: "累计检测目标",
    value: stats.value.total_objects,
    icon: Aim,
    color: "#27ae60",
    bgColor: "rgba(39,174,96,0.1)",
  },
  {
    label: "检测成功率",
    value: stats.value.success_rate + "%",
    icon: Check,
    color: "#e6a23c",
    bgColor: "rgba(230,162,60,0.1)",
  },
  {
    label: "使用天数",
    value: stats.value.days_used,
    icon: Clock,
    color: "#909399",
    bgColor: "rgba(144,147,153,0.1)",
  },
]);

const formatDate = (dateStr) => {
  if (!dateStr) return "未知";
  return dateStr.substring(0, 10);
};

const getImageUrl = (url) => {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return "http://localhost:8000" + url;
};

const onImageError = (e) => {
  e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='40'%3E%3Crect fill='%23f0f0f0' width='60' height='40'/%3E%3Ctext fill='%23999' font-size='10' x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle'%3EN/A%3C/text%3E%3C/svg%3E";
};

const fetchUserInfo = async () => {
  try {
    const res = await getUserInfo();
    if (res.success && res.user) {
      userInfo.value = res.user;
      localStorage.setItem("user", JSON.stringify(res.user));
    }
  } catch (e) {
    try {
      const stored = localStorage.getItem("user");
      if (stored) userInfo.value = JSON.parse(stored);
    } catch {}
  }
};

const fetchStats = async () => {
  try {
    const res = await getUserStats();
    if (res.success && res.data) {
      stats.value = res.data;
    }
  } catch (e) {
    console.error("获取统计数据失败:", e);
  }
};

const fetchRecentRecords = async () => {
  try {
    const res = await getHistoryList({ page: 1, page_size: 5 });
    if (res.success) {
      recentRecords.value = res.data || [];
    }
  } catch (e) {
    console.error("获取最近记录失败:", e);
  }
};

const initCharts = () => {
  nextTick(() => {
    if (trendChartRef.value) {
      trendChart = echarts.init(trendChartRef.value);
      updateTrendChart();
    }
    if (pieChartRef.value) {
      pieChart = echarts.init(pieChartRef.value);
      updatePieChart();
    }
  });
};

const updateTrendChart = () => {
  if (!trendChart) return;
  const data = stats.value.monthly_detections || [];
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category",
      data: data.map((d) => d.month),
      axisLabel: { color: "#6b7280", fontSize: 11 },
      axisLine: { lineStyle: { color: "#e5e7eb" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#6b7280", fontSize: 11 },
      splitLine: { lineStyle: { color: "#f3f4f6" } },
    },
    series: [
      {
        name: "检测次数",
        type: "line",
        smooth: true,
        data: data.map((d) => d.count),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(64,158,255,0.3)" },
            { offset: 1, color: "rgba(64,158,255,0.02)" },
          ]),
        },
        lineStyle: { color: "#409EFF", width: 3 },
        itemStyle: { color: "#409EFF" },
      },
    ],
  });
};

const updatePieChart = () => {
  if (!pieChart) return;
  const data = stats.value.model_stats || [];
  if (data.length === 0) {
    pieChart.setOption({
      graphic: {
        type: "text",
        left: "center",
        top: "center",
        style: { text: "暂无数据", fontSize: 14, fill: "#9ca3af" },
      },
    });
    return;
  }
  pieChart.setOption({
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: "#fff", borderWidth: 2 },
        label: { show: true, formatter: "{b}\n{c}次" },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: "bold" },
        },
        data: data.map((d, i) => ({
          name: d.model,
          value: d.count,
          itemStyle: {
            color: ["#409EFF", "#27ae60", "#e6a23c", "#f56c6c"][i % 4],
          },
        })),
      },
    ],
  });
};

watch(
  () => stats.value,
  () => {
    updateTrendChart();
    updatePieChart();
  },
  { deep: true }
);

const handleUpdateProfile = async () => {
  isUpdating.value = true;
  try {
    const res = await updateProfile({
      nickname: editForm.nickname,
      email: editForm.email,
    });
    if (res.success) {
      ElMessage.success("个人信息更新成功");
      showEditDialog.value = false;
      if (res.user) {
        userInfo.value = { ...userInfo.value, ...res.user };
        localStorage.setItem("user", JSON.stringify(userInfo.value));
      }
      fetchUserInfo();
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "更新失败");
  } finally {
    isUpdating.value = false;
  }
};

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return;
  try {
    await passwordFormRef.value.validate();
  } catch {
    return;
  }
  isChangingPwd.value = true;
  try {
    const res = await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    });
    if (res.success) {
      ElMessage.success("密码修改成功，请重新登录");
      showPasswordDialog.value = false;
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.push("/login");
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "密码修改失败");
  } finally {
    isChangingPwd.value = false;
  }
};

watch(showEditDialog, (val) => {
  if (val) {
    editForm.nickname = userInfo.value.nickname || "";
    editForm.email = userInfo.value.email || "";
  }
});

watch(showPasswordDialog, (val) => {
  if (val) {
    passwordForm.old_password = "";
    passwordForm.new_password = "";
    passwordForm.confirm_password = "";
  }
});

const handleResize = () => {
  trendChart?.resize();
  pieChart?.resize();
};

onMounted(async () => {
  isLoading.value = true;
  await Promise.all([fetchUserInfo(), fetchStats(), fetchRecentRecords()]);
  isLoading.value = false;
  initCharts();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  trendChart?.dispose();
  pieChart?.dispose();
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped lang="scss">
.profile-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 22px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;

      .el-icon {
        color: var(--primary-color);
      }
    }

    .page-subtitle {
      font-size: 13px;
      color: var(--text-secondary);
    }
  }

  .profile-content {
    display: flex;
    flex-direction: column;
    gap: 24px;

    .top-section {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .user-info-card {
      background-color: #ffffff;
      border-radius: 12px;
      padding: 24px;
      box-shadow: var(--card-shadow);

      .user-avatar-section {
        display: flex;
        align-items: center;

        .user-avatar {
          flex-shrink: 0;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }

        .user-basic-info {
          margin-left: 20px;
          flex: 1;

          .user-name {
            font-size: 22px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
          }

          .user-role {
            margin-bottom: 10px;
          }

          .user-meta {
            display: flex;
            gap: 20px;

            .meta-item {
              display: flex;
              align-items: center;
              gap: 4px;
              font-size: 13px;
              color: var(--text-secondary);
            }
          }
        }

        .user-actions {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }
      }
    }

    .stats-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;

      .stat-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--card-shadow);
        display: flex;
        align-items: center;
        gap: 16px;
        transition: transform 0.2s, box-shadow 0.2s;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .stat-content {
          .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.2;
          }

          .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 4px;
          }
        }
      }
    }

    .charts-section {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;

      .chart-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--card-shadow);

        .chart-header {
          margin-bottom: 16px;

          .chart-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .chart-subtitle {
            font-size: 12px;
            color: var(--text-secondary);
          }
        }

        .chart-body {
          .chart-container {
            width: 100%;
            height: 260px;
          }
        }
      }
    }

    .recent-section {
      background-color: #ffffff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--card-shadow);

      .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;

        .section-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
        }
      }

      .recent-list {
        display: flex;
        flex-direction: column;
        gap: 8px;

        .recent-item {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 10px 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.2s;

          &:hover {
            background-color: #f9fafb;
          }

          .recent-preview {
            width: 56px;
            height: 40px;
            border-radius: 6px;
            overflow: hidden;
            flex-shrink: 0;
            background: #f5f5f5;

            img {
              width: 100%;
              height: 100%;
              object-fit: cover;
            }
          }

          .recent-info {
            flex: 1;
            min-width: 0;

            .recent-name {
              font-size: 13px;
              font-weight: 500;
              color: var(--text-primary);
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }

            .recent-meta {
              font-size: 11px;
              color: var(--text-secondary);
              margin-top: 3px;
              display: flex;
              gap: 12px;
            }
          }

          .recent-arrow {
            color: var(--text-tertiary);
            font-size: 14px;
          }
        }

        .empty-recent {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 30px 0;
          color: var(--text-tertiary);
          font-size: 13px;
          gap: 8px;
        }
      }
    }
  }
}
</style>
