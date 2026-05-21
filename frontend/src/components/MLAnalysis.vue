<template>
  <div class="ml-analysis">
    <!-- 模型训练区域 -->
    <el-card class="training-section">
      <template #header>
        <div class="section-header">
          <div class="header-title">
            <el-icon class="header-icon"><Avatar /></el-icon>
            <span>机器学习模型管理</span>
          </div>
          <el-tag :type="modelStatus.type" size="small">{{ modelStatus.text }}</el-tag>
        </div>
      </template>
        <div class="training-content">
        <!-- 训练配置区域 -->
        <div class="training-config">
          <el-row :gutter="20" align="middle">
            <el-col :span="8">
              <div class="form-item">
                <label class="form-label">
                  <el-icon><Monitor /></el-icon>
                  选择训练设备
                </label>
                <el-select 
                  v-model="selectedTrainingDevice" 
                  placeholder="选择要训练的设备（可选全部设备）"
                  size="large"
                  style="width: 100%"
                  filterable
                  clearable
                >
                  <el-option
                    label="🏭 全部设备（推荐）"
                    value="all"
                  >
                    <div class="device-option">
                      <span class="device-name">全部设备</span>
                      <span class="device-type">综合训练</span>
                    </div>
                  </el-option>
                  <el-option
                    v-for="device in availableDevices"
                    :key="device.device_name"
                    :label="`${getDeviceChineseName(device.device_name)} (${device.device_type})`"
                    :value="device.device_name"
                  >
                    <div class="device-option">
                      <span class="device-name">{{ getDeviceChineseName(device.device_name) }}</span>
                      <span class="device-type">{{ device.device_type }}</span>
                    </div>
                  </el-option>
                </el-select>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="form-item">
                <label class="form-label">
                  <el-icon><DataBoard /></el-icon>
                  训练数据时间范围
                </label>
                <el-select 
                  v-model="trainingDataHours" 
                  placeholder="选择训练数据时间范围"
                  size="large"
                  style="width: 100%"
                >
                  <el-option 
                    label="最近3天数据" 
                    :value="72"
                  >
                    <div class="time-option">
                      <span>最近3天</span>
                      <small>快速训练</small>
                    </div>
                  </el-option>
                  <el-option 
                    label="最近7天数据（推荐）" 
                    :value="168"
                  >
                    <div class="time-option">
                      <span>最近7天</span>
                      <small>平衡效果与速度</small>
                    </div>
                  </el-option>
                  <el-option 
                    label="最近15天数据" 
                    :value="360"
                  >
                    <div class="time-option">
                      <span>最近15天</span>
                      <small>高精度训练</small>
                    </div>
                  </el-option>
                  <el-option 
                    label="最近30天数据" 
                    :value="720"
                  >
                    <div class="time-option">
                      <span>最近30天</span>
                      <small>最高精度，耗时较长</small>
                    </div>
                  </el-option>
                </el-select>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="form-item">
                <label class="form-label">&nbsp;</label>
                <el-button 
                  type="primary" 
                  size="large"
                  @click="trainModels"
                  :loading="trainingModels"
                  :icon="trainingModels ? Loading : Cpu"
                  class="train-button"
                  style="width: 100%"
                  :disabled="!selectedTrainingDevice"
                >
                  <span v-if="trainingModels">
                    <i class="loading-dots"></i>
                    模型训练中...
                  </span>
                  <span v-else>
                    🚀 开始训练模型
                  </span>
                </el-button>
              </div>
            </el-col>
          </el-row>
          
          <!-- 训练配置说明 -->
          <div class="training-config-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>
              <strong>训练说明：</strong>
              <template v-if="selectedTrainingDevice === 'all'">
                选择全部设备将训练通用模型，适用于所有设备类型的异常检测。
              </template>
              <template v-else-if="selectedTrainingDevice">
                选择单个设备将训练专属模型，针对该设备特性优化，分析精度更高。
              </template>
              <template v-else>
                请选择要训练的设备和时间范围，更多的历史数据可以提高模型准确性。
              </template>
            </span>          </div>
        </div>
        
        <!-- 模型状态信息 -->
        <div class="model-status-info">
          <div v-if="!lastTrainingResult" class="status-item warning">
            <el-icon><Warning /></el-icon>
            <span>模型未训练，请先选择设备和时间范围进行训练以获得准确的分析结果</span>
          </div>
          <div v-else-if="lastTrainingResult.success" class="status-item success">
            <el-icon><Avatar /></el-icon>
            <span>模型已训练完成，可以进行设备分析</span>
          </div>
          <div v-else class="status-item error">
            <el-icon><Warning /></el-icon>
            <span>模型训练失败，建议重新训练</span>
          </div>
        </div>
        
        <!-- 训练进度和状态 -->
        <div v-if="trainingModels" class="training-progress">
          <el-progress 
            :percentage="trainingProgress" 
            :status="trainingProgress === 100 ? 'success' : undefined"
            :show-text="false"
          />
          <div class="progress-text">{{ trainingStatusText }}</div>
        </div>
        
        <!-- 训练结果反馈 -->
        <el-alert
          v-if="lastTrainingResult"
          :title="lastTrainingResult.success ? '训练成功' : '训练失败'"
          :type="lastTrainingResult.success ? 'success' : 'error'"
          :description="lastTrainingResult.message"
          :closable="false"
          style="margin-top: 15px;"
        />
      </div>
    </el-card>

    <!-- 设备选择区域 -->
    <el-card class="device-selector">
      <template #header>
        <div class="section-header">
          <div class="header-title">
            <el-icon class="header-icon"><Monitor /></el-icon>
            <span>设备智能分析</span>
          </div>
        </div>
      </template>
      
      <div class="device-selection">        <el-row :gutter="20" align="middle">          <el-col :span="18">
            <div class="form-item">
              <label class="form-label">
                <el-icon><Monitor /></el-icon>
                选择分析设备
              </label>
              <el-select 
                v-model="selectedDevice" 
                placeholder="请选择要进行智能分析的设备"
                @change="onDeviceChange"
                size="large"
                style="width: 100%"
                filterable
              >
                <el-option
                  v-for="device in availableDevices"
                  :key="device.device_name"
                  :label="`${getDeviceChineseName(device.device_name)} (${device.device_type})`"
                  :value="device.device_name"
                >
                  <div class="device-option">
                    <span class="device-name">{{ getDeviceChineseName(device.device_name) }}</span>
                    <span class="device-type">{{ device.device_type }}</span>
                  </div>
                </el-option>
              </el-select>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="form-item">
              <label class="form-label">&nbsp;</label>              <el-button 
                type="success" 
                size="large"
                @click="analyzeDevice"
                :loading="analyzing"
                :disabled="!selectedDevice"
                :icon="analyzing ? Loading : Promotion"
                style="width: 100%"
                class="analyze-button"
              >
                <span v-if="analyzing">
                  <i class="loading-dots"></i>
                  智能分析中...
                </span>
                <span v-else>
                  🔍 开始智能分析
                </span>
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 分析结果展示区域 -->
    <div v-if="analysisResult" class="analysis-results">
      <!-- 概览卡片 -->
      <el-row :gutter="20" class="overview-cards">
        <el-col :span="6">
          <el-card class="overview-card anomaly">
            <div class="card-content">
              <div class="icon">🔍</div>
              <div class="info">
                <div class="title">异常检测</div>
                <div class="value" :class="getAnomalyClass()">
                  {{ getAnomalyStatus() }}
                </div>
                <div class="subtitle">
                  置信度: {{ getAnomalyConfidence() }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card prediction">
            <div class="card-content">
              <div class="icon">🔮</div>
              <div class="info">
                <div class="title">故障预测</div>
                <div class="value" :class="getPredictionClass()">
                  {{ getPredictionRisk() }}
                </div>
                <div class="subtitle">
                  故障概率: {{ getFailureProbability() }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card stats">
            <div class="card-content">
              <div class="icon">📊</div>
              <div class="info">
                <div class="title">数据质量</div>
                <div class="value" :class="getQualityClass()">
                  {{ getDataQuality() }}
                </div>
                <div class="subtitle">
                  数据点: {{ analysisResult.data_points }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card trend">
            <div class="card-content">
              <div class="icon">📈</div>
              <div class="info">
                <div class="title">数据趋势</div>
                <div class="value" :class="getTrendClass()">
                  {{ getTrendLabel() }}
                </div>
                <div class="subtitle">
                  异常率: {{ getAnomalyRate() }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 详细分析结果 -->
      <el-row :gutter="20" class="detail-results">
        <!-- 统计信息 -->
        <el-col :span="12">
          <el-card class="statistics-card">
            <template #header>
              <span>📈 统计分析</span>
            </template>
            
            <div class="statistics-grid">
              <div class="stat-item">
                <span class="label">设备类型:</span>
                <span class="value">{{ analysisResult.statistics?.device_type || 'unknown' }}</span>
              </div>
              <div class="stat-item">
                <span class="label">数据单位:</span>
                <span class="value">{{ analysisResult.statistics?.unit || '--' }}</span>
              </div>
              <div class="stat-item">
                <span class="label">平均值:</span>
                <span class="value">{{ formatNumber(analysisResult.statistics?.mean) }}</span>
              </div>
              <div class="stat-item">
                <span class="label">标准差:</span>
                <span class="value">{{ formatNumber(analysisResult.statistics?.std) }}</span>
              </div>
              <div class="stat-item">
                <span class="label">最小值:</span>
                <span class="value">{{ formatNumber(analysisResult.statistics?.min) }}</span>
              </div>
              <div class="stat-item">
                <span class="label">最大值:</span>
                <span class="value">{{ formatNumber(analysisResult.statistics?.max) }}</span>
              </div>
              <div class="stat-item">
                <span class="label">中位数:</span>
                <span class="value">{{ formatNumber(analysisResult.statistics?.median) }}</span>
              </div>
              <div class="stat-item">
                <span class="label">异常次数:</span>
                <span class="value">{{ analysisResult.statistics?.anomaly_count || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 维护建议 -->
        <el-col :span="12">
          <el-card class="recommendations-card">
            <template #header>
              <span>💡 维护建议</span>
            </template>
            
            <div class="recommendations-list">
              <div 
                v-for="(rec, index) in analysisResult.recommendations" 
                :key="index"
                class="recommendation-item"
                :class="rec.type"
              >
                <div class="rec-header">
                  <el-tag :type="getRecommendationType(rec.type)" size="small">
                    {{ getRecommendationIcon(rec.type) }} {{ rec.title }}
                  </el-tag>
                  <el-tag 
                    v-if="rec.priority" 
                    :type="getPriorityType(rec.priority)" 
                    size="small"
                  >
                    {{ rec.priority }}
                  </el-tag>
                </div>
                <div class="rec-description">{{ rec.description }}</div>
                <div class="rec-action">
                  <strong>建议行动:</strong> {{ rec.action }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 设备专属分析 -->
      <el-card v-if="hasDeviceSpecificAnalysis()" class="device-specific-card">
        <template #header>
          <span>🔧 设备专属分析 - {{ getDeviceChineseName(selectedDevice) }}</span>
        </template>
        
        <div class="device-analysis">
          <el-row :gutter="20">
            <!-- 温度传感器特殊分析 -->
            <el-col v-if="isTemperatureSensor()" :span="12">
              <div class="analysis-section">
                <h4>🌡️ 温度分析</h4>
                <div class="temp-analysis">
                  <div v-if="analysisResult.statistics?.high_temperature_risk" class="warning-item">
                    ⚠️ 检测到高温风险 (最高: {{ analysisResult.statistics?.max_temp_recorded?.toFixed(1) }}°C)
                  </div>
                  <div v-if="analysisResult.statistics?.avg_temperature_change" class="info-item">
                    📊 平均温度变化: {{ analysisResult.statistics?.avg_temperature_change?.toFixed(2) }}°C
                  </div>
                </div>
              </div>
            </el-col>

            <!-- 压力传感器特殊分析 -->
            <el-col v-if="isPressureSensor()" :span="12">
              <div class="analysis-section">
                <h4>💧 压力分析</h4>
                <div class="pressure-analysis">
                  <div v-if="analysisResult.statistics?.high_pressure_risk" class="warning-item">
                    ⚠️ 检测到高压力风险
                  </div>
                  <div v-if="analysisResult.statistics?.pressure_stability" class="info-item">
                    📊 压力稳定性: {{ analysisResult.statistics?.pressure_stability }}
                  </div>
                </div>
              </div>
            </el-col>

            <!-- 流量传感器特殊分析 -->
            <el-col v-if="isFlowSensor()" :span="12">
              <div class="analysis-section">
                <h4>🌊 流量分析</h4>
                <div class="flow-analysis">
                  <div v-if="analysisResult.statistics?.flow_interruption_rate > 0.1" class="warning-item">
                    ⚠️ 频繁流量中断 (中断率: {{ analysisResult.statistics?.flow_interruption_rate }}%)
                  </div>
                  <div v-if="analysisResult.statistics?.average_flow_rate" class="info-item">
                    📊 平均流量: {{ analysisResult.statistics?.average_flow_rate?.toFixed(1) }} L/min
                  </div>
                </div>
              </div>
            </el-col>

            <!-- 电机/风扇特殊分析 -->
            <el-col v-if="isMotorOrFan()" :span="12">
              <div class="analysis-section">
                <h4>⚙️ 电机分析</h4>
                <div class="motor-analysis">
                  <div v-if="analysisResult.statistics?.average_rpm" class="info-item">
                    📊 平均转速: {{ analysisResult.statistics?.average_rpm?.toFixed(0) }} RPM
                  </div>
                  <div v-if="analysisResult.statistics?.rpm_stability === 'unstable'" class="warning-item">
                    ⚠️ 转速不稳定
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>    <!-- 加载状态 -->
    <div v-else-if="analyzing" class="loading-state">
      <el-card class="loading-card">
        <div class="loading-content">          <div class="loading-animation">
            <el-icon class="rotating-icon">
              <Promotion />
            </el-icon>
          </div>
          <div class="loading-text">
            <h3>正在进行智能分析</h3>
            <p>正在分析设备 <strong>{{ getDeviceChineseName(selectedDevice) }}</strong> 的运行数据</p>
            <p class="loading-details">
              分析范围：{{ getTimeRangeText() }} • 
              使用机器学习算法进行异常检测和故障预测
            </p>
          </div>
          <div class="loading-steps">
            <div class="step active">
              <div class="step-icon">1</div>
              <div class="step-text">数据提取</div>
            </div>
            <div class="step active">
              <div class="step-icon">2</div>
              <div class="step-text">特征分析</div>
            </div>
            <div class="step">
              <div class="step-icon">3</div>
              <div class="step-text">模型预测</div>
            </div>
            <div class="step">
              <div class="step-icon">4</div>
              <div class="step-text">生成报告</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-card class="empty-card">
        <div class="empty-content">
          <div class="empty-icon">🎯</div>
          <h3>开始智能设备分析</h3>
          <p>选择设备和时间范围，使用机器学习算法分析设备运行状态</p>
          <div class="empty-features">
            <div class="feature-item">
              <el-icon><DataBoard /></el-icon>
              <span>异常检测</span>
            </div>            <div class="feature-item">
              <el-icon><Warning /></el-icon>
              <span>故障预测</span>
            </div>
            <div class="feature-item">
              <el-icon><Monitor /></el-icon>
              <span>维护建议</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { 
  Loading, 
  Avatar, 
  DataBoard, 
  InfoFilled, 
  Monitor, 
  Promotion,
  Warning,
  Cpu
} from '@element-plus/icons-vue'
import { useDeviceStore } from '../stores/device'
import mlAPI from '../api/ml'

// 响应式数据
const deviceStore = useDeviceStore()
const selectedDevice = ref('')
const analysisHours = 24 // 固定使用24小时数据进行分析
const selectedTrainingDevice = ref('all') // 训练设备选择，默认为全部设备
const trainingDataHours = ref(168) // 训练数据时间范围，默认7天
const analyzing = ref(false)
const trainingModels = ref(false)
const trainingProgress = ref(0)
const trainingStatusText = ref('')
const analysisResult = ref(null)
const lastTrainingResult = ref(null)

// 设备名称中文映射
const deviceNameMap = {
  'pressure_sensor_001': '主管道压力传感器',
  'temp_sensor_001': '车间A温度传感器',
  'temp_sensor_002': '车间B温度传感器',
  'flow_sensor_001': '主管道流量传感器',
  'vibration_sensor_001': '主轴振动传感器',
  'humidity_sensor_001': '环境湿度传感器',
  'level_sensor_001': '储罐液位传感器',
  'ph_sensor_001': 'pH值传感器',
  'conductivity_sensor_001': '电导率传感器',
  'turbidity_sensor_001': '浊度传感器'
}

// 获取设备中文名称
function getDeviceChineseName(deviceName) {
  return deviceNameMap[deviceName] || deviceName
}

// 计算属性
const availableDevices = computed(() => deviceStore.devices || [])

const modelStatus = computed(() => {
  if (lastTrainingResult.value) {
    if (lastTrainingResult.value.success) {
      return { type: 'success', text: '模型已训练' }
    } else {
      return { type: 'danger', text: '训练失败' }
    }
  }
  return { type: 'info', text: '未训练' }
})

// 生命周期
onMounted(() => {
  deviceStore.fetchDevices()
})

// 方法
async function onDeviceChange() {
  analysisResult.value = null
}

async function trainModels() {
  if (!selectedTrainingDevice.value) {
    ElMessage.warning('请先选择要训练的设备')
    return
  }

  trainingModels.value = true
  trainingProgress.value = 0
  trainingStatusText.value = '正在初始化训练环境...'
  lastTrainingResult.value = null
  // 显示训练开始通知
  const deviceText = selectedTrainingDevice.value === 'all' ? '全部设备' : getDeviceChineseName(selectedTrainingDevice.value)
  const timeText = getTrainingTimeRangeText()
  ElNotification({
    title: '🚀 开始模型训练',
    message: `正在为 ${deviceText} 训练模型，使用${timeText}的数据`,
    type: 'info',
    duration: 3000
  })
  
  try {
    // 模拟训练进度
    const progressInterval = setInterval(() => {
      if (trainingProgress.value < 90) {
        trainingProgress.value += Math.random() * 10
        if (trainingProgress.value < 20) {
          trainingStatusText.value = `正在加载${timeText}的训练数据...`
        } else if (trainingProgress.value < 40) {
          trainingStatusText.value = '正在进行数据预处理和特征提取...'
        } else if (trainingProgress.value < 70) {
          trainingStatusText.value = '正在训练异常检测模型...'
        } else if (trainingProgress.value < 90) {
          trainingStatusText.value = '正在训练故障预测模型...'
        }
      }
    }, 500)
    
    try {
      const response = await mlAPI.trainModels(selectedTrainingDevice.value, trainingDataHours.value)
      
      clearInterval(progressInterval)
      trainingProgress.value = 100
      trainingStatusText.value = '训练完成！'
      
      console.log('训练响应:', response) // 添加日志记录
      console.log('响应类型:', typeof response) // 检查响应类型
      console.log('响应success字段:', response?.success) // 检查success字段
      
      // 检查响应是否成功
      if (response && response.success === true) {
        lastTrainingResult.value = {
          success: true,
          message: `模型训练成功！使用了 ${response.data_points || 'N/A'} 个数据点，覆盖 ${response.devices_count || 'N/A'} 个设备`
        }
        
        ElNotification({
          title: '🎉 模型训练成功',
          message: '机器学习模型已更新，现在可以进行更准确的设备分析',
          type: 'success',
          duration: 5000
        })
      } else {
        // 处理训练不成功的情况
        const errorMsg = response?.message || response?.error || '训练过程中发生未知错误'
        console.warn('训练未成功:', errorMsg)
        throw new Error(errorMsg)
      }    } catch (innerError) {
      clearInterval(progressInterval)
      throw innerError
    }
    
  } catch (error) {
    console.error('训练错误详情:', error) // 添加详细错误日志
    trainingProgress.value = 0
    trainingStatusText.value = ''
    
    // 详细的错误分析
    let errorMessage = '训练失败'
    let errorDetails = ''
    
    if (error.message.includes('timeout')) {
      errorMessage = '训练超时'
      errorDetails = '训练时间过长，可能是由于数据量较大。请稍后重试。'
    } else if (error.message.includes('connection') || error.message.includes('Network Error')) {
      errorMessage = '连接失败'
      errorDetails = '无法连接到机器学习服务。请检查网络连接。'
    } else if (error.message.includes('data')) {
      errorMessage = '数据错误'
      errorDetails = '训练数据存在问题。请检查设备数据是否正常采集。'
    } else if (error.response) {
      errorMessage = '服务器错误'
      errorDetails = `服务器返回错误：${error.response.status} - ${error.response.data?.message || error.message}`
    } else {
      errorDetails = error.message || '发生未知错误，请稍后重试。'
    }
    
    lastTrainingResult.value = {
      success: false,
      message: `${errorMessage}：${errorDetails}`
    }
    
    ElMessage.error({
      message: `模型训练失败: ${errorMessage}`,
      duration: 5000
    })
  } finally {
    trainingModels.value = false
  }
}

async function analyzeDevice() {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择要分析的设备')
    return
  }

  analyzing.value = true
  
  // 显示分析开始通知
  ElNotification({
    title: '🔍 开始设备分析',
    message: `正在分析设备 ${getDeviceChineseName(selectedDevice.value)}，使用${getTimeRangeText()}的数据`,
    type: 'info',
    duration: 3000
  })
  
  try {
    const response = await mlAPI.analyzeDevice(selectedDevice.value, analysisHours)
    if (response.success) {
      analysisResult.value = response
      
      ElNotification({
        title: '✅ 分析完成',
        message: `设备 ${getDeviceChineseName(selectedDevice.value)} 的智能分析已完成，请查看详细结果`,
        type: 'success',
        duration: 4000
      })
    } else {
      throw new Error(response.message || '分析过程中发生错误')
    }
  } catch (error) {
    // 详细的错误分析和反馈
    let errorMessage = '分析失败'
    let errorSuggestion = ''
    
    if (error.message.includes('timeout')) {
      errorMessage = '分析超时'
      errorSuggestion = '建议减少分析时间范围或稍后重试'
    } else if (error.message.includes('data')) {
      errorMessage = '数据不足'
      errorSuggestion = '该设备可能缺少足够的历史数据，请选择其他设备或等待更多数据积累'
    } else if (error.message.includes('model')) {
      errorMessage = '模型未训练'
      errorSuggestion = '请先训练机器学习模型'
    } else {
      errorSuggestion = '请检查网络连接或联系管理员'
    }
    
    ElNotification({
      title: '❌ 分析失败',
      message: `${errorMessage}：${error.message}。${errorSuggestion}`,
      type: 'error',
      duration: 6000
    })
    
    analysisResult.value = null
  } finally {
    analyzing.value = false
  }
}

function getTimeRangeText() {
  return '最近24小时'
}

function getTrainingTimeRangeText() {
  const timeMap = {
    72: '最近3天',
    168: '最近7天',
    360: '最近15天', 
    720: '最近30天'
  }
  return timeMap[trainingDataHours.value] || `最近${Math.round(trainingDataHours.value/24)}天`
}

// 辅助方法
function getAnomalyStatus() {
  const anomaly = analysisResult.value?.anomaly_detection
  if (!anomaly) return '未知'
  return anomaly.is_anomaly ? '检测到异常' : '正常'
}

function getAnomalyClass() {
  const anomaly = analysisResult.value?.anomaly_detection
  if (!anomaly) return 'unknown'
  return anomaly.is_anomaly ? 'danger' : 'success'
}

function getAnomalyConfidence() {
  const anomaly = analysisResult.value?.anomaly_detection
  if (!anomaly || typeof anomaly.confidence !== 'number') return '--'
  return (anomaly.confidence * 100).toFixed(2) + '%'  // 转换为百分比显示
}

function getPredictionRisk() {
  const prediction = analysisResult.value?.failure_prediction
  if (!prediction) return '未知'
  
  const riskLabels = {
    'low': '低风险',
    'medium': '中等风险', 
    'high': '高风险',
    'critical': '严重风险'
  }
  return riskLabels[prediction.risk_level] || prediction.risk_level
}

function getPredictionClass() {
  const prediction = analysisResult.value?.failure_prediction
  if (!prediction) return 'unknown'
  
  const classMap = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return classMap[prediction.risk_level] || 'info'
}

function getFailureProbability() {
  const prediction = analysisResult.value?.failure_prediction
  if (!prediction || typeof prediction.failure_probability !== 'number') return '--'
  return prediction.failure_probability + '%'  // 已经是百分比，直接显示
}

function getDataQuality() {
  const quality = analysisResult.value?.data_quality
  if (!quality) return '未知'
  
  const score = quality.quality_score
  if (score >= 90) return '优秀'
  if (score >= 70) return '良好'
  if (score >= 50) return '一般'
  return '较差'
}

function getQualityClass() {
  const quality = analysisResult.value?.data_quality
  if (!quality) return 'unknown'
  
  const score = quality.quality_score
  if (score >= 90) return 'success'
  if (score >= 70) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

function getTrendLabel() {
  const trend = analysisResult.value?.statistics?.trend
  const trendLabels = {
    'increasing': '上升',
    'decreasing': '下降',
    'stable': '稳定',
    'insufficient_data': '数据不足',
    'unknown': '未知'
  }
  return trendLabels[trend] || trend || '未知'
}

function getTrendClass() {
  const trend = analysisResult.value?.statistics?.trend
  const classMap = {
    'increasing': 'warning',
    'decreasing': 'warning',
    'stable': 'success',
    'insufficient_data': 'info',
    'unknown': 'info'
  }
  return classMap[trend] || 'info'
}

function getAnomalyRate() {
  const rate = analysisResult.value?.statistics?.anomaly_rate
  if (typeof rate !== 'number') return '--'
  return rate + '%'  // 已经是百分比，直接显示
}

function formatNumber(num) {
  if (typeof num !== 'number') return '--'
  return num.toFixed(2)
}

function getRecommendationType(type) {
  const typeMap = {
    'critical': 'danger',
    'warning': 'warning',
    'info': 'info',
    'success': 'success'
  }
  return typeMap[type] || 'info'
}

function getRecommendationIcon(type) {
  const iconMap = {
    'critical': '🚨',
    'warning': '⚠️',
    'info': 'ℹ️',
    'success': '✅'
  }
  return iconMap[type] || 'ℹ️'
}

function getPriorityType(priority) {
  const typeMap = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return typeMap[priority] || 'info'
}

function hasDeviceSpecificAnalysis() {
  return selectedDevice.value && analysisResult.value?.statistics
}

function isTemperatureSensor() {
  return selectedDevice.value?.toLowerCase().includes('temperature')
}

function isPressureSensor() {
  return selectedDevice.value?.toLowerCase().includes('pressure')
}

function isFlowSensor() {
  return selectedDevice.value?.toLowerCase().includes('flow')
}

function isMotorOrFan() {
  const name = selectedDevice.value?.toLowerCase() || ''
  return name.includes('motor') || name.includes('fan')
}
</script>

<style scoped>
.ml-analysis {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 介绍卡片 */
.intro-card {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.intro-content {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.intro-icon {
  font-size: 48px;
  margin-right: 20px;
}

.intro-text h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.intro-text p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

/* 训练区域 */
.training-section {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 12px rgba(103, 194, 58, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  margin-right: 8px;
  font-size: 18px;
  color: #409EFF;
}

.training-content {
  padding: 20px 0;
}

.training-config {
  margin-bottom: 20px;
}

.training-config-tip {
  display: flex;
  align-items: flex-start;
  margin-top: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border-radius: 8px;
  border-left: 4px solid #67C23A;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.1);
}

.training-config-tip .el-icon {
  margin-right: 10px;
  margin-top: 2px;
  color: #67C23A;
  font-size: 16px;
}

.training-config-tip span {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.training-config-tip strong {
  color: #303133;
  font-weight: 600;
}

.training-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.info-item {
  display: flex;
  align-items: flex-start;
  flex: 1;
  margin-right: 30px;
}

.info-icon {
  margin-right: 12px;
  margin-top: 2px;
  font-size: 20px;
  color: #67C23A;
}

.info-text .info-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.info-text .info-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.training-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.training-tip {
  display: flex;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.training-tip .el-icon {
  margin-right: 5px;
}

.model-status-info {
  margin-top: 15px;
}

.status-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 8px;
}

.status-item .el-icon {
  margin-right: 8px;
  font-size: 14px;
}

.status-item.warning {
  background: linear-gradient(135deg, #fdf6ec 0%, #fef3e2 100%);
  color: #E6A23C;
  border-left: 3px solid #E6A23C;
}

.status-item.success {
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  color: #67C23A;
  border-left: 3px solid #67C23A;
}

.status-item.error {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #F56C6C;
  border-left: 3px solid #F56C6C;
}

.training-progress {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

/* 设备选择区域 */
.device-selector {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.device-selection {
  padding: 20px 0;
}

.form-item {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.device-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-name {
  font-weight: 600;
  color: #303133;
}

.device-type {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 12px;
}

.time-option {
  display: flex;
  flex-direction: column;
}

.time-option small {
  color: #909399;
  font-size: 11px;
}

.analysis-tip {
  display: flex;
  align-items: flex-start;
  margin-top: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.analysis-tip .el-icon {
  margin-right: 10px;
  margin-top: 2px;
  color: #409EFF;
  font-size: 16px;
}

.analysis-tip span {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.analysis-tip strong {
  color: #303133;
  font-weight: 600;
}

.analysis-tip em {
  color: #409EFF;
  font-style: normal;
  font-weight: 600;
}

/* 概览卡片优化 */
.overview-cards {
  margin-bottom: 20px;
}

.overview-card {
  height: 120px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.overview-card .card-content {
  display: flex;
  align-items: center;
  height: 100%;
  
  .icon {
    font-size: 36px;
    margin-right: 15px;
  }
  
  .info {
    flex: 1;
    
    .title {
      font-size: 14px;
      color: #666;
      margin-bottom: 5px;
    }
    
    .value {
      font-size: 18px;
      font-weight: bold;
      margin-bottom: 5px;
      
      &.success { color: #67C23A; }
      &.warning { color: #E6A23C; }
      &.danger { color: #F56C6C; }
      &.info { color: #409EFF; }
      &.unknown { color: #909399; }
    }
    
    .subtitle {
      font-size: 12px;
      color: #999;
    }
  }
}

/* 加载状态 */
.loading-state {
  margin-top: 20px;
}

.loading-card {
  border: none;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.loading-content {
  text-align: center;
  padding: 40px 20px;
}

.loading-animation {
  margin-bottom: 20px;
}

.rotating-icon {
  font-size: 48px;
  color: #409EFF;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 18px;
}

.loading-text p {
  margin: 0 0 5px 0;
  color: #606266;
  font-size: 14px;
}

.loading-details {
  color: #909399;
  font-size: 13px;
}

.loading-steps {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  gap: 20px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.3;
  transition: opacity 0.3s;
}

.step.active {
  opacity: 1;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #909399;
  margin-bottom: 8px;
}

.step.active .step-icon {
  background: #409EFF;
  color: white;
}

.step-text {
  font-size: 12px;
  color: #606266;
}

/* 空状态 */
.empty-state {
  margin-top: 40px;
}

.empty-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.empty-content {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 20px;
}

.empty-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 20px;
}

.empty-content p {
  margin: 0 0 30px 0;
  color: #606266;
  font-size: 14px;
}

.empty-features {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #606266;
}

.feature-item .el-icon {
  font-size: 24px;
  color: #409EFF;
  margin-bottom: 8px;
}

.feature-item span {
  font-size: 14px;
}

/* 按钮增强样式 */
.train-button {
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.train-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.analyze-button {
  background: linear-gradient(135deg, #67C23A 0%, #5daf34 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  transition: all 0.3s ease;
}

.analyze-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.4);
}

.loading-dots {
  display: inline-block;
  margin-right: 8px;
}

.loading-dots::after {
  content: '';
  display: inline-block;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: currentColor;
  animation: loading-dots 1.4s infinite linear;
  margin-left: 4px;
}

@keyframes loading-dots {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}
.detail-results {
  margin-bottom: 20px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  
  .stat-item {
    display: flex;
    justify-content: space-between;
    padding: 12px 15px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 8px;
    border-left: 3px solid #409EFF;
    
    .label {
      color: #666;
      font-size: 14px;
      font-weight: 500;
    }
    
    .value {
      font-weight: bold;
      color: #333;
    }
  }
}

.recommendations-list {
  max-height: 400px;
  overflow-y: auto;
}

.recommendation-item {
  margin-bottom: 15px;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
  transition: transform 0.2s;
  
  &:hover {
    transform: translateX(5px);
  }
  
  &.critical {
    background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
    border-left-color: #F56C6C;
  }
  
  &.warning {
    background: linear-gradient(135deg, #fdf6ec 0%, #fef3e2 100%);
    border-left-color: #E6A23C;
  }
  
  &.success {
    background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
    border-left-color: #67C23A;
  }
  
  .rec-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .rec-description {
    color: #666;
    margin-bottom: 8px;
    font-size: 14px;
    line-height: 1.5;
  }
  
  .rec-action {
    font-size: 14px;
    color: #333;
    font-weight: 500;
  }
}

.device-specific-card {
  margin-top: 20px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.analysis-section {
  h4 {
    margin-bottom: 15px;
    color: #333;
    font-size: 16px;
    display: flex;
    align-items: center;
  }
  
  .warning-item {
    color: #E6A23C;
    margin-bottom: 8px;
    padding: 8px 12px;
    background: #fdf6ec;
    border-radius: 6px;
    border-left: 3px solid #E6A23C;
  }
  
  .info-item {
    color: #666;
    margin-bottom: 8px;
    padding: 8px 12px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 3px solid #409EFF;
  }
}
</style>
