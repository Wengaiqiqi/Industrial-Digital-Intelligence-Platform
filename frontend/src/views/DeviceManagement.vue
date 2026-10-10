<template>
  <div class="page">
    <div class="filters">
      <el-input v-model="q" placeholder="搜索位号、名称或 MQTT 点位" clearable aria-label="搜索设备" class="search" />
      <el-select v-model="fKind" placeholder="全部类型" clearable aria-label="设备类型"><el-option v-for="k in kindOptions" :key="k" :label="k" :value="k" /></el-select>
      <el-select v-model="fStatus" placeholder="全部状态" clearable aria-label="状态"><el-option v-for="(label, s) in STATUS_LABEL" :key="s" :label="label" :value="s" /></el-select>
      <el-select v-model="fZone" placeholder="全部区域" clearable aria-label="区域"><el-option v-for="z in zoneOptions" :key="z" :label="z" :value="z" /></el-select>
      <span class="spacer"></span>
      <el-button type="primary" @click="addOpen = true">新增设备</el-button>
    </div>

    <div class="row align-start">
      <section class="card flush grow-3" aria-label="设备列表">
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>设备</th><th>类型</th><th>区域</th><th class="num">当前值</th><th>阈值</th><th>状态</th><th>上报</th><th class="num">操作</th></tr></thead>
            <tbody>
              <tr v-for="r in filtered" :key="r.id" class="clickable" :aria-selected="r.id === selectedId" @click="selectedId = r.id">
                <td><div class="cell-title"><span class="mono">{{ r.tag }}</span><span>{{ r.name }}</span></div></td>
                <td>{{ r.kind }}</td>
                <td>{{ r.zone }}</td>
                <td class="num val" :data-status="r.status">{{ r.value }}</td>
                <td class="mono muted small">{{ r.alarm ? r.alarm.join(' – ') : '—' }}</td>
                <td><span class="badge" :data-status="r.status"><span class="dot" :data-status="r.status"></span>{{ STATUS_LABEL[r.status] }}</span></td>
                <td class="mono muted small">{{ r.reading ? fmtTime(r.reading.receivedAt) : '—' }}</td>
                <td class="num"><button type="button" class="ghost-btn" :aria-label="`删除 ${r.tag}`" @click.stop="remove(r)">删除</button></td>
              </tr>
            </tbody>
          </table>
          <div v-if="!filtered.length" class="empty">没有符合条件的设备</div>
        </div>
      </section>

      <aside v-if="sel" class="card grow-1 detail" aria-label="设备详情">
        <div class="card-head"><span class="mono muted">{{ sel.tag }} · {{ [sel.mqtt].flat().join(' · ') }}</span><span class="badge" :data-status="sel.status">{{ STATUS_LABEL[sel.status] }}</span></div>
        <h2>{{ sel.name }}</h2>
        <div class="muted small">{{ sel.kind }} · {{ sel.zone }}<template v-if="sel.loc"> · {{ sel.loc }}</template></div>
        <div class="big mono val" :data-status="sel.status">{{ sel.value }}</div>
        <div v-if="sel.status === 'alarm' || sel.status === 'warn'" class="note" :data-status="sel.status">
          {{ sel.status === 'alarm' ? `数值越过阈值 ${sel.alarm ? sel.alarm.join(' – ') : ''} ${sel.unit || ''}` : '数值接近阈值上下限（8% 以内）' }}
        </div>

        <fieldset class="control">
          <legend>远程控制</legend>
          <div class="segmented" role="group" aria-label="运行状态">
            <button type="button" :aria-pressed="false" :disabled="busy" @click="send('start')">启动</button>
            <button type="button" :aria-pressed="false" :disabled="busy" @click="send('stop')">停止</button>
            <button type="button" :aria-pressed="false" :disabled="busy" @click="send('reset')">复位</button>
          </div>
          <template v-if="setpointRange">
            <label class="field">
              <span>目标值 <b class="mono">{{ setpoint }} {{ sel.unit }}</b></span>
              <el-slider v-model="setpoint" :min="setpointRange[0]" :max="setpointRange[1]" :step="setpointStep" :aria-label="`${sel.name}目标值`" />
            </label>
            <el-button type="primary" :loading="busy" @click="send('set_value', setpoint)">下发指令</el-button>
          </template>
          <p class="muted small">指令经 /api/control/device 下发；设备离线时后端会拒绝。</p>
        </fieldset>

        <dl class="facts">
          <dt>运行时长</dt><dd class="mono">{{ statusInfo ? deviceStore.formatRuntime(statusInfo.total_runtime) : '—' }}</dd>
          <dt>故障次数</dt><dd class="mono">{{ statusInfo?.error_count ?? '—' }}</dd>
          <dt>量程</dt><dd class="mono">{{ sel.range ? `${sel.range.join(' – ')} ${sel.unit || ''}` : '—' }}</dd>
        </dl>
        <div class="links">
          <router-link to="/3d-scene"><el-button>三维定位</el-button></router-link>
          <router-link to="/historical-data"><el-button>历史数据</el-button></router-link>
        </div>
      </aside>
    </div>

    <el-dialog v-model="addOpen" title="新增设备" width="440px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="MQTT 设备名" prop="device_name"><el-input v-model="form.device_name" placeholder="例如 level_sensor_1，需与上报的设备名一致" /></el-form-item>
        <el-form-item label="类型" prop="device_type">
          <el-select v-model="form.device_type" style="width: 100%"><el-option v-for="(label, t) in TYPE_LABEL" :key="t" :label="label" :value="t" /></el-select>
        </el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" placeholder="例如 °C、bar、L/min" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addOpen = false">取消</el-button>
        <el-button type="primary" :loading="busy" @click="add">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDeviceStore } from '../stores/device'
import { useLine, fmtTime } from '../composables/useLine'
import { STATUS_LABEL } from '../utils/plantLayout'

const TYPE_LABEL = { sensor: '传感器', actuator: '执行器', indicator: '指示灯', io: '数字 I/O' }
const { rows, refresh } = useLine()
const deviceStore = useDeviceStore()

const q = ref('')
const fKind = ref('')
const fStatus = ref('')
const fZone = ref('')
const selectedId = ref('FAN02')
const busy = ref(false)

const kindOptions = computed(() => [...new Set(rows.value.map((r) => r.kind))])
const zoneOptions = computed(() => [...new Set(rows.value.map((r) => r.zone))])
const filtered = computed(() => {
  const s = q.value.trim().toLowerCase()
  return rows.value.filter((r) =>
    (!s || `${r.tag}${r.name}${[r.mqtt].flat().join('')}`.toLowerCase().includes(s)) &&
    (!fKind.value || r.kind === fKind.value) && (!fStatus.value || r.status === fStatus.value) && (!fZone.value || r.zone === fZone.value))
})
const sel = computed(() => rows.value.find((r) => r.id === selectedId.value) || filtered.value[0])
const statusInfo = computed(() => sel.value && deviceStore.devices.find((d) => d.device_name === [sel.value.mqtt].flat()[0]))

// 可设定目标值的执行器：风机转速、伺服角度
const setpointRange = computed(() => (sel.value && /风机|伺服/.test(sel.value.kind) ? sel.value.range : null))
const setpointStep = computed(() => (sel.value?.unit === 'RPM' ? 50 : 1))
const setpoint = ref(0)
// 切换设备或首次收到读数时，用当前值初始化目标值
watch(() => `${sel.value?.id}:${sel.value?.num != null}`, () => { setpoint.value = Math.round(sel.value?.num ?? 0) }, { immediate: true })

async function send(command, value) {
  busy.value = true
  const ok = await deviceStore.controlDevice([sel.value.mqtt].flat()[0], command, value)
  busy.value = false
  if (ok) ElMessage.success('指令已下发')
}

async function remove(r) {
  try {
    await ElMessageBox.confirm(`删除 ${r.tag}（${[r.mqtt].flat().join('、')}）的设备记录？历史数据不会删除。`, '删除设备', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  for (const name of [r.mqtt].flat()) await deviceStore.deleteDevice(name).catch(() => {})
  ElMessage.success('已删除')
  deviceStore.fetchDevices()
}

const addOpen = ref(false)
const formRef = ref(null)
const form = reactive({ device_name: '', device_type: 'sensor', unit: '' })
const rules = {
  device_name: [{ required: true, message: '请输入设备名', trigger: 'blur' }, { pattern: /^[\w-]+$/, message: '只能包含字母、数字、下划线和连字符', trigger: 'blur' }],
  device_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}
function resetForm() { formRef.value?.resetFields() }
async function add() {
  if (!(await formRef.value.validate().catch(() => false))) return
  busy.value = true
  try {
    if (await deviceStore.addDevice({ ...form })) {
      ElMessage.success('设备已添加，收到上报数据后显示读数')
      addOpen.value = false
      deviceStore.fetchDevices()
      refresh()
    }
  } catch { /* 错误提示由请求拦截器显示 */ } finally { busy.value = false }
}

onMounted(() => deviceStore.fetchDevices())
</script>

<style scoped>
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.filters .search { flex: 2 1 260px; }
.filters .el-select { flex: 1 1 150px; max-width: 200px; }
.spacer { flex: 1; }
.align-start { align-items: flex-start; }
.detail h2 { margin: 0; font-size: 20px; }
.big { font-size: 40px; font-weight: 600; line-height: 1; }
.note { padding: 10px 12px; border-radius: 10px; font-size: 13px; }
.note[data-status="warn"] { color: var(--warn-fg); background: var(--warn-soft); }
.note[data-status="alarm"] { color: var(--alarm-fg); background: var(--alarm-soft); }
.control { display: flex; flex-direction: column; gap: 12px; margin: 0; padding: 14px 0 0; border: 0; border-top: 1px solid var(--grid); }
.control legend { float: left; width: 100%; margin-bottom: 4px; padding: 0; font-size: 14px; font-weight: 700; }
.control .segmented button { flex: 1; justify-content: center; }
.control .segmented { display: flex; }
.field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.field span { display: flex; justify-content: space-between; }
.facts { display: grid; grid-template-columns: 76px minmax(0, 1fr); gap: 8px 12px; margin: 0; padding-top: 14px; border-top: 1px solid var(--grid); font-size: 13px; }
.facts dt { color: var(--muted); }
.facts dd { margin: 0; }
.links { display: flex; gap: 8px; }
.links a { flex: 1; }
.links .el-button { width: 100%; }
</style>
