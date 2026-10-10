<template>
  <div class="app-shell">
    <nav class="app-nav" aria-label="主导航">
      <router-link class="brand" to="/dashboard" aria-label="返回运行总览">
        <svg viewBox="0 0 28 28" aria-hidden="true">
          <path d="M14 2 25 8.5v11L14 26 3 19.5v-11z" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path d="M14 9l6 3.5v7L14 23l-6-3.5v-7z" fill="currentColor" fill-opacity=".2" stroke="currentColor" stroke-width="1.2" />
        </svg>
        <span>
          <span class="brand-name">工业数智平台</span>
          <span class="brand-sub">LINE-01 · 演示产线</span>
        </span>
      </router-link>
      <template v-for="group in navGroups" :key="group.label">
        <div class="nav-group">{{ group.label }}</div>
        <router-link v-for="item in group.items" :key="item.to" :to="item.to" class="nav-item" active-class="is-active">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <span v-if="item.to === '/alarms' && unreadAlarms" class="nav-badge">{{ unreadAlarms }}</span>
        </router-link>
      </template>
    </nav>

    <div class="workspace">
      <header class="app-header">
        <div>
          <h1 class="route-title">{{ route.meta.title || '工业数智平台' }}</h1>
          <p v-if="routeSubtitle" class="route-subtitle">{{ routeSubtitle }}</p>
        </div>
        <div class="header-tools">
          <span class="live-pill">实时 · 2 s</span>
          <span class="system-clock">{{ currentTime }}</span>
          <div class="segmented" role="group" aria-label="界面主题">
            <button type="button" :aria-pressed="theme === 'dark'" @click="theme = 'dark'"><el-icon><Moon /></el-icon>深色</button>
            <button type="button" :aria-pressed="theme === 'light'" @click="theme = 'light'"><el-icon><Sunny /></el-icon>浅色</button>
          </div>
          <button type="button" class="icon-button" :aria-label="`查看告警，${unreadAlarms} 条未确认`" @click="showAlarmDialog = true">
            <el-icon><Bell /></el-icon>
            <span v-if="unreadAlarms" class="dot"></span>
          </button>
          <span class="admin-user"><span class="avatar">管</span>管理员</span>
        </div>
      </header>
      <main class="app-main">
        <router-view />
      </main>
    </div>

    <el-dialog v-model="showAlarmDialog" title="系统告警" width="min(920px, 90vw)" class="alarm-dialog">
      <AlarmList :compact="true" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAlarmStore } from './stores/alarm'
import { theme } from './theme'
import AlarmList from './components/AlarmList.vue'
import { Bell, Box, Clock, Connection, Grid, Moon, Sunny, TrendCharts, VideoPlay } from '@element-plus/icons-vue'

const navGroups = [
  { label: '监视', items: [
    { to: '/dashboard', label: '运行总览', icon: Grid },
    { to: '/3d-scene', label: '三维场景', icon: Box },
    { to: '/realtime-monitor', label: '实时监控', icon: VideoPlay }
  ] },
  { label: '管理', items: [
    { to: '/devices', label: '设备管理', icon: Connection },
    { to: '/alarms', label: '告警中心', icon: Bell }
  ] },
  { label: '分析', items: [
    { to: '/historical-data', label: '历史数据', icon: Clock },
    { to: '/prediction', label: '预测分析', icon: TrendCharts }
  ] }
]

const route = useRoute()
const alarmStore = useAlarmStore()
const showAlarmDialog = ref(false)
const currentTime = ref('')
const unreadAlarms = computed(() => alarmStore.unreadCount)
const routeSubtitle = computed(() => ({
  '/dashboard': 'LINE-01 演示产线 · 数据每 2 秒刷新',
  '/3d-scene': 'LINE-01 数字孪生 · 点击设备查看实时数据',
  '/alarms': '优先处理高风险事件，追踪处置闭环',
  '/prediction': 'IsolationForest 异常检测 · LSTM 时序预测'
}[route.path] || ''))

let clockTimer
function updateClock() {
  currentTime.value = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  }).format(new Date()).replaceAll('/', '-')
}

onMounted(() => {
  updateClock()
  clockTimer = window.setInterval(updateClock, 1000)
  alarmStore.fetchAlarms({ hours: 24 })
})

onBeforeUnmount(() => window.clearInterval(clockTimer))
</script>
