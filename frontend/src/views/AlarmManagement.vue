<template>
  <div class="page">
    <section class="kpi-grid" aria-label="告警统计">
      <div class="card stat" data-status="alarm"><span class="kpi-label">严重 · 未确认</span><span class="kpi-value">{{ open.filter((a) => alarmLevel(a) === 'alarm').length }}</span></div>
      <div class="card stat" data-status="warn"><span class="kpi-label">预警 · 未确认</span><span class="kpi-value">{{ open.filter((a) => alarmLevel(a) === 'warn').length }}</span></div>
      <div class="card stat"><span class="kpi-label">今日已确认</span><span class="kpi-value">{{ ackedToday }}</span></div>
      <div class="card stat"><span class="kpi-label">{{ rangeLabel }}告警总数</span><span class="kpi-value">{{ alarmStore.alarms.length }}</span></div>
    </section>

    <div class="toolbar">
      <div class="segmented" role="group" aria-label="告警状态">
        <button v-for="t in tabs" :key="t.id" type="button" :aria-pressed="tab === t.id" @click="tab = t.id">{{ t.label }} <span class="mono">{{ t.count }}</span></button>
      </div>
      <div class="toolbar-right">
        <el-select v-model="level" aria-label="级别" style="width: 130px"><el-option label="全部级别" value="all" /><el-option label="严重" value="alarm" /><el-option label="预警" value="warn" /></el-select>
        <el-select v-model="hours" aria-label="时间范围" style="width: 130px"><el-option v-for="r in ranges" :key="r.h" :label="r.label" :value="r.h" /></el-select>
        <el-button :disabled="!open.length" :loading="busy" @click="ackAll">全部确认</el-button>
      </div>
    </div>

    <div class="row align-start">
      <section class="grow-3 list" aria-label="告警列表">
        <article v-for="a in list" :key="a.id" class="alarm card" :data-status="a.acknowledged ? 'done' : alarmLevel(a)">
          <span class="badge" :data-status="a.acknowledged ? 'done' : alarmLevel(a)">{{ a.acknowledged ? '已确认' : alarmLevel(a) === 'alarm' ? '严重' : '预警' }}</span>
          <div class="alarm-copy">
            <h2>{{ a.message }}</h2>
            <div class="mono muted small">{{ tagOf(a.device_name) }} · {{ deviceOf(a.device_name)?.zone || a.device_name }} · {{ fmtTime(a.timestamp, true) }}</div>
            <div v-if="a.acknowledged" class="muted small">由 {{ a.ack_user || '—' }} 于 {{ fmtTime(a.ack_time, true) }} 确认</div>
          </div>
          <div class="alarm-value">
            <span class="mono val" :data-status="a.acknowledged ? '' : alarmLevel(a)">{{ fmtNum(a.value) }} {{ deviceOf(a.device_name)?.unit || '' }}</span>
            <span class="mono muted small">阈值 {{ thresholdText(a) }}</span>
          </div>
          <div class="alarm-actions">
            <router-link to="/3d-scene" class="ghost-btn">三维定位</router-link>
            <el-button v-if="!a.acknowledged" type="primary" @click="ack(a)">确认</el-button>
          </div>
        </article>
        <div v-if="!list.length" class="card empty">{{ tab === 'open' ? '没有未确认的告警' : '该范围内没有告警记录' }}</div>
      </section>

      <aside class="grow-1 side">
        <section class="card" aria-labelledby="h-by">
          <h2 id="h-by" class="side-title">{{ rangeLabel }} · 按设备</h2>
          <div v-for="b in byDevice" :key="b.name" class="bar-row">
            <span class="mono small">{{ b.tag }}</span>
            <span class="bar"><span :style="{ width: b.pct + '%' }" :data-status="b.level"></span></span>
            <span class="mono small">{{ b.count }}</span>
          </div>
          <div v-if="!byDevice.length" class="muted small">暂无数据</div>
        </section>
        <section class="card" aria-labelledby="h-tl">
          <h2 id="h-tl" class="side-title">近 24 小时时间轴</h2>
          <div class="timeline" role="img" :aria-label="`近 24 小时共 ${last24.length} 条告警`">
            <span v-for="t in last24" :key="t.id" :style="{ left: t.x + '%' }" :data-status="t.level" :title="`${tagOf(t.device_name)} ${fmtTime(t.timestamp)}`"></span>
          </div>
          <div class="timeline-axis mono muted small"><span>24 小时前</span><span>12 小时前</span><span>现在</span></div>
          <router-link class="link" to="/prediction">在预测分析中查看趋势 →</router-link>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useAlarmStore } from '../stores/alarm'
import { alarmLevel, deviceOf, fmtTime, tagOf } from '../composables/useLine'

const alarmStore = useAlarmStore()
const ranges = [{ h: 24, label: '近 24 小时' }, { h: 168, label: '近 7 天' }, { h: 720, label: '近 30 天' }]
const hours = ref(168)
const rangeLabel = computed(() => ranges.find((r) => r.h === hours.value).label)
const tab = ref('open')
const level = ref('all')
const busy = ref(false)

const load = () => alarmStore.fetchAlarms({ hours: hours.value, limit: 1000 })
watch(hours, load)
onMounted(load)

const open = computed(() => alarmStore.alarms.filter((a) => !a.acknowledged))
const tabs = computed(() => [
  { id: 'open', label: '未确认', count: open.value.length },
  { id: 'done', label: '已确认', count: alarmStore.alarms.length - open.value.length },
  { id: 'all', label: '全部', count: alarmStore.alarms.length }
])
const list = computed(() => alarmStore.alarms
  .filter((a) => (tab.value === 'all' || (tab.value === 'open') === !a.acknowledged) && (level.value === 'all' || alarmLevel(a) === level.value))
  .sort((a, b) => (alarmLevel(a) === 'alarm' ? 0 : 1) - (alarmLevel(b) === 'alarm' ? 0 : 1) || new Date(b.timestamp) - new Date(a.timestamp))
  .slice(0, 200))

const ackedToday = computed(() => {
  const today = new Date().toDateString()
  return alarmStore.alarms.filter((a) => a.acknowledged && a.ack_time && new Date(a.ack_time).toDateString() === today).length
})

const byDevice = computed(() => {
  const counts = {}
  for (const a of alarmStore.alarms) (counts[a.device_name] ||= { name: a.device_name, count: 0, level: 'warn' }).count++
  for (const a of alarmStore.alarms) if (alarmLevel(a) === 'alarm') counts[a.device_name].level = 'alarm'
  const list = Object.values(counts).sort((a, b) => b.count - a.count).slice(0, 8)
  const max = list[0]?.count || 1
  return list.map((b) => ({ ...b, tag: tagOf(b.name), pct: (b.count / max) * 100 }))
})

const last24 = computed(() => {
  const now = Date.now()
  return alarmStore.alarms
    .map((a) => ({ ...a, level: alarmLevel(a), x: 100 - ((now - new Date(a.timestamp).getTime()) / 864e5) * 100 }))
    .filter((a) => a.x >= 0 && a.x <= 100)
})

const fmtNum = (v) => (v == null ? '—' : Math.abs(v) >= 100 ? Math.round(v).toLocaleString('en-US') : Number(v).toFixed(2))
const thresholdText = (a) => {
  const d = deviceOf(a.device_name)
  if (a.threshold != null) return fmtNum(a.threshold)
  return d?.alarm ? `${d.alarm[0]} – ${d.alarm[1]}` : '—'
}

async function ack(a) {
  if (await alarmStore.acknowledgeAlarm(a.id)) ElMessage.success('告警已确认')
}
async function ackAll() {
  busy.value = true
  const n = await alarmStore.acknowledgeMultipleAlarms(open.value.map((a) => a.id))
  busy.value = false
  ElMessage.success(`已确认 ${n} 条告警`)
}
</script>

<style scoped>
.stat { gap: 6px; }
.stat[data-status="alarm"] { background: var(--alarm-soft); border-color: var(--alarm-line); }
.stat[data-status="alarm"] .kpi-label, .stat[data-status="alarm"] .kpi-value { color: var(--alarm-fg); }
.stat[data-status="warn"] { background: var(--warn-soft); border-color: var(--warn-line); }
.stat[data-status="warn"] .kpi-label, .stat[data-status="warn"] .kpi-value { color: var(--warn-fg); }
.toolbar, .toolbar-right { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; }
.align-start { align-items: flex-start; }
.list { display: flex; flex-direction: column; gap: 10px; }
.alarm { flex-direction: row; flex-wrap: wrap; align-items: center; gap: 16px; padding: 16px 18px; }
.alarm[data-status="alarm"] { border-color: var(--alarm-line); }
.alarm[data-status="warn"] { border-color: var(--warn-line); }
.alarm[data-status="done"] { opacity: .8; }
.alarm-copy { display: flex; flex: 1 1 260px; flex-direction: column; gap: 4px; min-width: 0; }
.alarm-copy h2 { margin: 0; font-size: 15px; font-weight: 600; }
.alarm-value { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; min-width: 110px; }
.alarm-value .val { font-size: 18px; font-weight: 600; }
.alarm-actions { display: flex; gap: 8px; }
.side { display: flex; flex-direction: column; gap: 16px; }
.side-title { margin: 0; font-size: 15px; font-weight: 700; }
.bar-row { display: grid; grid-template-columns: 64px minmax(0, 1fr) 32px; align-items: center; gap: 10px; }
.bar-row .mono:last-child { text-align: right; }
.bar { height: 10px; overflow: hidden; background: var(--quiet); border-radius: 5px; }
.bar span { display: block; height: 100%; background: var(--warn); border-radius: 5px; }
.bar span[data-status="alarm"] { background: var(--alarm); }
.timeline { position: relative; height: 44px; border-bottom: 2px solid var(--grid); }
.timeline span { position: absolute; bottom: 0; width: 3px; height: 28px; background: var(--warn); border-radius: 2px; transform: translateX(-50%); }
.timeline span[data-status="alarm"] { height: 40px; background: var(--alarm); }
.timeline-axis { display: flex; justify-content: space-between; }
</style>
