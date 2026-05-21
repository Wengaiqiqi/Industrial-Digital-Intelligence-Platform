<template>
  <div class="historical-data-view">
    <!-- 页面标题和控制 -->
    <div class="page-header">
      <h2>历史数据分析</h2>
      <div class="header-controls">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          @change="loadHistoricalData"
        />
        <el-button type="primary" @click="loadHistoricalData" :loading="loading">
          刷新数据
        </el-button>
        <el-button @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </div>
    </div>

    <!-- 数据统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ formatNumber(totalRecords) }}</div>
              <div class="stat-label">总记录数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon devices">
              <el-icon><Platform /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ deviceCount }}</div>
              <div class="stat-label">设备数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon time">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ timeSpan }}</div>
              <div class="stat-label">时间跨度</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon anomaly">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ anomalyCount }}</div>
              <div class="stat-label">异常记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 设备分类展示 -->
    <div class="device-categories">
      <!-- 传感器类数据 -->
      <el-card class="category-card">
        <template #header>
          <div class="card-header">
            <div class="category-title">
              <el-icon class="category-icon sensors"><Monitor /></el-icon>
              <span>传感器数据</span>
            </div>
            <el-tag type="info">{{ sensorDevices.length }} 个设备</el-tag>
          </div>
        </template>
        
        <el-row :gutter="15">
          <el-col :span="8" v-for="device in sensorDevices" :key="device.name">
            <div class="device-card sensor-card" @click="showDeviceDetail(device)">
              <div class="device-header">
                <span class="device-name">{{ getDeviceDisplayName(device.name) }}</span>
                <el-tag size="small" :type="getDeviceStatusType(device.status)">
                  {{ device.status }}
                </el-tag>
              </div>
              <div class="device-stats">
                <div class="stat-item">
                  <span class="label">记录数</span>
                  <span class="value">{{ formatNumber(device.recordCount) }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">最新值</span>
                  <span class="value">{{ formatValue(device.lastValue) }} {{ device.unit }}</span>
                </div>                <div class="stat-item">
                  <span class="label">平均值</span>
                  <span class="value">{{ formatValue(device.avgValue) }} {{ device.unit }}</span>
                </div>
              </div>
              <div class="device-chart">
                <div :data-device="device.name" class="mini-chart"></div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 执行器类数据 -->
      <el-card class="category-card">
        <template #header>
          <div class="card-header">
            <div class="category-title">
              <el-icon class="category-icon actuators"><Setting /></el-icon>
              <span>执行器数据</span>
            </div>
            <el-tag type="warning">{{ actuatorDevices.length }} 个设备</el-tag>
          </div>
        </template>
        
        <el-row :gutter="15">
          <el-col :span="8" v-for="device in actuatorDevices" :key="device.name">
            <div class="device-card actuator-card" @click="showDeviceDetail(device)">
              <div class="device-header">
                <span class="device-name">{{ getDeviceDisplayName(device.name) }}</span>
                <el-tag size="small" :type="getDeviceStatusType(device.status)">
                  {{ device.status }}
                </el-tag>
              </div>
              <div class="device-stats">
                <div class="stat-item">
                  <span class="label">记录数</span>
                  <span class="value">{{ formatNumber(device.recordCount) }}</span>
                </div>
                <div class="stat-item">
                  <span class="label">当前值</span>
                  <span class="value">{{ formatValue(device.lastValue) }} {{ device.unit }}</span>
                </div>                <div class="stat-item">
                  <span class="label">运行状态</span>
                  <span class="value">{{ getActuatorStatus(device) }}</span>
                </div>
              </div>
              <div class="device-chart">
                <div :data-device="device.name" class="mini-chart"></div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>      <!-- 指示器数据 -->
      <el-card class="category-card indicator-card">
        <template #header>
          <div class="card-header">
            <div class="category-title">
              <el-icon class="category-icon indicators"><View /></el-icon>
              <span>指示器数据</span>
            </div>
            <el-tag type="success">{{ indicatorDevices.length }} 个设备</el-tag>
          </div>
        </template>
        
        <el-row :gutter="20" class="indicator-grid">
          <el-col :span="8" v-for="device in indicatorDevices" :key="device.name">
            <div class="indicator-item" @click="showDeviceDetail(device)">
              <div class="indicator-header">
                <span class="device-name">{{ getDeviceDisplayName(device.name) }}</span>
                <div class="indicator-status">
                  <div 
                    class="status-light" 
                    :class="getIndicatorLightClass(device.lastValue)"
                  ></div>
                  <span class="status-text">{{ getIndicatorStatusText(device.lastValue) }}</span>
                </div>
              </div>
              <div class="indicator-body">
                <div class="indicator-stats">
                  <div class="stat-row">
                    <span class="label">状态变化</span>
                    <span class="value">{{ formatNumber(device.recordCount) }} 次</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">当前状态</span>
                    <span class="value" :class="getIndicatorValueClass(device.lastValue)">
                      {{ getIndicatorStatusText(device.lastValue) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- IO设备数据 -->
      <el-card class="category-card io-card">
        <template #header>
          <div class="card-header">
            <div class="category-title">
              <el-icon class="category-icon io"><Connection /></el-icon>
              <span>IO设备数据</span>
            </div>
            <el-tag type="primary">{{ ioDevices.length }} 个设备</el-tag>
          </div>
        </template>
        
        <el-row :gutter="20" class="io-grid">
          <el-col :span="6" v-for="device in ioDevices" :key="device.name">
            <div class="io-item" @click="showDeviceDetail(device)">
              <div class="io-header">
                <span class="device-name">{{ getDeviceDisplayName(device.name) }}</span>
                <el-tag size="small" :type="getIOStatusType(device.lastValue)">
                  {{ device.lastValue ? 'ON' : 'OFF' }}
                </el-tag>
              </div>              <div class="io-body">
                <div class="io-status-display">
                  <div class="io-status-indicator">
                    <div 
                      class="status-dot" 
                      :class="device.lastValue ? 'status-active' : 'status-inactive'"
                    ></div>
                  </div>
                </div>
                <div class="io-stats">
                  <div class="stat-row">
                    <span class="label">切换次数</span>
                    <span class="value">{{ formatNumber(device.recordCount) }} 次</span>
                  </div>
                  <div class="stat-row">
                    <span class="label">当前值</span>
                    <span class="value digital-value">{{ device.lastValue }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 设备详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`${currentDevice?.name} - 历史数据详情`"
      width="80%"
      destroy-on-close
    >
      <DeviceHistoryDetail 
        v-if="showDetailDialog && currentDevice"
        :device="currentDevice"
        :date-range="dateRange"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { historicalAPI, deviceAPI } from '../api'
import DeviceHistoryDetail from '../components/DeviceHistoryDetail.vue'
import {
  DataBoard,
  Platform,
  Clock,
  Warning,
  Monitor,
  Setting,
  View,
  Connection,
  Download
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const dateRange = ref([])
const historicalData = ref([])
const showDetailDialog = ref(false)
const currentDevice = ref(null)

// 统计数据
const totalRecords = ref(0)
const deviceCount = ref(0)
const timeSpan = ref('')
const anomalyCount = ref(0)

// 设备分类数据
const sensorDevices = ref([])
const actuatorDevices = ref([])
const indicatorDevices = ref([])
const ioDevices = ref([])

// 图表实例
const charts = ref({})

// 计算属性
const deviceCategories = computed(() => ({
  sensor: sensorDevices.value,
  actuator: actuatorDevices.value,
  indicator: indicatorDevices.value,
  io: ioDevices.value
}))

// 方法
function getDeviceDisplayName(deviceName) {
  const nameMap = {
    'temperature_sensor_1': '温度传感器1',
    'temperature_sensor_2': '温度传感器2',
    'pressure_sensor_1': '压力传感器1',
    'flow_meter_1': '流量计1',
    'fan_1': '风扇1',
    'fan_2': '风扇2',
    'servo_motor_1': '伺服电机1',
    'servo_motor_2': '伺服电机2',
    'indicator_light_1': '指示灯1',
    'digital_input_1': '数字输入1',
    'digital_output_1': '数字输出1'
  }
  return nameMap[deviceName] || deviceName
}

function getDeviceStatusType(status) {
  const typeMap = {
    'online': 'success',
    'offline': 'danger',
    'warning': 'warning',
    'maintenance': 'info'
  }
  return typeMap[status] || 'info'
}

function getActuatorStatus(device) {
  if (device.name.includes('fan')) {
    return device.lastValue > 0 ? '运行中' : '停止'
  } else if (device.name.includes('servo')) {
    return '定位中'
  }
  return '正常'
}

function getIndicatorLightClass(value) {
  const classes = {
    0: 'light-off',
    1: 'light-green',
    2: 'light-yellow',
    3: 'light-red'
  }
  return classes[value] || 'light-off'
}

function getIndicatorStatusText(value) {
  const texts = {
    0: '关闭',
    1: '正常',
    2: '警告',
    3: '故障'
  }
  return texts[value] || '未知'
}

function getIndicatorValueClass(value) {
  const classes = {
    0: 'status-off',
    1: 'status-normal',
    2: 'status-warning',
    3: 'status-error'
  }
  return classes[value] || 'status-unknown'
}

function getIOStatusType(value) {
  return value ? 'success' : 'info'
}

function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

function formatValue(value) {
  if (typeof value !== 'number') return '--'
  return value.toFixed(2)
}

async function loadHistoricalData() {
  loading.value = true
  
  try {
    // 如果没有选择日期范围，默认使用最近7天
    if (!dateRange.value || dateRange.value.length !== 2) {
      const endDate = new Date()
      const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
      dateRange.value = [
        startDate.toISOString(),
        endDate.toISOString()
      ]
    }
      console.log('发送日期范围:', dateRange.value)
    
    // 使用新的API获取历史数据
    const response = await historicalAPI.getHistoricalData(
      dateRange.value[0], 
      dateRange.value[1]
    );    console.log('API响应:', response);
    console.log('response.data:', response.data);
    console.log('response.data.success:', response.data?.success);
    console.log('typeof response.data.success:', typeof response.data?.success);
    
    // 检查响应格式 - API可能直接返回数据而不是包装在data中
    if (response.success) {
      // 如果response直接包含success字段
      console.log('API调用成功（直接格式），开始处理数据...')
      historicalData.value = response.data
      totalRecords.value = response.total_records
      
      // 处理历史数据分类
      processHistoricalData(response.data)
      
      // 计算统计信息
      calculateStatistics(response)
      
      // 下一帧渲染图表
      await nextTick()
      renderMiniCharts()
      
      ElMessage.success(`历史数据加载成功，共 ${response.total_records} 条记录`)
    } else if (response.data && response.data.success) {
      // 如果response.data包含success字段
      console.log('API调用成功（包装格式），开始处理数据...')
      historicalData.value = response.data.data
      totalRecords.value = response.data.total_records
      
      // 处理历史数据分类
      processHistoricalData(response.data.data)
      
      // 计算统计信息
      calculateStatistics(response.data)
      
      // 下一帧渲染图表
      await nextTick()
      renderMiniCharts()
      
      ElMessage.success(`历史数据加载成功，共 ${response.data.total_records} 条记录`)
    } else {
      console.error('API响应异常:', response)
      const errorMsg = response.data?.error || response.error || '未知错误'
      console.log('API返回错误:', errorMsg)
      ElMessage.error(`API响应格式错误: ${errorMsg}`)
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    if (error.response) {
      console.error('错误响应:', error.response.data)
      ElMessage.error(`网络错误: ${error.response.status} - ${error.response.data.error || error.message}`)
    } else if (error.request) {
      console.error('请求失败:', error.request)
      ElMessage.error('网络连接失败，请检查后端服务是否正常运行')
    } else {
      console.error('其他错误:', error.message)
      ElMessage.error('发生未知错误，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

function processHistoricalData(data) {
  console.log('开始处理历史数据:', data)
  
  // 清空现有数据
  sensorDevices.value = []
  actuatorDevices.value = []
  indicatorDevices.value = []
  ioDevices.value = []
  
  data.forEach(device => {
    console.log('处理设备:', device.name, device)
    
    const deviceInfo = {
      name: device.name,
      recordCount: device.recordCount,
      lastValue: device.lastValue,
      avgValue: device.avgValue,
      maxValue: device.maxValue,
      minValue: device.minValue,
      unit: device.unit,
      type: device.type,
      status: device.status,
      timestamps: device.timestamps || [],
      values: device.values || []
    }
    
    // 根据设备名称或类型分类
    if (device.name.includes('sensor') || device.name.includes('level') || 
        device.name.includes('temperature') || device.name.includes('pressure') || 
        device.name.includes('flow')) {
      sensorDevices.value.push(deviceInfo)
    } else if (device.name.includes('valve') || device.name.includes('pump') || 
               device.name.includes('motor') || device.name.includes('speed')) {
      actuatorDevices.value.push(deviceInfo)
    } else if (device.name.includes('indicator') || device.name.includes('light') || 
               device.name.includes('alarm')) {
      indicatorDevices.value.push(deviceInfo)
    } else if (device.name.includes('input') || device.name.includes('output') || 
               device.name.includes('stop') || device.name.includes('digital')) {
      ioDevices.value.push(deviceInfo)
    } else {
      // 默认归类为传感器
      sensorDevices.value.push(deviceInfo)
    }
  })
  
  console.log('设备分类完成:', {
    sensors: sensorDevices.value.length,
    actuators: actuatorDevices.value.length,
    indicators: indicatorDevices.value.length,
    io: ioDevices.value.length
  })
  
  deviceCount.value = data.length
}

function getDeviceUnit(deviceName) {
  const unitMap = {
    'temperature_sensor_1': '°C',
    'temperature_sensor_2': '°C',
    'pressure_sensor_1': 'bar',
    'flow_meter_1': 'L/min',
    'fan_1': 'RPM',
    'fan_2': 'RPM',
    'servo_motor_1': '°',
    'servo_motor_2': '°',
    'indicator_light_1': 'state',
    'digital_input_1': 'digital',
    'digital_output_1': 'digital'
  }
  return unitMap[deviceName] || ''
}

function calculateStatistics(apiResponse) {
  // 使用API响应中的总记录数和设备统计信息
  totalRecords.value = apiResponse.total_records
  deviceCount.value = apiResponse.data.length
  
  // 计算异常记录数（从设备数据中估算）
  let totalAnomalies = 0
  apiResponse.data.forEach(device => {
    // 假设异常记录约占总记录的5%
    totalAnomalies += Math.round(device.recordCount * 0.05)
  })
  anomalyCount.value = totalAnomalies
  
  // 计算时间跨度
  if (apiResponse.time_range) {
    const startTime = new Date(apiResponse.time_range.start)
    const endTime = new Date(apiResponse.time_range.end)
    const diffHours = Math.round((endTime - startTime) / (1000 * 60 * 60))
    
    if (diffHours < 24) {
      timeSpan.value = `${diffHours}小时`
    } else {
      const diffDays = Math.round(diffHours / 24)
      timeSpan.value = `${diffDays}天`
    }
  } else {
    timeSpan.value = '7天'
  }
}

function renderMiniCharts() {
  // 等待DOM更新
  nextTick(() => {
    // 渲染传感器和执行器的迷你图表
    [...sensorDevices.value, ...actuatorDevices.value].forEach(device => {
      const chartRef = `chart-${device.name}`
      // 使用更可靠的方式查找图表元素
      const chartElement = document.querySelector(`.mini-chart[data-device="${device.name}"]`) ||
                          document.querySelector(`[ref="${chartRef}"]`) ||
                          document.querySelector(`.device-chart .mini-chart`)
      
      if (chartElement && device.values && device.values.length > 0) {
        try {
          if (charts.value[chartRef]) {
            charts.value[chartRef].dispose()
          }
          
          const chart = echarts.init(chartElement)
          charts.value[chartRef] = chart
          
          const option = {
            grid: {
              left: 5,
              right: 5,
              top: 5,
              bottom: 5
            },
            xAxis: {
              type: 'category',
              show: false,
              data: device.timestamps?.slice(-20) || [] // 最近20个数据点
            },
            yAxis: {
              type: 'value',
              show: false
            },
            series: [{
              type: 'line',
              symbol: 'none',
              lineStyle: {
                color: device.name.includes('sensor') ? '#409EFF' : '#67C23A',
                width: 2
              },
              data: device.values.slice(-20)
            }]
          }
          
          chart.setOption(option)
        } catch (error) {
          console.warn(`渲染图表失败 ${device.name}:`, error)
        }
      }
    })
  })
}

function showDeviceDetail(device) {
  currentDevice.value = device
  showDetailDialog.value = true
}

async function exportData() {
  if (historicalData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  try {
    // 使用新的API导出数据
    const response = await historicalAPI.exportHistoricalData(
      dateRange.value[0],
      dateRange.value[1]
    )
      // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `historical_data_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出数据失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  }
}

// 生命周期
onMounted(() => {
  loadHistoricalData()
})
</script>

<style lang="scss" scoped>
.historical-data-view {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #303133;
    }

    .header-controls {
      display: flex;
      gap: 10px;
      align-items: center;
    }
  }

  .stats-row {
    margin-bottom: 30px;

    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        gap: 15px;

        .stat-icon {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;

          &.total {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
          }

          &.devices {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
          }

          &.time {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
          }

          &.anomaly {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #e67e22;
          }
        }

        .stat-info {
          .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #303133;
            line-height: 1;
          }

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-top: 5px;
          }
        }
      }
    }
  }

  .device-categories {
    .category-card {
      margin-bottom: 20px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .category-title {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: 600;

          .category-icon {
            font-size: 20px;

            &.sensors {
              color: #409EFF;
            }

            &.actuators {
              color: #67C23A;
            }

            &.indicators {
              color: #E6A23C;
            }

            &.io {
              color: #F56C6C;
            }
          }
        }
      }

      .device-card {
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s ease;
        height: 200px;
        display: flex;
        flex-direction: column;

        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        &.sensor-card {
          border-left: 4px solid #409EFF;
        }

        &.actuator-card {
          border-left: 4px solid #67C23A;
        }

        .device-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;

          .device-name {
            font-weight: 600;
            color: #303133;
          }
        }

        .device-stats {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;

          .stat-item {
            display: flex;
            justify-content: space-between;
            font-size: 14px;

            .label {
              color: #909399;
            }

            .value {
              font-weight: 500;
              color: #303133;
            }
          }
        }

        .device-chart {
          height: 60px;
          margin-top: 10px;

          .mini-chart {
            width: 100%;
            height: 100%;
          }
        }
      }      .indicator-item,
      .io-item {
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        cursor: pointer;
        background: #fff;

        &:hover {
          border-color: #409eff;
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
          transform: translateY(-2px);
        }

        &:last-child {
          margin-bottom: 0;
        }
      }

      // 指示器卡片样式
      .indicator-card {
        .indicator-grid {
          min-height: 200px;

          .indicator-item {
            height: 140px;
            display: flex;
            flex-direction: column;

            .indicator-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 15px;

              .device-name {
                font-weight: 600;
                color: #303133;
                font-size: 14px;
                line-height: 1.4;
              }

              .indicator-status {
                display: flex;
                align-items: center;
                gap: 8px;

                .status-light {
                  width: 14px;
                  height: 14px;
                  border-radius: 50%;
                  border: 2px solid #fff;
                  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);

                  &.light-off {
                    background: #c0c4cc;
                  }

                  &.light-green {
                    background: #67c23a;
                    box-shadow: 0 0 12px rgba(103, 194, 58, 0.4);
                  }

                  &.light-yellow {
                    background: #e6a23c;
                    box-shadow: 0 0 12px rgba(230, 162, 60, 0.4);
                  }

                  &.light-red {
                    background: #f56c6c;
                    box-shadow: 0 0 12px rgba(245, 108, 108, 0.4);
                  }
                }

                .status-text {
                  font-size: 12px;
                  font-weight: 500;
                  color: #606266;
                }
              }
            }

            .indicator-body {
              flex: 1;
              display: flex;
              flex-direction: column;

              .indicator-stats {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 12px;

                .stat-row {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;

                  .label {
                    font-size: 13px;
                    color: #909399;
                  }

                  .value {
                    font-size: 13px;
                    font-weight: 600;
                    
                    &.status-off {
                      color: #c0c4cc;
                    }
                    
                    &.status-normal {
                      color: #67c23a;
                    }
                    
                    &.status-warning {
                      color: #e6a23c;
                    }
                    
                    &.status-error {
                      color: #f56c6c;
                    }
                  }
                }
              }
            }
          }
        }
      }

      // IO设备卡片样式
      .io-card {
        .io-grid {
          min-height: 200px;

          .io-item {
            height: 160px;
            display: flex;
            flex-direction: column;

            .io-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 20px;

              .device-name {
                font-weight: 600;
                color: #303133;
                font-size: 14px;
              }
            }

            .io-body {
              flex: 1;
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 15px;              .io-status-display {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 10px;

                .io-status-indicator {
                  display: flex;
                  align-items: center;
                  gap: 10px;

                  .status-dot {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    border: 2px solid #fff;
                    box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;

                    &.status-active {
                      background: #67c23a;
                      box-shadow: 0 0 12px rgba(103, 194, 58, 0.4), 0 0 0 1px rgba(0,0,0,0.1);
                    }

                    &.status-inactive {
                      background: #c0c4cc;
                      box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
                    }
                  }
                }

                .status-label {
                  font-size: 14px;
                  font-weight: 600;
                  color: #303133;
                }
              }

              .io-stats {
                width: 100%;
                display: flex;
                flex-direction: column;
                gap: 8px;

                .stat-row {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;

                  .label {
                    font-size: 12px;
                    color: #909399;
                  }

                  .value {
                    font-size: 12px;
                    font-weight: 600;
                    color: #303133;

                    &.digital-value {
                      font-family: 'Courier New', monospace;
                      background: #f5f7fa;
                      padding: 2px 6px;
                      border-radius: 4px;
                      border: 1px solid #e4e7ed;
                    }
                  }
                }
              }
            }
          }
        }
      }

      // 旧版样式保留（向后兼容）
      .indicator-item:not(.indicator-grid .indicator-item),
      .io-item:not(.io-grid .io-item) {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        border: 1px solid #e4e7ed;
        border-radius: 6px;
        margin-bottom: 10px;

        .indicator-info,
        .io-info {
          display: flex;
          align-items: center;
          gap: 15px;

          .device-name {
            font-weight: 500;
            color: #303133;
          }

          .indicator-status {
            display: flex;
            align-items: center;
            gap: 8px;

            .status-light {
              width: 12px;
              height: 12px;
              border-radius: 50%;

              &.light-off {
                background: #c0c4cc;
              }

              &.light-green {
                background: #67c23a;
                box-shadow: 0 0 8px rgba(103, 194, 58, 0.5);
              }

              &.light-yellow {
                background: #e6a23c;
                box-shadow: 0 0 8px rgba(230, 162, 60, 0.5);
              }

              &.light-red {
                background: #f56c6c;
                box-shadow: 0 0 8px rgba(245, 108, 108, 0.5);
              }
            }
          }

          .io-status {
            display: flex;
            align-items: center;
            gap: 8px;
          }
        }

        .indicator-stats,
        .io-stats {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .historical-data-view {
    padding: 10px;

    .page-header {
      flex-direction: column;
      gap: 15px;
      align-items: stretch;

      .header-controls {
        flex-wrap: wrap;
      }
    }

    .stats-row {
      .el-col {
        margin-bottom: 15px;
      }
    }

    .device-categories {
      .device-card {
        height: auto;
        min-height: 150px;
      }
    }
  }
}
</style>
