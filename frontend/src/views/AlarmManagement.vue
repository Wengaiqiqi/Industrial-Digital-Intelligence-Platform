<template>
  <div class="alarm-management">
    <div class="page-header">
      <h2>报警管理</h2>      <div class="header-actions">
        <el-button 
          type="primary" 
          :loading="alarmStore.loading"
          @click="refreshAlarms"
        >
          刷新
        </el-button>
        <el-button 
          type="warning" 
          @click="clearAcknowledged"
        >
          清除已确认
        </el-button>
      </div>
    </div>

    <!-- 报警统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card critical">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStats.critical }}</div>
            <div class="stat-label">严重报警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card high">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStats.high }}</div>
            <div class="stat-label">高级报警</div>
          </div>
        </el-card>
      </el-col>      <el-col :span="6">
        <el-card class="stat-card medium">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStats.medium }}</div>
            <div class="stat-label">中级报警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStats.warning }}</div>
            <div class="stat-label">警告报警</div>
          </div>        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card unread">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStore.unreadCount }}</div>
            <div class="stat-label">未确认</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-number">{{ alarmStore.alarms.length }}</div>
            <div class="stat-label">总报警数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <!-- 预留空间 -->
      </el-col>
      <el-col :span="6">
        <!-- 预留空间 -->
      </el-col>
    </el-row>

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
import { Search } from '@element-plus/icons-vue'

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
      color: #333;
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
          color: #666;
        }
      }      &.critical .stat-number {
        color: #f56c6c;
      }

      &.high .stat-number {
        color: #e6a23c;
      }

      &.medium .stat-number {
        color: #409eff;
      }      &.warning .stat-number {
        color: #f7ba2a;
      }

      &.total .stat-number {
        color: #67c23a;
      }

      &.unread .stat-number {
        color: #909399;
      }
    }
  }

  .filter-card {
    margin-bottom: 20px;
  }
}
</style>
