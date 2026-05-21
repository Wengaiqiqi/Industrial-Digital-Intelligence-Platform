<template>
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="status-card">
          <div class="stat-header">
            <el-icon class="stat-icon online"><Platform /></el-icon>
            <span class="stat-title">在线设备</span>
          </div>
          <div class="stat-value">{{ deviceStats.online }}/{{ deviceStats.total }}</div>
          <div class="stat-description">设备运行正常</div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="status-card">
          <div class="stat-header">
            <el-icon class="stat-icon warning"><Warning /></el-icon>
            <span class="stat-title">报警设备</span>
          </div>
          <div class="stat-value">{{ deviceStats.warning + deviceStats.error }}</div>
          <div class="stat-description">需要关注</div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="status-card">
          <div class="stat-header">
            <el-icon class="stat-icon alarm"><Bell /></el-icon>
            <span class="stat-title">未读报警</span>
          </div>
          <div class="stat-value">{{ alarmStore.unreadCount }}</div>
          <div class="stat-description">待处理报警</div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="status-card">
          <div class="stat-header">
            <el-icon class="stat-icon efficiency"><TrendCharts /></el-icon>
            <span class="stat-title">系统效率</span>
          </div>
          <div class="stat-value">{{ systemEfficiency }}%</div>
          <div class="stat-description">运行效率良好</div>
        </div>
      </el-col>
    </el-row>    <!-- 实时数据展示 -->
    <el-row :gutter="20" class="content-row">
      <!-- 设备状态监控 -->
      <el-col :span="24">
        <el-card class="device-monitor-card">
          <template #header>
            <div class="card-header">
              <span>设备实时状态</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="refreshDevices"
                :loading="deviceStore.loading"
              >
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="device-grid">
            <div 
              v-for="device in displayDevices" 
              :key="device.device_name"
              class="device-item"
              @click="showDeviceDetail(device)"
            >
              <div class="device-header">
                <span class="device-name">{{ getDeviceDisplayName(device.device_name) }}</span>
                <div :class="['status-indicator', device.status]"></div>
              </div>
              <div class="device-value">
                <span class="value">{{ formatValue(device.last_value) }}</span>
                <span class="unit">{{ device.unit }}</span>
              </div>
              <div class="device-type">{{ getDeviceTypeLabel(device.device_type) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 报警和系统状态 -->
    <el-row :gutter="20" class="content-row">
      <!-- 最新报警 -->
      <el-col :span="16">
        <el-card class="alarm-card">
          <template #header>
            <div class="card-header">
              <span>最新报警</span>
              <el-link type="primary" @click="$router.push('/alarms')">查看全部</el-link>
            </div>
          </template>
          
          <el-table :data="recentAlarms" style="width: 100%" max-height="300">
            <el-table-column prop="device_name" label="设备" width="120">
              <template #default="{ row }">
                {{ getDeviceDisplayName(row.device_name) }}
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ getSeverityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="报警信息" />
            <el-table-column prop="timestamp" label="时间" width="150">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button 
                  v-if="!row.acknowledged"
                  type="primary" 
                  size="small" 
                  @click="acknowledgeAlarm(row.id)"
                >
                  确认
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 系统信息 -->
      <el-col :span="8">
        <el-card class="system-info-card">
          <template #header>
            <span>系统信息</span>
          </template>
          
          <div class="system-info">
            <div class="info-item">
              <span class="label">数据更新:</span>
              <span class="value">{{ formatTime(lastDataUpdate) }}</span>
            </div>
            <div class="info-item">
              <span class="label">运行时间:</span>
              <span class="value">{{ systemUptime }}</span>
            </div>
            <div class="info-item">
              <span class="label">连接状态:</span>
              <span class="value">
                <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'" size="small">
                  {{ connectionStatus === 'connected' ? '已连接' : '断开' }}
                </el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="label">数据点数:</span>
              <span class="value">{{ totalDataPoints.toLocaleString() }}</span>
            </div>
          </div>        </el-card>
      </el-col>
    </el-row>

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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useDeviceStore } from '../stores/device'
import { useAlarmStore } from '../stores/alarm'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  Platform, 
  Warning, 
  Bell, 
  TrendCharts 
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

async function loadDeviceChart(deviceName) {
  if (!deviceChartRef.value) return
  
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
        boundaryGap: false
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        name: '历史数据',
        type: 'line',
        smooth: true,
        data: values,
        areaStyle: {
          opacity: 0.3
        },
        lineStyle: {
          color: '#67c23a'
        }
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
          color: #67c23a;
        }
        
        &.warning {
          color: #e6a23c;
        }
        
        &.alarm {
          color: #f56c6c;
        }
        
        &.efficiency {
          color: #409eff;
        }
      }

      .stat-title {
        font-size: 14px;
        color: #666;
      }
    }

    .stat-value {
      font-size: 32px;
      font-weight: 600;
      color: #333;
      margin: 10px 0;
    }

    .stat-description {
      font-size: 12px;
      color: #999;
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
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
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
          color: #409eff;
        }

        .unit {
          font-size: 12px;
          color: #999;
          margin-left: 4px;
        }
      }

      .device-type {
        font-size: 12px;
        color: #666;
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
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .label {
        font-size: 14px;
        color: #666;
      }

      .value {
        font-size: 14px;
        font-weight: 500;
        color: #333;
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
