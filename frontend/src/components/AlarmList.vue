<template>
  <div class="alarm-list">
    <el-table 
      :data="displayAlarms" 
      v-loading="alarmStore.loading"
      :height="compact ? 300 : 'auto'"
      @selection-change="handleSelectionChange"
    >
      <el-table-column v-if="!compact" type="selection" width="55" />
      
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
      
      <el-table-column prop="message" label="报警信息" min-width="150" />
      
      <el-table-column v-if="!compact" prop="value" label="报警值" width="100">
        <template #default="{ row }">
          {{ row.value?.toFixed(1) || '--' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="timestamp" label="时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.timestamp) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="acknowledged" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.acknowledged ? 'success' : 'warning'" size="small">
            {{ row.acknowledged ? '已确认' : '待确认' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="100">
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
    
    <div v-if="!compact && totalAlarms > pageSize" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="totalAlarms"
        layout="sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlarmStore } from '../stores/alarm'
import { ElMessage } from 'element-plus'

const props = defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})

const alarmStore = useAlarmStore()
const currentPage = ref(1)
const pageSize = ref(20)
const selectedAlarms = ref([])

const displayAlarms = computed(() => {
  if (props.compact) {
    return alarmStore.recentAlarms.slice(0, 10)
  }
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return alarmStore.alarms.slice(start, end)
})

const totalAlarms = computed(() => alarmStore.alarms.length)

function getDeviceDisplayName(deviceName) {
  const nameMap = {
    'temperature_sensor_1': '温度传感器1',
    'temperature_sensor_2': '温度传感器2',
    'fan_1': '风扇1',
    'fan_2': '风扇2',
    'servo_motor_1': '伺服电机1',
    'servo_motor_2': '伺服电机2',
    'pressure_sensor_1': '压力传感器1',
    'flow_meter_1': '流量计1'
  }
  return nameMap[deviceName] || deviceName
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

function formatTime(timestamp) {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString()
}

function handleSelectionChange(selection) {
  selectedAlarms.value = selection
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
}

function handleCurrentChange(page) {
  currentPage.value = page
}

async function acknowledgeAlarm(alarmId) {
  const success = await alarmStore.acknowledgeAlarm(alarmId)
  if (success) {
    ElMessage.success('报警已确认')
  }
}

onMounted(() => {
  if (!props.compact) {
    alarmStore.fetchAlarms()
  }
})
</script>

<style lang="scss" scoped>
.alarm-list {
  .pagination-container {
    margin-top: 20px;
    text-align: right;
  }
}
</style>
