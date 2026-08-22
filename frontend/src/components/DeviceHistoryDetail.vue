<template>
  <div class="device-history-detail">
    <!-- 设备基本信息 -->
    <div class="device-info-header">
      <el-card class="info-card">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="info-item">
              <label>设备名称</label>
              <span>{{ getDeviceDisplayName(device.name) }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <label>设备类型</label>
              <span>{{ getDeviceType(device.name) }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <label>数据单位</label>
              <span>{{ device.unit || 'N/A' }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <label>当前状态</label>
              <el-tag :type="getDeviceStatusType(device.status)">
                {{ device.status }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 数据统计 -->
    <el-row :gutter="15" class="stats-section">
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatNumber(device.recordCount) }}</div>
            <div class="stat-label">总记录数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatValue(device.lastValue) }}</div>
            <div class="stat-label">最新值</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatValue(device.avgValue) }}</div>
            <div class="stat-label">平均值</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatValue(device.maxValue) }}</div>
            <div class="stat-label">最大值</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatValue(device.minValue) }}</div>
            <div class="stat-label">最小值</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-mini-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatValue(device.stdValue) }}</div>
            <div class="stat-label">标准差</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史数据图表 -->
    <el-card class="chart-section">
      <template #header>
        <div class="chart-header">
          <span>历史趋势图</span>
          <div class="chart-controls">
            <el-radio-group v-model="chartType" size="small">
              <el-radio-button label="line">折线图</el-radio-button>
              <el-radio-button label="bar">柱状图</el-radio-button>
              <el-radio-button label="scatter">散点图</el-radio-button>
            </el-radio-group>
            <el-button size="small" @click="downloadChart">
              <el-icon><Download /></el-icon>
              下载图表
            </el-button>
          </div>
        </div>
      </template>
      
      <div ref="chartContainer" class="detail-chart" v-loading="chartLoading"></div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-section">
      <template #header>
        <div class="table-header">
          <span>详细数据记录</span>
          <div class="table-controls">
            <el-input
              v-model="searchText"
              placeholder="搜索数据..."
              size="small"
              style="width: 200px;"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button size="small" @click="exportTableData">
              <el-icon><Download /></el-icon>
              导出表格
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredTableData"
        v-loading="tableLoading"
        height="400"
        stripe
        border
      >
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTimestamp(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="value" label="数值" sortable>
          <template #default="{ row }">
            <span :class="getValueClass(row.value)">
              {{ formatValue(row.value) }} {{ device.unit }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="quality" label="数据质量" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getQualityType(row.quality)">
              {{ row.quality || 'GOOD' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变化幅度" width="100">
          <template #default="{ row, $index }">
            <span v-if="$index > 0" :class="getChangeClass(row.change)">
              {{ formatChange(row.change) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="table-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[50, 100, 200, 500]"
          :total="totalTableRecords"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 异常分析 -->
    <el-card class="anomaly-section" v-if="anomalies.length > 0">
      <template #header>
        <span>异常数据分析</span>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="anomaly in anomalies.slice(0, 10)"
          :key="anomaly.id"
          :timestamp="formatTimestamp(anomaly.timestamp)"
          type="warning"
        >
          <div class="anomaly-item">
            <div class="anomaly-value">
              异常值: {{ formatValue(anomaly.value) }} {{ device.unit }}
            </div>
            <div class="anomaly-description">
              {{ getAnomalyDescription(anomaly) }}
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
      
      <div v-if="anomalies.length > 10" class="more-anomalies">
        <el-button type="text" @click="showAllAnomalies">
          查看全部 {{ anomalies.length }} 个异常记录
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { deviceAPI } from '../api'
import { Download, Search } from '@element-plus/icons-vue'

const props = defineProps({
  device: {
    type: Object,
    required: true
  },
  dateRange: {
    type: Array,
    default: () => []
  }
})

// 响应式数据
const chartType = ref('line')
const chartLoading = ref(false)
const tableLoading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(100)
const totalTableRecords = ref(0)

// 图表和数据
const chartContainer = ref(null)
const chart = ref(null)
const rawTableData = ref([])
const anomalies = ref([])

// 计算属性
const filteredTableData = computed(() => {
  let data = rawTableData.value
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    data = data.filter(item => 
      item.value.toString().includes(search) ||
      item.timestamp.toLowerCase().includes(search)
    )
  }
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  
  return data.slice(start, end)
})

// 监听设备变化，重新加载数据
watch(() => props.device, () => {
  if (props.device) {
    loadDeviceData()
  }
}, { immediate: true })

// 监听图表类型变化
watch(chartType, () => {
  updateChart()
})

// 方法
const loadDeviceData = async () => {
  try {
    chartLoading.value = true
    tableLoading.value = true
    
    // 获取设备历史数据
    const hours = props.dateRange.length === 2 ? 
      Math.ceil((new Date(props.dateRange[1]) - new Date(props.dateRange[0])) / (1000 * 60 * 60)) : 24
    
    const [historyResponse, statsResponse] = await Promise.all([
      deviceAPI.getDeviceHistory(props.device.name, hours, 1000),
      deviceAPI.getDeviceStatistics(props.device.name, hours)
    ])
    
    if (historyResponse.data.success) {
      const data = historyResponse.data.data.map((item, index, array) => {
        const prevValue = index > 0 ? array[index - 1].value : item.value
        return {
          ...item,
          change: item.value - prevValue
        }
      })
      
      rawTableData.value = data
      totalTableRecords.value = data.length
      
      // 检测异常数据
      detectAnomalies(data)
    }
    
    if (statsResponse.data.success) {
      // 更新设备统计信息
      const stats = statsResponse.data.statistics
      props.device.maxValue = stats.maxValue
      props.device.minValue = stats.minValue
      props.device.stdValue = stats.stdValue
    }
    
    // 更新图表
    await nextTick()
    initChart()
    
  } catch (error) {
    console.error('加载设备数据失败:', error)
    ElMessage.error('加载设备数据失败')
  } finally {
    chartLoading.value = false
    tableLoading.value = false
  }
}

const generateHistoricalData = () => {
  const data = []
  const now = new Date()
  const baseValue = props.device.avgValue || 50
  
  // 生成最近24小时的数据，每5分钟一个点
  for (let i = 288; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 5 * 60 * 1000)
    const variation = (Math.random() - 0.5) * 20
    const value = baseValue + variation + Math.sin(i / 48) * 10
    
    const prevValue = data.length > 0 ? data[data.length - 1].value : value
    const change = value - prevValue
    
    data.push({
      timestamp: timestamp.toISOString(),
      value: Math.max(0, value),
      quality: Math.random() > 0.95 ? 'BAD' : 'GOOD',
      change: change
    })
  }
  
  return data
}

const detectAnomalies = (data) => {
  const values = data.map(item => item.value)
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const std = Math.sqrt(values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length)
  
  anomalies.value = data.filter(item => Math.abs(item.value - mean) > 2 * std)
    .map((item, index) => ({
      ...item,
      id: index,
      severity: Math.abs(item.value - mean) > 3 * std ? 'high' : 'medium'
    }))
}

const initChart = () => {
  if (!chartContainer.value) return
  
  chart.value = echarts.init(chartContainer.value)
  updateChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    chart.value?.resize()
  })
}

const updateChart = () => {
  if (!chart.value || !rawTableData.value.length) return
  
  const data = rawTableData.value.slice(-100) // 显示最近100个点
  const xData = data.map(item => new Date(item.timestamp).toLocaleTimeString())
  const yData = data.map(item => item.value)
  
  const option = {
    title: {
      text: `${getDeviceDisplayName(props.device.name)} 历史趋势`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const item = params[0]
        const dataItem = data[item.dataIndex]
        return `
          <div>
            <div>时间: ${formatTimestamp(dataItem.timestamp)}</div>
            <div>数值: ${formatValue(dataItem.value)} ${props.device.unit}</div>
            <div>质量: ${dataItem.quality}</div>
          </div>
        `
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
      data: xData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: props.device.unit,
      axisLabel: {
        formatter: value => formatValue(value)
      }
    },
    series: [{
      name: '数值',
      type: chartType.value,
      data: yData,
      smooth: chartType.value === 'line',
      itemStyle: {
        color: '#334EAC'
      },
      markLine: {
        data: [
          { type: 'average', name: '平均值' }
        ]
      }
    }]
  }
  
  chart.value.setOption(option)
}

// 工具方法
const getDeviceDisplayName = (name) => {
  const nameMap = {
    'tank1_level': '储罐1液位',
    'tank2_level': '储罐2液位', 
    'temperature_sensor': '温度传感器',
    'pressure_sensor': '压力传感器',
    'flow_sensor': '流量传感器',
    'valve_position': '阀门位置',
    'pump_speed': '泵速度',
    'motor_current': '电机电流',
    'alarm_indicator': '报警指示器',
    'status_light': '状态指示灯',
    'emergency_stop': '急停按钮',
    'digital_input': '数字输入',
    'digital_output': '数字输出',
    'analog_input': '模拟输入'
  }
  return nameMap[name] || name
}

const getDeviceType = (name) => {
  if (name.includes('sensor') || name.includes('level')) return '传感器'
  if (name.includes('valve') || name.includes('pump') || name.includes('motor')) return '执行器'
  if (name.includes('indicator') || name.includes('light') || name.includes('alarm')) return '指示器'
  if (name.includes('input') || name.includes('output') || name.includes('stop')) return 'IO设备'
  return '未知'
}

const getDeviceStatusType = (status) => {
  switch (status) {
    case 'online': return 'success'
    case 'offline': return 'danger'
    case 'error': return 'danger'
    case 'warning': return 'warning'
    default: return 'info'
  }
}

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatValue = (value) => {
  if (typeof value !== 'number') return value
  return value.toFixed(2)
}

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

const formatChange = (change) => {
  if (!change) return '0'
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${formatValue(change)}`
}

const getValueClass = (value) => {
  // 根据数值范围设置不同的样式类
  const avg = props.device.avgValue || 50
  if (value > avg * 1.2) return 'value-high'
  if (value < avg * 0.8) return 'value-low'
  return 'value-normal'
}

const getChangeClass = (change) => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-none'
}

const getQualityType = (quality) => {
  switch (quality) {
    case 'GOOD': return 'success'
    case 'BAD': return 'danger'
    case 'UNCERTAIN': return 'warning'
    default: return 'info'
  }
}

const getAnomalyDescription = (anomaly) => {
  const avg = props.device.avgValue || 50
  if (anomaly.value > avg * 1.5) {
    return '数值异常偏高，可能存在设备故障或测量误差'
  } else if (anomaly.value < avg * 0.5) {
    return '数值异常偏低，请检查设备连接或传感器状态'
  }
  return '数值超出正常范围'
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

const downloadChart = () => {
  if (!chart.value) return
  
  const url = chart.value.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#F7F2EB'
  })
  
  const link = document.createElement('a')
  link.href = url
  link.download = `${getDeviceDisplayName(props.device.name)}_chart.png`
  link.click()
  
  ElMessage.success('图表下载成功')
}

const exportTableData = () => {
  // 简单的CSV导出
  const headers = ['时间', '数值', '数据质量', '变化幅度']
  const csvContent = [
    headers.join(','),
    ...rawTableData.value.map((row, index) => [
      formatTimestamp(row.timestamp),
      formatValue(row.value),
      row.quality || 'GOOD',
      index > 0 ? formatChange(row.change) : '-'
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${getDeviceDisplayName(props.device.name)}_data.csv`
  link.click()
  
  ElMessage.success('数据导出成功')
}

const showAllAnomalies = () => {
  ElMessage.info('显示全部异常记录功能待实现')
}

// 生命周期
onMounted(() => {
  if (props.device) {
    loadDeviceData()
  }
})
</script>

<style scoped>
.device-history-detail {
  padding: 0;
}

.device-info-header {
  margin-bottom: 20px;
}

.info-card {
  border: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.info-item {
  text-align: center;
}

.info-item label {
  display: block;
  color: #7096D1;
  font-size: 12px;
  margin-bottom: 5px;
}

.info-item span {
  font-size: 14px;
  font-weight: 500;
  color: #081F5C;
}

.stats-section {
  margin-bottom: 20px;
}

.stat-mini-card {
  border: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: #334EAC;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #7096D1;
}

.chart-section,
.table-section,
.anomaly-section {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-header,
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls,
.table-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.detail-chart {
  height: 400px;
  width: 100%;
}

.table-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.value-high {
  color: #081F5C;
  font-weight: bold;
}

.value-low {
  color: #7096D1;
  font-weight: bold;
}

.value-normal {
  color: #7096D1;
}

.change-up {
  color: #081F5C;
}

.change-down {
  color: #7096D1;
}

.change-none {
  color: #7096D1;
}

.anomaly-item {
  padding: 10px;
  background: #F7F2EB;
  border-radius: 4px;
  border-left: 4px solid #7096D1;
}

.anomaly-value {
  font-weight: bold;
  color: #7096D1;
  margin-bottom: 5px;
}

.anomaly-description {
  font-size: 12px;
  color: #334EAC;
}

.more-anomalies {
  text-align: center;
  margin-top: 15px;
}
</style>
