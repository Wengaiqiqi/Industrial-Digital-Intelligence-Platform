<template>
  <div class="ml-design">
    <section class="model-strip">
      <h3 class="model-strip-title">机器学习模型管理</h3>
      <div class="model-state"><span class="pulse"></span><div><strong>异常检测模型</strong><small>{{ modelReady ? '模型已就绪，可进行实时推理' : '使用当前数据生成预测基线' }}</small></div></div>
      <el-select v-model="selectedDevice" placeholder="选择设备" filterable @change="runAnalysis">
        <el-option v-for="device in availableDevices" :key="device.device_name" :label="deviceLabel(device.device_name)" :value="device.device_name" />
      </el-select>
      <el-select v-model="trainingHours" aria-label="训练数据范围">
        <el-option label="最近 7 天" :value="168" /><el-option label="最近 15 天" :value="360" /><el-option label="最近 30 天" :value="720" />
      </el-select>
      <el-button type="primary" :loading="training" @click="trainModel">{{ training ? '训练中…' : '重新训练模型' }}</el-button>
      <div class="training-meta"><span>上次训练<b>今天 09:20</b></span><span>训练样本<b>12,840</b></span><span>模型准确率<b>{{ confidence }}%</b></span></div>
    </section>

    <div class="design-stats prediction-stats">
      <div class="design-stat-card"><span class="design-stat-icon"><TrendCharts /></span><div><span class="design-stat-label">异常概率</span><strong>{{ anomalyRate }}%</strong></div><span class="micro-bars"><i v-for="n in 9" :key="n" :style="{ height: `${7 + n * 2}px` }"></i></span></div>
      <div class="design-stat-card"><span class="design-stat-icon"><CircleCheck /></span><div><span class="design-stat-label">风险等级</span><strong>{{ anomalyRate > 25 ? '中' : '低' }}</strong></div></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Clock /></span><div><span class="design-stat-label">预计剩余寿命</span><strong>92 <small>天</small></strong></div><span class="micro-bars"><i v-for="n in 9" :key="n" :style="{ height: `${6 + (n * 4) % 21}px` }"></i></span></div>
      <div class="design-stat-card"><span class="design-stat-icon"><Document /></span><div><span class="design-stat-label">建议检查</span><strong>2 <small>项</small></strong></div><span class="micro-bars"><i v-for="n in 9" :key="n" :style="{ height: `${5 + (n * 6) % 22}px` }"></i></span></div>
    </div>

    <div class="prediction-visuals">
      <section class="prediction-panel trend-panel">
        <div class="panel-title"><div><span>未来 24 小时 · F2 预测线</span><h3>运行趋势处于安全区间</h3><p>实线 = 预测值 · 浅色带 = 置信区间</p></div><b>每 2 小时</b></div>
        <svg viewBox="0 0 760 250" role="img" aria-label="未来 24 小时预测趋势">
          <g class="grid"><line v-for="tick in [40,80,120,160,200]" :key="tick" x1="44" :y1="tick" x2="730" :y2="tick" /></g>
          <polygon :points="confidenceBand" class="confidence-band" />
          <polyline :points="predictionPoints" class="prediction-line" />
          <circle v-for="(value,index) in prediction" :key="index" :cx="px(index)" :cy="py(value)" r="3.2" class="prediction-point" />
          <text v-for="(hour,index) in forecastHours" :key="hour" :x="px(index)" y="238" text-anchor="middle">{{ hour }}</text>
        </svg>
        <footer><span><i class="line-key"></i>预测值</span><span><i class="band-key"></i>95% 置信区间</span><b>当前模型 · {{ confidence }}%</b></footer>
      </section>

      <section class="prediction-panel scatter-panel">
        <div class="panel-title"><div><span>异常诊断 · F8 散点</span><h3>样本远离风险边界</h3><p>点 = 运行样本 · 十字 = 当前状态</p></div></div>
        <svg viewBox="0 0 440 250" role="img" aria-label="异常诊断散点图">
          <g class="grid"><line v-for="tick in [48,88,128,168,208]" :key="`h-${tick}`" x1="42" :y1="tick" x2="415" :y2="tick" /><line v-for="tick in [70,140,210,280,350]" :key="`v-${tick}`" :x1="tick" y1="30" :x2="tick" y2="208" /></g>
          <line x1="42" y1="128" x2="415" y2="128" class="risk-line" /><line x1="280" y1="30" x2="280" y2="208" class="risk-line" />
          <circle v-for="point in scatter" :key="point.id" :cx="point.x" :cy="point.y" :r="point.r" :class="point.risk ? 'sample risk' : 'sample'" />
          <g class="current"><line :x1="currentPoint.x - 7" :y1="currentPoint.y" :x2="currentPoint.x + 7" :y2="currentPoint.y" /><line :x1="currentPoint.x" :y1="currentPoint.y - 7" :x2="currentPoint.x" :y2="currentPoint.y + 7" /></g>
          <text x="40" y="232">稳定</text><text x="388" y="232">异常</text>
        </svg>
        <footer><span><i class="dot-key"></i>历史样本</span><span><i class="cross-key">＋</i>当前状态</span><b>风险边界 0.65</b></footer>
      </section>
    </div>

    <section class="recommendation-card">
      <header><strong>诊断建议</strong><span>按影响程度排序</span></header>
      <table><thead><tr><th>优先级</th><th>诊断项</th><th>当前状态</th><th>模型判断</th><th>建议</th><th>预计窗口</th></tr></thead>
        <tbody><tr v-for="item in recommendations" :key="item.name"><td><span class="soft-tag">{{ item.level }}</span></td><td>{{ item.name }}</td><td>{{ item.status }}</td><td><strong>{{ item.result }}</strong></td><td>{{ item.advice }}</td><td>{{ item.window }}</td></tr></tbody>
      </table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, Clock, Document, TrendCharts } from '@element-plus/icons-vue'
import { useDeviceStore } from '../stores/device'
import mlAPI from '../api/ml'

const deviceStore = useDeviceStore()
const selectedDevice = ref('')
const trainingHours = ref(168)
const training = ref(false)
const analyzing = ref(false)
const modelReady = ref(true)
const result = ref(null)
const availableDevices = computed(() => deviceStore.devices || [])
const anomalyRate = computed(() => Math.round((result.value?.anomaly_detection?.anomaly_score ?? .08) * 100))
const confidence = computed(() => Math.round((result.value?.confidence ?? .94) * 100))
const forecastHours = ['00','02','04','06','08','10','12','14','16','18','20','22']
const prediction = computed(() => [62,64,66,63,68,71,69,74,72,76,73,75].map((value,index) => value + (anomalyRate.value > 20 && index > 7 ? 8 : 0)))
const px = index => 50 + index * 60.5
const py = value => 216 - value * 2
const predictionPoints = computed(() => prediction.value.map((value,index) => `${px(index)},${py(value)}`).join(' '))
const confidenceBand = computed(() => {
  const top = prediction.value.map((value,index) => `${px(index)},${py(value + 7)}`)
  const bottom = [...prediction.value].reverse().map((value,reverseIndex) => `${px(prediction.value.length - 1 - reverseIndex)},${py(value - 7)}`)
  return [...top, ...bottom].join(' ')
})
const scatter = Array.from({ length: 42 }, (_, index) => ({ id: index, x: 58 + (index * 73) % 326, y: 42 + (index * 47) % 150, r: 2.5 + index % 4, risk: index % 13 === 0 }))
const currentPoint = computed(() => ({ x: 185 + anomalyRate.value * 1.4, y: 126 - anomalyRate.value * .4 }))
const recommendations = computed(() => [
  { level: '常规', name: '温度稳定性', status: '波动 1.8%', result: '稳定', advice: '保持当前采样频率', window: '24 小时' },
  { level: anomalyRate.value > 20 ? '关注' : '常规', name: '振动趋势', status: `异常率 ${anomalyRate.value}%`, result: anomalyRate.value > 20 ? '轻微偏移' : '正常', advice: anomalyRate.value > 20 ? '安排一次点检' : '持续观察', window: '48 小时' },
  { level: '常规', name: '负载预测', status: '峰值 76%', result: '安全', advice: '无需调整运行计划', window: '7 天' }
])
const deviceLabel = name => ({ temperature_sensor_1:'温度传感器1', temperature_sensor_2:'温度传感器2', fan_1:'风扇1', fan_2:'风扇2', servo_motor_1:'伺服电机1', servo_motor_2:'伺服电机2', pressure_sensor_1:'压力传感器1', flow_meter_1:'流量计1' }[name] || name)

async function trainModel() {
  training.value = true
  try {
    const response = await mlAPI.trainModels(selectedDevice.value || 'all', trainingHours.value)
    modelReady.value = response?.success !== false
    ElMessage.success('预测模型已更新')
  } catch (error) {
    modelReady.value = false
    ElMessage.warning('训练服务暂不可用，已保留当前模型')
  } finally { training.value = false }
}

async function runAnalysis() {
  if (!selectedDevice.value) return ElMessage.warning('请先选择设备')
  analyzing.value = true
  try {
    const response = await mlAPI.analyzeDevice(selectedDevice.value, 24)
    result.value = response?.data || response
    ElMessage.success('设备分析完成')
  } catch (error) {
    ElMessage.warning('分析服务暂不可用，当前展示预测基线')
  } finally { analyzing.value = false }
}

onMounted(async () => {
  await deviceStore.fetchDevices()
  if (!selectedDevice.value && availableDevices.value.length) selectedDevice.value = availableDevices.value[0].device_name
})
</script>

<style scoped>
.ml-design { display: grid; gap: 18px; }
.model-strip { display: grid; grid-template-columns: 240px 210px 160px auto minmax(420px,1fr); grid-template-rows: 28px 62px; align-items: center; gap: 0 12px; min-height: 126px; padding: 12px 18px; background: #fbf8f3; border: 1px solid rgba(8,31,92,.14); border-radius: 10px; }
.model-strip-title { grid-column: 1 / -1; align-self: start; margin: 0; font-size: 17px; }
.model-state { display: flex; align-items: center; gap: 11px; }
.model-state .pulse { width: 9px; height: 9px; background: #334eac; border-radius: 50%; }
.model-state strong,.model-state small { display: block; }.model-state strong { font-size: 15px; }.model-state small { margin-top: 5px; color: rgba(8,31,92,.62); font-size: 12px; line-height: 1.35; }
.training-meta { display: grid; grid-template-columns: repeat(3,1fr); align-items: center; height: 48px; margin-left: 14px; border-left: 1px solid rgba(8,31,92,.12); }.training-meta span { padding-left: 20px; color: rgba(8,31,92,.6); border-right: 1px solid rgba(8,31,92,.12); font-size: 12px; }.training-meta b { display: block; margin-top: 6px; color: #081f5c; font-size: 14px; }
.prediction-stats { margin-bottom: 0 !important; }.prediction-stats .design-stat-card { height: 94px; }.stat-suffix { position: absolute; right: 16px; bottom: 16px; color: rgba(8,31,92,.55); font-size: 10px; }
.prediction-visuals { display: grid; grid-template-columns: 1.22fr 1fr; gap: 18px; }
.prediction-panel { display: flex; height: 358px; min-height: 0; flex-direction: column; padding: 16px 18px 12px; overflow: hidden; color: #081f5c; background: #fbf8f3; border: 1px solid rgba(8,31,92,.14); border-radius: 10px; }
.panel-title { display: flex; flex: 0 0 auto; justify-content: space-between; }.panel-title span { color: rgba(8,31,92,.62); font-size: 12px; font-weight: 750; letter-spacing: .05em; }.panel-title h3 { margin: 5px 0 0; font-size: 19px; }.panel-title p { margin: 5px 0 0; color: rgba(8,31,92,.62); font-size: 12px; }.panel-title b { color: rgba(8,31,92,.58); font-size: 12px; font-weight: 650; }
.prediction-panel svg { display: block; flex: 1 1 auto; width: 100%; height: 250px; min-height: 0; }
.prediction-panel svg text { fill: rgba(8,31,92,.58); font-size: clamp(9px, 1.05vw, 12px); font-weight: 650; }
.trend-panel svg text { font-size: clamp(9px, 1vw, 12px); }
.risk-line { stroke: rgba(8,31,92,.45); stroke-width: 1; stroke-dasharray: 5 5; }
.confidence-band { fill: rgba(186,214,235,.42); }.prediction-line { fill: none; stroke: #334eac; stroke-width: 2; }.prediction-point { fill: #fbf8f3; stroke: #334eac; stroke-width: 1.4; }
.sample { fill: #7096d1; opacity: .72; }.sample.risk { fill: #081f5c; }.current line { stroke: #081f5c; stroke-width: 2; }
.prediction-panel footer { display: flex; align-items: center; gap: 16px; margin-top: -3px; color: rgba(8,31,92,.62); font-size: 12px; }.prediction-panel footer span { display: flex; align-items: center; gap: 6px; }.prediction-panel footer b { margin-left: auto; font-weight: 650; }.line-key { width: 18px; height: 2px; background: #334eac; }.band-key { width: 18px; height: 7px; background: rgba(186,214,235,.55); }.dot-key { width: 6px; height: 6px; background: #7096d1; border-radius: 50%; }.cross-key { color: #081f5c; font-size: 15px; }
.recommendation-card { display: flex; flex-direction: column; min-height: 294px; overflow: hidden; background: #fbf8f3; border: 1px solid rgba(8,31,92,.14); border-radius: 10px; }.recommendation-card header { display: flex; align-items: center; justify-content: space-between; height: 52px; padding: 0 20px; border-bottom: 1px solid rgba(8,31,92,.14); font-size: 17px; }.recommendation-card header span { color: rgba(8,31,92,.62); font-size: 13px; }.recommendation-card table { width: calc(100% - 36px); margin: 0 18px; border-collapse: collapse; }.recommendation-card th,.recommendation-card td { height: 50px; padding: 0 10px; border-bottom: 1px solid rgba(8,31,92,.1); text-align: left; font-size: 14px; }.recommendation-card th { color: rgba(8,31,92,.62); font-size: 13px; }
.recommendation-card::after { display: block; min-height: 42px; margin-top: auto; padding: 13px 20px; color: rgba(8,31,92,.62); content: '共 3 条建议'; font-size: 13px; }
</style>
