<template>
  <div class="historical-data-view">
    <!-- 页面标题和控制 -->
    <div class="page-header">
      <div>
        <h2>历史数据</h2>
        <p>查询、对比并导出设备运行记录</p>
      </div>
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
        <el-select v-model="selectedHistoryDevice" placeholder="全部设备" clearable style="width: 150px">
          <el-option v-for="name in historyDeviceNames" :key="name" :label="getDeviceDisplayName(name)" :value="name" />
        </el-select>
        <el-button type="primary" @click="loadHistoricalData" :loading="loading">
          刷新数据
        </el-button>
        <el-button @click="exportData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </div>
    </div>

    <div class="design-stats">
      <div class="design-stat-card"><span class="design-stat-icon"><DataBoard /></span><div><span class="design-stat-label">总记录数</span><strong>{{ formatNumber(totalRecords) }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Platform /></span><div><span class="design-stat-label">设备数量</span><strong>{{ deviceCount }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Clock /></span><div><span class="design-stat-label">时间跨度</span><strong>{{ timeSpan }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Warning /></span><div><span class="design-stat-label">异常记录</span><strong>{{ anomalyCount }}</strong></div></div>
    </div>

    <!-- 设备分类展示 -->
    <div v-if="false" class="device-categories">
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

    <LieflatHistoryOverview :rows="historyRows" />

    <el-card class="history-records-card">
      <template #header>
        <div class="card-header">
          <div class="history-tabs" role="tablist" aria-label="历史数据视图">
            <button
              v-for="tab in historyTabs"
              :key="tab.value"
              type="button"
              role="tab"
              class="history-tab"
              :class="{ active: activeHistoryTab === tab.value }"
              :aria-selected="activeHistoryTab === tab.value"
              @click="activeHistoryTab = tab.value"
            >{{ tab.label }}</button>
          </div>
          <small>{{ activeHistoryDescription }}</small>
        </div>
      </template>
      <div class="history-table-wrap">
        <el-table v-if="activeHistoryTab === 'raw'" :data="historyRows" v-loading="loading" height="100%" empty-text="当前条件下暂无原始记录">
          <el-table-column prop="timestamp" label="时间" min-width="170">
            <template #default="{ row }">{{ formatHistoryTime(row.timestamp) }}</template>
          </el-table-column>
          <el-table-column prop="name" label="设备" min-width="150">
            <template #default="{ row }">{{ getDeviceDisplayName(row.name) }}</template>
          </el-table-column>
          <el-table-column prop="type" label="类型" min-width="100" />
          <el-table-column prop="value" label="数值" min-width="100">
            <template #default="{ row }"><strong>{{ formatValue(row.value) }}</strong></template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" min-width="80" />
          <el-table-column label="质量" min-width="90"><template #default><el-tag size="small">良好</el-tag></template></el-table-column>
          <el-table-column label="状态" min-width="90"><template #default><span class="status-indicator online"></span> 正常</template></el-table-column>
          <el-table-column label="操作" width="80"><template #default="{ row }"><el-button text @click="showDeviceDetail(row.device)">详情</el-button></template></el-table-column>
        </el-table>

        <el-table v-else-if="activeHistoryTab === 'summary'" :data="historySummaryRows" v-loading="loading" height="100%" empty-text="当前条件下暂无统计数据">
          <el-table-column prop="name" label="设备" min-width="160"><template #default="{ row }">{{ getDeviceDisplayName(row.name) }}</template></el-table-column>
          <el-table-column prop="type" label="类型" min-width="100" />
          <el-table-column prop="count" label="记录数" min-width="90" />
          <el-table-column prop="average" label="平均值" min-width="105"><template #default="{ row }"><strong>{{ formatValue(row.average) }}</strong></template></el-table-column>
          <el-table-column prop="minimum" label="最小值" min-width="100"><template #default="{ row }">{{ formatValue(row.minimum) }}</template></el-table-column>
          <el-table-column prop="maximum" label="最大值" min-width="100"><template #default="{ row }">{{ formatValue(row.maximum) }}</template></el-table-column>
          <el-table-column prop="latest" label="最新值" min-width="100"><template #default="{ row }">{{ formatValue(row.latest) }}</template></el-table-column>
          <el-table-column prop="unit" label="单位" min-width="80" />
          <el-table-column label="操作" width="80"><template #default="{ row }"><el-button text @click="showDeviceDetail(row.device)">详情</el-button></template></el-table-column>
        </el-table>

        <el-table v-else :data="historyAnomalyRows" v-loading="loading" height="100%" empty-text="当前条件下未发现异常记录">
          <el-table-column prop="timestamp" label="时间" min-width="170"><template #default="{ row }">{{ formatHistoryTime(row.timestamp) }}</template></el-table-column>
          <el-table-column prop="name" label="设备" min-width="150"><template #default="{ row }">{{ getDeviceDisplayName(row.name) }}</template></el-table-column>
          <el-table-column prop="value" label="异常值" min-width="100"><template #default="{ row }"><strong>{{ formatValue(row.value) }} {{ row.unit }}</strong></template></el-table-column>
          <el-table-column prop="average" label="设备均值" min-width="110"><template #default="{ row }">{{ formatValue(row.average) }} {{ row.unit }}</template></el-table-column>
          <el-table-column prop="deviation" label="偏离幅度" min-width="110"><template #default="{ row }">{{ formatValue(row.deviation) }} {{ row.unit }}</template></el-table-column>
          <el-table-column prop="score" label="异常指数" min-width="100"><template #default="{ row }"><el-tag size="small">{{ row.score.toFixed(1) }}</el-tag></template></el-table-column>
          <el-table-column label="状态" min-width="100"><template #default><strong>需要关注</strong></template></el-table-column>
          <el-table-column label="操作" width="80"><template #default="{ row }"><el-button text @click="showDeviceDetail(row.device)">详情</el-button></template></el-table-column>
        </el-table>
      </div>
    </el-card>

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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { theme, cssVar } from '../theme'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { historicalAPI, deviceAPI } from '../api'
import DeviceHistoryDetail from '../components/DeviceHistoryDetail.vue'
import LieflatHistoryOverview from '../components/LieflatHistoryOverview.vue'
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
const selectedHistoryDevice = ref('')
const historicalData = ref([])
const showDetailDialog = ref(false)
const currentDevice = ref(null)
const activeHistoryTab = ref('raw')
const historyTabs = [
  { label: '原始记录', value: 'raw' },
  { label: '统计汇总', value: 'summary' },
  { label: '异常记录', value: 'anomaly' }
]

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

const historyDeviceNames = computed(() => historicalData.value.map(device => device.name).filter(Boolean))
const filteredHistoricalDevices = computed(() => historicalData.value
  .filter(device => !selectedHistoryDevice.value || device.name === selectedHistoryDevice.value)
)
const allHistoryRows = computed(() => filteredHistoricalDevices.value
  .flatMap(device => (device.timestamps || []).map((timestamp, index) => ({
    timestamp,
    name: device.name,
    type: device.type || '设备',
    value: device.values?.[index],
    unit: device.unit || '',
    device
  })))
  .filter(row => row.timestamp && typeof row.value === 'number')
  .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)))
const historyRows = computed(() => allHistoryRows.value.slice(0, 100))
const historySummaryRows = computed(() => filteredHistoricalDevices.value.map(device => {
  const values = (device.values || []).map(Number).filter(Number.isFinite)
  const latestIndex = Math.max(0, values.length - 1)
  return {
    name: device.name,
    type: device.type || '设备',
    count: values.length,
    average: values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0,
    minimum: values.length ? Math.min(...values) : 0,
    maximum: values.length ? Math.max(...values) : 0,
    latest: values[latestIndex] ?? 0,
    unit: device.unit || '',
    device
  }
}).filter(row => row.count > 0))
const historyAnomalyRows = computed(() => {
  const candidates = historySummaryRows.value.flatMap(summary => {
    const rows = allHistoryRows.value.filter(row => row.name === summary.name)
    const variance = rows.length ? rows.reduce((sum, row) => sum + (row.value - summary.average) ** 2, 0) / rows.length : 0
    const deviationScale = Math.sqrt(variance) || 1
    return rows.map(row => ({
      ...row,
      average: summary.average,
      deviation: Math.abs(row.value - summary.average),
      score: Math.abs(row.value - summary.average) / deviationScale
    }))
  }).sort((a, b) => b.score - a.score)
  return candidates.slice(0, Math.max(1, Math.round(candidates.length * .05)))
})
const activeHistoryDescription = computed(() => ({
  raw: `${allHistoryRows.value.length} 条当前查询记录 · 数据按时间倒序`,
  summary: `${historySummaryRows.value.length} 台设备 · 汇总当前时间范围`,
  anomaly: `${historyAnomalyRows.value.length} 条异常记录 · 按异常指数排序`
}[activeHistoryTab.value]))

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

function formatHistoryTime(timestamp) {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString('zh-CN', { hour12: false })
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

watch(theme, () => renderMiniCharts())

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
                color: cssVar(device.name.includes('sensor') ? '--data' : '--data-2'),
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
  .page-header {
    display: flex;
    flex-direction: column;
    align-items: stretch;

    > div:first-child { display: flex; align-items: baseline; gap: 20px; }
    > div:first-child p { margin: 0; }
    .header-controls { width: 100%; margin-top: 12px; }
    .header-controls .el-button:first-of-type { margin-left: auto; }
  }

  .history-tabs { display: flex; align-items: center; gap: 24px; }
  .history-tab { position: relative; min-height: 36px; padding: 0 2px; color: var(--muted); background: transparent; border: 0; cursor: pointer; font-size: 14px; font-weight: 700; }
  .history-tab::after { position: absolute; right: 0; bottom: -12px; left: 0; height: 2px; background: transparent; content: ''; }
  .history-tab:hover, .history-tab:focus-visible, .history-tab.active { color: var(--data); }
  .history-tab.active::after { background: var(--data); }
  .history-tab:focus-visible { outline: 2px solid var(--data-3); outline-offset: 3px; }
  .history-records-card :deep(.el-card__header) { padding-block: 12px; }
  .history-records-card :deep(.el-card__body) { padding: 0 16px 12px; }
  .history-table-wrap { height: clamp(300px, calc(100vh - 660px), 440px); }
  .history-records-card :deep(.el-table th.el-table__cell) { height: 46px; padding: 4px 0; }
  .history-records-card :deep(.el-table td.el-table__cell) { height: 48px; padding: 4px 0; }
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: var(--ink);
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
            background: var(--data);
            color: var(--on-accent);
          }

          &.devices {
            background: var(--accent-soft);
            color: var(--data-2);
          }

          &.time {
            background: var(--data-2);
            color: var(--on-accent);
          }

          &.anomaly {
            background: var(--data-3);
            color: var(--ink);
          }
        }

        .stat-info {
          .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: var(--ink);
            line-height: 1;
          }

          .stat-label {
            font-size: 14px;
            color: var(--data-2);
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
              color: var(--data);
            }

            &.actuators {
              color: var(--data-2);
            }

            &.indicators {
              color: var(--data-2);
            }

            &.io {
              color: var(--ink);
            }
          }
        }
      }

      .device-card {
        border: 1px solid var(--data-3);
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
          border-left: 4px solid var(--data);
        }

        &.actuator-card {
          border-left: 4px solid var(--data-2);
        }

        .device-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;

          .device-name {
            font-weight: 600;
            color: var(--ink);
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
              color: var(--data-2);
            }

            .value {
              font-weight: 500;
              color: var(--ink);
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
        border: 1px solid var(--data-3);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        cursor: pointer;
        background: var(--paper);

        &:hover {
          border-color: var(--data);
          box-shadow: 0 4px 12px var(--accent-soft);
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
                color: var(--ink);
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
                  border: 2px solid var(--paper);
                  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);

                  &.light-off {
                    background: var(--data-3);
                  }

                  &.light-green {
                    background: var(--data);
                    box-shadow: 0 0 12px var(--accent-soft);
                  }

                  &.light-yellow {
                    background: var(--warn);
                    box-shadow: 0 0 12px var(--warn-soft);
                  }

                  &.light-red {
                    background: var(--alarm);
                    box-shadow: 0 0 12px var(--alarm-soft);
                  }
                }

                .status-text {
                  font-size: 12px;
                  font-weight: 500;
                  color: var(--data);
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
                    color: var(--data-2);
                  }

                  .value {
                    font-size: 13px;
                    font-weight: 600;
                    
                    &.status-off {
                      color: var(--data-3);
                    }
                    
                    &.status-normal {
                      color: var(--data-2);
                    }
                    
                    &.status-warning {
                      color: var(--data-2);
                    }
                    
                    &.status-error {
                      color: var(--ink);
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
                color: var(--ink);
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
                    border: 2px solid var(--paper);
                    box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;

                    &.status-active {
                      background: var(--data-2);
                      box-shadow: 0 0 12px var(--accent-soft), 0 0 0 1px rgba(0,0,0,0.1);
                    }

                    &.status-inactive {
                      background: var(--data-3);
                      box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
                    }
                  }
                }

                .status-label {
                  font-size: 14px;
                  font-weight: 600;
                  color: var(--ink);
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
                    color: var(--data-2);
                  }

                  .value {
                    font-size: 12px;
                    font-weight: 600;
                    color: var(--ink);

                    &.digital-value {
                      font-family: 'Courier New', monospace;
                      background: var(--paper);
                      padding: 2px 6px;
                      border-radius: 4px;
                      border: 1px solid var(--data-3);
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
        border: 1px solid var(--data-3);
        border-radius: 6px;
        margin-bottom: 10px;

        .indicator-info,
        .io-info {
          display: flex;
          align-items: center;
          gap: 15px;

          .device-name {
            font-weight: 500;
            color: var(--ink);
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
                background: var(--data-3);
              }

              &.light-green {
                background: var(--data);
                box-shadow: 0 0 8px var(--accent-soft);
              }

              &.light-yellow {
                background: var(--warn);
                box-shadow: 0 0 8px var(--warn-soft);
              }

              &.light-red {
                background: var(--alarm);
                box-shadow: 0 0 8px var(--alarm-soft);
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
          color: var(--data-2);
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
