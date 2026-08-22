<template>
  <div class="lieflat-overview">
    <section class="lieflat-panel trend-panel">
      <div class="chart-kicker">24 小时运行趋势 · 实时</div>
      <h3>产线运行平稳，14:20 出现短时波动</h3>
      <svg ref="trendSvg" :viewBox="`0 0 ${chartWidth} 250`" role="img" aria-label="24 小时产线运行趋势">
        <g class="chart-grid">
          <line v-for="tick in [0, 25, 50, 75, 100]" :key="tick" x1="42" :y1="y(tick)" :x2="chartWidth - 24" :y2="y(tick)" />
          <text v-for="tick in [0, 25, 50, 75, 100]" :key="`label-${tick}`" x="32" :y="y(tick) + 3" text-anchor="end">{{ tick }}</text>
        </g>
        <line x1="42" y1="218" :x2="chartWidth - 24" y2="218" class="calendar-floor" />
        <line v-for="index in values.length" :key="`floor-${index}`" :x1="x(index - 1)" y1="218" :x2="x(index - 1)" y2="224" class="calendar-tick" />
        <polyline :points="points" class="trend-line" />
        <circle
          v-for="(value, index) in values"
          :key="index"
          :cx="x(index)"
          :cy="y(value)"
          :r="index === values.length - 1 ? 4.7 : 3.2"
          :class="index === values.length - 1 ? 'current-point' : 'data-point'"
        >
          <title>{{ hours[index] }} · {{ value }}</title>
        </circle>
        <text :x="x(13)" :y="y(values[13]) - 12" class="peak-label" text-anchor="middle">{{ values[13] }}</text>
        <text :x="x(values.length - 1)" :y="y(values.at(-1)) - 12" class="peak-label" text-anchor="middle">{{ values.at(-1) }}</text>
        <text v-for="index in [0, 4, 8, 12, 16, 20, 23]" :key="`hour-${index}`" :x="x(index)" y="243" class="axis-label" text-anchor="middle">{{ hours[index] }}</text>
      </svg>
      <div class="chart-source">一个点 = 1 小时 · 空心点 = 常规读数 · 实心点 = 当前值</div>
    </section>

    <section class="lieflat-panel gauge-panel">
      <div class="chart-kicker">系统效率 · 今日</div>
      <div class="gauge-spacer"></div>
      <svg viewBox="0 0 360 250" role="img" :aria-label="`系统效率 ${efficiency}%`">
        <line
          v-for="tick in 100"
          :key="tick"
          x1="180" y1="35" x2="180" :y2="tick <= efficiency ? 21 : 26"
          :class="tick <= efficiency ? 'gauge-tick active' : 'gauge-tick'"
          :transform="`rotate(${(tick - 1) * 3.6} 180 128)`"
        />
        <text x="180" y="128" text-anchor="middle" class="gauge-value">{{ efficiency }}%</text>
        <text x="180" y="149" text-anchor="middle" class="gauge-caption">效率</text>
        <text x="180" y="17" text-anchor="middle" class="gauge-side-label">SOCIAL · 14</text>
        <text x="350" y="132" text-anchor="end" class="gauge-side-label">ORGANIC · 37</text>
        <text x="180" y="243" text-anchor="middle" class="gauge-side-label">PAID · 28</text>
        <text x="10" y="132" class="gauge-side-label">REFERRAL · 21</text>
      </svg>
      <div class="gauge-meta"><span>目标 100%</span><span>较昨日 +1.2%</span></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

defineProps({ efficiency: { type: Number, default: 96.8 } })

const values = [61, 68, 73, 77, 76, 72, 66, 74, 80, 83, 77, 76, 70, 75, 86, 77, 74, 65, 64, 71, 73, 68, 60, 71]
const hours = values.map((_, index) => `${String(index).padStart(2, '0')}:00`)
const trendSvg = ref(null)
const chartWidth = ref(760)
const x = index => 48 + index * ((chartWidth.value - 78) / (values.length - 1))
const y = value => 214 - value * 1.62
const points = computed(() => values.map((value, index) => `${x(index)},${y(value)}`).join(' '))
let resizeObserver

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    const { width, height } = entry.contentRect
    if (width && height) chartWidth.value = Math.max(520, 250 * width / height)
  })
  resizeObserver.observe(trendSvg.value)
})

onBeforeUnmount(() => resizeObserver?.disconnect())

if (import.meta.env.DEV) console.assert(values.length === 24, 'Lieflat overview requires one point per hour')
</script>

<style scoped>
.lieflat-overview { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(360px, 1fr); gap: 18px; margin-bottom: 18px; }
.lieflat-panel { display: flex; flex-direction: column; min-width: 0; height: 380px; padding: 20px 22px 16px; overflow: hidden; color: #081f5c; background: #fbf8f3; border: 1px solid rgba(8, 31, 92, .14); border-radius: 10px; }
.chart-kicker { margin-bottom: 6px; color: rgba(8, 31, 92, .62); font-size: 13px; font-weight: 750; letter-spacing: .06em; }
h3 { margin: 0; font-size: 19px; font-weight: 800; }
.chart-sub { margin-top: 5px; color: rgba(8, 31, 92, .58); font-size: 11px; }
svg { display: block; width: 100%; min-height: 0; flex: 1; margin-top: 3px; }
.trend-panel svg { margin-top: -4px; }
.chart-grid line { stroke: rgba(8, 31, 92, .1); stroke-width: .8; }
.chart-grid text, .axis-label { fill: rgba(8, 31, 92, .58); font-size: 10px; font-weight: 650; }
.calendar-floor { stroke: rgba(8, 31, 92, .2); stroke-width: .8; }
.calendar-tick { stroke: rgba(8, 31, 92, .18); stroke-width: .8; }
.trend-line { fill: none; stroke: #334eac; stroke-width: 1.8; stroke-linejoin: round; stroke-linecap: round; }
.data-point { fill: #fbf8f3; stroke: #334eac; stroke-width: 1.5; }
.current-point { fill: #081f5c; stroke: #081f5c; }
.peak-label { fill: #081f5c; font-size: 12px; font-weight: 800; paint-order: stroke; stroke: #fbf8f3; stroke-width: 4px; }
.chart-source { margin-top: 2px; color: rgba(8, 31, 92, .62); font-size: 12px; font-weight: 600; letter-spacing: .02em; }
.gauge-spacer { height: 14px; }
.gauge-panel svg { min-height: 252px; margin-top: -4px; }
.gauge-tick { stroke: #bad6eb; stroke-width: 1.3; }
.gauge-tick.active { stroke: #334eac; stroke-width: 2; }
.gauge-value { fill: #081f5c; font-size: 30px; font-weight: 800; }
.gauge-caption { fill: rgba(8, 31, 92, .62); font-size: 11px; font-weight: 700; }
.gauge-side-label { fill: #334eac; font-size: 8px; font-weight: 800; letter-spacing: .05em; text-transform: uppercase; }
.gauge-meta { display: flex; justify-content: center; gap: 28px; margin-top: 0; color: #081f5c; font-size: 12px; }
@media (max-width: 1320px) { .lieflat-overview { grid-template-columns: minmax(0, 1.65fr) minmax(260px, .8fr); } }
</style>
