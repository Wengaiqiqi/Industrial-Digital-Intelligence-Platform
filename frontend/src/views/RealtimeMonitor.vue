<template>
  <div class="realtime-monitor">
    <div class="monitor-container">
      <!-- 左侧设备列表边栏 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h3>设备列表</h3>
          <div class="header-actions">
            <el-button 
              type="primary" 
              size="small" 
              :loading="deviceStore.loading"
              @click="refreshDevices"
            >
              刷新
            </el-button>
          </div>
        </div>

        <!-- 设备搜索和筛选 -->
        <div class="sidebar-filters">
          <el-input
            v-model="searchText"
            placeholder="搜索设备..."
            size="small"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="filterStatus"
            placeholder="筛选状态"
            size="small"
            style="width: 100%; margin-top: 10px;"
            clearable
          >
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="告警" value="warning" />
            <el-option label="错误" value="error" />
          </el-select>

          <el-select
            v-model="filterType"
            placeholder="设备类型"
            size="small"
            style="width: 100%; margin-top: 10px;"
            clearable
          >
            <el-option label="传感器" value="sensor" />
            <el-option label="执行器" value="actuator" />
            <el-option label="指示器" value="indicator" />
            <el-option label="IO设备" value="io" />
          </el-select>
        </div>

        <!-- 设备统计概览 -->
        <div class="device-stats">
          <div class="stat-item total">
            <span class="label">总设备</span>
            <span class="value">{{ deviceStats.total }}</span>
          </div>
          <div class="stat-item online">
            <span class="label">在线</span>
            <span class="value">{{ deviceStats.online }}</span>
          </div>
          <div class="stat-item warning">
            <span class="label">告警</span>
            <span class="value">{{ deviceStats.warning }}</span>
          </div>
          <div class="stat-item offline">
            <span class="label">离线</span>
            <span class="value">{{ deviceStats.offline }}</span>
          </div>
        </div>

        <!-- 设备列表 -->
        <div class="device-list">
          <div 
            v-for="device in filteredDevices" 
            :key="device.device_name"
            :class="['device-item', { active: selectedDevice?.device_name === device.device_name }]"
            @click="selectDevice(device)"
          >
            <div class="device-header">
              <div :class="['status-dot', device.status]"></div>
              <span class="device-name">{{ getDeviceDisplayName(device.device_name) }}</span>
            </div>
            <div class="device-info">
              <div class="device-type">{{ getDeviceTypeLabel(device.device_type) }}</div>              <div class="device-value">
                <span class="value">{{ formatValue(device.current_value || device.last_value) }}</span>
                <span class="unit">{{ device.unit }}</span>
              </div>
            </div>
            <div class="device-time">
              {{ formatRelativeTime(device.last_update) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧详情面板 -->
      <div class="detail-panel">
        <div v-if="!selectedDevice" class="no-selection">
          <el-empty description="请选择一个设备查看详细信息" />
        </div>

        <div v-else class="device-detail">
          <!-- 设备基本信息 -->
          <div class="detail-header">
            <div class="device-title">
              <h2>{{ getDeviceDisplayName(selectedDevice.device_name) }}</h2>
              <div class="device-badges">
                <el-tag :type="getStatusType(selectedDevice.status)" size="small">
                  {{ getStatusLabel(selectedDevice.status) }}
                </el-tag>
                <el-tag type="info" size="small">
                  {{ getDeviceTypeLabel(selectedDevice.device_type) }}
                </el-tag>
              </div>
            </div>            <div class="detail-actions">
              <el-button 
                type="primary" 
                size="small"
                @click="showControlDialog = true"
                :disabled="selectedDevice.status === 'offline'"
              >
                控制设备
              </el-button>
              <el-button 
                type="success" 
                size="small"
                @click="refreshDeviceData"
                :loading="refreshingData"
              >
                刷新数据
              </el-button>
              <el-button 
                type="warning" 
                size="small"
                @click="runQuickAnalysis"
                :loading="mlAnalysisLoading"
                :disabled="selectedDevice.status === 'offline'"
              >
                智能分析
              </el-button>
            </div>
          </div>

          <!-- 实时数据卡片 -->
          <div class="data-cards">
            <el-card class="data-card current-value">
              <template #header>
                <span>当前数值</span>
              </template>              <div class="card-content">
                <div class="main-value">
                  <span class="value">{{ formatValue(selectedDevice.current_value || selectedDevice.last_value) }}</span>
                  <span class="unit">{{ selectedDevice.unit }}</span>
                </div>
                <div class="value-trend">
                  <el-icon class="trend-icon up"><CaretTop /></el-icon>
                  <span class="trend-text">较上次 +2.3%</span>
                </div>
              </div>
            </el-card>

            <el-card class="data-card status-info">
              <template #header>
                <span>运行状态</span>
              </template>
              <div class="card-content">
                <div class="status-details">
                  <div class="status-item">
                    <span class="label">运行时间</span>
                    <span class="value">{{ formatRuntime(selectedDevice.total_runtime) }}</span>
                  </div>
                  <div class="status-item">
                    <span class="label">异常次数</span>
                    <span class="value error-count">{{ selectedDevice.error_count }}</span>
                  </div>
                  <div class="status-item">
                    <span class="label">最后更新</span>
                    <span class="value">{{ formatTime(selectedDevice.last_update) }}</span>
                  </div>
                </div>
              </div>
            </el-card>

            <el-card class="data-card alarm-status">
              <template #header>
                <span>报警状态</span>
              </template>
              <div class="card-content">
                <div class="alarm-summary">
                  <div class="alarm-count">
                    <span class="count">{{ deviceAlarms.length }}</span>
                    <span class="label">活跃报警</span>
                  </div>
                  <div class="alarm-level" v-if="deviceAlarms.length > 0">
                    <el-tag 
                      :type="getSeverityType(deviceAlarms[0].severity)" 
                      size="small"
                    >
                      {{ getSeverityLabel(deviceAlarms[0].severity) }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 历史数据图表 -->
          <div class="chart-section">
            <el-card class="chart-card">
              <template #header>
                <div class="chart-header">
                  <span>历史数据趋势</span>
                  <div class="chart-controls">
                    <el-select v-model="timeRange" size="small" style="width: 100px;">
                      <el-option label="1小时" value="1" />
                      <el-option label="6小时" value="6" />
                      <el-option label="24小时" value="24" />
                      <el-option label="7天" value="168" />
                    </el-select>
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click="loadHistoryChart"
                      :loading="chartLoading"
                    >
                      更新
                    </el-button>
                  </div>
                </div>
              </template>
              <div class="chart-container">
                <div ref="historyChartRef" class="chart"></div>
              </div>
            </el-card>
          </div>

          <!-- 实时数据表格 -->
          <div class="data-table-section">
            <el-card class="table-card">
              <template #header>
                <div class="table-header">
                  <span>最新数据记录</span>
                  <el-button 
                    type="text" 
                    size="small"
                    @click="loadRecentData"
                  >
                    查看更多
                  </el-button>
                </div>
              </template>
              <el-table 
                :data="recentData" 
                v-loading="tableLoading"
                size="small"
                max-height="300"
              >
                <el-table-column prop="timestamp" label="时间" width="150">
                  <template #default="{ row }">
                    {{ formatTime(row.timestamp) }}
                  </template>
                </el-table-column>
                <el-table-column prop="value" label="数值" width="100">
                  <template #default="{ row }">
                    {{ formatValue(row.value) }} {{ selectedDevice.unit }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)" size="small">
                      {{ getStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="备注" min-width="150" />
              </el-table>
            </el-card>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备控制对话框 -->
    <el-dialog
      v-model="showControlDialog"
      :title="`控制设备: ${selectedDevice?.device_name}`"
      width="500px"
    >
      <div v-if="selectedDevice" class="device-control">
        <el-form :model="controlForm" label-width="100px">
          <el-form-item label="设备名称:">
            <span>{{ getDeviceDisplayName(selectedDevice.device_name) }}</span>
          </el-form-item>
          
          <el-form-item label="当前状态:">
            <el-tag :type="getStatusType(selectedDevice.status)">
              {{ getStatusLabel(selectedDevice.status) }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="当前值:">
            <span class="value-display">
              {{ formatValue(selectedDevice.last_value) }}
              <span class="unit">{{ selectedDevice.unit }}</span>
            </span>
          </el-form-item>
          
          <el-divider />
          
          <el-form-item label="控制命令:">
            <el-select v-model="controlForm.command" placeholder="选择命令">
              <el-option label="设置数值" value="set_value" />
              <el-option label="启动设备" value="start" />
              <el-option label="停止设备" value="stop" />
              <el-option label="重置设备" value="reset" />
            </el-select>
          </el-form-item>
          
          <el-form-item 
            v-if="controlForm.command === 'set_value'" 
            label="目标值:"
          >
            <el-input-number
              v-model="controlForm.value"
              :min="0"
              :max="1000"
              :precision="1"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showControlDialog = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="executeControl"
            :loading="controlLoading"
          >
            执行
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDeviceStore } from '../stores/device'
import { useAlarmStore } from '../stores/alarm'
import { deviceAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  Search,
  CaretTop,
  Monitor,
  Warning,
  Bell
} from '@element-plus/icons-vue'

const router = useRouter()
const deviceStore = useDeviceStore()
const alarmStore = useAlarmStore()

// 响应式数据
const searchText = ref('')
const filterStatus = ref('')
const filterType = ref('')
const selectedDevice = ref(null)
const timeRange = ref('24')
const showControlDialog = ref(false)
const controlLoading = ref(false)
const refreshingData = ref(false)
const chartLoading = ref(false)
const tableLoading = ref(false)
const mlAnalysisLoading = ref(false)

// 图表相关
const historyChartRef = ref(null)
const historyChart = ref(null)

// 表格数据
const recentData = ref([])

// 控制表单
const controlForm = ref({
  command: '',
  value: null
})

// 定时器
let refreshTimer = null

// 计算属性
const deviceStats = computed(() => deviceStore.deviceStats)

const filteredDevices = computed(() => {
  let devices = deviceStore.devices

  // 搜索过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    devices = devices.filter(device => 
      device.device_name.toLowerCase().includes(search) ||
      getDeviceDisplayName(device.device_name).toLowerCase().includes(search)
    )
  }

  // 状态过滤
  if (filterStatus.value) {
    devices = devices.filter(device => device.status === filterStatus.value)
  }

  // 类型过滤
  if (filterType.value) {
    devices = devices.filter(device => device.device_type === filterType.value)
  }

  return devices
})

const deviceAlarms = computed(() => {
  if (!selectedDevice.value) return []
  return alarmStore.alarms.filter(alarm => 
    alarm.device_name === selectedDevice.value.device_name && 
    !alarm.acknowledged
  )
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

function getStatusType(status) {
  const typeMap = {
    'online': 'success',
    'offline': 'danger',
    'warning': 'warning',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

function getStatusLabel(status) {
  const labelMap = {
    'online': '在线',
    'offline': '离线',
    'warning': '告警',
    'error': '错误'
  }
  return labelMap[status] || status
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

function formatValue(value) {
  if (typeof value !== 'number') return '--'
  return value.toFixed(1)
}

function formatTime(timestamp) {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatRelativeTime(timestamp) {
  if (!timestamp) return '--'
  const now = new Date()
  const time = new Date(timestamp)
  const diff = now - time
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return `${Math.floor(diff / 86400000)}天前`
}

function formatRuntime(seconds) {
  // 如果没有seconds或为0，则计算从页面加载开始的时间
  let runtimeSeconds = seconds
  if (!seconds || seconds === 0) {
    runtimeSeconds = Math.floor((Date.now() - deviceStore.startTime) / 1000)
  }
  
  if (runtimeSeconds < 60) return `${runtimeSeconds}秒`
  const hours = Math.floor(runtimeSeconds / 3600)
  const minutes = Math.floor((runtimeSeconds % 3600) / 60)
  return hours > 0 ? `${hours}小时${minutes}分钟` : `${minutes}分钟`
}

async function refreshDevices() {
  await deviceStore.fetchRealtimeDevices()
}

function selectDevice(device) {
  selectedDevice.value = device
  loadHistoryChart()
  loadRecentData()
}

async function refreshDeviceData() {
  if (!selectedDevice.value) return
  
  refreshingData.value = true
  try {
    const response = await deviceAPI.getDeviceLatest(selectedDevice.value.device_name)
    if (response.data) {
      // 更新选中设备的数据
      const deviceIndex = deviceStore.devices.findIndex(d => d.device_name === selectedDevice.value.device_name)
      if (deviceIndex !== -1) {
        deviceStore.devices[deviceIndex] = { ...deviceStore.devices[deviceIndex], ...response.data }
        selectedDevice.value = deviceStore.devices[deviceIndex]
      }
    }
    ElMessage.success('设备数据已更新')
  } catch (error) {
    ElMessage.error('刷新设备数据失败')
  } finally {
    refreshingData.value = false
  }
}

async function loadHistoryChart() {
  if (!selectedDevice.value || !historyChartRef.value) return
  
  chartLoading.value = true
  try {
    const response = await deviceAPI.getDeviceHistory(
      selectedDevice.value.device_name, 
      parseInt(timeRange.value)
    )
    
    if (response.data) {
      const data = response.data.map(item => [
        new Date(item.timestamp).toLocaleTimeString(),
        item.value
      ])
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const time = params[0].axisValueLabel
            const value = params[0].value
            return `${time}<br/>${selectedDevice.value.device_name}: ${value}${selectedDevice.value.unit}`
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item[0]),
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: `{value}${selectedDevice.value.unit}`
          }
        },
        series: [{
          name: selectedDevice.value.device_name,
          type: 'line',
          smooth: true,
          data: data.map(item => item[1]),
          areaStyle: {
            opacity: 0.3
          },
          lineStyle: {
            color: '#409EFF'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{
                offset: 0, color: 'rgba(64, 158, 255, 0.3)'
              }, {
                offset: 1, color: 'rgba(64, 158, 255, 0.1)'
              }]
            }
          }
        }]
      }
      
      if (!historyChart.value) {
        historyChart.value = echarts.init(historyChartRef.value)
      }
      historyChart.value.setOption(option)
    }
  } catch (error) {
    ElMessage.error('加载历史数据失败')
  } finally {
    chartLoading.value = false
  }
}

async function loadRecentData() {  if (!selectedDevice.value) return
  
  tableLoading.value = true
  try {
    const response = await deviceAPI.getDeviceHistory(
      selectedDevice.value.device_name,
      1, // 最近1小时
      50  // 最多50条记录
    )
    
    if (response.data) {
      recentData.value = response.data.map(item => ({
        ...item,
        status: selectedDevice.value.status,
        description: '正常运行'
      }))
    }
  } catch (error) {
    ElMessage.error('加载最新数据失败')
  } finally {
    tableLoading.value = false
  }
}

async function executeControl() {
  if (!controlForm.value.command) {
    ElMessage.warning('请选择控制命令')
    return
  }

  controlLoading.value = true
  try {
    const success = await deviceStore.controlDevice(
      selectedDevice.value.device_name,
      controlForm.value.command,
      controlForm.value.value
    )
    
    if (success) {
      ElMessage.success('控制命令已发送')
      showControlDialog.value = false
      await refreshDeviceData()
    }
  } catch (error) {
    ElMessage.error('控制命令发送失败')
  } finally {
    controlLoading.value = false
  }
}

// 机器学习分析
async function runQuickAnalysis() {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }

  mlAnalysisLoading.value = true
  try {
    ElMessage.info('正在进行智能分析，请稍候...')
    
    // 导入API
    const { mlAPI } = await import('../api')
    
    // 进行快速分析（最近1小时数据）
    const result = await mlAPI.analyzeDevice(selectedDevice.value.device_name, 1)
    
    if (result.success) {
      // 显示分析结果对话框
      showAnalysisResult(result)
    } else {
      ElMessage.error(result.message || '分析失败')
    }
  } catch (error) {
    console.error('智能分析失败:', error)
    ElMessage.error('分析失败，请检查网络连接或稍后重试')
  } finally {
    mlAnalysisLoading.value = false
  }
}

function showAnalysisResult(result) {
  // 格式化分析结果
  let content = `<div style="text-align: left;">
    <h4 style="margin-top: 0;">设备: ${result.device_name}</h4>
    <p><strong>分析时间:</strong> ${new Date(result.analysis_time).toLocaleString()}</p>
    <p><strong>数据点数:</strong> ${result.data_points}</p>`

  // 异常检测结果
  if (result.anomaly_detection) {
    const isAnomaly = result.anomaly_detection.is_anomaly
    const confidence = result.anomaly_detection.confidence  // 0-1之间的小数
    const confidencePercent = (confidence * 100).toFixed(2)  // 转换为百分比
    content += `<p><strong>异常检测:</strong> 
      <span style="color: ${isAnomaly ? '#F56C6C' : '#67C23A'}">
        ${isAnomaly ? '检测到异常' : '运行正常'}
      </span> (置信度: ${confidencePercent}%)</p>`
  }

  // 故障预测结果
  if (result.failure_prediction) {
    const probability = result.failure_prediction.failure_probability  // 已经是百分比
    const riskLevel = result.failure_prediction.risk_level
    const riskColor = {
      'low': '#67C23A',
      'medium': '#E6A23C', 
      'high': '#F56C6C',
      'critical': '#F56C6C'
    }[riskLevel] || '#909399'
    
    content += `<p><strong>故障预测:</strong> ${probability}% 
      <span style="color: ${riskColor}">
        (${{'low': '低风险', 'medium': '中等风险', 'high': '高风险', 'critical': '严重风险'}[riskLevel] || '未知'})
      </span></p>`
  }

  // 建议
  if (result.recommendations && result.recommendations.length > 0) {
    content += '<h5>智能建议:</h5><ul>'
    result.recommendations.forEach(rec => {
      const color = {
        'critical': '#F56C6C',
        'warning': '#E6A23C',
        'info': '#409EFF',
        'success': '#67C23A'
      }[rec.type] || '#909399'
      
      content += `<li style="margin-bottom: 8px;">
        <span style="color: ${color}; font-weight: bold;">${rec.title}</span><br>
        <small style="color: #666;">${rec.description}</small><br>
        <small style="color: #999;">建议: ${rec.action}</small>
      </li>`
    })
    content += '</ul>'
  }

  content += '</div>'

  // 显示结果对话框
  ElMessageBox({
    title: '智能分析结果',
    message: content,
    dangerouslyUseHTMLString: true,
    confirmButtonText: '查看详细分析',
    cancelButtonText: '关闭',
    showCancelButton: true,
    type: 'info'
  }).then(() => {
    // 跳转到预测分析页面
    router.push('/prediction-analysis')
  }).catch(() => {
    // 用户取消，什么都不做
  })
}

// 启动定时刷新
function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    // 使用实时数据API刷新
    deviceStore.fetchRealtimeDevices()
    if (selectedDevice.value) {
      refreshDeviceData()
    }
  }, 5000) // 每5秒刷新一次，提高实时性
}

// 停止定时刷新
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听设备选择变化
watch(selectedDevice, (newDevice) => {
  if (newDevice) {
    nextTick(() => {
      loadHistoryChart()
      loadRecentData()
    })
  }
})

// 生命周期
onMounted(async () => {
  await deviceStore.fetchRealtimeDevices()
  await alarmStore.fetchAlarms()
  
  // 默认选择第一个设备
  if (deviceStore.devices.length > 0) {
    selectDevice(deviceStore.devices[0])
  }
  
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  if (historyChart.value) {
    historyChart.value.dispose()
  }
})
</script>

<style lang="scss" scoped>
.realtime-monitor {
  height: calc(100vh - 100px);
  
  .monitor-container {
    display: flex;
    height: 100%;
    gap: 20px;
  }
}

.sidebar {
  width: 350px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  
  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h3 {
      margin: 0;
      color: #333;
      font-size: 16px;
    }
  }
  
  .sidebar-filters {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .device-stats {
    padding: 15px 20px;
    border-bottom: 1px solid #f0f0f0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      
      .label {
        color: #666;
      }
      
      .value {
        font-weight: 600;
      }
      
      &.total {
        background: rgba(64, 158, 255, 0.1);
        .value { color: #409eff; }
      }
      
      &.online {
        background: rgba(103, 194, 58, 0.1);
        .value { color: #67c23a; }
      }
      
      &.warning {
        background: rgba(230, 162, 60, 0.1);
        .value { color: #e6a23c; }
      }
      
      &.offline {
        background: rgba(245, 108, 108, 0.1);
        .value { color: #f56c6c; }
      }
    }
  }
  
  .device-list {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    
    .device-item {
      padding: 12px;
      margin-bottom: 8px;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
      }
      
      &.active {
        border-color: #409eff;
        background: rgba(64, 158, 255, 0.05);
      }
      
      .device-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          
          &.online { background: #67c23a; }
          &.offline { background: #f56c6c; }
          &.warning { background: #e6a23c; }
          &.error { background: #f56c6c; }
        }
        
        .device-name {
          font-weight: 500;
          color: #333;
        }
      }
      
      .device-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        
        .device-type {
          font-size: 12px;
          color: #666;
        }
        
        .device-value {
          .value {
            font-weight: 600;
            color: #409eff;
          }
          
          .unit {
            font-size: 12px;
            color: #999;
            margin-left: 2px;
          }
        }
      }
      
      .device-time {
        font-size: 11px;
        color: #999;
      }
    }
  }
}

.detail-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  
  .no-selection {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .device-detail {
    height: 100%;
    overflow-y: auto;
    
    .detail-header {
      padding: 20px;
      border-bottom: 1px solid #e4e7ed;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .device-title {
        h2 {
          margin: 0 0 10px 0;
          color: #333;
        }
        
        .device-badges {
          display: flex;
          gap: 8px;
        }
      }
      
      .detail-actions {
        display: flex;
        gap: 10px;
      }
    }
    
    .data-cards {
      padding: 20px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      
      .data-card {
        .card-content {
          .main-value {
            text-align: center;
            margin-bottom: 15px;
            
            .value {
              font-size: 36px;
              font-weight: 600;
              color: #409eff;
            }
            
            .unit {
              font-size: 16px;
              color: #666;
              margin-left: 5px;
            }
          }
          
          .value-trend {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            
            .trend-icon {
              &.up { color: #67c23a; }
              &.down { color: #f56c6c; }
            }
            
            .trend-text {
              font-size: 12px;
              color: #666;
            }
          }
          
          .status-details {
            .status-item {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 8px 0;
              border-bottom: 1px solid #f0f0f0;
              
              &:last-child {
                border-bottom: none;
              }
              
              .label {
                font-size: 14px;
                color: #666;
              }
              
              .value {
                font-weight: 500;
                color: #333;
                
                &.error-count {
                  color: #f56c6c;
                }
              }
            }
          }
          
          .alarm-summary {
            text-align: center;
            
            .alarm-count {
              margin-bottom: 15px;
              
              .count {
                font-size: 36px;
                font-weight: 600;
                color: #f56c6c;
              }
              
              .label {
                display: block;
                font-size: 14px;
                color: #666;
                margin-top: 5px;
              }
            }
          }
        }
      }
    }
    
    .chart-section {
      padding: 0 20px 20px;
      
      .chart-card {
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .chart-controls {
            display: flex;
            gap: 10px;
            align-items: center;
          }
        }
        
        .chart-container {
          height: 300px;
          
          .chart {
            width: 100%;
            height: 100%;
          }
        }
      }
    }
    
    .data-table-section {
      padding: 0 20px 20px;
      
      .table-card {
        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
      }
    }
  }
}

.device-control {
  .value-display {
    font-size: 16px;
    font-weight: 500;
    
    .unit {
      color: #999;
      font-size: 14px;
      margin-left: 4px;
    }
  }
}
</style>
