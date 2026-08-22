<template>
  <el-container class="app-shell" :class="{ 'is-collapsed': collapsed }">
    <el-aside :width="collapsed ? '76px' : '212px'" class="app-aside">
      <router-link class="brand" to="/dashboard" aria-label="返回运行总览">
        <span v-show="!collapsed" class="brand-name">工业数智平台</span>
      </router-link>

      <el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="app-menu"
      >
        <el-menu-item index="/dashboard"><el-icon><Grid /></el-icon><template #title>运行总览</template></el-menu-item>
        <el-menu-item index="/devices"><el-icon><Connection /></el-icon><template #title>设备管理</template></el-menu-item>
        <el-menu-item index="/alarms"><el-icon><Bell /></el-icon><template #title>告警中心</template></el-menu-item>
        <el-menu-item index="/realtime-monitor"><el-icon><VideoPlay /></el-icon><template #title>实时监控</template></el-menu-item>
        <el-menu-item index="/historical-data"><el-icon><DataBoard /></el-icon><template #title>历史数据</template></el-menu-item>
        <el-menu-item index="/prediction"><el-icon><TrendCharts /></el-icon><template #title>预测分析</template></el-menu-item>
        <el-menu-item index="/3d-scene"><el-icon><Box /></el-icon><template #title>三维场景</template></el-menu-item>
      </el-menu>

      <button class="collapse-button" type="button" @click="collapsed = !collapsed">
        <el-icon><DArrowLeft v-if="!collapsed" /><DArrowRight v-else /></el-icon>
        <span v-if="!collapsed">收起菜单</span>
      </button>
    </el-aside>

    <el-container class="workspace">
      <el-header class="app-header">
        <div class="route-heading"><span class="route-title">{{ routeTitle }}</span><span v-if="routeSubtitle" class="route-subtitle">{{ routeSubtitle }}</span></div>
        <div class="header-tools">
          <span class="system-clock"><el-icon><Clock /></el-icon>{{ currentTime }}</span>
          <el-button text circle aria-label="日历"><el-icon><Calendar /></el-icon></el-button>
          <el-badge :value="unreadAlarms" :hidden="!unreadAlarms">
            <el-button text circle aria-label="查看告警" @click="showAlarmDialog = true"><el-icon><Bell /></el-icon></el-button>
          </el-badge>
          <el-button text circle aria-label="帮助"><el-icon><QuestionFilled /></el-icon></el-button>
          <span class="header-divider"></span>
          <span class="admin-user"><el-icon><User /></el-icon><span>管理员</span><el-icon class="chevron"><ArrowDown /></el-icon></span>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="showAlarmDialog" title="系统告警" width="min(920px, 90vw)" class="alarm-dialog">
      <AlarmList :compact="true" />
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAlarmStore } from './stores/alarm'
import AlarmList from './components/AlarmList.vue'
import {
  ArrowDown,
  Bell,
  Box,
  Calendar,
  Clock,
  Connection,
  DArrowLeft,
  DArrowRight,
  DataBoard,
  Grid,
  QuestionFilled,
  TrendCharts,
  User,
  VideoPlay
} from '@element-plus/icons-vue'

const route = useRoute()
const alarmStore = useAlarmStore()
const collapsed = ref(false)
const showAlarmDialog = ref(false)
const currentTime = ref('')
const unreadAlarms = computed(() => alarmStore.unreadCount)
const routeTitle = computed(() => route.path === '/devices' ? '' : (route.meta.title || '工业数智平台'))
const routeSubtitle = computed(() => ({
  '/alarms': '优先处理高风险事件，追踪处置闭环',
  '/prediction': '基于机器学习识别异常趋势与潜在故障'
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
