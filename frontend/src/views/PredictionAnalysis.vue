<template>
  <div class="page">
    <div class="toolbar">
      <div class="toolbar-group">
        <label class="field"><span class="muted small">设备</span>
          <el-select v-model="device" style="width: 220px" aria-label="分析设备"><el-option v-for="d in devices" :key="d.mqtt" :label="`${d.tag} ${d.name}`" :value="d.mqtt" /></el-select>
        </label>
        <label class="field"><span class="muted small">分析时段</span>
          <el-select v-model="hours" style="width: 130px" aria-label="分析时段"><el-option label="近 24 小时" :value="24" /><el-option label="近 7 天" :value="168" /></el-select>
        </label>
        <el-button type="primary" :loading="analyzing" @click="analyze">开始分析</el-button>
      </div>
      <div class="toolbar-group">
        <label class="field"><span class="muted small">训练数据</span>
          <el-select v-model="trainHours" style="width: 140px" aria-label="训练数据范围"><el-option label="近 7 天" :value="168" /><el-option label="近 30 天" :value="720" /></el-select>
        </label>
        <el-button :loading="training" @click="train">重新训练全局模型</el-button>
      </div>
    </div>

    <section class="card models" aria-label="模型状态">
      <div class="model"><span class="badge">异常检测</span><div><strong>IsolationForest</strong><div class="muted small">按设备数据单独拟合；数据不足 50 条时使用全局模型</div></div></div>
      <div class="model"><span class="badge">时序预测</span><div><strong>LSTM</strong><div class="muted small">输入窗口 10 点，预测下一时刻数值；数据不足 100 条时使用全局模型</div></div></div>
      <div v-if="trainResult" class="model"><span class="badge" :data-status="trainResult.ok ? 'ok' : 'warn'">{{ trainResult.ok ? '训练完成' : '训练未完成' }}</span><div class="small">{{ trainResult.text }}</div></div>
    </section>

    <div v-if="!result" class="card empty">{{ analyzing ? '分析中…' : '选择设备后点击“开始分析”，结果会显示在这里。' }}</div>

    <template v-else>
      <section class="kpi-grid" aria-label="分析结果">
        <div class="card">
          <div class="card-head"><span class="kpi-label">最新点异常检测</span><span class="badge" :data-status="anomaly.status">{{ anomaly.label }}</span></div>
          <div class="kpi-value">{{ anomaly.score }}</div>
          <div class="muted small">异常分数，大于 0 偏正常、小于 0 偏异常；置信度 {{ anomaly.confidence }}</div>
        </div>
        <div class="card">
          <div class="card-head"><span class="kpi-label">LSTM 下一时刻预测</span><span v-if="nextValue != null" class="badge" :data-status="nextStatus">{{ trendText }}</span></div>
          <div class="kpi-value">{{ nextValue != null ? fmt(nextValue) : '—' }}<small>{{ unit }}</small></div>
          <div class="muted small">{{ nextValue != null ? nextNote : '预测模型不可用：需要安装 TensorFlow，或该设备数据不足以训练' }}</div>
        </div>
        <div class="card">
          <div class="kpi-label">数据质量</div>
          <div class="kpi-value">{{ result.data_quality?.quality_score ?? '—' }}<small>/ 100</small></div>
          <div class="bar"><div :style="{ width: (result.data_quality?.quality_score || 0) + '%' }"></div></div>
          <div class="muted small">{{ qualityIssues }}</div>
        </div>
        <div class="card">
          <div class="kpi-label">统计 · {{ hours === 24 ? '近 24 小时' : '近 7 天' }}</div>
          <dl class="stats">
            <div><dt>均值</dt><dd class="mono">{{ fmt(st.mean) }}</dd></div>
            <div><dt>标准差</dt><dd class="mono">{{ fmt(st.std) }}</dd></div>
            <div><dt>采样点</dt><dd class="mono">{{ (st.count ?? 0).toLocaleString('en-US') }}</dd></div>
            <div><dt>趋势</dt><dd>{{ TREND[st.trend] || '—' }}</dd></div>
          </dl>
        </div>
      </section>

      <div class="row align-start">
        <section class="card grow-3" aria-labelledby="h-fc">
          <div class="card-head">
            <h2 id="h-fc">{{ current?.tag }} 实测与预测</h2>
            <div class="legend-row"><span><i></i>实测</span><span><i class="pred"></i>LSTM 预测</span><span v-if="current?.alarm"><i class="limit"></i>告警阈值</span></div>
          </div>
          <div ref="chartEl" class="fc-chart" role="img" :aria-label="`${current?.name} 实测曲线与下一时刻预测`"></div>
        </section>
        <section class="card grow-2" aria-labelledby="h-rec">
          <h2 id="h-rec" class="title">维护建议</h2>
          <article v-for="(r, i) in result.recommendations || []" :key="i" class="rec" :data-status="REC[r.type]">
            <span class="badge" :data-status="REC[r.type]">{{ REC_LABEL[r.type] || '提示' }}</span>
            <div>
              <h3>{{ r.title }}</h3>
              <p class="muted">{{ r.description }}</p>
              <p>建议：{{ r.action }}</p>
            </div>
          </article>
          <div v-if="!result.recommendations?.length" class="muted small">暂无建议</div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { deviceAPI } from '../api'
import mlAPI from '../api/ml'
import { useChart, baseOption } from '../composables/useChart'
import { DEVICES } from '../utils/plantLayout'

const TREND = { increasing: '上升', decreasing: '下降', stable: '平稳', insufficient_data: '数据不足', unknown: '未知' }
const REC = { critical: 'alarm', warning: 'warn', info: '', success: 'ok' }
const REC_LABEL = { critical: '严重', warning: '预警', info: '关注', success: '正常' }
const ISSUES = { missing_values: '存在缺失值（−20）', negative_values: '存在负值（−10）', irregular_intervals: '采样间隔不规则（−15）', high_anomaly_rate: '异常点比例过高（−25）', no_data: '没有数据' }

const devices = DEVICES.filter((d) => typeof d.mqtt === 'string' && d.alarm)
const device = ref('temperature_sensor_2')
const hours = ref(24)
const trainHours = ref(168)
const analyzing = ref(false)
const training = ref(false)
const result = ref(null)
const trainResult = ref(null)
const history = ref([])

const current = computed(() => DEVICES.find((d) => d.mqtt === device.value))
const unit = computed(() => current.value?.unit || '')
const st = computed(() => result.value?.statistics || {})
const fmt = (v) => (v == null || Number.isNaN(v) ? '—' : Math.abs(v) >= 100 ? Math.round(v).toLocaleString('en-US') : Number(v).toFixed(2))

const anomaly = computed(() => {
  const a = result.value?.anomaly_detection
  if (!a) return { label: '不可用', status: 'offline', score: '—', confidence: '—' }
  return { label: a.is_anomaly ? '异常' : '正常', status: a.is_anomaly ? 'alarm' : 'ok', score: Number(a.anomaly_score).toFixed(3), confidence: Number(a.confidence).toFixed(2) }
})

const lastValue = computed(() => history.value.at(-1)?.[1])
const nextValue = computed(() => result.value?.failure_prediction?.next_value_prediction ?? null)
const trendText = computed(() => (nextValue.value > lastValue.value ? '上升' : nextValue.value < lastValue.value ? '下降' : '持平'))
const nextStatus = computed(() => {
  const lim = current.value?.alarm
  if (!lim || nextValue.value == null) return ''
  if (nextValue.value < lim[0] || nextValue.value > lim[1]) return 'alarm'
  return nextValue.value > lim[1] - (lim[1] - lim[0]) * 0.08 ? 'warn' : 'ok'
})
const nextNote = computed(() => {
  const lim = current.value?.alarm
  const now = lastValue.value != null ? `当前 ${fmt(lastValue.value)} ${unit.value}，` : ''
  if (!lim) return now
  return nextStatus.value === 'alarm' ? `${now}预测越过阈值 ${lim.join(' – ')} ${unit.value}` : `${now}预测在阈值 ${lim.join(' – ')} ${unit.value} 以内`
})
const qualityIssues = computed(() => {
  const issues = result.value?.data_quality?.issues || []
  return issues.length ? `扣分项：${issues.map((i) => ISSUES[i] || i).join('、')}` : '无扣分项'
})

async function analyze() {
  analyzing.value = true
  result.value = null
  try {
    const [res, hist] = await Promise.all([
      mlAPI.analyzeDevice(device.value, hours.value),
      deviceAPI.getDeviceHistory(device.value, hours.value, 3000).catch(() => ({ data: [] }))
    ])
    history.value = (hist.data || []).map((d) => [new Date(d.timestamp).getTime(), d.value]).sort((a, b) => a[0] - b[0])
    result.value = res
  } catch {
    // 失败原因由请求拦截器提示
  } finally {
    analyzing.value = false
  }
}

async function train() {
  training.value = true
  try {
    const res = await mlAPI.trainModels('all', trainHours.value)
    trainResult.value = { ok: true, text: `使用 ${res.data_points?.toLocaleString('en-US')} 个数据点、${res.devices_count} 台设备完成训练` }
    ElMessage.success('模型训练完成')
  } catch (e) {
    const r = e.response?.data
    trainResult.value = { ok: false, text: r?.error || r?.message || e.message }
    ElMessage.error('模型训练未完成')
  } finally {
    training.value = false
  }
}

const chartEl = ref(null)
useChart(chartEl, (c) => {
  const last = history.value.at(-1)
  const pred = last && nextValue.value != null ? [last, [last[0] + 2000, nextValue.value]] : []
  return baseOption(c, {
    series: [
      { type: 'line', showSymbol: false, data: history.value, lineStyle: { color: c('--data'), width: 2 }, itemStyle: { color: c('--data') },
        markLine: current.value?.alarm ? { symbol: 'none', silent: true, label: { show: false }, lineStyle: { color: c('--alarm'), type: 'dashed', opacity: 0.7 }, data: current.value.alarm.map((y) => ({ yAxis: y })) } : undefined },
      { type: 'line', data: pred, symbolSize: 7, lineStyle: { color: c('--warn'), type: 'dashed', width: 2 }, itemStyle: { color: c('--warn') } }
    ]
  })
}, () => [history.value, nextValue.value])
</script>

<style scoped>
.toolbar, .toolbar-group { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 10px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.models { flex-direction: row; flex-wrap: wrap; gap: 24px; }
.model { display: flex; flex: 1 1 260px; align-items: flex-start; gap: 12px; }
.model strong { font-size: 14px; }
.bar { height: 6px; overflow: hidden; background: var(--quiet); border-radius: 3px; }
.bar div { height: 100%; background: var(--data); }
.stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; margin: 0; font-size: 12px; }
.stats dt { color: var(--muted); }
.stats dd { margin: 0; font-size: 15px; }
.align-start { align-items: flex-start; }
.fc-chart { height: 280px; }
.legend-row .pred { height: 0; background: none; border-top: 2px dashed var(--warn); }
.legend-row .limit { height: 0; background: none; border-top: 2px dashed var(--alarm); }
.title { margin: 0; font-size: 16px; font-weight: 700; }
.rec { display: flex; gap: 12px; padding: 12px 14px; background: var(--surface-2); border: 1px solid var(--grid); border-radius: 12px; }
.rec[data-status="alarm"] { border-color: var(--alarm-line); }
.rec[data-status="warn"] { border-color: var(--warn-line); }
.rec .badge { align-self: flex-start; }
.rec h3 { margin: 0 0 4px; font-size: 14px; font-weight: 600; }
.rec p { margin: 0; font-size: 12px; line-height: 1.6; }
</style>
