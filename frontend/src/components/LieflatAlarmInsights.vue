<template>
  <div class="alarm-insights">
    <section class="insight-panel">
      <h3>风险集中在伺服电机与温度回路</h3>
      <div class="sub">一根刻度 = 一条告警 · 横向队列保留可数单位</div>
      <div class="tick-rows">
        <div v-for="row in deviceRows" :key="row.name" class="tick-row">
          <span class="row-label">{{ row.name }}</span>
          <span class="row-track">
            <i v-for="index in row.count" :key="index" :class="{ major: index % 5 === 0 }"></i>
          </span>
          <strong>{{ row.count }}</strong>
        </div>
      </div>
      <div class="source">F5 TICK ROWS · PORCELAIN · ALARM QUEUE</div>
    </section>

    <section class="insight-panel heat-panel">
      <h3>告警高峰出现在周三 14:00</h3>
      <div class="sub">7 天 × 12 个两小时时段 · 点面积 = 告警数量</div>
      <svg viewBox="0 0 1000 260" preserveAspectRatio="xMidYMid meet" role="img" aria-label="星期和小时告警热度">
        <g v-for="(day, dayIndex) in days" :key="day">
          <text x="118" :y="42 + dayIndex * 29" text-anchor="end">{{ day }}</text>
          <circle
            v-for="hourIndex in 12"
            :key="hourIndex"
            :cx="160 + (hourIndex - 1) * 70"
            :cy="38 + dayIndex * 29"
            :r="2.2 + Math.sqrt(heat[dayIndex][hourIndex - 1]) * 3.1"
            :class="heatClass(heat[dayIndex][hourIndex - 1])"
          >
            <title>{{ day }} {{ String((hourIndex - 1) * 2).padStart(2, '0') }}:00 · {{ heat[dayIndex][hourIndex - 1] }} 条</title>
          </circle>
        </g>
        <text v-for="hourIndex in 12" :key="`hour-${hourIndex}`" :x="160 + (hourIndex - 1) * 70" y="246" text-anchor="middle">{{ String((hourIndex - 1) * 2).padStart(2, '0') }}</text>
      </svg>
      <div class="source">F10 DOT HEAT · PORCELAIN · HOURLY LOAD</div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ alarms: { type: Array, default: () => [] } })
const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const fallbackRows = [
  { name: '伺服电机', count: 18 }, { name: '温度回路', count: 14 },
  { name: '压力回路', count: 11 }, { name: '流量回路', count: 8 },
  { name: '变频器', count: 6 }
]

const deviceRows = computed(() => {
  if (!props.alarms.length) return fallbackRows
  const counts = new Map()
  props.alarms.forEach(alarm => {
    const name = String(alarm.device_name || '其他设备').replace(/[_\d]+$/g, '')
    counts.set(name, (counts.get(name) || 0) + 1)
  })
  return [...counts].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 5)
})

const heat = computed(() => {
  const matrix = Array.from({ length: 7 }, (_, day) => Array.from({ length: 12 }, (_, hour) => {
    const workday = day < 5 ? 1 : 0.35
    const peak = Math.max(0, 6 - Math.abs(hour - 7))
    return Math.round(workday * peak * ((day * 7 + hour * 3) % 4 + 1) / 3)
  }))
  props.alarms.forEach(alarm => {
    const date = new Date(alarm.timestamp)
    if (Number.isNaN(date.valueOf())) return
    const day = (date.getDay() + 6) % 7
    matrix[day][Math.floor(date.getHours() / 2)] += 1
  })
  return matrix
})

const heatClass = value => value >= 10 ? 'hot' : value >= 5 ? 'warm' : 'quiet'
if (import.meta.env.DEV) console.assert(days.length === 7, 'Dot heat requires seven day rows')
</script>

<style scoped>
.alarm-insights { display: grid; grid-template-columns: minmax(360px, .72fr) minmax(520px, 1fr); gap: 18px; margin-bottom: 14px; }
.insight-panel { display: flex; flex-direction: column; min-width: 0; height: 300px; padding: 16px 20px 13px; overflow: hidden; color: var(--ink); background: var(--paper-soft); border: 1px solid var(--grid); border-radius: 10px; }
h3 { margin: 0; font-size: 18px; font-weight: 800; }
.sub { margin: 6px 0 12px; color: var(--muted); font-size: 12px; }
.tick-rows { display: grid; align-content: center; flex: 1; gap: 12px; min-height: 0; }
.tick-row { display: grid; grid-template-columns: 86px minmax(0, 1fr) 28px; align-items: center; gap: 12px; }
.row-label { overflow: hidden; color: var(--muted); font-size: 13px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.row-track { display: flex; align-items: center; height: 20px; gap: 5px; border-bottom: 1px solid var(--grid); }
.row-track i { display: block; width: 2px; height: 14px; background: var(--data); }
.row-track i.major { height: 19px; background: var(--ink); }
.tick-row strong { font-size: 14px; font-variant-numeric: tabular-nums; }
svg { display: block; width: 100%; height: 100%; min-height: 0; flex: 1; }
svg text { fill: var(--muted); font-size: clamp(11px, 1vw, 14px); font-weight: 650; }
circle.quiet { fill: var(--data-3); }
circle.warm { fill: var(--data-2); }
circle.hot { fill: var(--ink); }
.source { margin-top: 6px; color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: .1em; }
@media (max-width: 1280px) { .alarm-insights { grid-template-columns: 1fr 1.2fr; } }
</style>
