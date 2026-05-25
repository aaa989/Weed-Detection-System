<template>
  <div class="analysis-page">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon :size="22"><DataAnalysis /></el-icon>
        结果分析
      </h2>
      <div class="header-actions">
        <el-select v-model="timeRange" size="small" @change="refreshCharts">
          <el-option label="近7天" value="7d" />
          <el-option label="近30天" value="30d" />
          <el-option label="近90天" value="90d" />
        </el-select>
        <el-button size="small" @click="refreshCharts">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
      </div>
    </div>

    <div class="charts-grid">
      <!-- 饼图：各类别目标占比 -->
      <div class="chart-card">
        <div class="chart-header">
          <span class="chart-title">目标类别分布</span>
          <span class="chart-subtitle">各类别检测占比</span>
        </div>
        <div class="chart-body" ref="pieChartRef"></div>
      </div>

      <!-- 柱状图：每日检测量 -->
      <div class="chart-card chart-card-wide">
        <div class="chart-header">
          <span class="chart-title">每日检测趋势</span>
          <span class="chart-subtitle">检测次数统计</span>
        </div>
        <div class="chart-body" ref="barChartRef"></div>
      </div>

      <!-- 统计概览卡片 -->
      <div class="chart-card">
        <div class="chart-header">
          <span class="chart-title">检测概览</span>
          <span class="chart-subtitle">累计统计数据</span>
        </div>
        <div class="summary-body">
          <div class="summary-item">
            <div class="summary-icon" style="background: rgba(64,158,255,0.15)">
              <el-icon :size="24"><PictureFilled /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ stats.totalDetections }}</div>
              <div class="summary-label">总检测次数</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon" style="background: rgba(54,207,201,0.15)">
              <el-icon :size="24"><Aim /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ stats.totalObjects }}</div>
              <div class="summary-label">总检测目标数</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon" style="background: rgba(255,181,71,0.15)">
              <el-icon :size="24"><Timer /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ stats.avgTime.toFixed(2) }}s</div>
              <div class="summary-label">平均检测耗时</div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-icon" style="background: rgba(255,77,79,0.15)">
              <el-icon :size="24"><TrendCharts /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ stats.topClass }}</div>
              <div class="summary-label">最常见目标</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { DataAnalysis, Refresh, PictureFilled, Aim, Timer, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const timeRange = ref('7d')
const pieChartRef = ref<HTMLDivElement | null>(null)
const barChartRef = ref<HTMLDivElement | null>(null)

let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

const stats = ref({
  totalDetections: 128,
  totalObjects: 456,
  avgTime: 0.52,
  topClass: '飞机',
})

const classData = [
  { name: '飞机', value: 186, color: '#409EFF' },
  { name: '油罐', value: 128, color: '#36cfc9' },
  { name: '立交桥', value: 82, color: '#ffb547' },
  { name: '操场', value: 60, color: '#ff4d4f' },
]

const dailyData = {
  days: ['05/14', '05/15', '05/16', '05/17', '05/18', '05/19', '05/20'],
  counts: [12, 18, 15, 22, 20, 25, 16],
}

onMounted(() => {
  nextTick(() => {
    initPieChart()
    initBarChart()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  barChart?.dispose()
})

function handleResize() {
  pieChart?.resize()
  barChart?.resize()
}

function initPieChart() {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value, 'dark')
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#c8d6e5', fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['55%', '78%'],
        center: ['50%', '48%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#0d1137',
          borderWidth: 3,
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          color: '#c8d6e5',
          fontSize: 11,
        },
        data: classData.map((item) => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: item.color },
        })),
      },
    ],
  })
}

function initBarChart() {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value, 'dark')
  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dailyData.days,
      axisLine: { lineStyle: { color: 'rgba(200,214,229,0.2)' } },
      axisLabel: { color: '#c8d6e5', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '检测次数',
      nameTextStyle: { color: 'rgba(200,214,229,0.5)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(64,158,255,0.08)' } },
      axisLabel: { color: '#c8d6e5', fontSize: 11 },
    },
    series: [
      {
        type: 'bar',
        data: dailyData.counts,
        barWidth: '50%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: 'rgba(64,158,255,0.15)' },
          ]),
        },
      },
    ],
  })
}

function refreshCharts() {
  pieChart?.setOption({
    series: [{ data: classData.map((item) => ({ ...item, itemStyle: { color: item.color } })) }],
  })
  barChart?.setOption({
    series: [{ data: dailyData.counts }],
  })
}
</script>

<style scoped>
.analysis-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #e8ecf4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title .el-icon {
  color: #409EFF;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.charts-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr auto;
  gap: 20px;
  min-height: 0;
}

.chart-card-wide {
  grid-column: 1 / -1;
}

.chart-card {
  background: rgba(13, 17, 55, 0.6);
  border: 1px solid rgba(64, 158, 255, 0.1);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-header {
  padding: 16px 20px 0;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #e8ecf4;
  display: block;
}

.chart-subtitle {
  font-size: 11px;
  color: rgba(200, 214, 229, 0.4);
}

.chart-body {
  flex: 1;
  min-height: 280px;
  padding: 8px;
}

.summary-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: rgba(64, 158, 255, 0.04);
  border: 1px solid rgba(64, 158, 255, 0.06);
  border-radius: 10px;
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #409EFF;
}

.summary-icon .el-icon {
  color: #409EFF;
}

.summary-info {
  flex: 1;
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #409EFF;
}

.summary-label {
  font-size: 12px;
  color: rgba(200, 214, 229, 0.5);
  margin-top: 2px;
}
</style>