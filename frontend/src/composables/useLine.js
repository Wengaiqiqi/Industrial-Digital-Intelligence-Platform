import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { deviceAPI } from '../api'
import { DEVICES, deviceStatus, formatValue, readingFor } from '../utils/plantLayout'

// 各页面共用一份实时数据：有页面在用时每 2 秒拉取一次 /api/devices/realtime
const raw = ref({})
const readings = reactive({})
const history = reactive({})
const stream = ref([])
const lastPoll = ref(null)
let timer = null
let users = 0

const KIND_BY_TYPE = { sensor: '传感器', actuator: '执行器', indicator: '指示灯', io: '数字 I/O' }
const covered = new Set(DEVICES.flatMap((d) => [d.mqtt].flat()))

// 布局外的设备（在设备管理里新增的）按通用规则展示
function extraDefs() {
  return Object.keys(raw.value).filter((k) => !covered.has(k)).map((k) => ({
    id: k, tag: k, name: k, kind: KIND_BY_TYPE[raw.value[k].type] || raw.value[k].type || '设备', zone: '未分区', mqtt: k, extra: true
  }))
}

async function poll() {
  try {
    const res = await deviceAPI.getRealtimeDevices()
    const data = res.data || {}
    raw.value = Array.isArray(data)
      ? Object.fromEntries(data.map((d) => [d.device_name, { value: d.value, unit: d.unit, type: d.type, status: d.status, timestamp: d.timestamp }]))
      : data
  } catch {
    // 后端不可用时保留旧读数，超时后自然显示为离线
  }
  const now = Date.now()
  const fresh = []
  for (const def of [...DEVICES, ...extraDefs()]) {
    const r = readingFor(def, raw.value, now)
    if (!r || r.timestamp === readings[def.id]?.timestamp) continue
    readings[def.id] = r
    const h = (history[def.id] ||= [])
    h.push({ t: now, v: r.value })
    if (h.length > 150) h.shift()
    fresh.push({ def, r })
  }
  const time = new Date(now).toLocaleTimeString('zh-CN', { hour12: false })
  stream.value = [...fresh.map(({ def, r }) => ({ key: `${now}-${def.id}`, time, tag: def.tag, topic: [def.mqtt].flat().join(' · '), value: formatValue(def, r), status: deviceStatus(def, r) })), ...stream.value].slice(0, 40)
  lastPoll.value = now
}

const rows = computed(() => {
  lastPoll.value // 每次拉取后重新计算，离线判断依赖当前时间
  return [...DEVICES, ...extraDefs()].map((def) => {
    const reading = readings[def.id] || null
    return { ...def, reading, num: reading?.value ?? null, status: deviceStatus(def, reading), value: formatValue(def, reading), history: history[def.id] || [] }
  })
})

export function useLine() {
  onMounted(() => {
    if (users++ === 0) { poll(); timer = setInterval(poll, 2000) }
  })
  onBeforeUnmount(() => {
    if (--users === 0) { clearInterval(timer); timer = null }
  })
  return { rows, stream, lastPoll, refresh: poll }
}

export const STATUS_ORDER = { alarm: 0, warn: 1, offline: 2, ok: 3 }

// 告警记录的级别：critical / high / error 视为严重，其余为预警
export const alarmLevel = (a) => (['critical', 'high', 'error'].includes(a.severity) ? 'alarm' : 'warn')

export const fmtTime = (ts, withDate = false) => {
  if (!ts) return '—'
  const d = new Date(ts)
  return withDate
    ? d.toLocaleString('zh-CN', { hour12: false, month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : d.toLocaleTimeString('zh-CN', { hour12: false })
}

export const tagOf = (mqttName) => DEVICES.find((d) => [d.mqtt].flat().includes(mqttName))?.tag || mqttName
export const deviceOf = (mqttName) => DEVICES.find((d) => [d.mqtt].flat().includes(mqttName))
