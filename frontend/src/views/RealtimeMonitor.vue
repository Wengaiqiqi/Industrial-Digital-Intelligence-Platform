<template>
  <div class="page">
    <div class="toolbar">
      <div class="chips" role="group" aria-label="设备类型筛选">
        <button v-for="k in kinds" :key="k.name" type="button" class="chip" :aria-pressed="kind === k.name" @click="kind = k.name">
          {{ k.name }}<span class="mono muted">{{ k.count }}</span>
        </button>
      </div>
      <div class="segmented" role="group" aria-label="时间窗">
        <button v-for="w in windows" :key="w.min" type="button" :aria-pressed="windowMin === w.min" @click="windowMin = w.min">{{ w.label }}</button>
      </div>
    </div>

    <div class="row">
      <section class="card grow-3" aria-labelledby="h-live">
        <div class="card-head">
          <div>
            <h2 id="h-live">{{ current ? `${current.tag} ${current.name}` : '选择一个点位' }}</h2>
            <div class="sub mono">{{ current ? [current.mqtt].flat().join(' · ') : '' }} · 近 {{ windowLabel }} · {{ series.length }} 个采样</div>
          </div>
          <div class="legend-row"><span><i></i>实测值</span><span v-if="current?.alarm"><i class="limit"></i>告警阈值</span></div>
        </div>
        <div ref="chartEl" class="live-chart" role="img" :aria-label="`${current?.name || ''} 实时曲线`"></div>
      </section>

      <section v-if="current" class="card grow-1" aria-label="当前读数">
        <div class="card-head"><span class="kpi-label">当前值</span><span class="badge" :data-status="current.status">{{ STATUS_LABEL[current.status] }}</span></div>
        <div class="big mono val" :data-status="current.status">{{ current.value }}</div>
        <div class="small">{{ limitText }}</div>
        <dl class="stats">
          <div><dt>最低</dt><dd class="mono">{{ stat.min }}</dd></div>
          <div><dt>平均</dt><dd class="mono">{{ stat.avg }}</dd></div>
          <div><dt>最高</dt><dd class="mono">{{ stat.max }}</dd></div>
        </dl>
        <router-link to="/3d-scene"><el-button style="width: 100%">在三维场景中定位</el-button></router-link>
      </section>
    </div>

    <section class="gauges" aria-label="点位仪表">
      <button v-for="g in gauges" :key="g.id" type="button" class="gauge" :data-status="g.status" :aria-pressed="g.id === selectedId" @click="selectedId = g.id">
        <span class="gauge-top"><span class="mono muted">{{ g.tag }}</span><span class="dot" :data-status="g.status"></span></span>
        <span class="small">{{ g.name }}</span>
        <svg viewBox="0 0 120 70" aria-hidden="true">
          <path class="track" d="M10 62A50 50 0 0 1 110 62" />
          <path class="arc" :data-status="g.status" d="M10 62A50 50 0 0 1 110 62" :stroke-dasharray="`${g.dash} 157`" />
          <text x="60" y="56" text-anchor="middle">{{ g.short }}</text>
        </svg>
        <span class="gauge-range mono muted"><span>{{ g.min }}</span><span>{{ g.unit }}</span><span>{{ g.max }}</span></span>
      </button>
    </section>

    <section class="card flush" aria-labelledby="h-stream">
      <div class="card-head"><h2 id="h-stream">数据流</h2><span class="muted small">最新在上 · 最近 40 条</span></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>时间</th><th>位号</th><th>MQTT 点位</th><th class="num">数值</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="s in stream" :key="s.key">
              <td class="mono muted">{{ s.time }}</td><td class="mono">{{ s.tag }}</td><td class="mono muted">{{ s.topic }}</td>
              <td class="num val" :data-status="s.status">{{ s.value }}</td>
              <td><span class="badge" :data-status="s.status">{{ STATUS_LABEL[s.status] }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-if="!stream.length" class="empty">等待实时数据…</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { deviceAPI } from '../api'
import { useLine } from '../composables/useLine'
import { useChart, baseOption } from '../composables/useChart'
import { STATUS_LABEL } from '../utils/plantLayout'

const { rows, stream } = useLine()
const windows = [{ min: 5, label: '5 分钟' }, { min: 15, label: '15 分钟' }, { min: 60, label: '1 小时' }]
const windowMin = ref(5)
const windowLabel = computed(() => windows.find((w) => w.min === windowMin.value).label)
const kind = ref('全部')
const selectedId = ref('TT201')

const kinds = computed(() => {
  const counts = {}
  rows.value.forEach((r) => { counts[r.kind] = (counts[r.kind] || 0) + 1 })
  return [{ name: '全部', count: rows.value.length }, ...Object.entries(counts).map(([name, count]) => ({ name, count }))]
})
const visible = computed(() => rows.value.filter((r) => kind.value === '全部' || r.kind === kind.value))
const current = computed(() => rows.value.find((r) => r.id === selectedId.value) || visible.value[0])

// 选中点位时先补一段历史，之后由实时轮询续上
const seed = ref([])
watch(() => current.value?.id, async () => {
  seed.value = []
  const name = [current.value?.mqtt].flat()[0]
  if (!name) return
  try {
    const res = await deviceAPI.getDeviceHistory(name, 1, 2000)
    seed.value = (res.data || []).map((d) => ({ t: new Date(d.timestamp).getTime(), v: d.value }))
  } catch { /* 无历史时只显示实时数据 */ }
}, { immediate: true })

const series = computed(() => {
  const since = Date.now() - windowMin.value * 60000
  const live = current.value?.history || []
  const firstLive = live[0]?.t ?? Infinity
  return [...seed.value.filter((p) => p.t < firstLive), ...live].filter((p) => p.t >= since).sort((a, b) => a.t - b.t)
})

const fmt = (v) => (v == null ? '—' : Math.abs(v) >= 100 ? Math.round(v).toLocaleString('en-US') : v.toFixed(2))
const stat = computed(() => {
  const vs = series.value.map((p) => p.v)
  if (!vs.length) return { min: '—', avg: '—', max: '—' }
  return { min: fmt(Math.min(...vs)), avg: fmt(vs.reduce((a, b) => a + b, 0) / vs.length), max: fmt(Math.max(...vs)) }
})

const limitText = computed(() => {
  const c = current.value
  if (!c || c.num == null) return '暂无读数'
  if (!c.alarm) return `量程 ${c.range ? c.range.join(' – ') : '—'} ${c.unit || ''}`
  const [min, max] = c.alarm
  if (c.num > max) return `已超上限 ${max} ${c.unit}，高出 ${fmt(c.num - max)}`
  if (c.num < min) return `已低于下限 ${min} ${c.unit}，低 ${fmt(min - c.num)}`
  return `距上限 ${max} ${c.unit} 还有 ${fmt(max - c.num)}，距下限 ${fmt(c.num - min)}`
})

const gauges = computed(() => visible.value.map((r) => {
  const [min, max] = r.range || [0, 1]
  const frac = r.num == null ? 0 : Math.max(0, Math.min(1, (r.num - min) / (max - min || 1)))
  return { id: r.id, tag: r.tag, name: r.name, status: r.status, unit: r.unit ?? r.reading?.unit ?? '', min, max, dash: (157 * frac).toFixed(1), short: r.num == null ? '—' : r.special ? r.value : fmt(r.num) }
}))

const chartEl = ref(null)
useChart(chartEl, (c) => {
  const cur = current.value
  const color = c(cur?.status === 'alarm' ? '--alarm' : cur?.status === 'warn' ? '--warn' : '--data')
  return baseOption(c, {
    series: [{
      type: 'line', showSymbol: false, data: series.value.map((p) => [p.t, p.v]), lineStyle: { color, width: 2 }, itemStyle: { color },
      areaStyle: { color, opacity: 0.08 },
      markLine: cur?.alarm ? { symbol: 'none', silent: true, label: { color: c('--muted'), fontSize: 11 }, lineStyle: { color: c('--warn'), type: 'dashed' }, data: cur.alarm.map((y) => ({ yAxis: y })) } : undefined
    }]
  })
}, series)
</script>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
.live-chart { height: 280px; }
.legend-row .limit { height: 0; background: none; border-top: 2px dashed var(--warn); }
.big { font-size: 48px; font-weight: 600; line-height: 1; }
.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 0; padding-top: 14px; border-top: 1px solid var(--grid); }
.stats dt { color: var(--muted); font-size: 12px; }
.stats dd { margin: 4px 0 0; font-size: 18px; }
.gauges { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; }
.gauge { display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; color: var(--ink); background: var(--paper-soft); border: 1px solid var(--grid); border-radius: var(--panel-radius); cursor: pointer; text-align: left; }
.gauge[data-status="warn"] { border-color: var(--warn-line); }
.gauge[data-status="alarm"] { border-color: var(--alarm-line); }
.gauge[aria-pressed="true"] { outline: 2px solid var(--data); outline-offset: -1px; }
.gauge-top, .gauge-range { display: flex; align-items: center; justify-content: space-between; font-size: 11px; }
.gauge svg { width: 100%; height: 80px; }
.gauge .track { fill: none; stroke: var(--grid); stroke-width: 9; stroke-linecap: round; }
.gauge .arc { fill: none; stroke: var(--data); stroke-width: 9; stroke-linecap: round; }
.gauge .arc[data-status="warn"] { stroke: var(--warn); }
.gauge .arc[data-status="alarm"] { stroke: var(--alarm); }
.gauge .arc[data-status="offline"] { stroke: var(--muted); }
.gauge text { fill: var(--ink); font: 600 18px var(--font-mono); }
</style>
