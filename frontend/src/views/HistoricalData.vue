<template>
  <div class="page">
    <form class="card query" aria-label="查询条件" @submit.prevent="query">
      <div class="field">
        <span class="muted small">快捷范围</span>
        <div class="segmented" role="group" aria-label="快捷范围">
          <button v-for="p in presets" :key="p.h" type="button" :aria-pressed="preset === p.h" @click="usePreset(p.h)">{{ p.label }}</button>
        </div>
      </div>
      <label class="field">
        <span class="muted small">时间范围</span>
        <el-date-picker v-model="range" type="datetimerange" range-separator="至" start-placeholder="开始" end-placeholder="结束" :clearable="false" @change="preset = 0" />
      </label>
      <label class="field grow">
        <span class="muted small">设备（已选 {{ picked.length }}）</span>
        <el-select v-model="picked" multiple collapse-tags collapse-tags-tooltip :max-collapse-tags="4" placeholder="选择要对比的设备" aria-label="选择设备">
          <el-option v-for="o in deviceOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </label>
      <div class="actions">
        <el-button type="primary" native-type="submit" :loading="loading">查询</el-button>
        <el-button :loading="exporting" @click="exportCsv">导出 CSV</el-button>
      </div>
    </form>

    <section class="card" aria-labelledby="h-trend">
      <div class="card-head">
        <h2 id="h-trend">趋势 · {{ rangeText }}</h2>
        <span class="muted small">各设备单位不同，按行分开绘制，时间轴共用；虚线为告警阈值</span>
      </div>
      <div v-for="s in seriesList" :key="s.name" class="multiple">
        <div class="multiple-label">
          <span class="mono">{{ s.tag }}</span>
          <span class="small">{{ s.title }}</span>
          <span class="mono muted small">{{ s.unit }}<template v-if="s.alarm"> · 阈值 {{ s.alarm.join(' – ') }}</template></span>
        </div>
        <MiniChart :points="s.points" :alarm="s.alarm" :range="chartRange" />
      </div>
      <div v-if="!seriesList.length" class="empty">选择设备后点击查询</div>
    </section>

    <section class="card flush" aria-labelledby="h-stats">
      <div class="card-head"><h2 id="h-stats">统计摘要</h2><span class="mono muted small">共 {{ totalRecords.toLocaleString('en-US') }} 条原始记录</span></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>设备</th><th class="num">采样数</th><th class="num">最小</th><th class="num">平均</th><th class="num">最大</th><th class="num">最新</th><th class="num">越限次数</th></tr></thead>
          <tbody>
            <tr v-for="t in stats" :key="t.name">
              <td><div class="cell-title"><span class="mono">{{ t.tag }}</span><span>{{ t.title }}</span></div></td>
              <td class="num">{{ t.recordCount.toLocaleString('en-US') }}</td>
              <td class="num">{{ fmt(t.minValue) }}</td>
              <td class="num">{{ fmt(t.avgValue) }}</td>
              <td class="num val" :data-status="t.overMax ? 'alarm' : ''">{{ fmt(t.maxValue) }}</td>
              <td class="num">{{ fmt(t.lastValue) }} <span class="muted small">{{ t.unit }}</span></td>
              <td class="num val" :data-status="t.over ? 'warn' : ''">{{ t.over ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!stats.length" class="empty">该时间范围内没有数据</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceAPI, historicalAPI } from '../api'
import { useChart, baseOption } from '../composables/useChart'
import { DEVICES } from '../utils/plantLayout'
import { deviceOf, tagOf } from '../composables/useLine'

// 小多图：每台设备一行，共用时间轴
const MiniChart = defineComponent({
  props: { points: Array, alarm: Array, range: Array },
  setup(props) {
    const el = ref(null)
    useChart(el, (c) => baseOption(c, {
      grid: { left: 44, right: 12, top: 8, bottom: 22 },
      xAxis: { type: 'time', min: props.range[0], max: props.range[1], axisLine: { lineStyle: { color: c('--grid') } }, axisTick: { show: false }, axisLabel: { color: c('--muted'), fontSize: 10, hideOverlap: true }, splitLine: { show: false } },
      series: [{
        type: 'line', showSymbol: false, data: props.points, lineStyle: { color: c('--data'), width: 1.6 }, itemStyle: { color: c('--data') }, areaStyle: { color: c('--data'), opacity: 0.08 },
        markLine: props.alarm ? { symbol: 'none', silent: true, label: { show: false }, lineStyle: { color: c('--warn'), type: 'dashed' }, data: props.alarm.map((y) => ({ yAxis: y })) } : undefined
      }]
    }), () => props.points)
    return () => h('div', { ref: el, style: 'height: 110px', role: 'img', 'aria-label': '趋势图' })
  }
})

const presets = [{ h: 24, label: '24 小时' }, { h: 168, label: '7 天' }, { h: 720, label: '30 天' }]
const preset = ref(24)
const range = ref([new Date(Date.now() - 864e5), new Date()])
const picked = ref(['temperature_sensor_2', 'pressure_sensor_1', 'flow_meter_1'])
const loading = ref(false)
const exporting = ref(false)
const seriesList = ref([])
const stats = ref([])
const totalRecords = ref(0)
const chartRange = computed(() => range.value.map((d) => new Date(d).getTime()))

const deviceOptions = computed(() => DEVICES.flatMap((d) => [d.mqtt].flat().map((m) => ({ value: m, label: `${d.tag} ${d.name}${Array.isArray(d.mqtt) ? ` (${m})` : ''}` }))))
const titleOf = (name) => deviceOf(name)?.name || name
const rangeText = computed(() => range.value.map((d) => new Date(d).toLocaleString('zh-CN', { hour12: false, month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })).join(' – '))
const fmt = (v) => (v == null ? '—' : Math.abs(v) >= 100 ? Math.round(v).toLocaleString('en-US') : Number(v).toFixed(2))
// 后端按本地时间解析，不带时区后缀
const localIso = (d) => { const x = new Date(d); return new Date(x.getTime() - x.getTimezoneOffset() * 60000).toISOString().slice(0, 19) }

function usePreset(hours) {
  preset.value = hours
  range.value = [new Date(Date.now() - hours * 36e5), new Date()]
  query()
}

async function query() {
  loading.value = true
  const [start, end] = chartRange.value
  const hours = Math.ceil((Date.now() - start) / 36e5)
  try {
    const [hist, summary] = await Promise.all([
      Promise.all(picked.value.map(async (name) => {
        try {
          const res = await deviceAPI.getDeviceHistory(name, hours, 5000)
          const points = (res.data || []).map((d) => [new Date(d.timestamp).getTime(), d.value]).filter(([t]) => t >= start && t <= end).sort((a, b) => a[0] - b[0])
          const dev = deviceOf(name)
          return { name, tag: tagOf(name), title: titleOf(name), unit: dev?.unit || res.data?.[0]?.unit || '', alarm: dev?.alarm, points }
        } catch { return null }
      })),
      historicalAPI.getHistoricalData(localIso(start), localIso(end)).catch(() => ({ data: [] }))
    ])
    seriesList.value = hist.filter(Boolean)
    totalRecords.value = summary.total_records || 0
    stats.value = (summary.data || []).map((s) => {
      const dev = deviceOf(s.name)
      const series = seriesList.value.find((x) => x.name === s.name)
      const over = dev?.alarm && series ? series.points.filter(([, v]) => v < dev.alarm[0] || v > dev.alarm[1]).length : null
      return { ...s, tag: tagOf(s.name), title: titleOf(s.name), over, overMax: dev?.alarm && s.maxValue > dev.alarm[1] }
    }).sort((a, b) => a.tag.localeCompare(b.tag))
  } finally {
    loading.value = false
  }
}

async function exportCsv() {
  exporting.value = true
  try {
    const [start, end] = chartRange.value
    const blob = await historicalAPI.exportHistoricalData(localIso(start), localIso(end))
    const url = URL.createObjectURL(new Blob([blob], { type: 'text/csv' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: `historical_data_${localIso(start).slice(0, 10)}_${localIso(end).slice(0, 10)}.csv` })
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

onMounted(query)
</script>

<style scoped>
.query { flex-direction: row; flex-wrap: wrap; align-items: flex-end; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field.grow { flex: 1 1 280px; }
.actions { display: flex; gap: 8px; }
.multiple { display: grid; grid-template-columns: 130px minmax(0, 1fr); align-items: center; gap: 12px; padding: 6px 0; border-top: 1px solid var(--grid); }
.multiple-label { display: flex; flex-direction: column; gap: 2px; }
</style>
