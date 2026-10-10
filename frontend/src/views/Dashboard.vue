<template>
  <div class="page">
    <section class="kpi-grid" aria-label="关键指标">
      <div class="card">
        <div class="kpi-label">在线设备</div>
        <div class="kpi-value">{{ onlineCount }}<small>/ {{ rows.length }}</small></div>
        <div class="segments"><span v-for="r in rows" :key="r.id" :data-status="r.status" :title="r.tag"></span></div>
        <div class="muted small">{{ onlineCount === rows.length ? '全部在线' : `${rows.length - onlineCount} 台超过 15 秒未上报` }}</div>
      </div>
      <div class="card">
        <div class="kpi-label">未确认告警</div>
        <div class="kpi-value" :class="{ hot: openAlarms.length }">{{ openAlarms.length }}<small>{{ severeCount }} 严重 · {{ openAlarms.length - severeCount }} 预警</small></div>
        <div class="split"><span :style="{ flex: severeCount }" data-status="alarm"></span><span :style="{ flex: openAlarms.length - severeCount }" data-status="warn"></span></div>
        <router-link class="link" to="/alarms">前往告警中心 →</router-link>
      </div>
      <div class="card">
        <div class="kpi-label">当前异常点位</div>
        <div class="kpi-value">{{ abnormal.length }}<small>/ {{ rows.length }}</small></div>
        <div class="muted small">{{ abnormal.length ? abnormal.map((r) => r.tag).join('、') : '所有点位在阈值范围内' }}</div>
        <router-link class="link" to="/3d-scene">在三维场景中查看 →</router-link>
      </div>
      <div class="card">
        <div class="kpi-label">数据刷新</div>
        <div class="kpi-value">{{ lastPoll ? fmtTime(lastPoll) : '—' }}</div>
        <div class="muted small">每 2 秒拉取一次实时数据</div>
        <router-link class="link" to="/prediction">异常检测与预测分析 →</router-link>
      </div>
    </section>

    <div class="row">
      <section class="card grow-2" aria-labelledby="h-zones">
        <div class="card-head">
          <div><h2 id="h-zones">产线态势</h2><div class="sub">按区域汇总点位状态</div></div>
          <router-link to="/3d-scene"><el-button type="primary">进入三维场景</el-button></router-link>
        </div>
        <div class="zones">
          <div v-for="z in zoneSummary" :key="z.name" class="zone" :data-status="z.status">
            <div class="zone-top"><strong>{{ z.name }}</strong><span class="badge" :data-status="z.status">{{ STATUS_LABEL[z.status] }}</span></div>
            <div v-for="r in z.rows" :key="r.id" class="zone-row">
              <span class="dot" :data-status="r.status"></span>
              <span class="mono">{{ r.tag }}</span>
              <span class="mono val" :data-status="r.status">{{ r.value }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="card flush grow-1" aria-labelledby="h-queue">
        <div class="card-head"><h2 id="h-queue">告警队列</h2><router-link class="link" to="/alarms">全部告警</router-link></div>
        <div v-if="!openAlarms.length" class="empty">没有未确认的告警</div>
        <div v-for="a in openAlarms.slice(0, 5)" :key="a.id" class="queue-item">
          <span class="badge" :data-status="alarmLevel(a)">{{ alarmLevel(a) === 'alarm' ? '严重' : '预警' }}</span>
          <div class="queue-copy">
            <div>{{ a.message }}</div>
            <div class="mono muted small">{{ tagOf(a.device_name) }} · {{ fmtTime(a.timestamp, true) }}</div>
          </div>
          <button type="button" class="ghost-btn" @click="ack(a)">确认</button>
        </div>
      </section>
    </div>

    <div class="row">
      <section class="card grow-3" aria-labelledby="h-trend">
        <div class="card-head">
          <h2 id="h-trend">关键参数 · 近 24 小时</h2>
          <div class="legend-row">
            <span><i></i>反应釜温度 TT-201 (°C)</span>
            <span><i class="second"></i>泵出口压力 PT-101 (bar)</span>
            <span><i class="limit"></i>温度上限 85 °C</span>
          </div>
        </div>
        <div ref="trendEl" class="trend" role="img" aria-label="近 24 小时反应釜温度与泵出口压力趋势"></div>
        <div v-if="!trend.t.length && !trend.p.length" class="empty">近 24 小时暂无历史数据</div>
      </section>

      <section class="card grow-2" aria-labelledby="h-matrix">
        <div class="card-head"><h2 id="h-matrix">设备矩阵</h2><router-link class="link" to="/devices">设备管理</router-link></div>
        <div class="matrix">
          <div v-for="r in rows" :key="r.id" class="tile" :data-status="r.status">
            <div class="tile-top"><span class="mono muted">{{ r.tag }}</span><span class="dot" :data-status="r.status"></span></div>
            <div class="small">{{ r.name }}</div>
            <div class="mono tile-val val" :data-status="r.status">{{ r.value }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceAPI } from '../api'
import { useAlarmStore } from '../stores/alarm'
import { useLine, alarmLevel, fmtTime, tagOf, STATUS_ORDER } from '../composables/useLine'
import { useChart, baseOption } from '../composables/useChart'
import { ZONES, STATUS_LABEL } from '../utils/plantLayout'

const { rows, lastPoll } = useLine()
const alarmStore = useAlarmStore()

const onlineCount = computed(() => rows.value.filter((r) => r.status !== 'offline').length)
const abnormal = computed(() => rows.value.filter((r) => r.status === 'warn' || r.status === 'alarm'))
const openAlarms = computed(() => alarmStore.alarms.filter((a) => !a.acknowledged))
const severeCount = computed(() => openAlarms.value.filter((a) => alarmLevel(a) === 'alarm').length)

const worst = (list) => list.reduce((w, r) => (STATUS_ORDER[r.status] < STATUS_ORDER[w] ? r.status : w), 'ok')
const zoneSummary = computed(() => [...ZONES.map((z) => z.name), '未分区']
  .map((name) => ({ name, rows: rows.value.filter((r) => r.zone === name) }))
  .filter((z) => z.rows.length)
  .map((z) => ({ ...z, status: worst(z.rows) })))

async function ack(a) {
  if (await alarmStore.acknowledgeAlarm(a.id)) ElMessage.success('告警已确认')
}

const trendEl = ref(null)
const trend = reactive({ t: [], p: [] })
async function loadTrend() {
  const get = async (name) => {
    try {
      const res = await deviceAPI.getDeviceHistory(name, 24, 2000)
      return (res.data || []).map((d) => [new Date(d.timestamp).getTime(), d.value]).sort((a, b) => a[0] - b[0])
    } catch { return [] }
  }
  ;[trend.t, trend.p] = await Promise.all([get('temperature_sensor_2'), get('pressure_sensor_1')])
}
useChart(trendEl, (c) => baseOption(c, {
  grid: { left: 44, right: 44, top: 16, bottom: 28 },
  yAxis: [
    { type: 'value', scale: true, axisLabel: { color: c('--muted'), fontSize: 11 }, splitLine: { lineStyle: { color: c('--chart-grid') } } },
    { type: 'value', scale: true, axisLabel: { color: c('--muted'), fontSize: 11 }, splitLine: { show: false } }
  ],
  series: [
    { name: 'TT-201', type: 'line', showSymbol: false, data: trend.t, lineStyle: { color: c('--data'), width: 2 }, itemStyle: { color: c('--data') },
      markLine: { symbol: 'none', silent: true, label: { show: false }, lineStyle: { color: c('--warn'), type: 'dashed' }, data: [{ yAxis: 85 }] } },
    { name: 'PT-101', type: 'line', yAxisIndex: 1, showSymbol: false, data: trend.p, lineStyle: { color: c('--chart-2'), width: 1.6 }, itemStyle: { color: c('--chart-2') } }
  ]
}), trend)

let alarmTimer
onMounted(() => {
  loadTrend()
  alarmTimer = setInterval(() => alarmStore.fetchAlarms({ hours: 24 }), 10000)
})
onBeforeUnmount(() => clearInterval(alarmTimer))
</script>

<style scoped>
.kpi-value.hot { color: var(--alarm-fg); }
.segments { display: flex; gap: 3px; }
.segments span { flex: 1; height: 6px; background: var(--data); border-radius: 2px; }
.segments span[data-status="warn"] { background: var(--warn); }
.segments span[data-status="alarm"] { background: var(--alarm); }
.segments span[data-status="offline"] { background: var(--quiet); }
.split { display: flex; gap: 2px; height: 6px; overflow: hidden; background: var(--quiet); border-radius: 3px; }
.split span[data-status="alarm"] { background: var(--alarm); }
.split span[data-status="warn"] { background: var(--warn); }
.zones { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
.zone { display: flex; flex-direction: column; gap: 6px; padding: 12px 14px; background: var(--surface-2); border: 1px solid var(--grid); border-radius: 10px; }
.zone[data-status="warn"] { border-color: var(--warn-line); }
.zone[data-status="alarm"] { border-color: var(--alarm-line); }
.zone-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; font-size: 14px; }
.zone-row { display: grid; grid-template-columns: 8px auto 1fr; align-items: center; gap: 8px; font-size: 12px; }
.zone-row .val { text-align: right; }
.queue-item { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid var(--grid); }
.queue-item:last-child { border-bottom: 0; }
.queue-copy { display: flex; flex: 1; flex-direction: column; gap: 4px; min-width: 0; font-size: 13px; }
.trend { height: 260px; }
.legend-row .second { background: var(--chart-2); }
.legend-row .limit { height: 0; background: none; border-top: 2px dashed var(--warn); }
.matrix { display: grid; grid-template-columns: repeat(auto-fill, minmax(124px, 1fr)); gap: 8px; }
.tile { display: flex; flex-direction: column; gap: 4px; padding: 10px 12px; background: var(--surface-2); border: 1px solid var(--grid); border-radius: 10px; }
.tile[data-status="warn"] { border-color: var(--warn-line); }
.tile[data-status="alarm"] { border-color: var(--alarm-line); }
.tile-top { display: flex; align-items: center; justify-content: space-between; font-size: 11px; }
.tile-val { font-size: 15px; font-weight: 600; }
</style>
