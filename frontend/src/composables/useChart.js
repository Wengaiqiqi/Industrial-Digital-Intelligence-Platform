import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { theme, cssVar } from '../theme'

// ECharts 读不到 CSS 变量：每次渲染时取当前主题色；主题切换、数据变化、容器尺寸变化时重画。
// 容器可以晚于组件出现（v-if），渲染时再绑定。
export function useChart(elRef, buildOption, deps) {
  let chart = null
  const ro = new ResizeObserver(() => chart?.resize())
  const render = () => {
    const el = elRef.value
    if (chart && chart.getDom() !== el) { chart.dispose(); chart = null }
    if (!el) return
    if (!chart) { chart = echarts.init(el); ro.observe(el) }
    chart.setOption(buildOption(cssVar), true)
  }
  onMounted(render)
  watch([theme, deps], () => nextTick(render), { deep: true })
  onBeforeUnmount(() => { ro.disconnect(); chart?.dispose() })
}

// 统一的坐标轴、网格、提示框样式
export function baseOption(c, extra = {}) {
  return {
    animation: false,
    grid: { left: 44, right: 16, top: 16, bottom: 28 },
    tooltip: { trigger: 'axis', backgroundColor: c('--paper-soft'), borderColor: c('--grid'), textStyle: { color: c('--ink'), fontSize: 12 } },
    xAxis: { type: 'time', axisLine: { lineStyle: { color: c('--grid') } }, axisTick: { show: false }, axisLabel: { color: c('--muted'), fontSize: 11, hideOverlap: true }, splitLine: { show: false } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: c('--muted'), fontSize: 11 }, splitLine: { lineStyle: { color: c('--chart-grid') } } },
    ...extra
  }
}
