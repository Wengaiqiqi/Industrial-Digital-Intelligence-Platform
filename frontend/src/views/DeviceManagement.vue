<template>
  <div class="device-management">
    <div class="page-header">
      <div>
        <h2>设备管理</h2>
        <p>统一管理现场设备、连接状态与维护计划</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDeviceDialog = true">添加设备</el-button>
        <el-button @click="bulkInput?.click()">批量导入</el-button>
        <input ref="bulkInput" class="visually-hidden" type="file" accept=".csv,.xlsx" @change="handleBulkImport">
      </div>
    </div>

    <div class="design-stats">
      <div class="design-stat-card"><span class="design-stat-icon"><Monitor /></span><div><span class="design-stat-label">设备总数</span><strong>{{ deviceStats.total }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Platform /></span><div><span class="design-stat-label">在线设备</span><strong>{{ deviceStats.online }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Warning /></span><div><span class="design-stat-label">告警设备</span><strong>{{ deviceStats.warning }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Close /></span><div><span class="design-stat-label">离线设备</span><strong>{{ deviceStats.offline }}</strong></div></div>
    </div>

    <section class="availability-strip" aria-label="设备在线率">
      <div class="availability-copy"><strong>设备在线率</strong><span>{{ onlineRate }}%</span></div>
      <div class="availability-ticks"><i v-for="n in 48" :key="n" :class="{ active: n <= Math.round(onlineRate * .48) }"></i></div>
      <div class="availability-axis"><span v-for="label in ['00','02','04','06','08','10','12']" :key="label">{{ label }}</span></div>
      <div class="availability-legend"><span><i class="active"></i>在线</span><span><i></i>离线</span><b>数据更新于刚刚</b></div>
    </section>

    <div class="device-filter-row">
      <el-input v-model="searchText" placeholder="搜索设备名称或 ID" clearable><template #prefix><el-icon><Search /></el-icon></template></el-input>
      <el-select v-model="filterStatus" placeholder="全部状态" clearable><el-option label="在线" value="online" /><el-option label="离线" value="offline" /><el-option label="告警" value="warning" /><el-option label="错误" value="error" /></el-select>
      <el-select v-model="filterType" placeholder="全部类型" clearable><el-option label="传感器" value="sensor" /><el-option label="执行器" value="actuator" /><el-option label="指示器" value="indicator" /><el-option label="IO设备" value="io" /></el-select>
      <el-button :loading="deviceStore.loading" @click="refreshDevices">刷新</el-button>
    </div>

    <el-card class="device-list-card">
      <template #header>
        <div class="card-header"><span>设备清单</span><small>共 {{ totalDevices }} 台设备</small></div>
      </template>

      <el-table :data="paginatedDevices" v-loading="deviceStore.loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="46" />
        
        <el-table-column prop="device_name" label="设备名称" min-width="150">
          <template #default="{ row }">
            <div class="device-name-cell">
              <div :class="['status-indicator', row.status]"></div>
              <span>{{ getDeviceDisplayName(row.device_name) }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="device_type" label="设备类型" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ getDeviceTypeLabel(row.device_type) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_value" label="当前值与趋势" min-width="180">
          <template #default="{ row }">
            <div class="value-with-ticks">
              <span class="value-display">
                {{ formatValue(row.last_value) }}
                <span class="unit">{{ row.unit }}</span>
              </span>
              <span class="table-ticks" aria-hidden="true">
                <i v-for="index in 7" :key="index" :style="{ height: `${5 + ((index * 3 + row.device_name.length) % 9)}px` }"></i>
              </span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_runtime" label="运行时间" width="110">
          <template #default="{ row }">
            {{ deviceStore.formatRuntime(row.total_runtime) }}
          </template>
        </el-table-column>

        <el-table-column prop="last_update" label="最后更新" width="155">
          <template #default="{ row }">{{ formatTime(row.last_update) }}</template>
        </el-table-column>
        
        <el-table-column prop="error_count" label="异常次数" width="84">
          <template #default="{ row }">
            <span :class="{ 'error-count': row.error_count > 0 }">
              {{ row.error_count }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="154" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                size="small"
                type="primary"
                @click="showDeviceDetail(row)"
              >
                详情
              </el-button>
              <el-dropdown @command="handleDeviceAction">
                <el-button size="small">
                  更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      :command="{ action: 'control', device: row }"
                      :disabled="row.status === 'offline'"
                    >
                      设备控制
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'restart', device: row }">
                      重启设备
                    </el-dropdown-item>
                    <el-dropdown-item 
                      :command="{ action: 'delete', device: row }"
                      style="color: var(--ink);"
                    >
                      删除设备
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[6, 10, 20, 50]"
          :total="totalDevices"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 设备控制对话框 -->
    <el-dialog
      v-model="showControlDialog"
      :title="`控制设备: ${currentDevice?.device_name}`"
      width="500px"
    >
      <div v-if="currentDevice" class="device-control">
        <el-form :model="controlForm" label-width="100px">
          <el-form-item label="设备名称:">
            <span>{{ getDeviceDisplayName(currentDevice.device_name) }}</span>
          </el-form-item>
          
          <el-form-item label="当前状态:">
            <el-tag :type="getStatusType(currentDevice.status)">
              {{ getStatusLabel(currentDevice.status) }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="当前值:">
            <span class="value-display">
              {{ formatValue(currentDevice.last_value) }}
              <span class="unit">{{ currentDevice.unit }}</span>
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

    <!-- 设备详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`设备详情: ${currentDevice?.device_name}`"
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
          <el-descriptions-item label="总运行时间">
            {{ deviceStore.formatRuntime(currentDevice.total_runtime) }}
          </el-descriptions-item>
          <el-descriptions-item label="异常次数">
            {{ currentDevice.error_count }}
          </el-descriptions-item>
          <el-descriptions-item label="设备ID">
            {{ currentDevice.device_name }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 添加设备对话框 -->
    <el-dialog
      v-model="showAddDeviceDialog"
      title="添加新设备"
      width="600px"
      @close="resetAddDeviceForm"
    >
      <el-form :model="addDeviceForm" :rules="addDeviceRules" ref="addDeviceFormRef" label-width="120px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="addDeviceForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="type">
          <el-select v-model="addDeviceForm.type" placeholder="请选择设备类型" style="width: 100%">
            <el-option-group label="传感器">
              <el-option label="温度传感器" value="temperature_sensor" />
              <el-option label="压力传感器" value="pressure_sensor" />
              <el-option label="流量计" value="flow_meter" />
              <el-option label="液位传感器" value="level_sensor" />
              <el-option label="湿度传感器" value="humidity_sensor" />
            </el-option-group>
            <el-option-group label="执行器">
              <el-option label="风扇" value="fan" />
              <el-option label="伺服电机" value="servo_motor" />
              <el-option label="电磁阀" value="valve" />
              <el-option label="加热器" value="heater" />
              <el-option label="泵" value="pump" />
            </el-option-group>
            <el-option-group label="指示器">
              <el-option label="指示灯" value="indicator_light" />
              <el-option label="显示屏" value="display" />
              <el-option label="报警器" value="alarm" />
            </el-option-group>
            <el-option-group label="IO设备">
              <el-option label="数字输入" value="digital_input" />
              <el-option label="数字输出" value="digital_output" />
              <el-option label="模拟输入" value="analog_input" />
              <el-option label="模拟输出" value="analog_output" />
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <el-form-item label="设备ID" prop="deviceId">
          <el-input v-model="addDeviceForm.deviceId" placeholder="设备唯一标识符" />
          <div class="form-tip">设备的唯一标识符，用于MQTT通信</div>
        </el-form-item>
        
        <el-form-item label="MQTT主题" prop="topic">
          <el-input v-model="addDeviceForm.topic" placeholder="MQTT主题路径" />
          <div class="form-tip">例如: sensors/temperature/001</div>
        </el-form-item>
        
        <el-form-item label="数据单位" prop="unit">
          <el-select v-model="addDeviceForm.unit" placeholder="选择数据单位" style="width: 100%">
            <el-option label="摄氏度 (°C)" value="°C" />
            <el-option label="华氏度 (°F)" value="°F" />
            <el-option label="百分比 (%)" value="%" />
            <el-option label="帕斯卡 (Pa)" value="Pa" />
            <el-option label="巴 (bar)" value="bar" />
            <el-option label="升/分钟 (L/min)" value="L/min" />
            <el-option label="转/分钟 (RPM)" value="RPM" />
            <el-option label="伏特 (V)" value="V" />
            <el-option label="安培 (A)" value="A" />
            <el-option label="瓦特 (W)" value="W" />
            <el-option label="米 (m)" value="m" />
            <el-option label="厘米 (cm)" value="cm" />
            <el-option label="无单位" value="" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="采样频率" prop="sampleRate">
          <el-input-number 
            v-model="addDeviceForm.sampleRate" 
            :min="1" 
            :max="3600" 
            placeholder="秒"
            style="width: 100%"
          />
          <div class="form-tip">数据采样的频率，单位：秒</div>
        </el-form-item>
        
        <el-form-item label="报警阈值">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-input-number 
                v-model="addDeviceForm.warningThreshold" 
                placeholder="警告阈值"
                style="width: 100%"
              />
            </el-col>
            <el-col :span="12">
              <el-input-number 
                v-model="addDeviceForm.dangerThreshold" 
                placeholder="危险阈值"
                style="width: 100%"
              />
            </el-col>
          </el-row>
          <div class="form-tip">设置设备数据的报警阈值</div>
        </el-form-item>
        
        <el-form-item label="设备描述">
          <el-input 
            v-model="addDeviceForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="设备的详细描述信息"
          />
        </el-form-item>
        
        <el-form-item label="启用设备">
          <el-switch v-model="addDeviceForm.enabled" />
          <div class="form-tip">是否立即启用该设备</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDeviceDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmAddDevice" :loading="addDeviceLoading">
            确定添加
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useDeviceStore } from '../stores/device'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Platform,
  Close,
  Warning,
  Monitor,
  Search,
  ArrowDown
} from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()

// 响应式数据
const searchText = ref('')
const filterStatus = ref('')
const filterType = ref('')
const bulkInput = ref(null)
const currentPage = ref(1)
const pageSize = ref(6)
const selectedDevices = ref([])
const showControlDialog = ref(false)
const showDetailDialog = ref(false)
const showAddDeviceDialog = ref(false)
const currentDevice = ref(null)
const controlLoading = ref(false)
const addDeviceLoading = ref(false)
const addDeviceFormRef = ref(null)

// 定时器
let runtimeUpdateTimer = null

// 控制表单
const controlForm = ref({
  command: '',
  value: null
})

// 添加设备表单
const addDeviceForm = ref({
  name: '',
  type: '',
  deviceId: '',
  topic: '',
  unit: '',
  sampleRate: 60,
  warningThreshold: null,
  dangerThreshold: null,
  description: '',
  enabled: true
})

// 添加设备表单验证规则
const addDeviceRules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 2, max: 50, message: '设备名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  deviceId: [
    { required: true, message: '请输入设备ID', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '设备ID只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  topic: [
    { required: true, message: '请输入MQTT主题', trigger: 'blur' }
  ],
  unit: [
    { required: true, message: '请选择数据单位', trigger: 'change' }
  ],
  sampleRate: [
    { required: true, message: '请设置采样频率', trigger: 'blur' }
  ]
}

// 计算属性
const deviceStats = computed(() => deviceStore.deviceStats)
const onlineRate = computed(() => deviceStats.value.total ? Math.round(deviceStats.value.online / deviceStats.value.total * 100) : 0)

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

  if (filterType.value) {
    devices = devices.filter(device => device.device_type === filterType.value)
  }

  return devices
})

const totalDevices = computed(() => filteredDevices.value.length)

const paginatedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDevices.value.slice(start, end)
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

function formatValue(value) {
  if (typeof value !== 'number') return '--'
  return value.toFixed(1)
}

function formatTime(timestamp) {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString()
}

// 删除本地的formatRuntime函数，使用store中的

// 更新设备运行时间
function updateDeviceRuntimes() {
  deviceStore.devices.forEach(device => {
    device.total_runtime = deviceStore.calculateDeviceRuntime(device.device_name)
  })
}

async function refreshDevices() {
  await deviceStore.fetchDevices()
}

function handleBulkImport(event) {
  const file = event.target.files?.[0]
  if (!file) return
  ElMessage.success(`已读取 ${file.name}，请在确认后完成批量导入`)
  event.target.value = ''
}

function handleSelectionChange(selection) {
  selectedDevices.value = selection
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
}

function handleCurrentChange(page) {
  currentPage.value = page
}

function showDeviceDetail(device) {
  currentDevice.value = device
  showDetailDialog.value = true
}

function showControlDevice(device) {
  currentDevice.value = device
  controlForm.value = {
    command: '',
    value: null
  }
  showControlDialog.value = true
}

async function executeControl() {
  if (!controlForm.value.command) {
    ElMessage.warning('请选择控制命令')
    return
  }

  controlLoading.value = true
  
  try {
    const success = await deviceStore.controlDevice(
      currentDevice.value.device_name,
      controlForm.value.command,
      controlForm.value.value
    )
    
    if (success) {
      ElMessage.success('控制命令已发送')
      showControlDialog.value = false
      await refreshDevices()
    }
  } catch (error) {
    ElMessage.error('控制命令发送失败')
  } finally {
    controlLoading.value = false
  }
}

function handleDeviceAction({ action, device }) {
  switch (action) {
    case 'control':
      showControlDevice(device)
      break
    case 'restart':
      handleRestartDevice(device)
      break
    case 'delete':
      handleDeleteDevice(device)
      break
  }
}

async function handleRestartDevice(device) {
  try {
    await ElMessageBox.confirm(
      `确定要重启设备 ${getDeviceDisplayName(device.device_name)} 吗？`,
      '确认重启',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const success = await deviceStore.controlDevice(device.device_name, 'restart')
    if (success) {
      ElMessage.success('设备重启命令已发送')
      await refreshDevices()
    }
  } catch {
    // 用户取消
  }
}

async function handleDeleteDevice(device) {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 ${getDeviceDisplayName(device.device_name)} 吗？此操作无法恢复！`,
      '确认删除设备',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    const success = await deviceStore.deleteDevice(device.device_name)
    if (success) {
      ElMessage.success('设备删除成功')
      await refreshDevices()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设备删除失败: ' + (error.message || '未知错误'))
    }
  }
}

// 添加设备相关方法
function resetAddDeviceForm() {
  addDeviceForm.value = {
    name: '',
    type: '',
    deviceId: '',
    topic: '',
    unit: '',
    sampleRate: 60,
    warningThreshold: null,
    dangerThreshold: null,
    description: '',
    enabled: true
  }
  
  if (addDeviceFormRef.value) {
    addDeviceFormRef.value.resetFields()
  }
}

async function confirmAddDevice() {
  if (!addDeviceFormRef.value) return
  
  try {
    await addDeviceFormRef.value.validate()
  } catch (error) {
    ElMessage.warning('请检查表单输入')
    return
  }
  
  addDeviceLoading.value = true
  
  try {
    // 构建设备数据
    const deviceData = {
      device_name: addDeviceForm.value.deviceId,
      display_name: addDeviceForm.value.name,
      device_type: getDeviceTypeFromSelection(addDeviceForm.value.type),
      mqtt_topic: addDeviceForm.value.topic,
      unit: addDeviceForm.value.unit,
      sample_rate: addDeviceForm.value.sampleRate,
      warning_threshold: addDeviceForm.value.warningThreshold,
      danger_threshold: addDeviceForm.value.dangerThreshold,
      description: addDeviceForm.value.description,
      enabled: addDeviceForm.value.enabled,
      status: 'offline',
      last_value: 0,
      error_count: 0
    }
    
    // 调用后端API添加设备
    const success = await deviceStore.addDevice(deviceData)
    
    if (success) {
      ElMessage.success('设备添加成功')
      showAddDeviceDialog.value = false
      await refreshDevices()
      resetAddDeviceForm()
    } else {
      ElMessage.error('设备添加失败')
    }
  } catch (error) {
    console.error('添加设备错误:', error)
    ElMessage.error('设备添加失败: ' + (error.message || '未知错误'))
  } finally {
    addDeviceLoading.value = false
  }
}

function getDeviceTypeFromSelection(selection) {
  const typeMap = {
    'temperature_sensor': 'sensor',
    'pressure_sensor': 'sensor',
    'flow_meter': 'sensor',
    'level_sensor': 'sensor',
    'humidity_sensor': 'sensor',
    'fan': 'actuator',
    'servo_motor': 'actuator',
    'valve': 'actuator',
    'heater': 'actuator',
    'pump': 'actuator',
    'indicator_light': 'indicator',
    'display': 'indicator',
    'alarm': 'indicator',
    'digital_input': 'io',
    'digital_output': 'io',
    'analog_input': 'io',
    'analog_output': 'io'
  }
  return typeMap[selection] || 'sensor'
}

// 监听设备类型变化，自动生成相关字段
function watchDeviceType() {
  watch(() => addDeviceForm.value.type, (newType) => {
    if (!newType) return
    
    // 自动生成设备ID
    if (!addDeviceForm.value.deviceId) {
      const timestamp = Date.now().toString().slice(-4)
      addDeviceForm.value.deviceId = `${newType}_${timestamp}`
    }
    
    // 自动生成MQTT主题
    if (!addDeviceForm.value.topic) {
      addDeviceForm.value.topic = `devices/${newType}/${addDeviceForm.value.deviceId || 'device'}`
    }
    
    // 根据设备类型设置默认单位
    const defaultUnits = {
      'temperature_sensor': '°C',
      'pressure_sensor': 'bar',
      'flow_meter': 'L/min',
      'level_sensor': '%',
      'humidity_sensor': '%',
      'fan': 'RPM',
      'servo_motor': 'RPM',
      'valve': '%',
      'heater': 'W',
      'pump': 'L/min',
      'indicator_light': '',
      'display': '',
      'alarm': '',
      'digital_input': '',
      'digital_output': '',
      'analog_input': 'V',
      'analog_output': 'V'
    }
    
    if (!addDeviceForm.value.unit && defaultUnits[newType]) {
      addDeviceForm.value.unit = defaultUnits[newType]
    }
  })
}

// 生命周期
onMounted(async () => {
  await deviceStore.fetchDevices()
  
  // 启动运行时间更新定时器，每秒更新一次
  runtimeUpdateTimer = setInterval(updateDeviceRuntimes, 1000)
  
  // 启用设备类型变化监听
  watchDeviceType()
})

onUnmounted(() => {
  if (runtimeUpdateTimer) {
    clearInterval(runtimeUpdateTimer)
  }
})
</script>

<style lang="scss" scoped>
.device-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: var(--ink);
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        gap: 15px;

        .stat-icon {
          width: 50px;
          height: 50px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;

          &.online {
            background: var(--accent-soft);
            color: var(--data-2);
          }

          &.offline {
            background: var(--alarm-soft);
            color: var(--ink);
          }

          &.warning {
            background: var(--warn-soft);
            color: var(--data-2);
          }

          &.total {
            background: var(--accent-soft);
            color: var(--data);
          }
        }

        .stat-info {
          .stat-number {
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
          }

          .stat-label {
            font-size: 14px;
            color: var(--data);
            margin-top: 4px;
          }
        }
      }
    }
  }

  .device-list-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-controls {
        display: flex;
        align-items: center;
      }
    }

    .device-name-cell {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .value-display {
      font-weight: 500;

      .unit {
        color: var(--data-2);
        font-size: 12px;
        margin-left: 4px;
      }
    }

    .error-count {
      color: var(--ink);
      font-weight: 500;
    }

    .action-buttons { display: flex; align-items: center; gap: 5px; flex-wrap: nowrap; }

    .pagination-container {
      margin-top: 20px;
      text-align: right;
    }
  }

  .visually-hidden { position: fixed; width: 1px; height: 1px; opacity: 0; pointer-events: none; }

  .availability-strip {
    display: grid;
    grid-template-columns: 150px minmax(0, 1fr) 260px;
    grid-template-rows: 42px 20px;
    align-items: center;
    min-height: 96px;
    margin-bottom: 14px;
    padding: 12px 20px;
    background: var(--paper-soft);
    border: 1px solid var(--grid);
    border-radius: 10px;
  }
  .availability-copy { display: flex; align-items: flex-start; flex-direction: column; gap: 2px; align-self: center; }
  .availability-copy strong { font-size: 14px; line-height: 1.2; }
  .availability-copy span { color: var(--data); font-size: 26px; font-weight: 800; line-height: 1.05; }
  .availability-ticks { display: flex; align-items: flex-end; justify-content: space-between; width: 100%; height: 32px; gap: 0; }
  .availability-ticks i { width: 2px; height: 19px; background: var(--data-3); }
  .availability-ticks i:nth-child(3n) { height: 30px; }
  .availability-ticks i.active { background: var(--data); }
  .availability-axis { display: flex; justify-content: space-between; grid-column: 2; color: var(--muted); font-size: 10px; }
  .availability-legend { display: flex; align-items: center; justify-content: flex-end; align-self: center; gap: 16px; grid-column: 3; grid-row: 1 / 3; color: var(--muted); font-size: 12px; }
  .availability-legend span { display: flex; align-items: center; gap: 5px; }
  .availability-legend i { width: 2px; height: 12px; background: var(--data-3); }
  .availability-legend i.active { background: var(--data); }
  .availability-legend b { font-weight: 600; }

  .page-header { margin-bottom: 30px; }
  .device-filter-row { display: grid; grid-template-columns: minmax(260px, 1fr) 148px 148px auto; gap: 10px; margin-bottom: 20px; }
  .device-list-card :deep(.el-card__header) { padding-block: 12px; }
  .device-list-card .card-header small { color: var(--muted); font-size: 12px; font-weight: 600; }
  .device-list-card :deep(.el-card__body) { padding: 0 16px 10px; }
  .device-list-card .pagination-container { margin-top: 10px; }

  .device-control {
    .value-display {
      font-size: 16px;
      font-weight: 500;

      .unit {
        color: var(--data-2);
        font-size: 14px;
        margin-left: 4px;
      }
    }
  }

  .device-detail {
    .value-display {
      font-size: 16px;
      font-weight: 500;

      .unit {
        color: var(--data-2);
        font-size: 14px;
        margin-left: 4px;
      }
    }
  }
}
</style>
