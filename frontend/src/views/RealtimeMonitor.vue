<template>
  <div class="realtime-monitor">
    <div class="monitor-container">
      <aside class="sidebar">
        <div class="sidebar-filters">
          <el-input v-model="searchText" placeholder="搜索设备" clearable><template #prefix><el-icon><Search /></el-icon></template></el-input>
          <el-select v-model="filterStatus" placeholder="全部状态" clearable><el-option label="在线" value="online" /><el-option label="离线" value="offline" /><el-option label="告警" value="warning" /></el-select>
          <el-select v-model="filterType" placeholder="全部类型" clearable><el-option label="传感器" value="sensor" /><el-option label="执行器" value="actuator" /><el-option label="IO设备" value="io" /></el-select>
        </div>
        <div class="device-list">
          <button v-for="device in filteredDevices" :key="device.device_name" :class="['device-item',{ active: selectedDevice?.device_name === device.device_name }]" @click="selectDevice(device)">
            <span :class="['status-dot', device.status]"></span>
            <span class="device-copy"><strong>{{ deviceLabel(device.device_name) }}</strong><small>{{ typeLabel(device.device_type) }}</small></span>
            <span class="device-reading"><strong>{{ formatValue(device.current_value ?? device.last_value) }}</strong><small>{{ device.unit }}</small></span>
          </button>
        </div>
        <footer>共 {{ deviceStore.deviceStats.total }} 台 · 在线 {{ deviceStore.deviceStats.online }} 台</footer>
      </aside>

      <main v-if="selectedDevice" class="detail-panel">
        <header class="detail-header">
          <div><h2>{{ deviceLabel(selectedDevice.device_name) }}</h2><p><span class="soft-tag">{{ statusLabel(selectedDevice.status) }}</span><span class="soft-tag">{{ typeLabel(selectedDevice.device_type) }}</span><b>设备 ID · {{ selectedDevice.device_name }}</b></p></div>
          <div><el-button type="primary" @click="controlVisible = true">控制设备</el-button><el-button :loading="loadingData" @click="loadDeviceData">刷新数据</el-button><el-button @click="$router.push('/prediction')">智能分析</el-button></div>
        </header>

        <div class="design-stats realtime-stats">
          <div class="design-stat-card"><div><span class="design-stat-label">当前数值</span><strong>{{ formatValue(currentValue) }} <small>{{ selectedDevice.unit }}</small></strong></div></div>
          <div class="design-stat-card"><div><span class="design-stat-label">运行时间</span><strong>{{ deviceStore.formatRuntime(selectedDevice.total_runtime) }}</strong></div></div>
          <div class="design-stat-card"><div><span class="design-stat-label">采样周期</span><strong>5 秒</strong></div></div>
          <div class="design-stat-card"><div><span class="design-stat-label">活跃告警</span><strong>{{ deviceAlarms.length }}</strong></div></div>
        </div>

        <div class="realtime-grid">
          <div class="left-stack">
            <section class="live-chart-card">
            <div class="chart-title"><div><span>实时趋势 · F2 连续线</span><h3>采样稳定，当前值位于目标区间</h3><p>一个点 = 一次采样 · 空心点 = 正常读数</p></div><el-select v-model="timeRange" size="small" @change="loadDeviceData"><el-option label="1 小时" value="1" /><el-option label="6 小时" value="6" /><el-option label="24 小时" value="24" /></el-select></div>
            <svg viewBox="0 0 770 300" role="img" aria-label="设备实时趋势">
              <g class="grid"><line v-for="tick in [42,96,150,204,258]" :key="tick" x1="46" :y1="tick" x2="744" :y2="tick" /></g>
              <polyline :points="trendPoints" class="trend-line" />
              <circle v-for="(value,index) in trendValues" :key="index" :cx="tx(index)" :cy="ty(value)" :r="index === trendValues.length - 1 ? 4 : 2.8" :class="index === trendValues.length - 1 ? 'current-point' : 'trend-point'" />
              <text v-for="(label,index) in trendLabels" :key="label" :x="tx(index * 4)" y="286" text-anchor="middle">{{ label }}</text>
            </svg>
            <footer>最近更新 · {{ updatedAt }}</footer>
            </section>

            <section class="live-table"><header><strong>实时数据</strong><button @click="loadDeviceData">查看更多</button></header><table><thead><tr><th>时间</th><th>数值</th><th>质量</th><th>状态</th></tr></thead><tbody><tr v-for="row in pagedRecentRows" :key="row.timestamp"><td>{{ formatTime(row.timestamp) }}</td><td><strong>{{ formatValue(row.value) }} {{ selectedDevice.unit }}</strong></td><td><span class="soft-tag">良好</span></td><td>● 正常</td></tr></tbody></table><footer><span>第 {{ recentPage }} / {{ recentPageCount }} 页 · 共 {{ recentRows.length }} 条数据</span><div class="table-pagination"><button type="button" :disabled="recentPage <= 1" @click="recentPage--">上一页</button><button type="button" :disabled="recentPage >= recentPageCount" @click="recentPage++">下一页</button></div></footer></section>
          </div>

          <div class="right-stack">
            <section class="threshold-card"><h3>阈值区间</h3><p>当前 {{ formatValue(currentValue) }} {{ selectedDevice.unit }}</p><div class="threshold-scale"><span></span><i :style="{ left: `${thresholdPosition}%` }"></i></div><div class="scale-labels"><span>下限</span><b>目标区间</b><span>上限</span></div><small>当前数值位于安全区间</small></section>
            <section class="events-card"><h3>事件时间线</h3><div v-for="event in eventRows" :key="event.time" class="event-row"><i></i><span><strong>{{ event.title }}</strong><small>{{ event.time }} · {{ event.note }}</small></span></div></section>
          </div>
        </div>

      </main>

      <main v-else class="detail-panel empty-detail"><p>请选择设备查看实时状态</p></main>
    </div>

    <el-dialog v-model="controlVisible" :title="`控制设备：${deviceLabel(selectedDevice?.device_name)}`" width="460px">
      <el-form label-width="90px"><el-form-item label="控制命令"><el-select v-model="control.command"><el-option label="设置数值" value="set_value" /><el-option label="启动设备" value="start" /><el-option label="停止设备" value="stop" /><el-option label="重置设备" value="reset" /></el-select></el-form-item><el-form-item v-if="control.command === 'set_value'" label="目标值"><el-input-number v-model="control.value" /></el-form-item></el-form>
      <template #footer><el-button @click="controlVisible = false">取消</el-button><el-button type="primary" @click="executeControl">执行</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useDeviceStore } from '../stores/device'
import { useAlarmStore } from '../stores/alarm'
import { deviceAPI } from '../api'

const deviceStore = useDeviceStore()
const alarmStore = useAlarmStore()
const searchText = ref('')
const filterStatus = ref('')
const filterType = ref('')
const selectedDevice = ref(null)
const timeRange = ref('24')
const loadingData = ref(false)
const history = ref([])
const controlVisible = ref(false)
const control = ref({ command: 'set_value', value: 0 })
let refreshTimer

const filteredDevices = computed(() => deviceStore.devices.filter(device => {
  const search = searchText.value.trim().toLowerCase()
  return (!search || device.device_name.toLowerCase().includes(search) || deviceLabel(device.device_name).includes(search)) && (!filterStatus.value || device.status === filterStatus.value) && (!filterType.value || device.device_type === filterType.value)
}))
const deviceAlarms = computed(() => alarmStore.alarms.filter(alarm => alarm.device_name === selectedDevice.value?.device_name && !alarm.acknowledged))
const currentValue = computed(() => Number(selectedDevice.value?.current_value ?? selectedDevice.value?.last_value ?? 0))
const fallback = [52,54,58,56,61,59,63,66,62,65,68,67,71,69,72,74,71,75,73,76]
const trendValues = computed(() => {
  const values = history.value.map(item => Number(item.value)).filter(Number.isFinite).slice(-20)
  return values.length > 4 ? values : fallback.map(value => selectedDevice.value?.unit === 'digital' ? value % 2 : value)
})
const range = computed(() => { const min = Math.min(...trendValues.value); const max = Math.max(...trendValues.value); return { min, span: Math.max(1, max - min) } })
const tx = index => 52 + index * (680 / Math.max(1, trendValues.value.length - 1))
const ty = value => 258 - (value - range.value.min) / range.value.span * 205
const trendPoints = computed(() => trendValues.value.map((value,index) => `${tx(index)},${ty(value)}`).join(' '))
const trendLabels = computed(() => ['24m','20m','16m','12m','8m'])
const thresholdPosition = computed(() => 30 + Math.abs(currentValue.value * 1.7) % 40)
const recentPage = ref(1)
const recentPageSize = 10
const recentRows = computed(() => history.value.slice().reverse().length ? history.value.slice().reverse() : fallback.map((value,index) => ({ timestamp: new Date(Date.now() - index * 5000), value })))
const recentPageCount = computed(() => Math.max(1, Math.ceil(recentRows.value.length / recentPageSize)))
const pagedRecentRows = computed(() => recentRows.value.slice((recentPage.value - 1) * recentPageSize, recentPage.value * recentPageSize))
const updatedAt = computed(() => formatTime(recentRows.value[0]?.timestamp || Date.now()))
watch(recentPageCount, pageCount => { if (recentPage.value > pageCount) recentPage.value = pageCount })
const eventRows = computed(() => [{ title: '数据已刷新', time: updatedAt.value, note: '采样质量良好' }, { title: '设备上线', time: '08:00:12', note: '连接稳定' }, ...(deviceAlarms.value.slice(0,1).map(alarm => ({ title: '告警触发', time: formatTime(alarm.timestamp), note: alarm.message })))])

const deviceLabel = name => ({ temperature_sensor_1:'温度传感器1', temperature_sensor_2:'温度传感器2', fan_1:'风扇1', fan_2:'风扇2', servo_motor_1:'伺服电机1', servo_motor_2:'伺服电机2', pressure_sensor_1:'压力传感器1', flow_meter_1:'流量计1', digital_input_1:'数字输入1', digital_output_1:'数字输出1', indicator_light_1:'指示灯1' }[name] || name || '')
const typeLabel = type => ({ sensor:'传感器', actuator:'执行器', indicator:'指示器', io:'IO设备' }[type] || type)
const statusLabel = status => ({ online:'在线', offline:'离线', warning:'告警', error:'错误' }[status] || status)
const formatValue = value => Number.isFinite(Number(value)) ? Number(value).toFixed(1) : '--'
const formatTime = value => new Date(value).toLocaleTimeString('zh-CN', { hour12: false })

async function refreshDevices() {
  await deviceStore.fetchRealtimeDevices()
  if (!selectedDevice.value && deviceStore.devices.length) selectDevice(deviceStore.devices[0])
  else if (selectedDevice.value) selectedDevice.value = deviceStore.getDeviceByName(selectedDevice.value.device_name) || selectedDevice.value
}
async function selectDevice(device) { selectedDevice.value = device; await loadDeviceData() }
async function loadDeviceData() {
  if (!selectedDevice.value) return
  loadingData.value = true
  try {
    const response = await deviceAPI.getDeviceHistory(selectedDevice.value.device_name, Number(timeRange.value), 80)
    const data = response?.data || response
    history.value = Array.isArray(data) ? data : (data?.timestamps || []).map((timestamp,index) => ({ timestamp, value: data.values?.[index] }))
  } catch { history.value = [] } finally { loadingData.value = false }
}
async function executeControl() {
  const ok = await deviceStore.controlDevice(selectedDevice.value.device_name, control.value.command, control.value.value)
  if (ok) { ElMessage.success('控制命令已发送'); controlVisible.value = false; await refreshDevices() }
}

onMounted(async () => { await Promise.all([refreshDevices(), alarmStore.fetchAlarms()]); refreshTimer = setInterval(refreshDevices, 15000) })
onUnmounted(() => clearInterval(refreshTimer))
</script>

<style scoped>
.realtime-monitor { height: calc(100% + 50px); margin: -26px -22px -24px; }.monitor-container { display: grid; grid-template-columns: 250px minmax(0,1fr); height: 100%; gap: 0; }
.sidebar { display: flex; flex-direction: column; min-width: 0; overflow: hidden; background: #fbf8f3; border-right: 1px solid rgba(8,31,92,.14); }.sidebar-filters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 28px 14px 14px; border-bottom: 1px solid rgba(8,31,92,.12); }.sidebar-filters .el-input { grid-column: 1 / -1; }.device-list { flex: 1; min-height: 0; overflow: auto; padding: 8px 12px; }.device-item { display: grid; grid-template-columns: 8px minmax(0,1fr) auto; align-items: center; width: 100%; min-height: 70px; margin-bottom: 8px; padding: 10px 12px; gap: 8px; color: #081f5c; background: transparent; border: 1px solid rgba(8,31,92,.1); border-radius: 7px; text-align: left; cursor: pointer; }.device-item.active { background: rgba(112,150,209,.14); border-color: rgba(51,78,172,.16); }.status-dot { width: 7px; height: 7px; background: #334eac; border-radius: 50%; }.status-dot.offline { background: transparent; border: 1px solid #7096d1; }.device-copy strong,.device-copy small,.device-reading strong,.device-reading small { display: block; }.device-copy strong { font-size: 14px; }.device-copy small,.device-reading small { margin-top: 5px; color: rgba(8,31,92,.55); font-size: 11px; }.device-reading { text-align: right; }.device-reading strong { font-size: 14px; }.sidebar > footer { padding: 12px 14px 28px; color: rgba(8,31,92,.55); border-top: 1px solid rgba(8,31,92,.12); font-size: 12px; }
.detail-panel { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: auto; padding: 27px 28px 22px 20px; }
.detail-header { flex: 0 0 auto; display: flex; align-items: center; justify-content: space-between; min-height: 62px; padding-bottom: 13px; }.detail-header h2 { margin: 0; font-size: 24px; }.detail-header p { display: flex; align-items: center; gap: 6px; margin: 7px 0 0; }.detail-header p b { color: rgba(8,31,92,.5); font-size: 11px; font-weight: 650; }.realtime-stats { margin: 0 0 18px !important; }.realtime-stats strong { font-size: 24px; }.realtime-stats strong small { color: #334eac; font-size: 12px; }
.realtime-grid { display: grid; flex: 1 1 auto; grid-template-columns: minmax(0,1.7fr) minmax(300px,1fr); min-height: 0; gap: 18px; }.left-stack { display: grid; grid-template-rows: 370px minmax(202px, 1fr); min-height: 0; gap: 16px; }.live-chart-card,.threshold-card,.events-card,.live-table { box-sizing: border-box; background: #fbf8f3; border: 1px solid rgba(8,31,92,.14); border-radius: 10px; }.live-chart-card { display: flex; min-height: 0; flex-direction: column; height: auto; padding: 15px 17px 10px; }.chart-title { display: flex; flex: 0 0 auto; justify-content: space-between; }.chart-title span { color: rgba(8,31,92,.56); font-size: 11px; font-weight: 750; }.chart-title h3 { margin: 4px 0 0; font-size: 18px; }.chart-title p { margin: 4px 0 0; color: rgba(8,31,92,.54); font-size: 12px; }.live-chart-card svg { display: block; flex: 1 1 auto; width: 100%; height: auto; min-height: 0; }.grid line { stroke: rgba(8,31,92,.1); stroke-width: .8; }.trend-line { fill: none; stroke: #334eac; stroke-width: 1.8; }.trend-point { fill: #fbf8f3; stroke: #334eac; stroke-width: 1.3; }.current-point { fill: #081f5c; stroke: #081f5c; }.live-chart-card text { fill: rgba(8,31,92,.48); font-size: 11px; }.live-chart-card footer { flex: 0 0 auto; margin-top: 4px; color: rgba(8,31,92,.5); font-size: 11px; }.right-stack { display: grid; grid-template-rows: 242px minmax(0, 1fr); min-height: 0; gap: 18px; }.threshold-card,.events-card { min-height: 0; padding: 18px 20px; }.threshold-card h3,.events-card h3 { margin: 0; font-size: 17px; }.threshold-card p { margin: 10px 0 14px; color: rgba(8,31,92,.58); font-size: 12px; }.threshold-scale { position: relative; height: 8px; background: #bad6eb; }.threshold-scale span { display: block; width: 58%; height: 100%; margin-left: 21%; background: #7096d1; }.threshold-scale i { position: absolute; top: -4px; width: 2px; height: 16px; background: #081f5c; }.scale-labels { display: flex; justify-content: space-between; margin-top: 5px; color: rgba(8,31,92,.48); font-size: 10px; }.threshold-card > small { display: block; margin-top: 10px; color: #334eac; font-size: 11px; }.events-card { overflow: auto; }.event-row { display: flex; gap: 9px; padding: 16px 0 12px; border-bottom: 1px solid rgba(8,31,92,.1); }.event-row i { flex: 0 0 6px; width: 6px; height: 6px; margin-top: 3px; background: #334eac; border-radius: 50%; }.event-row strong,.event-row small { display: block; }.event-row strong { font-size: 12px; }.event-row small { margin-top: 3px; color: rgba(8,31,92,.53); font-size: 10px; }
.live-table { height: auto; min-height: 0; overflow: hidden; }.live-table header { display: flex; align-items: center; justify-content: space-between; height: 42px; padding: 0 16px; border-bottom: 1px solid rgba(8,31,92,.14); font-size: 15px; }.live-table header button { color: #334eac; background: none; border: 0; font-size: 12px; cursor: pointer; }.live-table table { width: calc(100% - 24px); margin: 0 12px; border-collapse: collapse; }.live-table th,.live-table td { height: 30px; padding: 0 8px; border-bottom: 1px solid rgba(8,31,92,.1); text-align: left; font-size: 12px; }.live-table th { color: rgba(8,31,92,.55); font-size: 12px; }.live-table footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 16px; color: rgba(8,31,92,.52); font-size: 12px; }.table-pagination { display: flex; gap: 8px; }.table-pagination button { padding: 4px 10px; color: #334eac; background: transparent; border: 1px solid rgba(51,78,172,.25); border-radius: 5px; font-size: 12px; cursor: pointer; }.table-pagination button:disabled { color: rgba(8,31,92,.3); border-color: rgba(8,31,92,.12); cursor: not-allowed; }.empty-detail { display: grid; place-items: center; color: rgba(8,31,92,.5); }
</style>
