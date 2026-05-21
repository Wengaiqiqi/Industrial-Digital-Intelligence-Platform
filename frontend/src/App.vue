<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-left">
          <h1 class="system-title">
            <el-icon class="title-icon"><Platform /></el-icon>
            工业数智平台
          </h1>
        </div>
        <div class="header-right">
          <el-badge :value="unreadAlarms" class="alarm-badge">
            <el-button 
              type="danger" 
              :icon="Bell" 
              circle 
              @click="showAlarmDialog = true"
            />
          </el-badge>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边导航栏 -->
        <el-aside width="200px" class="app-aside">
          <el-menu
            :default-active="$route.path"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item index="/dashboard">
              <el-icon><Monitor /></el-icon>
              <span>总览</span>
            </el-menu-item>            <el-menu-item index="/devices">
              <el-icon><Setting /></el-icon>
              <span>设备管理</span>
            </el-menu-item>
            <el-menu-item index="/alarms">
              <el-icon><Bell /></el-icon>
              <span>报警管理</span>
            </el-menu-item>
            <el-menu-item index="/3d-scene">
              <el-icon><View /></el-icon>
              <span>3D场景</span>
            </el-menu-item>            <el-menu-item index="/prediction">
              <el-icon><TrendCharts /></el-icon>
              <span>预测分析</span>
            </el-menu-item>
            <el-menu-item index="/historical-data">
              <el-icon><DataBoard /></el-icon>
              <span>历史数据</span>
            </el-menu-item>
            <el-menu-item index="/realtime-monitor">
              <el-icon><Monitor /></el-icon>
              <span>实时监控</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主内容区域 -->
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- 报警对话框 -->
    <el-dialog
      v-model="showAlarmDialog"
      title="系统报警"
      width="60%"
    >
      <AlarmList :compact="true" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAlarmStore } from './stores/alarm'
import AlarmList from './components/AlarmList.vue'
import { 
  Platform, 
  Bell, 
  Monitor, 
  Setting, 
  TrendCharts, 
  View,
  DataBoard
} from '@element-plus/icons-vue'

const alarmStore = useAlarmStore()
const showAlarmDialog = ref(false)
const unreadAlarms = ref(0)

onMounted(() => {
  // 获取未读报警数量
  alarmStore.fetchAlarms()
  unreadAlarms.value = alarmStore.unreadCount
})
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-left {
  .system-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;

    .title-icon {
      font-size: 24px;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;

  .alarm-badge {
    :deep(.el-badge__content) {
      right: -5px;
      top: -5px;
    }
  }
}

.app-aside {
  background-color: #545c64;
  box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}

.app-main {
  padding: 20px;
  background-color: #f5f5f5;
  overflow-y: auto;
}
</style>
