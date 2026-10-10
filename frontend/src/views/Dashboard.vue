<template>
  <div class="dashboard">
    <div class="design-stats dashboard-stats">
      <div class="design-stat-card">
        <span class="design-stat-icon"><Platform /></span>
        <div><span class="design-stat-label">在线设备</span><strong>{{ deviceStats.online }}/{{ deviceStats.total }}</strong></div>
        <span class="micro-bars" aria-hidden="true"><i v-for="n in 9" :key="n" :style="{ height: `${8 + (n * 7) % 28}px` }"></i></span>
      </div>
      <div class="design-stat-card">
        <span class="design-stat-icon"><Bell /></span>
        <div><span class="design-stat-label">待处理告警</span><strong>{{ alarmStore.unreadCount }}</strong></div>
        <span class="micro-bars" aria-hidden="true"><i v-for="n in 9" :key="n" :style="{ height: `${6 + (n * 11) % 30}px` }"></i></span>
      </div>
      <div class="design-stat-card">
        <span class="design-stat-icon"><TrendCharts /></span>
        <div><span class="design-stat-label">系统效率</span><strong>{{ systemEfficiency }}%</strong></div>
        <span class="micro-line" aria-hidden="true">⌁⌁⌁</span>
      </div>
      <div class="design-stat-card">
        <span class="design-stat-icon"><DataBoard /></span>
        <div><span class="design-stat-label">今日数据点</span><strong>{{ totalDataPoints.toLocaleString() }}</strong></div>
        <span class="micro-bars" aria-hidden="true"><i v-for="n in 9" :key="n" :style="{ height: `${7 + (n * 5) % 31}px` }"></i></span>
      </div>
    </div>

    <LieflatOverview :efficiency="systemEfficiency" />

    <div class="dashboard-tables">
      <section class="design-table-card">
        <h3>设备状态</h3>
        <table>
          <thead><tr><th>设备</th><th>状态</th><th>当前值</th><th>趋势</th><th>最后更新</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="device in displayDevices.slice(0, 6)" :key="device.device_name">
              <td>{{ getDeviceDisplayName(device.device_name) }}</td>
              <td><span class="soft-tag">{{ getStatusLabel(device.status) }}</span></td>
              <td><strong>{{ formatValue(device.last_value) }}</strong> {{ device.unit }}</td>
              <td><span class="table-ticks"><i v-for="n in 8" :key="n" :style="{ height: `${4 + (n * 5 + device.device_name.length) % 10}px` }"></i></span></td>
              <td>{{ new Date(device.last_update || Date.now()).toLocaleTimeString('zh-CN', { hour12: false }) }}</td>
              <td><button class="table-link" @click="showDeviceDetail(device)">详情</button></td>
            </tr>
            <tr v-if="!displayDevices.length"><td colspan="6" class="empty-row">暂无设备数据</td></tr>
          </tbody>
        </table>
        <footer>共 {{ deviceStats.total }} 台设备，在线 {{ deviceStats.online }} 台，离线 {{ deviceStats.offline }} 台</footer>
      </section>

      <section class="design-table-card">
        <h3>最近告警</h3>
        <table>
          <thead><tr><th>设备</th><th>状态</th><th>当前值</th><th>趋势</th><th>最后更新</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="alarm in recentAlarms" :key="alarm.id">
              <td>{{ getDeviceDisplayName(alarm.device_name) }}</td>
              <td><span class="soft-tag">{{ getSeverityLabel(alarm.severity) }}</span></td>
              <td class="message-cell">{{ alarm.message }}</td>
              <td><span class="table-ticks"><i v-for="n in 8" :key="n" :style="{ height: `${4 + (n * 3 + String(alarm.id).length) % 10}px` }"></i></span></td>
              <td>{{ new Date(alarm.timestamp || Date.now()).toLocaleTimeString('zh-CN', { hour12: false }) }}</td>
              <td><button class="table-link" @click="$router.push('/alarms')">详情</button></td>
            </tr>
            <tr v-if="!recentAlarms.length"><td colspan="6" class="empty-row">暂无告警</td></tr>
          </tbody>
        </table>
        <footer>共 {{ alarmStore.alarms.length }} 条告警，待处理 {{ alarmStore.unreadCount }} 条</footer>
      </section>
    </div>

    <!-- 设备详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`设备详情: ${currentDevice?.device_name ? getDeviceDisplayName(currentDevice.device_name) : ''}`"
      width="800px"
    >
      <div v-if="currentDevice" class="device-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备名称">
            {{ getDeviceDisplayName(currentDevice.device_name) }}
          </el-descriptions-item>
          <el-descriptions-item label="设备类型">
            {{ getDeviceTypeLabel(currentDevice.device_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(currentDevice.status)">
              {{ getStatusLabel(currentDevice.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前值">
            {{ formatValue(currentDevice.last_value) }} {{ currentDevice.unit }}
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">
            {{ formatTime(currentDevice.last_update) }}
          </el-descriptions-item>
          <el-descriptions-item label="运行时间">
            {{ formatRuntime(currentDevice.total_runtime) }}
          </el-descriptions-item>
          <el-descriptions-item label="异常次数">
            {{ currentDevice.error_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="设备ID">
            {{ currentDevice.device_name }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 历史数据图表 -->
        <div class="device-chart" style="margin-top: 20px;">
          <h4>24小时历史数据</h4>
          <div ref="deviceChartRef" class="chart-container-detail"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { theme, cssVar } from '../theme'
import { useDeviceStore } from '../stores/device'
import { useAlarmStore } from '../stores/alarm'
import LieflatOverview from '../components/LieflatOverview.vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  Platform, 
  Bell, 
  TrendCharts,
  DataBoard
} from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const alarmStore = useAlarmStore()

// 响应式数据
const lastDataUpdate = ref(new Date())
const systemUptime = ref('') // 从前端启动开始计算
const connectionStatus = ref('connected')
const totalDataPoints = ref(0) // 动态更新数据点数
const systemEfficiency = ref(96.8)

// 设备详情对话框相关
const showDetailDialog = ref(false)
const currentDevice = ref(null)
const deviceChartRef = ref(null)
const deviceChart = ref(null)

// 数据更新定时器
let dataUpdateTimer = null

// 计算属性
const deviceStats = computed(() => deviceStore.deviceStats)

const displayDevices = computed(() => {
  return deviceStore.devices.slice(0, 12) // 显示前12个设备，适应全宽布局
})

const recentAlarms = computed(() => {
  return alarmStore.recentAlarms.slice(0, 5) // 显示最新5条报警
})

// 方法
function getDeviceDisplayName(deviceName) {
  const nameMap = {
    'temperature_sensor_1': '温度传感器1',
    'temperature_sensor_2': '温度传感器2',
    'fan_1': '风扇1',
    'fan_2': '风扇2',
    'servo_motor_1': '伺服电机1',
    'servo_motor_2': '伺服电机2',
    'pressure_sensor_1': '压力传感器1',
    'flow_meter_1': '流量计1',
    'indicator_light_1': '指示灯1',
    'digital_input_1': '数字输入1',
    'digital_output_1': '数字输出1'
  }
  return nameMap[deviceName] || deviceName
}

function getDeviceTypeLabel(deviceType) {
  const typeMap = {
    'sensor': '传感器',
    'actuator': '执行器',
    'indicator': '指示器',
    'io': 'IO设备'
  }
  return typeMap[deviceType] || deviceType
}

function formatValue(value) {
  if (typeof value !== 'number') return '--'
  return value.toFixed(1)
}

function formatTime(timestamp) {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString()
}

function getSeverityType(severity) {
  const typeMap = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return typeMap[severity] || 'info'
}

function getSeverityLabel(severity) {
  const labelMap = {
    'critical': '严重',
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labelMap[severity] || severity
}

function showDeviceDetail(device) {
  currentDevice.value = device
  showDetailDialog.value = true
  
  // 加载设备历史数据图表
  nextTick(() => {
    loadDeviceChart(device.device_name)
  })
}

function getStatusType(status) {
  const typeMap = {
    'online': 'success',
    'offline': 'danger',
    'warning': 'warning',
    'error': 'danger',
    'maintenance': 'info'
  }
  return typeMap[status] || 'info'
}

function getStatusLabel(status) {
  const labelMap = {
    'online': '在线',
    'offline': '离线',
    'warning': '告警',
    'error': '故障',
    'maintenance': '维护中'
  }
  return labelMap[status] || status
}

function formatRuntime(runtime) {
  // 使用设备store中的格式化函数
  return deviceStore.formatRuntime(runtime)
}

let chartDevice = null
watch(theme, () => chartDevice && nextTick(() => loadDeviceChart(chartDevice)))

async function loadDeviceChart(deviceName) {
  if (!deviceChartRef.value) return
  chartDevice = deviceName
  
  try {
    // 获取设备历史数据
    const response = await fetch(`/api/devices/${deviceName}/history?hours=24`)
    const data = await response.json()
    
    if (!deviceChart.value) {
      deviceChart.value = echarts.init(deviceChartRef.value)
    }
    
    const times = data.data?.map(item => new Date(item.timestamp).toLocaleTimeString()) || []
    const values = data.data?.map(item => item.value) || []
    
    const option = {
      title: {
        show: false
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const time = params[0].axisValueLabel
          const value = params[0].value
          return `${time}<br/>数值: ${value}`
        }
      },
      xAxis: {
        type: 'category',
        data: times,
        boundaryGap: false,
        axisLine: { lineStyle: { color: cssVar('--grid') } },
        axisTick: { lineStyle: { color: cssVar('--grid') } },
        axisLabel: { color: cssVar('--muted') }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: cssVar('--chart-grid') } },
        axisLabel: { color: cssVar('--muted') }
      },
      series: [{
        name: '历史数据',
        type: 'line',
        smooth: false,
        symbol: 'circle',
        symbolSize: 5,
        showAllSymbol: values.length <= 30,
        data: values,
        lineStyle: {
          color: cssVar('--data'),
          width: 1.8
        },
        itemStyle: { color: cssVar('--paper-soft'), borderColor: cssVar('--data'), borderWidth: 1.5 }
      }]
    }
    
    deviceChart.value.setOption(option)
  } catch (error) {
    console.error('加载设备历史数据失败:', error)
    ElMessage.warning('加载历史数据失败')
  }
}

async function acknowledgeAlarm(alarmId) {
  const success = await alarmStore.acknowledgeAlarm(alarmId)
  if (success) {
    ElMessage.success('报警已确认')
  }
}

// 更新系统运行时间
function updateSystemUptime() {
  const startTime = deviceStore.startTime
  const currentTime = Date.now()
  const uptimeSeconds = Math.floor((currentTime - startTime) / 1000)
  systemUptime.value = deviceStore.formatRuntime(uptimeSeconds)
}

// 更新总数据点数
async function updateTotalDataPoints() {
  try {
    const response = await fetch('/api/statistics/dashboard')
    const data = await response.json()
    if (data.success && data.data.data_points) {
      totalDataPoints.value = data.data.data_points.total
    }
  } catch (error) {
    console.error('获取数据点统计失败:', error)
  }
}

async function refreshDevices() {
  await deviceStore.fetchRealtimeDevices()
  lastDataUpdate.value = new Date()
  updateSystemUptime()
}

// 生命周期
onMounted(async () => {
  // 初始化数据
  await deviceStore.fetchDevices()
  await alarmStore.fetchAlarms({ hours: 24 })
  
  // 初始化系统运行时间和数据点数
  updateSystemUptime()
  await updateTotalDataPoints()
  
  // 启动定时更新
  dataUpdateTimer = setInterval(() => {
    refreshDevices()
    updateTotalDataPoints() // 每次都更新数据点数
  }, 5000) // 5秒更新一次设备数据
  
  // 启动运行时间更新定时器
  setInterval(() => {
    updateSystemUptime()
  }, 1000) // 每秒更新运行时间
})

onUnmounted(() => {
  if (dataUpdateTimer) {
    clearInterval(dataUpdateTimer)
  }
  if (deviceChart.value) {
    deviceChart.value.dispose()
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stats-row {
    margin-bottom: 20px;
  }

  .content-row {
    margin-bottom: 20px;
  }

  .status-card {
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    .stat-header {
      display: flex;
      align-items: center;
      gap: 8px;

      .stat-icon {
        font-size: 24px;
        
        &.online {
          color: var(--data-2);
        }
        
        &.warning {
          color: var(--data-2);
        }
        
        &.alarm {
          color: var(--ink);
        }
        
        &.efficiency {
          color: var(--data);
        }
      }

      .stat-title {
        font-size: 14px;
        color: var(--data);
      }
    }

    .stat-value {
      font-size: 32px;
      font-weight: 600;
      color: var(--ink);
      margin: 10px 0;
    }

    .stat-description {
      font-size: 12px;
      color: var(--data-2);
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .device-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 15px;

    @media (max-width: 1600px) {
      grid-template-columns: repeat(4, 1fr);
    }

    @media (max-width: 1200px) {
      grid-template-columns: repeat(3, 1fr);
    }

    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }

    .device-item {
      padding: 15px;
      border: 1px solid var(--data-3);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        border-color: var(--data);
        box-shadow: 0 2px 8px var(--accent-soft);
      }

      .device-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .device-name {
          font-size: 14px;
          font-weight: 500;
        }
      }

      .device-value {
        margin-bottom: 5px;

        .value {
          font-size: 20px;
          font-weight: 600;
          color: var(--data);
        }

        .unit {
          font-size: 12px;
          color: var(--data-2);
          margin-left: 4px;
        }
      }

      .device-type {
        font-size: 12px;
        color: var(--data);
      }
    }
  }

  .chart-container {
    height: 300px;

    .chart {
      width: 100%;
      height: 100%;
    }
  }

  .system-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid var(--paper);

      &:last-child {
        border-bottom: none;
      }

      .label {
        font-size: 14px;
        color: var(--data);
      }

      .value {
        font-size: 14px;
        font-weight: 500;
        color: var(--ink);
      }    }
  }

  .device-detail {
    .chart-container-detail {
      height: 300px;
      margin-top: 10px;
    }
  }
}
</style>
