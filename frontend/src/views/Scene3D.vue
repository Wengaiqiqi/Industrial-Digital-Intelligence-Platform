<template>
  <div class="scene-page">
    <div class="scene-toolbar">
      <div class="segmented" role="group" aria-label="场景模式">
        <button type="button" :aria-pressed="mode === 'monitor'" @click="setMode('monitor')">监视</button>
        <button type="button" :aria-pressed="mode === 'edit'" @click="setMode('edit')">编辑</button>
      </div>
      <template v-if="mode === 'edit'">
        <div class="segmented" role="group" aria-label="变换工具">
          <button v-for="t in tools" :key="t.id" type="button" :aria-pressed="tool === t.id" @click="setTool(t.id)">
            {{ t.label }}<kbd>{{ t.key }}</kbd>
          </button>
        </div>
        <button type="button" class="tool-btn" :aria-pressed="snap" @click="toggleSnap">吸附网格 <span class="mono">0.5 m</span></button>
        <button type="button" class="tool-btn" @click="fileInput.click()">导入模型 <span class="mono">glTF · OBJ · FBX</span></button>
        <input ref="fileInput" type="file" accept=".gltf,.glb,.obj,.fbx" hidden @change="importModel">
        <span class="spacer"></span>
        <span v-if="dirty" class="dirty">有未保存的更改</span>
        <button type="button" class="tool-btn" @click="resetLayout">恢复默认布局</button>
        <el-button type="primary" @click="saveLayout">保存布局</el-button>
      </template>
      <template v-else>
        <span class="spacer"></span>
        <span class="mono muted">{{ boundCount }} 个数据点位 · {{ lastPoll ? `更新于 ${lastPoll}` : '等待数据…' }}</span>
      </template>
    </div>

    <div class="scene-body">
      <aside class="panel side-panel" :aria-label="mode === 'edit' ? '设备库' : '场景大纲'">
        <template v-if="mode === 'monitor'">
          <div class="panel-head"><h2>场景大纲</h2><span class="mono muted">{{ zones.length }} 区 · {{ boundCount }} 点位</span></div>
          <el-input v-model="search" placeholder="搜索位号 / 名称" clearable aria-label="搜索设备位号或名称" />
          <div v-for="z in outline" :key="z.name" class="zone">
            <div class="zone-name">{{ z.name }}</div>
            <button v-for="row in z.rows" :key="row.id" type="button" class="outline-row" :aria-pressed="selectedId === row.id" @click="select(row.id, true)">
              <span class="dot" :data-status="row.status"></span>
              <span class="row-copy"><span class="mono muted">{{ row.tag }}</span><span>{{ row.name }}</span></span>
              <span class="mono row-value" :data-status="row.status">{{ row.value }}</span>
            </button>
          </div>
        </template>
        <template v-else>
          <div class="panel-head"><h2>设备库</h2><span class="mono muted">点击添加到场景中心</span></div>
          <div class="library">
            <button v-for="m in MODEL_LIBRARY" :key="m.type" type="button" class="library-item" @click="addFromLibrary(m)">
              <span>{{ m.name }}</span>
              <span class="mono muted">{{ m.category }} · {{ m.grade }}</span>
            </button>
          </div>
          <p class="hint">按 1 单位 = 1 m 建模；导入的模型自动居中并缩放到 2 m 内，仅在本次会话有效。</p>
        </template>
      </aside>

      <section class="viewport-col" aria-label="三维视口">
        <div ref="viewport" class="viewport" :class="{ editing: mode === 'edit' }">
          <div class="overlay top-left segmented" role="group" aria-label="视角预设">
            <button v-for="v in views" :key="v.id" type="button" :aria-pressed="view === v.id" @click="goView(v.id)">{{ v.label }}</button>
          </div>
          <div class="overlay top-right segmented" role="group" aria-label="图层">
            <button v-for="l in layerDefs" :key="l.id" type="button" :aria-pressed="layers[l.id]" @click="layers[l.id] = !layers[l.id]">
              <span class="check"></span>{{ l.label }}
            </button>
          </div>
          <div class="overlay bottom-right zoom">
            <button type="button" aria-label="放大" @click="zoom(0.8)">+</button>
            <span class="mono">{{ zoomLabel }}</span>
            <button type="button" aria-label="缩小" @click="zoom(1.25)">−</button>
            <button type="button" aria-label="适应屏幕" @click="goView(view)"><el-icon><FullScreen /></el-icon></button>
          </div>
          <div class="overlay bottom-left legend">
            <span><i data-status="ok"></i>正常</span>
            <span><i data-status="warn"></i>预警</span>
            <span><i data-status="alarm"></i>告警</span>
            <span><i data-status="offline"></i>离线</span>
            <span class="mono muted">网格 1 m</span>
          </div>
          <div v-if="mode === 'edit'" class="overlay top-center edit-tip">编辑中 · 拖动手柄变换对象，W / E / R 切换移动、旋转、缩放</div>
        </div>
        <div class="events">
          <button v-for="e in events" :key="e.id" type="button" class="event" :data-status="e.status" @click="select(e.id, true)">
            <span class="mono">{{ e.tag }}</span><span class="event-text">{{ e.name }} {{ e.value }}</span><span class="event-go">定位</span>
          </button>
          <div v-if="!events.length" class="event quiet">全部设备运行正常</div>
        </div>
      </section>

      <aside class="panel inspector" aria-label="设备检视">
        <template v-if="selected">
          <div class="insp-head">
            <div class="insp-row"><span class="mono muted">{{ selected.tag }}</span><span v-if="selected.bound" class="badge" :data-status="selected.status">{{ STATUS_LABEL[selected.status] }}</span></div>
            <h2>{{ selected.name }}</h2>
            <div class="muted small">{{ selected.kind }}<template v-if="selected.zone"> · {{ selected.zone }}</template></div>
          </div>

          <div v-if="selected.bound" class="insp-section">
            <div class="big-value mono" :data-status="selected.status">{{ selected.value }}</div>
            <div v-if="selected.range" class="range">
              <div class="bar"><div :style="{ width: selected.pct + '%' }" :data-status="selected.status"></div></div>
              <div class="mono muted small range-text"><span>量程 / 阈值</span><span>{{ selected.range }}</span></div>
            </div>
            <div v-if="selected.note" class="note" :data-status="selected.status">{{ selected.note }}</div>
            <div class="spark">
              <div class="muted small range-text"><span>近 2 分钟</span><span class="mono">{{ selected.samples }} 个采样</span></div>
              <svg viewBox="0 0 260 60" preserveAspectRatio="none" role="img" aria-label="近 2 分钟数值走势"><polyline :points="selected.spark" /></svg>
            </div>
          </div>

          <dl class="insp-section facts">
            <template v-if="selected.loc"><dt>安装位置</dt><dd>{{ selected.loc }}</dd></template>
            <dt>MQTT 点位</dt><dd class="mono">{{ selected.mqttText }}</dd>
            <dt>模型</dt><dd>{{ selected.model }}</dd>
          </dl>

          <div v-if="mode === 'edit'" class="insp-section edit">
            <div class="field-label">位置 m</div>
            <div class="xyz">
              <el-input-number v-for="(axis, i) in ['X', 'Y', 'Z']" :key="axis" v-model="xform.p[i]" :step="0.5" :precision="2" size="small" controls-position="right" :aria-label="`位置 ${axis}`" @change="applyXform" />
            </div>
            <div class="field-label">朝向 °（绕竖直轴）</div>
            <el-input-number v-model="xform.ry" :step="15" size="small" controls-position="right" aria-label="朝向角度" @change="applyXform" />
            <div class="field-label">缩放</div>
            <el-input-number v-model="xform.s" :step="0.1" :min="0.1" :precision="2" size="small" controls-position="right" aria-label="缩放" @change="applyXform" />
            <div class="field-label">绑定 MQTT 设备</div>
            <el-select v-model="xform.mqtt" clearable filterable placeholder="未绑定" aria-label="绑定 MQTT 设备" @change="applyBinding">
              <el-option v-for="k in mqttOptions" :key="k" :label="k" :value="k" />
            </el-select>
            <el-button v-if="selected.added" type="danger" plain @click="removeSelected">删除对象</el-button>
          </div>

          <div class="insp-actions">
            <el-button type="primary" @click="focusSelected">聚焦设备</el-button>
            <router-link class="link-btn" to="/historical-data">历史曲线</router-link>
            <router-link class="link-btn wide" to="/devices">设备详情与控制</router-link>
          </div>
        </template>
        <div v-else class="insp-empty muted">在场景或左侧大纲中选择一台设备，查看实时数值、阈值和走势。</div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FullScreen } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import { deviceAPI } from '../api'
import { theme } from '../theme'
import { ModelLoader } from '../utils/ModelLoader.js'
import { DEVICES, STRUCTURES, PIPES, ZONES, STATUS_LABEL, deviceStatus, formatValue, readingFor } from '../utils/plantLayout'
import { PALETTES, MODEL_LIBRARY, buildModel, buildPipe, buildFloor, rethemeFloor, retheme, buildStatusRing, applyStatus, animateStatus } from '../utils/plantModels'

const LAYOUT_KEY = 'idp-scene-layout-v1'
const DEFAULT_DIST = 30
const tools = [{ id: 'translate', label: '移动', key: 'W' }, { id: 'rotate', label: '旋转', key: 'E' }, { id: 'scale', label: '缩放', key: 'R' }]
const views = [{ id: 'iso', label: '等轴测' }, { id: 'top', label: '俯视' }, { id: 'line', label: '沿产线' }]
const layerDefs = [{ id: 'labels', label: '数据标签' }, { id: 'flow', label: '介质流向' }, { id: 'heat', label: '告警热区' }]
const MODEL_NAMES = Object.fromEntries(MODEL_LIBRARY.map((m) => [m.type, `${m.name} · ${m.grade} 级`]))
const zones = ZONES

const viewport = ref(null)
const fileInput = ref(null)
const mode = ref('monitor')
const tool = ref('translate')
const snap = ref(true)
const view = ref('iso')
const layers = reactive({ labels: true, flow: true, heat: true })
const search = ref('')
const selectedId = ref(null)
const dirty = ref(false)
const lastPoll = ref('')
const zoomLabel = ref('100%')
const rawKeys = ref([])
const xform = reactive({ p: [0, 0, 0], ry: 0, s: 1, mqtt: null })
// 设备读数与状态：渲染循环外的 Vue 视图通过 tick 刷新
const tick = ref(0)
const objects = shallowRef(new Map())

let scene, camera, renderer, labelRenderer, controls, transform, floor, hemi, sun, fill, selectionBox, modelLoader
let pipes = []
let raw = {}
let pollTimer, frameId, resizeObserver
const clock = new THREE.Clock()
const tween = { t: 1, fromPos: new THREE.Vector3(), toPos: new THREE.Vector3(), fromTarget: new THREE.Vector3(), toTarget: new THREE.Vector3() }

const palette = () => PALETTES[theme.value]

// ---------- 对象（设备 / 结构 / 自添加） ----------

function addObject(def) {
  const model = buildModel(def.model, palette(), { sensorAt: def.sensorAt, level: def.level, length: def.length })
  model.position.fromArray(def.pos)
  if (def.rot) model.rotation.set(...def.rot)
  if (def.scale) model.scale.setScalar(def.scale)
  model.userData.objectId = def.id
  scene.add(model)
  const obj = { def, model, status: 'offline', history: [], reading: null, ringGroup: null, label: null }
  objects.value.set(def.id, obj)
  if (def.mqtt) bindObject(obj)
  return obj
}

function bindObject(obj) {
  const ringGroup = buildStatusRing(obj.model.userData.footprint || 1)
  scene.add(ringGroup)
  const el = document.createElement('button')
  el.type = 'button'
  el.className = 'scene-label'
  el.innerHTML = '<i></i><span class="tag"></span><span class="name"></span><b class="val">—</b>'
  el.querySelector('.tag').textContent = obj.def.tag
  el.querySelector('.name').textContent = obj.def.name
  el.addEventListener('click', () => select(obj.def.id, false))
  const label = new CSS2DObject(el)
  label.center.set(0.5, 1)
  label.position.set(0, obj.model.userData.labelY || 1.5, 0)
  obj.model.add(label)
  Object.assign(obj, { ringGroup, label, el })
  updateObject(obj)
}

function unbindObject(obj) {
  if (!obj.ringGroup) return
  scene.remove(obj.ringGroup)
  obj.model.remove(obj.label)
  obj.el.remove()
  Object.assign(obj, { ringGroup: null, label: null, el: null, reading: null, history: [] })
  obj.model.traverse((o) => { if (o.material?.userData?.role) { o.material.emissiveIntensity = 0; o.material.opacity = 1; o.material.transparent = false } })
}

function updateObject(obj) {
  const status = deviceStatus(obj.def, obj.reading)
  applyStatus(obj, status, palette())
  obj.el.dataset.status = status
  obj.el.querySelector('.val').textContent = formatValue(obj.def, obj.reading)
}

function disposeObject(obj) {
  if (obj.ringGroup) unbindObject(obj)
  scene.remove(obj.model)
  obj.model.traverse((o) => { o.geometry?.dispose(); if (o.material && !Array.isArray(o.material)) o.material.dispose() })
  objects.value.delete(obj.def.id)
}

// ---------- 场景搭建 ----------

function loadSavedLayout() {
  try { return JSON.parse(localStorage.getItem(LAYOUT_KEY)) || {} } catch { return {} }
}

function buildPlant() {
  const p = palette()
  floor = buildFloor(p)
  scene.add(floor)
  pipes = PIPES.map((pts) => { const g = buildPipe(pts, p); scene.add(g); return g })
  const saved = loadSavedLayout()
  for (const def of [...STRUCTURES, ...DEVICES]) {
    const o = saved.overrides?.[def.id]
    addObject(o ? { ...def, pos: o.p, rot: o.r, scale: o.s, mqtt: o.mqtt === undefined ? def.mqtt : o.mqtt } : { ...def })
  }
  for (const def of saved.added || []) addObject({ ...def, added: true })
}

function clearPlant() {
  select(null)
  for (const obj of [...objects.value.values()]) disposeObject(obj)
  for (const g of [...pipes, floor]) scene.remove(g)
  pipes = []
}

function applyTheme() {
  const p = palette()
  renderer.setClearColor(p.bg)
  scene.fog.color.set(p.bg)
  hemi.color.set(p.hemiSky)
  hemi.groundColor.set(p.hemiGround)
  hemi.intensity = p.hemi
  sun.intensity = p.sun
  fill.intensity = p.fill
  rethemeFloor(floor, p)
  pipes.forEach((g) => retheme(g, p))
  for (const obj of objects.value.values()) {
    retheme(obj.model, p)
    if (obj.ringGroup) applyStatus(obj, obj.status, p)
  }
  selectionBox.material.color.set(p.select)
}

function init() {
  const el = viewport.value
  const { clientWidth: w, clientHeight: h } = el
  scene = new THREE.Scene()
  scene.fog = new THREE.Fog(palette().bg, 30, 120)
  camera = new THREE.PerspectiveCamera(35, w / h, 0.1, 400)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  el.prepend(renderer.domElement)

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(w, h)
  labelRenderer.domElement.className = 'label-layer'
  el.appendChild(labelRenderer.domElement)

  hemi = new THREE.HemisphereLight()
  sun = new THREE.DirectionalLight(0xffffff, 1)
  sun.position.set(-10, 18, -8)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, far: 60 })
  fill = new THREE.DirectionalLight(0xffffff, 0.3)
  fill.position.set(10, 8, 12)
  scene.add(hemi, sun, fill)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2.05
  controls.minDistance = 4
  controls.maxDistance = 60
  controls.addEventListener('change', updateZoomLabel)

  transform = new TransformControls(camera, renderer.domElement)
  transform.setTranslationSnap(0.5)
  transform.setRotationSnap(THREE.MathUtils.degToRad(15))
  transform.setScaleSnap(0.1)
  transform.addEventListener('dragging-changed', (e) => { controls.enabled = !e.value })
  transform.addEventListener('objectChange', () => { dirty.value = true; syncXform() })
  scene.add(transform)

  selectionBox = new THREE.BoxHelper(undefined, palette().select)
  selectionBox.visible = false
  scene.add(selectionBox)

  modelLoader = new ModelLoader(scene)
  buildPlant()
  applyTheme()
  goView('iso', true)

  let down = null
  renderer.domElement.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY] })
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4 || transform.dragging) return
    pick(e)
  })
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(el)
  animate()
}

function resize() {
  const { clientWidth: w, clientHeight: h } = viewport.value
  if (!w || !h) return
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
  labelRenderer.setSize(w, h)
}

const raycaster = new THREE.Raycaster()
function pick(e) {
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1)
  raycaster.setFromCamera(ndc, camera)
  const models = [...objects.value.values()].map((o) => o.model)
  const hit = raycaster.intersectObjects(models, true)[0]
  let o = hit?.object
  while (o && !o.userData.objectId) o = o.parent
  select(o ? o.userData.objectId : null)
}

// ---------- 选择、相机 ----------

function select(id, focus = false) {
  selectedId.value = id
  const obj = id && objects.value.get(id)
  selectionBox.visible = !!obj
  if (obj) selectionBox.setFromObject(obj.model)
  if (mode.value === 'edit' && obj) transform.attach(obj.model)
  else transform.detach()
  if (obj) syncXform()
  if (obj && focus) focusSelected()
}

function syncXform() {
  const obj = objects.value.get(selectedId.value)
  if (!obj) return
  const m = obj.model
  xform.p = m.position.toArray().map((v) => +v.toFixed(2))
  xform.ry = Math.round(THREE.MathUtils.radToDeg(m.rotation.y))
  xform.s = +m.scale.x.toFixed(2)
  xform.mqtt = Array.isArray(obj.def.mqtt) ? obj.def.mqtt.join(',') : obj.def.mqtt || null
}

function applyXform() {
  const obj = objects.value.get(selectedId.value)
  if (!obj) return
  obj.model.position.fromArray(xform.p.map((v) => v ?? 0))
  obj.model.rotation.y = THREE.MathUtils.degToRad(xform.ry || 0)
  obj.model.scale.setScalar(xform.s || 1)
  dirty.value = true
}

function applyBinding(value) {
  const obj = objects.value.get(selectedId.value)
  if (!obj) return
  unbindObject(obj)
  obj.def = { ...obj.def, mqtt: value ? (value.includes(',') ? value.split(',') : value) : null }
  if (obj.def.mqtt) {
    bindObject(obj)
    obj.reading = readingFor(obj.def, raw)
    updateObject(obj)
  }
  dirty.value = true
  tick.value++
}

function startTween(pos, target, instant) {
  tween.fromPos.copy(camera.position)
  tween.fromTarget.copy(controls.target)
  tween.toPos.copy(pos)
  tween.toTarget.copy(target)
  tween.t = instant ? 1 : 0
  if (instant) { camera.position.copy(pos); controls.target.copy(target) }
}

function goView(id, instant = false) {
  view.value = id
  const target = new THREE.Vector3(1.2, 1, 0)
  const pos = {
    iso: new THREE.Vector3(1, 0.95, 1).normalize().multiplyScalar(DEFAULT_DIST).add(target),
    top: new THREE.Vector3(0, DEFAULT_DIST * 1.15, 0.01).add(target),
    line: new THREE.Vector3(-2.5, 4.2, 9.5)
  }[id]
  startTween(pos, id === 'line' ? new THREE.Vector3(5, 1, 2.5) : target, instant)
}

function focusSelected() {
  const obj = objects.value.get(selectedId.value)
  if (!obj) return
  const target = obj.model.getWorldPosition(new THREE.Vector3())
  target.y += (obj.model.userData.labelY || 2) * 0.4
  const dir = camera.position.clone().sub(controls.target).normalize()
  const fp = obj.model.userData.footprint || 1
  startTween(target.clone().add(dir.multiplyScalar(Math.max(8, fp * 6 + (obj.model.userData.labelY || 2) * 1.5))), target)
}

function zoom(factor) {
  const offset = camera.position.clone().sub(controls.target).multiplyScalar(factor)
  const len = THREE.MathUtils.clamp(offset.length(), controls.minDistance, controls.maxDistance)
  startTween(controls.target.clone().add(offset.setLength(len)), controls.target.clone())
}

function updateZoomLabel() {
  zoomLabel.value = Math.round((DEFAULT_DIST / camera.position.distanceTo(controls.target)) * 100) + '%'
}

// ---------- 渲染循环 ----------

const _v = new THREE.Vector3()
function animate() {
  frameId = requestAnimationFrame(animate)
  const dt = Math.min(clock.getDelta(), 0.1)
  const t = clock.elapsedTime
  if (tween.t < 1) {
    tween.t = Math.min(1, tween.t + dt / 0.6)
    const k = 1 - Math.pow(1 - tween.t, 3)
    camera.position.lerpVectors(tween.fromPos, tween.toPos, k)
    controls.target.lerpVectors(tween.fromTarget, tween.toTarget, k)
  }
  controls.update()

  for (const g of pipes) {
    const flow = g.getObjectByName('flow')
    flow.visible = layers.flow
    flow.material.map.offset.x -= dt * 1.2
  }
  for (const obj of objects.value.values()) {
    const m = obj.model
    const value = obj.reading?.value
    const blade = m.getObjectByName('blade')
    if (blade) blade.rotation.y += dt * (value == null ? 0 : Math.min(value, 3000) / 3000) * 14
    const joint = m.getObjectByName('joint_1')
    if (joint && value != null) joint.rotation.y += (THREE.MathUtils.degToRad(value) - joint.rotation.y) * Math.min(1, dt * 4)
    if (m.userData.model === 'conveyor') {
      m.getObjectByName('belt').material.map.offset.x -= dt * 0.25
      const half = m.userData.length / 2 - 0.3
      for (const b of m.getObjectByName('products').children) b.position.x = b.position.x + dt * 0.4 > half ? -half : b.position.x + dt * 0.4
    }
    if (obj.def.special === 'lamp') for (let i = 1; i <= 3; i++) m.getObjectByName(`lamp_${i}`).material.emissiveIntensity = value === i ? 1.3 : 0
    if (obj.def.special === 'io') {
      m.getObjectByName('di').material.emissiveIntensity = obj.reading?.di ? 1.3 : 0
      m.getObjectByName('do').material.emissiveIntensity = obj.reading?.do ? 1.3 : 0
    }
    if (obj.ringGroup) {
      m.getWorldPosition(_v)
      obj.ringGroup.position.set(_v.x, obj.def.special === 'lamp' ? _v.y : 0, _v.z)
      animateStatus(obj, t, layers.heat)
      obj.label.visible = layers.labels
      const d = camera.position.distanceTo(_v)
      obj.el.dataset.lod = d > 44 ? 'far' : d > 26 ? 'mid' : 'near'
    }
  }
  if (selectionBox.visible) selectionBox.setFromObject(objects.value.get(selectedId.value).model)
  renderer.render(scene, camera)
  labelRenderer.render(scene, camera)
}

// ---------- 数据 ----------

async function poll() {
  try {
    const res = await deviceAPI.getRealtimeDevices()
    const data = res.data || {}
    raw = Array.isArray(data) ? Object.fromEntries(data.map((d) => [d.device_name, d])) : data
    rawKeys.value = Object.keys(raw).sort()
    lastPoll.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch {
    // 后端不可用：保留旧读数，超时后自然转为离线
  }
  const now = Date.now()
  for (const obj of objects.value.values()) {
    if (!obj.def.mqtt) continue
    const r = readingFor(obj.def, raw, now)
    if (r && r.timestamp !== obj.reading?.timestamp) {
      obj.reading = r
      obj.history.push(r.value)
      if (obj.history.length > 60) obj.history.shift()
    }
    updateObject(obj)
  }
  tick.value++
}

// ---------- 编辑 ----------

function setMode(m) {
  mode.value = m
  select(selectedId.value)
}

function setTool(id) {
  tool.value = id
  transform.setMode(id)
}

function toggleSnap() {
  snap.value = !snap.value
  transform.setTranslationSnap(snap.value ? 0.5 : null)
  transform.setRotationSnap(snap.value ? THREE.MathUtils.degToRad(15) : null)
}

function onKey(e) {
  if (mode.value !== 'edit' || e.target.closest('input, textarea, select')) return
  const id = { w: 'translate', e: 'rotate', r: 'scale' }[e.key.toLowerCase()]
  if (id) setTool(id)
}

function addFromLibrary(m) {
  const id = `obj-${Date.now().toString(36)}`
  const obj = addObject({ id, tag: id.slice(4).toUpperCase(), name: m.name, model: m.type, pos: [0, 0, 0], added: true })
  dirty.value = true
  select(obj.def.id)
}

async function importModel(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  try {
    const { model } = await modelLoader.loadFromFile(file)
    const box = new THREE.Box3().setFromObject(model)
    const size = box.getSize(new THREE.Vector3())
    model.scale.multiplyScalar(2 / Math.max(size.x, size.y, size.z, 0.001))
    box.setFromObject(model)
    model.position.sub(new THREE.Vector3((box.min.x + box.max.x) / 2, box.min.y, (box.min.z + box.max.z) / 2))
    const id = `imp-${Date.now().toString(36)}`
    model.userData = { ...model.userData, objectId: id, model: 'imported', labelY: 2.4, footprint: 1.2 }
    objects.value.set(id, { def: { id, tag: id.slice(4).toUpperCase(), name: file.name, model: 'imported', added: true, imported: true }, model, status: 'ok', history: [], reading: null })
    select(id)
    ElMessage.success(`已导入 ${file.name}`)
  } catch (err) {
    ElMessage.error(`导入失败：${err.message}`)
  }
}

function removeSelected() {
  const obj = objects.value.get(selectedId.value)
  if (!obj?.def.added) return
  select(null)
  disposeObject(obj)
  dirty.value = true
  tick.value++
}

function saveLayout() {
  const overrides = {}
  const added = []
  for (const { def, model } of objects.value.values()) {
    if (def.imported) continue
    const entry = { p: model.position.toArray(), r: [model.rotation.x, model.rotation.y, model.rotation.z], s: model.scale.x, mqtt: def.mqtt ?? null }
    if (def.added) added.push({ id: def.id, tag: def.tag, name: def.name, model: def.model, pos: entry.p, rot: entry.r, scale: entry.s, mqtt: entry.mqtt })
    else overrides[def.id] = entry
  }
  localStorage.setItem(LAYOUT_KEY, JSON.stringify({ overrides, added }))
  dirty.value = false
  ElMessage.success('布局已保存')
}

async function resetLayout() {
  try {
    await ElMessageBox.confirm('将删除已保存的布局和新增对象，恢复 LINE-01 默认布局。', '恢复默认布局', { type: 'warning', confirmButtonText: '恢复', cancelButtonText: '取消' })
  } catch { return }
  localStorage.removeItem(LAYOUT_KEY)
  clearPlant()
  buildPlant()
  applyTheme()
  dirty.value = false
  poll()
}

// ---------- 面板数据 ----------

const objectsList = computed(() => { tick.value; return [...objects.value.values()] })
const boundCount = computed(() => objectsList.value.filter((o) => o.def.mqtt).length)
const mqttOptions = computed(() => {
  const opts = new Set(rawKeys.value)
  DEVICES.forEach((d) => [d.mqtt].flat().forEach((k) => opts.add(k)))
  opts.add('digital_input_1,digital_output_1')
  return [...opts]
})

const rowOf = (o) => ({ id: o.def.id, tag: o.def.tag, name: o.def.name, status: o.status, value: formatValue(o.def, o.reading) })

const outline = computed(() => {
  const q = search.value.trim().toLowerCase()
  const rows = objectsList.value.filter((o) => o.def.mqtt && (!q || `${o.def.tag}${o.def.name}`.toLowerCase().includes(q)))
  const groups = ZONES.map((z) => ({ name: z.name, rows: rows.filter((o) => o.def.zone === z.name).map(rowOf) }))
  const other = rows.filter((o) => !ZONES.some((z) => z.name === o.def.zone)).map(rowOf)
  if (other.length) groups.push({ name: '新增对象', rows: other })
  return groups.filter((g) => g.rows.length)
})

const events = computed(() => objectsList.value
  .filter((o) => o.def.mqtt && (o.status === 'alarm' || o.status === 'warn'))
  .sort((a, b) => (a.status === 'alarm' ? -1 : 1) - (b.status === 'alarm' ? -1 : 1))
  .map(rowOf))

const selected = computed(() => {
  tick.value
  const o = selectedId.value && objects.value.get(selectedId.value)
  if (!o) return null
  const d = o.def
  const bound = !!d.mqtt
  const [min, max] = d.range || []
  const v = o.reading?.value
  const pct = d.range && v != null ? Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100)) : 0
  const hist = o.history
  const lo = d.range ? min : Math.min(...hist), hi = d.range ? max : Math.max(...hist)
  const spark = hist.map((h, i) => `${(i / Math.max(hist.length - 1, 1)) * 260},${Math.min(58, Math.max(2, 56 - ((h - lo) / ((hi - lo) || 1)) * 52))}`).join(' ')
  const note = { alarm: d.alarm && `数值越过阈值 ${d.alarm[0]} – ${d.alarm[1]} ${d.unit}，请立即检查。`, warn: d.alarm ? `接近阈值上下限（8% 以内）。` : d.special === 'lamp' ? '塔灯处于预警状态。' : '', offline: bound ? '超过 15 秒未收到该点位数据。' : '' }[o.status]
  return {
    tag: d.tag, name: d.name, kind: d.kind || MODEL_NAMES[d.model] || '导入模型', zone: d.zone, loc: d.loc, added: d.added,
    bound, status: o.status, value: formatValue(d, o.reading), pct,
    range: d.range && d.unit !== undefined ? `${min} – ${max} ${d.unit}`.trim() : '',
    note, spark, samples: hist.length,
    mqttText: [d.mqtt].flat().filter(Boolean).join(' · ') || '未绑定',
    model: MODEL_NAMES[d.model] || '导入模型'
  }
})

watch(() => theme.value, () => scene && applyTheme())

onMounted(() => {
  init()
  poll()
  pollTimer = setInterval(poll, 2000)
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
  cancelAnimationFrame(frameId)
  resizeObserver?.disconnect()
  window.removeEventListener('keydown', onKey)
  transform.dispose()
  controls.dispose()
  renderer.dispose()
})
</script>

<style scoped>
.scene-page { display: flex; flex-direction: column; gap: 14px; height: calc(100vh - 120px); min-height: 680px; }
.scene-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.spacer { flex: 1; }
.mono { font-family: var(--font-mono); }
.muted { color: var(--muted); }
.small { font-size: 12px; }
kbd { margin-left: 4px; color: var(--muted); font-family: var(--font-mono); font-size: 11px; }
.tool-btn { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 12px; color: var(--ink); background: var(--paper-soft); border: 1px solid var(--grid); border-radius: 10px; cursor: pointer; font-size: 13px; }
.tool-btn[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--data-3); }
.tool-btn .mono { color: var(--muted); font-size: 11px; }
.dirty { color: var(--warn-fg); font-size: 13px; }

.scene-body { display: grid; flex: 1; grid-template-columns: 250px minmax(0, 1fr) 300px; gap: 14px; min-height: 0; }
.panel { display: flex; flex-direction: column; gap: 12px; min-height: 0; padding: 14px; overflow: auto; background: var(--paper-soft); border: 1px solid var(--grid); border-radius: var(--panel-radius); }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.panel-head h2, .insp-head h2 { margin: 0; font-size: 15px; font-weight: 700; }
.panel-head .mono { font-size: 11px; }
.zone-name { padding: 6px 4px; color: var(--muted); font-size: 12px; letter-spacing: .06em; }
.outline-row { display: flex; align-items: center; gap: 10px; width: 100%; min-height: 44px; padding: 6px 10px; color: var(--ink); background: transparent; border: 1px solid transparent; border-radius: 9px; cursor: pointer; text-align: left; }
.outline-row:hover { background: var(--quiet); }
.outline-row[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--data-3); }
.row-copy { display: flex; flex: 1; flex-direction: column; min-width: 0; font-size: 13px; }
.row-copy .mono { font-size: 12px; }
.row-value { color: var(--muted); font-size: 12px; white-space: nowrap; }
.row-value[data-status="warn"] { color: var(--warn-fg); }
.row-value[data-status="alarm"] { color: var(--alarm-fg); }
.dot { flex: none; width: 8px; height: 8px; border-radius: 4px; background: var(--data); }
[data-status="warn"].dot, .legend i[data-status="warn"] { background: var(--warn); }
[data-status="alarm"].dot, .legend i[data-status="alarm"] { background: var(--alarm); }
[data-status="offline"].dot, .legend i[data-status="offline"] { background: transparent; border: 1.5px dashed var(--muted); }
.library { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.library-item { display: flex; flex-direction: column; gap: 4px; padding: 10px; color: var(--ink); background: var(--surface-2); border: 1px solid var(--grid); border-radius: 10px; cursor: pointer; text-align: left; font-size: 13px; }
.library-item:hover { border-color: var(--data-3); background: var(--accent-soft); }
.library-item .mono { font-size: 11px; }
.hint { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.6; }

.viewport-col { display: flex; flex-direction: column; gap: 10px; min-width: 0; min-height: 0; }
.viewport { position: relative; flex: 1; min-height: 0; overflow: hidden; border: 1px solid var(--grid); border-radius: var(--panel-radius); }
.viewport.editing { border-color: var(--warn-line); }
.viewport :deep(canvas) { display: block; }
.viewport :deep(.label-layer) { position: absolute; inset: 0; z-index: 1; pointer-events: none; }
.overlay { position: absolute; z-index: 2; }
.top-left { top: 12px; left: 12px; }
.top-right { top: 12px; right: 12px; }
.top-center { top: 60px; left: 50%; transform: translateX(-50%); }
.bottom-right { right: 12px; bottom: 12px; }
.bottom-left { left: 12px; bottom: 12px; }
.overlay.segmented { background: color-mix(in srgb, var(--paper-soft) 90%, transparent); }
.check { width: 14px; height: 14px; border: 1.5px solid currentColor; border-radius: 4px; }
[aria-pressed="true"] > .check { background: var(--data); border-color: var(--data); }
.zoom { display: flex; flex-direction: column; overflow: hidden; background: color-mix(in srgb, var(--paper-soft) 92%, transparent); border: 1px solid var(--grid); border-radius: 10px; }
.zoom button { display: grid; place-items: center; width: 42px; height: 38px; color: var(--ink); background: transparent; border: 0; cursor: pointer; font-size: 18px; }
.zoom span { padding: 4px 0; color: var(--muted); border-block: 1px solid var(--grid); font-size: 11px; text-align: center; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 12px; color: var(--ink); background: color-mix(in srgb, var(--paper-soft) 92%, transparent); border: 1px solid var(--grid); border-radius: 10px; font-size: 12px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 8px; height: 8px; border-radius: 4px; background: var(--data); box-sizing: border-box; }
.edit-tip { padding: 6px 12px; color: var(--warn-fg); background: var(--warn-soft); border: 1px solid var(--warn-line); border-radius: 10px; font-size: 13px; white-space: nowrap; }

.events { display: flex; flex-wrap: wrap; gap: 10px; }
.event { display: flex; flex: 1 1 240px; align-items: center; gap: 12px; min-height: 44px; padding: 8px 14px; color: var(--ink); background: var(--paper-soft); border: 1px solid var(--grid); border-radius: 12px; cursor: pointer; text-align: left; font-size: 13px; }
.event[data-status="alarm"] { background: var(--alarm-soft); border-color: var(--alarm-line); }
.event[data-status="warn"] { background: var(--warn-soft); border-color: var(--warn-line); }
.event[data-status="alarm"] .mono { color: var(--alarm-fg); }
.event[data-status="warn"] .mono { color: var(--warn-fg); }
.event-text { flex: 1; min-width: 0; }
.event-go { color: var(--muted); font-size: 12px; }
.event.quiet { color: var(--muted); cursor: default; }

.inspector { gap: 0; padding: 0; }
.insp-head, .insp-section, .insp-actions { padding: 14px 18px; border-bottom: 1px solid var(--grid); }
.insp-head { display: flex; flex-direction: column; gap: 6px; }
.insp-head h2 { font-size: 20px; }
.insp-row { display: flex; align-items: center; justify-content: space-between; }
.badge { padding: 3px 10px; color: var(--data-2); background: var(--accent-soft); border-radius: 6px; font-size: 12px; font-weight: 600; }
.badge[data-status="warn"], .note[data-status="warn"] { color: var(--warn-fg); background: var(--warn-soft); }
.badge[data-status="alarm"], .note[data-status="alarm"] { color: var(--alarm-fg); background: var(--alarm-soft); }
.badge[data-status="offline"], .note[data-status="offline"] { color: var(--muted); background: var(--quiet); }
.insp-section { display: flex; flex-direction: column; gap: 12px; }
.big-value { font-size: 36px; font-weight: 600; line-height: 1; }
.big-value[data-status="warn"] { color: var(--warn-fg); }
.big-value[data-status="alarm"] { color: var(--alarm-fg); }
.bar { height: 8px; overflow: hidden; background: var(--quiet); border-radius: 4px; }
.bar div { height: 100%; background: var(--data); border-radius: 4px; }
.bar div[data-status="warn"] { background: var(--warn); }
.bar div[data-status="alarm"] { background: var(--alarm); }
.range-text { display: flex; justify-content: space-between; margin-top: 6px; }
.note { padding: 10px 12px; color: var(--data-2); background: var(--accent-soft); border-radius: 10px; font-size: 13px; line-height: 1.5; }
.spark svg { width: 100%; height: 60px; margin-top: 6px; background: var(--surface-2); border-radius: 8px; }
.spark polyline { fill: none; stroke: var(--data); stroke-width: 2; vector-effect: non-scaling-stroke; }
.facts { display: grid; grid-template-columns: 76px minmax(0, 1fr); gap: 8px 12px; margin: 0; font-size: 13px; }
.facts dt { color: var(--muted); }
.facts dd { margin: 0; word-break: break-all; }
.facts .mono { font-size: 12px; }
.field-label { color: var(--muted); font-size: 12px; }
.xyz { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.edit :deep(.el-input-number) { width: 100%; }
.insp-actions { display: flex; flex-wrap: wrap; gap: 8px; border-bottom: 0; }
.insp-actions .el-button { flex: 1 1 110px; margin: 0; }
.link-btn { display: inline-flex; flex: 1 1 110px; align-items: center; justify-content: center; height: 32px; color: var(--ink); border: 1px solid var(--grid); border-radius: 9px; font-size: 13px; }
.link-btn.wide { flex-basis: 100%; }
.insp-empty { padding: 24px 18px; font-size: 13px; line-height: 1.7; }

@media (max-width: 1360px) {
  .scene-body { grid-template-columns: 220px minmax(0, 1fr) 270px; }
}
</style>

<style>
/* CSS2D 标签挂在 three 的独立图层上，不受 scoped 影响 */
.scene-label {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
  align-items: center;
  margin-bottom: 8px;
  padding: 6px 10px;
  color: var(--ink);
  background: color-mix(in srgb, var(--paper-soft) 93%, transparent);
  border: 1px solid var(--grid);
  border-radius: 6px;
  cursor: pointer;
  font: 11px/1.3 var(--font-mono);
  pointer-events: auto;
  text-align: left;
  white-space: nowrap;
}
.scene-label i { width: 7px; height: 7px; background: var(--data); border-radius: 4px; }
.scene-label .tag { color: var(--muted); }
.scene-label .name { display: none; }
.scene-label .val { grid-column: 1 / -1; color: var(--ink-strong); font-size: 15px; font-weight: 600; }
.scene-label[data-lod="near"] .name { display: inline; grid-column: 2; color: var(--muted); font-family: "Noto Sans SC", system-ui, sans-serif; }
.scene-label[data-lod="near"] { grid-template-columns: auto auto 1fr; }
.scene-label[data-lod="near"] .val { grid-column: 1 / -1; }
.scene-label[data-lod="mid"] { grid-template-columns: auto auto auto; }
.scene-label[data-lod="mid"] .val { grid-column: auto; font-size: 13px; }
.scene-label[data-lod="far"] { padding: 3px; border-radius: 8px; }
.scene-label[data-lod="far"] .tag, .scene-label[data-lod="far"] .val { display: none; }
.scene-label[data-status="warn"] { background: color-mix(in srgb, var(--warn-soft) 95%, transparent); border-color: var(--warn-line); }
.scene-label[data-status="warn"] i { background: var(--warn); }
.scene-label[data-status="warn"] .val { color: var(--warn-fg); }
.scene-label[data-status="alarm"] { z-index: 10 !important; background: color-mix(in srgb, var(--alarm-soft) 96%, transparent); border-color: var(--alarm); }
.scene-label[data-status="alarm"] i { background: var(--alarm); }
.scene-label[data-status="alarm"] .val { color: var(--alarm-fg); }
.scene-label[data-status="offline"] { opacity: .7; }
.scene-label[data-status="offline"] i { background: transparent; border: 1.5px dashed var(--muted); }
</style>
