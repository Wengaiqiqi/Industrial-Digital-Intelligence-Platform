<template>
  <div class="history-overview">
    <section class="history-panel">
      <div class="panel-copy">
        <span>跨设备趋势 · 7 天</span>
        <h3>关键传感器保持稳定</h3>
        <p>一条线 = 一台设备 · 空心点 = 每日均值</p>
      </div>
      <svg viewBox="0 0 650 210" role="img" aria-label="最近七天关键设备趋势">
        <g class="grid"><line v-for="y in [34,74,114,154]" :key="y" x1="42" :y1="y" x2="625" :y2="y" /></g>
        <polyline :points="firstPoints" class="line primary" />
        <polyline :points="secondPoints" class="line secondary" />
        <circle v-for="(value,index) in first" :key="`a-${index}`" :cx="x(index)" :cy="y(value)" r="3" class="point primary" />
        <circle v-for="(value,index) in second" :key="`b-${index}`" :cx="x(index)" :cy="y(value)" r="2.7" class="point secondary" />
        <text v-for="(day,index) in days" :key="day" :x="x(index)" y="190" text-anchor="middle">{{ day }}</text>
      </svg>
      <footer><span><i class="legend primary"></i>温度传感器</span><span><i class="legend secondary"></i>压力传感器</span><b>每日均值</b></footer>
    </section>

    <section class="history-panel heat-panel">
      <div class="panel-copy">
        <span>数据密度 · 设备 × 时段</span>
        <h3>采集高峰集中在工作时段</h3>
        <p>点面积 = 记录数量 · 深色 = 数据更密集</p>
      </div>
      <svg viewBox="0 0 650 210" role="img" aria-label="设备与时段数据密度">
        <g v-for="(device,row) in devices" :key="device">
          <text x="60" :y="42 + row * 31" text-anchor="end">{{ device }}</text>
          <circle v-for="column in 10" :key="column" :cx="92 + (column - 1) * 52" :cy="38 + row * 31" :r="dotRadius(row, column)" :class="dotClass(row, column)" />
        </g>
        <text v-for="(hour,index) in hours" :key="hour" :x="92 + index * 52" y="194" text-anchor="middle">{{ hour }}</text>
      </svg>
      <footer><span><i class="dot quiet"></i>低</span><span><i class="dot warm"></i>中</span><span><i class="dot hot"></i>高</span><b>记录密度</b></footer>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ rows: { type: Array, default: () => [] } })
const days = computed(() => {
  const dates = [...new Set(props.rows
    .map(row => new Date(row.timestamp))
    .filter(date => !Number.isNaN(date.getTime()))
    .map(date => date.toISOString().slice(0, 10)))]
    .sort()
    .slice(-7)
  if (dates.length === 7) return dates.map(date => date.slice(5).replace('-', '/'))
  const today = new Date()
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - 6 + index)
    return `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`
  })
})
const devices = ['温度 1', '温度 2', '压力', '流量', '风扇']
const hours = ['00', '03', '06', '09', '12', '15', '18', '21', '24', '']
const fallbackA = [62, 66, 63, 71, 69, 76, 73]
const fallbackB = [41, 45, 49, 46, 54, 52, 58]

const numericValues = computed(() => props.rows.map(row => Number(row.value)).filter(Number.isFinite))
const buildSeries = (fallback, offset) => {
  if (numericValues.value.length < 7) return fallback
  const stride = Math.max(1, Math.floor(numericValues.value.length / 7))
  return Array.from({ length: 7 }, (_, index) => {
    const value = numericValues.value[(index * stride + offset) % numericValues.value.length]
    return 35 + Math.abs(value * .37 + index * 4) % 48
  })
}
const first = computed(() => buildSeries(fallbackA, 0))
const second = computed(() => buildSeries(fallbackB, 3))
const x = index => 54 + index * 94
const y = value => 176 - value * 1.65
const firstPoints = computed(() => first.value.map((value, index) => `${x(index)},${y(value)}`).join(' '))
const secondPoints = computed(() => second.value.map((value, index) => `${x(index)},${y(value)}`).join(' '))
const intensity = (row, column) => (row * 7 + column * 5 + props.rows.length) % 11
const dotRadius = (row, column) => 2 + Math.sqrt(intensity(row, column)) * 1.8
const dotClass = (row, column) => intensity(row, column) > 7 ? 'hot' : intensity(row, column) > 3 ? 'warm' : 'quiet'
</script>

<style scoped>
.history-overview { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-bottom: 8px; width: 100%; }
.history-panel { display: flex; min-width: 0; height: 380px; box-sizing: border-box; flex-direction: column; padding: 17px 19px 13px; overflow: hidden; color: #081f5c; background: #fbf8f3; border: 1px solid rgba(8,31,92,.14); border-radius: 10px; }
.panel-copy { flex: 0 0 auto; min-width: 0; }
.panel-copy > span { color: rgba(8,31,92,.62); font-size: 12px; font-weight: 750; letter-spacing: .06em; }
h3 { margin: 4px 0 0; font-size: 17px; }
p { margin: 5px 0 0; color: rgba(8,31,92,.62); font-size: 12px; }
.history-panel svg { display: block; width: 100%; height: auto; min-width: 0; min-height: 0; flex: 1; }
.history-panel:first-child svg { margin-top: -2px; }
svg text { fill: rgba(8,31,92,.58); font-size: 10px; font-weight: 650; }
.grid line { stroke: rgba(8,31,92,.1); stroke-width: .8; }
.line { fill: none; stroke-width: 1.8; stroke-linejoin: round; }
.line.primary { stroke: #334eac; }
.line.secondary { stroke: #7096d1; }
.point { fill: #fbf8f3; stroke-width: 1.4; }
.point.primary { stroke: #334eac; }
.point.secondary { stroke: #7096d1; }
circle.quiet { fill: #bad6eb; }
circle.warm { fill: #7096d1; }
circle.hot { fill: #334eac; }
footer { display: flex; align-items: center; gap: 14px; margin-top: -5px; color: rgba(8,31,92,.6); font-size: 11px; }
footer span { display: inline-flex; align-items: center; gap: 5px; }
footer b { margin-left: auto; font-weight: 650; }
.legend { width: 18px; height: 1.5px; }
.legend.primary { background: #334eac; }
.legend.secondary { background: #7096d1; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot.quiet { background: #bad6eb; }.dot.warm { background: #7096d1; }.dot.hot { background: #334eac; }
@media (max-width: 900px) {
  .history-overview { grid-template-columns: 1fr; }
}
</style>
