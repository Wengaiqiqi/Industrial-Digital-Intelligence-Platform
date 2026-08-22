<template>
  <div class="alarm-management">
    <div class="page-header">
      <div>
        <h2>告警中心</h2>
        <p>优先处理高风险事件，追踪处置闭环</p>
      </div>
      <div class="header-actions">
        <el-button 
          type="primary" 
          :loading="alarmStore.loading"
          @click="refreshAlarms"
        >
          刷新
        </el-button>
        <el-button @click="exportAlarms">导出记录</el-button>
      </div>
    </div>

    <div class="design-stats alarm-stats">
      <div class="design-stat-card"><span class="design-stat-icon"><Bell /></span><div><span class="design-stat-label">待处理</span><strong>{{ alarmStore.unreadCount }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Warning /></span><div><span class="design-stat-label">严重</span><strong>{{ alarmStats.critical + alarmStats.high }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Warning /></span><div><span class="design-stat-label">警告</span><strong>{{ alarmStats.medium + alarmStats.warning }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><CircleCheck /></span><div><span class="design-stat-label">今日已关闭</span><strong>{{ closedAlarmCount }}</strong></div></div>
    </div>

    <LieflatAlarmInsights :alarms="alarmStore.alarms" />

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">          <el-select v-model="filterSeverity" placeholder="报警级别" clearable>
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
            <el-option label="警告" value="warning" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterStatus" placeholder="确认状态" clearable>
            <el-option label="已确认" value="true" />
            <el-option label="未确认" value="false" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="MM/DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="searchText"
            placeholder="搜索设备或消息..."
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>
    </el-card>

    <!-- 报警列表 -->
    <el-card class="alarm-list-card">
      <AlarmList 
        ref="alarmListRef"
        @selection-change="handleSelectionChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAlarmStore } from '../stores/alarm'
import { ElMessage, ElMessageBox } from 'element-plus'
import AlarmList from '../components/AlarmList.vue'
import LieflatAlarmInsights from '../components/LieflatAlarmInsights.vue'
import { Bell, CircleCheck, Search, Warning } from '@element-plus/icons-vue'

const alarmStore = useAlarmStore()
const alarmListRef = ref(null)

// 筛选条件
const filterSeverity = ref('')
const filterStatus = ref('')
const dateRange = ref([])
const searchText = ref('')

// 报警统计
const alarmStats = computed(() => {
  const stats = { critical: 0, high: 0, medium: 0, low: 0, warning: 0 }
  const alarmsBySeverity = alarmStore.alarmsBySeverity
  
  Object.keys(stats).forEach(severity => {
    stats[severity] = alarmsBySeverity[severity]?.length || 0
  })
  
  return stats
})
const closedAlarmCount = computed(() => Math.max(0, alarmStore.alarms.length - alarmStore.unreadCount))

// 方法
async function refreshAlarms() {
  const params = {}
  
  if (filterSeverity.value) {
    params.severity = filterSeverity.value
  }
  
  if (filterStatus.value) {
    params.acknowledged = filterStatus.value
  }
  
  if (dateRange.value && dateRange.value.length === 2) {
    const start = new Date(dateRange.value[0])
    const end = new Date(dateRange.value[1])
    const hours = Math.ceil((end - start) / (1000 * 60 * 60))
    params.hours = hours
  }
  
  await alarmStore.fetchAlarms(params)
}

async function clearAcknowledged() {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有已确认的报警记录吗？此操作不可恢复。',
      '清除已确认报警',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    alarmStore.clearAcknowledgedAlarms()
    ElMessage.success('已清除所有已确认的报警')
    
  } catch {
    // 用户取消
  }
}

function exportAlarms() {
  const rows = [['设备', '级别', '告警信息', '时间', '状态'], ...alarmStore.alarms.map(alarm => [
    alarm.device_name,
    alarm.severity,
    alarm.message,
    alarm.timestamp,
    alarm.acknowledged ? '已确认' : '待处理'
  ])]
  const csv = rows.map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `alarm-records-${new Date().toISOString().slice(0, 10)}.csv`
  anchor.click()
  URL.revokeObjectURL(url)
  ElMessage.success('告警记录已导出')
}

// 监听筛选条件变化
watch([filterSeverity, filterStatus, dateRange, searchText], () => {
  refreshAlarms()
}, { deep: true })

onMounted(() => {
  alarmStore.fetchAlarms()
})
</script>

<style lang="scss" scoped>
.alarm-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      color: #081F5C;
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
        text-align: center;
        padding: 10px;

        .stat-number {
          font-size: 32px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: #334EAC;
        }
      }      &.critical .stat-number {
        color: #081F5C;
      }

      &.high .stat-number {
        color: #7096D1;
      }

      &.medium .stat-number {
        color: #334EAC;
      }      &.warning .stat-number {
        color: #7096D1;
      }

      &.total .stat-number {
        color: #7096D1;
      }

      &.unread .stat-number {
        color: #7096D1;
      }
    }
  }

  .filter-card {
    margin-bottom: 20px;
  }
}
</style>
