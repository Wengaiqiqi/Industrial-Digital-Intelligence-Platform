import * as THREE from 'three'
import { ZONES } from './plantLayout'

// 按《三维建模规范》：1 单位 = 1 m，原点在底面中心，Y 向上；本体只用中性金属色，状态色留给数据层。
export const PALETTES = {
  dark: {
    bg: '#0a0e12', floor: '#0f151b', grid: '#1b2630', zone: '#2e3d49', zoneText: '#78878f', walkway: '#2a3742',
    steel: '#8896a1', paint: '#56636e', iron: '#3a4652', rubber: '#1a2128', motor: '#6a8399', vessel: '#7d95a7',
    glass: '#16222a', liquid: '#46c2d6', screen: '#0f1a20', cardboard: '#8a8173', lampOff: '#3b4752',
    hemiSky: '#cfe3f0', hemiGround: '#0b0f13', hemi: 0.75, sun: 1.25, fill: 0.3,
    ok: '#46c2d6', warn: '#f0a33a', alarm: '#ff6a55', offline: '#5d6873', select: '#e8eef2', accent: '#46c2d6'
  },
  light: {
    bg: '#e9eef2', floor: '#e6ebef', grid: '#d2dae1', zone: '#aeb9c3', zoneText: '#5b6975', walkway: '#c3cdd6',
    steel: '#7f8d98', paint: '#6e7b87', iron: '#4e5a65', rubber: '#3a4652', motor: '#5e7a90', vessel: '#6e8496',
    glass: '#2b3740', liquid: '#2fd0e6', screen: '#1b2a33', cardboard: '#b2a284', lampOff: '#8c9aa6',
    hemiSky: '#ffffff', hemiGround: '#9aa6b0', hemi: 1.0, sun: 1.05, fill: 0.35,
    ok: '#0f7f91', warn: '#c27a0e', alarm: '#d0402a', offline: '#8c9aa6', select: '#16202a', accent: '#0f7f91'
  }
}

const MAT_DEFS = {
  steel: { metalness: 0.45, roughness: 0.42 },
  paint: { metalness: 0.2, roughness: 0.6 },
  iron: { metalness: 0.3, roughness: 0.75 },
  rubber: { metalness: 0, roughness: 0.9 },
  motor: { metalness: 0.3, roughness: 0.5 },
  vessel: { metalness: 0.5, roughness: 0.38 },
  glass: { metalness: 0.1, roughness: 0.15 },
  liquid: { metalness: 0, roughness: 0.3, emissive: true },
  screen: { metalness: 0, roughness: 0.4 },
  cardboard: { metalness: 0, roughness: 0.95 },
  lampOff: { metalness: 0.1, roughness: 0.4 }
}

// 每台设备一套材质，便于单独叠加状态自发光；role 用于切换主题时换色
export function createMaterials(p) {
  const mats = {}
  for (const [role, def] of Object.entries(MAT_DEFS)) {
    const m = new THREE.MeshStandardMaterial({ color: p[role], metalness: def.metalness, roughness: def.roughness })
    if (def.emissive) { m.emissive.set(p[role]); m.emissiveIntensity = 0.35 }
    m.userData.role = role
    mats[role] = m
  }
  return mats
}

export function retheme(root, p) {
  root.traverse((o) => {
    const m = o.material
    if (!m || Array.isArray(m)) return
    if (m.userData.role) m.color.set(p[m.userData.role])
    if (m.userData.role === 'liquid') m.emissive.set(p.liquid)
    if (m.userData.statusRole) m.color.set(p[m.userData.statusRole])
  })
}

const mesh = (geo, mat, x = 0, y = 0, z = 0) => {
  const m = new THREE.Mesh(geo, mat)
  m.position.set(x, y, z)
  m.castShadow = true
  m.receiveShadow = true
  return m
}
const box = (w, h, d, mat, x, y, z) => mesh(new THREE.BoxGeometry(w, h, d), mat, x, y, z)
const cyl = (rt, rb, h, mat, x, y, z, seg = 32) => mesh(new THREE.CylinderGeometry(rt, rb, h, seg), mat, x, y, z)

function lamp(color, on) {
  const m = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: on ? 1.2 : 0, roughness: 0.3 })
  return m
}

// ---------- 设备模型 ----------

function tank(mats, { level = 0.62 } = {}) {
  const g = new THREE.Group()
  const r = 1, h = 3.75
  g.add(cyl(r * 1.04, r * 1.04, 0.12, mats.iron, 0, 0.06, 0))
  g.add(cyl(r, r, h, mats.steel, 0, h / 2 + 0.12, 0, 48))
  const head = mesh(new THREE.SphereGeometry(r, 48, 16, 0, Math.PI * 2, 0, Math.PI / 2), mats.steel, 0, h + 0.12, 0)
  head.scale.y = 0.28
  g.add(head)
  g.add(cyl(0.32, 0.32, 0.18, mats.iron, 0, h + 0.4, 0))
  for (const y of [1.1, 2.4]) {
    const seam = mesh(new THREE.TorusGeometry(r + 0.005, 0.025, 8, 64), mats.iron, 0, y, 0)
    seam.rotation.x = Math.PI / 2
    g.add(seam)
  }
  // 液位视窗：独立网格，按液位缩放
  g.add(box(0.14, h * 0.8, 0.06, mats.glass, 0.55, h * 0.48, r * 0.86))
  const liquid = box(0.09, h * 0.8, 0.07, mats.liquid, 0.55, h * 0.08, r * 0.86)
  liquid.geometry.translate(0, h * 0.4, 0)
  liquid.scale.y = level
  g.add(liquid)
  g.userData.labelY = h + 0.9
  g.userData.footprint = 1.25
  return g
}

function reactor(mats) {
  const g = new THREE.Group()
  const r = 1.3, h = 3.9
  for (const a of [0, 2.1, 4.2]) g.add(cyl(0.08, 0.08, 0.6, mats.iron, Math.cos(a) * r * 0.8, 0.3, Math.sin(a) * r * 0.8, 12))
  g.add(cyl(r, r, h, mats.vessel, 0, 0.6 + h / 2, 0, 48))
  const bottom = mesh(new THREE.SphereGeometry(r, 48, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), mats.vessel, 0, 0.6, 0)
  bottom.scale.y = 0.25
  g.add(bottom)
  const dome = mesh(new THREE.SphereGeometry(r, 48, 16, 0, Math.PI * 2, 0, Math.PI / 2), mats.vessel, 0, 0.6 + h, 0)
  dome.scale.y = 0.45
  g.add(dome)
  for (const y of [1.6, 3.2]) {
    const band = mesh(new THREE.TorusGeometry(r + 0.03, 0.06, 8, 64), mats.iron, 0, y, 0)
    band.rotation.x = Math.PI / 2
    g.add(band)
  }
  g.add(cyl(0.38, 0.38, 0.65, mats.motor, 0, 0.6 + h + 0.85, 0))
  g.add(cyl(0.42, 0.42, 0.12, mats.iron, 0, 0.6 + h + 0.5, 0))
  g.add(box(0.36, 0.6, 0.08, mats.glass, 0, 2.35, r + 0.02))
  g.userData.labelY = 0.6 + h + 1.6
  g.userData.footprint = 1.6
  return g
}

function pump(mats) {
  const g = new THREE.Group()
  g.add(box(1.25, 0.3, 0.85, mats.iron, 0, 0.15, 0))
  const motor = cyl(0.3, 0.3, 0.75, mats.motor, -0.2, 0.62, 0)
  motor.rotation.z = Math.PI / 2
  g.add(motor)
  for (let i = 0; i < 5; i++) {
    const fin = cyl(0.33, 0.33, 0.03, mats.motor, -0.5 + i * 0.12, 0.62, 0)
    fin.rotation.z = Math.PI / 2
    g.add(fin)
  }
  const volute = cyl(0.38, 0.38, 0.3, mats.paint, 0.4, 0.62, 0)
  volute.rotation.x = Math.PI / 2
  g.add(volute)
  const flange = cyl(0.14, 0.14, 0.2, mats.steel, 0.62, 0.62, 0)
  flange.rotation.z = Math.PI / 2
  g.add(flange)
  g.userData.labelY = 1.4
  g.userData.footprint = 0.9
  return g
}

function coolingUnit(mats) {
  const g = new THREE.Group()
  const w = 1.75, h = 1.4
  g.add(box(w, h, w, mats.paint, 0, h / 2, 0))
  for (let i = 0; i < 4; i++) g.add(box(w * 0.8, 0.05, 0.02, mats.iron, 0, 0.3 + i * 0.22, w / 2 + 0.01))
  const well = cyl(0.7, 0.7, 0.06, mats.rubber, 0, h + 0.01, 0, 48)
  g.add(well)
  const blade = new THREE.Group()
  blade.name = 'blade'
  for (let i = 0; i < 3; i++) {
    const b = box(0.62, 0.025, 0.2, mats.steel, 0.3, 0, 0)
    b.rotation.x = 0.35
    const arm = new THREE.Group()
    arm.rotation.y = (i * Math.PI * 2) / 3
    arm.add(b)
    blade.add(arm)
  }
  blade.add(cyl(0.1, 0.1, 0.08, mats.steel, 0, 0, 0, 16))
  blade.position.y = h + 0.08
  g.add(blade)
  const guard = mesh(new THREE.TorusGeometry(0.7, 0.025, 8, 48), mats.iron, 0, h + 0.1, 0)
  guard.rotation.x = Math.PI / 2
  g.add(guard)
  g.userData.labelY = h + 0.9
  g.userData.footprint = 1.35
  return g
}

function robotArm(mats) {
  const g = new THREE.Group()
  g.add(cyl(0.45, 0.5, 0.6, mats.iron, 0, 0.3, 0))
  g.add(cyl(0.2, 0.22, 1.2, mats.motor, 0, 1.2, 0))
  const joint = new THREE.Group()
  joint.name = 'joint_1'
  joint.position.y = 1.85
  joint.add(mesh(new THREE.SphereGeometry(0.22, 24, 16), mats.steel))
  const arm = box(0.2, 0.2, 1.35, mats.motor, 0, 0, -0.65)
  joint.add(arm)
  const wrist = mesh(new THREE.SphereGeometry(0.13, 16, 12), mats.steel, 0, 0, -1.35)
  joint.add(wrist)
  joint.add(cyl(0.035, 0.035, 0.45, mats.steel, 0, -0.22, -1.35, 8))
  joint.add(box(0.2, 0.06, 0.05, mats.steel, 0, -0.46, -1.35))
  g.add(joint)
  g.userData.labelY = 2.6
  g.userData.footprint = 0.7
  return g
}

function beltTexture() {
  const c = document.createElement('canvas')
  c.width = 64; c.height = 8
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 64, 8)
  ctx.fillStyle = '#7a7a7a'; ctx.fillRect(0, 0, 10, 8)
  const t = new THREE.CanvasTexture(c)
  t.wrapS = t.wrapT = THREE.RepeatWrapping
  t.repeat.set(20, 1)
  return t
}

function conveyor(mats, { length = 5 } = {}) {
  const g = new THREE.Group()
  const d = 1.1, top = 0.7
  g.add(box(length, 0.12, d, mats.iron, 0, top - 0.06, 0))
  for (const x of [-length / 2 + 0.2, 0, length / 2 - 0.2]) for (const z of [-d / 2 + 0.06, d / 2 - 0.06]) g.add(box(0.08, top - 0.12, 0.08, mats.iron, x, (top - 0.12) / 2, z))
  const beltMat = mats.rubber.clone()
  beltMat.map = beltTexture()
  beltMat.userData.role = 'rubber'
  const belt = box(length, 0.05, d * 0.9, beltMat, 0, top + 0.02, 0)
  belt.name = 'belt'
  g.add(belt)
  for (const x of [-length / 2, length / 2]) {
    const roller = cyl(0.1, 0.1, d * 0.92, mats.steel, x, top - 0.02, 0, 16)
    roller.rotation.x = Math.PI / 2
    g.add(roller)
  }
  const products = new THREE.Group()
  products.name = 'products'
  for (let i = 0; i < 4; i++) products.add(box(0.5, 0.42, 0.5, mats.cardboard, -length / 2 + 0.6 + i * 1.25, top + 0.26, 0))
  g.add(products)
  g.userData.length = length
  g.userData.labelY = 1.6
  g.userData.footprint = 1.2
  return g
}

function cabinet(mats) {
  const g = new THREE.Group()
  const w = 2.25, h = 2.75, d = 0.85
  g.add(box(w, h, d, mats.paint, 0, h / 2, 0))
  g.add(box(0.02, h - 0.2, 0.02, mats.iron, 0, h / 2, d / 2 + 0.005))
  g.add(box(0.75, 0.85, 0.02, mats.screen, 0.55, 1.7, d / 2 + 0.01))
  const screenGlow = new THREE.Mesh(new THREE.PlaneGeometry(0.65, 0.75), new THREE.MeshBasicMaterial({ color: 0x46c2d6, transparent: true, opacity: 0.18 }))
  screenGlow.position.set(0.55, 1.7, d / 2 + 0.025)
  g.add(screenGlow)
  const io = new THREE.Group()
  io.name = 'io'
  for (let i = 0; i < 2; i++) {
    g.add(box(0.32, 0.5, 0.04, mats.rubber, -0.85 + i * 0.42, 1.4, d / 2 + 0.02))
    const led = mesh(new THREE.SphereGeometry(0.05, 12, 8), lamp('#46c2d6', false), -0.85 + i * 0.42, 1.55, d / 2 + 0.06)
    led.name = i ? 'do' : 'di'
    io.add(led)
  }
  g.add(io)
  g.userData.labelY = h + 0.6
  g.userData.footprint = 1.5
  return g
}

function stackLight() {
  const g = new THREE.Group()
  g.add(cyl(0.03, 0.03, 0.3, new THREE.MeshStandardMaterial({ color: '#7d8a96' }), 0, 0.15, 0, 8))
  const colors = ['#2fc47a', '#f0a33a', '#ff5a45']
  colors.forEach((c, i) => {
    const seg = mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.2, 24), lamp(c, false), 0, 0.42 + i * 0.21, 0)
    seg.name = `lamp_${i + 1}`
    g.add(seg)
  })
  g.add(cyl(0.12, 0.12, 0.04, new THREE.MeshStandardMaterial({ color: '#8c9aa6' }), 0, 1.06, 0, 24))
  g.userData.labelY = 1.5
  g.userData.footprint = 0.3
  return g
}

function gauge(mats) {
  const g = new THREE.Group()
  g.add(cyl(0.04, 0.04, 0.25, mats.steel, 0, 0.12, 0, 8))
  const face = cyl(0.17, 0.17, 0.08, mats.steel, 0, 0.42, 0)
  face.rotation.x = Math.PI / 2
  g.add(face)
  const dial = new THREE.Mesh(new THREE.CircleGeometry(0.14, 24), new THREE.MeshBasicMaterial({ color: 0xf2f4f6 }))
  dial.position.set(0, 0.42, 0.045)
  g.add(dial)
  g.userData.labelY = 0.9
  g.userData.footprint = 0.35
  return g
}

function flowMeter(mats) {
  const g = new THREE.Group()
  g.add(box(0.4, 0.34, 0.34, mats.motor, 0, 0, 0))
  g.add(box(0.26, 0.2, 0.26, mats.paint, 0, 0.27, 0))
  const disp = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 0.1), new THREE.MeshBasicMaterial({ color: 0x46c2d6 }))
  disp.position.set(0, 0.29, 0.135)
  g.add(disp)
  g.userData.labelY = 0.9
  g.userData.footprint = 0.35
  return g
}

function valve(mats) {
  const g = new THREE.Group()
  const body = cyl(0.16, 0.16, 0.45, mats.paint, 0, 0.6, 0)
  body.rotation.z = Math.PI / 2
  g.add(body)
  g.add(cyl(0.03, 0.03, 0.35, mats.steel, 0, 0.85, 0, 8))
  const wheel = mesh(new THREE.TorusGeometry(0.16, 0.025, 8, 24), mats.iron, 0, 1.03, 0)
  wheel.rotation.x = Math.PI / 2
  g.add(wheel)
  g.userData.labelY = 1.5
  g.userData.footprint = 0.4
  return g
}

function probe(mats) {
  const g = new THREE.Group()
  const stem = cyl(0.025, 0.025, 0.3, mats.steel, 0, 0, 0.15, 8)
  stem.rotation.x = Math.PI / 2
  g.add(stem)
  g.add(box(0.14, 0.14, 0.1, mats.iron, 0, 0, 0.32))
  return g
}

export const MODEL_LIBRARY = [
  { type: 'tank', name: '储罐', grade: 'L', category: '工艺设备' },
  { type: 'reactor', name: '反应釜', grade: 'L', category: '工艺设备' },
  { type: 'pump', name: '离心泵', grade: 'M', category: '工艺设备' },
  { type: 'coolingUnit', name: '冷却单元', grade: 'M', category: '执行器' },
  { type: 'robotArm', name: '机械臂', grade: 'M', category: '执行器' },
  { type: 'conveyor', name: '传送带', grade: 'L', category: '执行器' },
  { type: 'valve', name: '阀门', grade: 'S', category: '执行器' },
  { type: 'gauge', name: '压力表', grade: 'S', category: '传感器' },
  { type: 'flowMeter', name: '流量计', grade: 'S', category: '传感器' },
  { type: 'cabinet', name: '控制柜', grade: 'L', category: '结构件' },
  { type: 'stackLight', name: '三色塔灯', grade: 'S', category: '结构件' }
]

const BUILDERS = { tank, reactor, pump, coolingUnit, robotArm, conveyor, cabinet, stackLight, gauge, flowMeter, valve }

export function buildModel(type, palette, opts = {}) {
  const mats = createMaterials(palette)
  const g = BUILDERS[type](mats, opts)
  g.userData.model = type
  if (opts.sensorAt) {
    const p = probe(mats)
    p.position.fromArray(opts.sensorAt)
    g.add(p)
  }
  return g
}

// ---------- 管线与介质流向 ----------

function flowTexture() {
  const c = document.createElement('canvas')
  c.width = 64; c.height = 4
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, 16, 4)
  const t = new THREE.CanvasTexture(c)
  t.wrapS = THREE.RepeatWrapping
  return t
}

export function buildPipe(points, palette) {
  const g = new THREE.Group()
  const mats = createMaterials(palette)
  const pts = points.map((p) => new THREE.Vector3(...p))
  const path = new THREE.CurvePath()
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1]
    const len = a.distanceTo(b)
    const seg = cyl(0.11, 0.11, len, mats.steel, 0, 0, 0, 16)
    seg.position.copy(a).add(b).multiplyScalar(0.5)
    seg.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize())
    g.add(seg)
    path.add(new THREE.LineCurve3(a, b))
  }
  for (const p of pts) g.add(mesh(new THREE.SphereGeometry(0.13, 16, 12), mats.steel, p.x, p.y, p.z))
  const tex = flowTexture()
  tex.repeat.set(Math.max(1, path.getLength() * 3), 1)
  const flow = new THREE.Mesh(
    new THREE.TubeGeometry(path, Math.max(8, pts.length * 24), 0.135, 12, false),
    new THREE.MeshBasicMaterial({ color: palette.accent, map: tex, transparent: true, opacity: 0.85, alphaMap: tex, depthWrite: false })
  )
  flow.material.userData.statusRole = 'accent'
  flow.name = 'flow'
  g.add(flow)
  return g
}

// ---------- 地面、分区、状态光圈、告警热区 ----------

function textSprite(text, color) {
  const c = document.createElement('canvas')
  c.width = 512; c.height = 96
  const ctx = c.getContext('2d')
  ctx.font = '500 52px "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
  ctx.fillStyle = color
  ctx.textBaseline = 'middle'
  ctx.fillText(text, 8, 48)
  const t = new THREE.CanvasTexture(c)
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 0.45), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }))
  m.rotation.x = -Math.PI / 2
  return m
}

export function buildFloor(palette) {
  const g = new THREE.Group()
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(17, 12), new THREE.MeshStandardMaterial({ color: palette.floor, roughness: 0.95 }))
  floor.rotation.x = -Math.PI / 2
  floor.receiveShadow = true
  floor.material.userData.statusRole = 'floor'
  g.add(floor)
  const gridPts = []
  for (let x = -8; x <= 8; x++) gridPts.push(x, 0.002, -5.5, x, 0.002, 5.5)
  for (let z = -5.5; z <= 5.5; z++) gridPts.push(-8, 0.002, z, 8, 0.002, z)
  const gridGeo = new THREE.BufferGeometry()
  gridGeo.setAttribute('position', new THREE.Float32BufferAttribute(gridPts, 3))
  const grid = new THREE.LineSegments(gridGeo, new THREE.LineBasicMaterial({ color: palette.grid }))
  grid.material.userData.statusRole = 'grid'
  g.add(grid)
  const zoneMat = new THREE.LineDashedMaterial({ color: palette.zone, dashSize: 0.25, gapSize: 0.18 })
  zoneMat.userData.statusRole = 'zone'
  for (const z of ZONES) {
    const pts = [[z.x[0], z.z[0]], [z.x[1], z.z[0]], [z.x[1], z.z[1]], [z.x[0], z.z[1]], [z.x[0], z.z[0]]].map(([x, zz]) => new THREE.Vector3(x, 0.005, zz))
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), zoneMat)
    line.computeLineDistances()
    g.add(line)
    const label = textSprite(z.name, palette.zoneText)
    label.position.set(z.x[0] + 1.3, 0.006, z.z[1] - 0.35)
    label.userData.zoneLabel = z.name
    g.add(label)
  }
  const walkMat = new THREE.LineBasicMaterial({ color: palette.walkway })
  walkMat.userData.statusRole = 'walkway'
  for (const pts of [[[-8, 2.15], [8, 2.15]], [[-2.75, -5.5], [-2.75, 5.5]]]) {
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts.map(([x, z]) => new THREE.Vector3(x, 0.004, z))), walkMat))
  }
  return g
}

// 主题切换时重画分区文字
export function rethemeFloor(floorGroup, palette) {
  retheme(floorGroup, palette)
  floorGroup.children.filter((c) => c.userData.zoneLabel).forEach((old) => {
    const fresh = textSprite(old.userData.zoneLabel, palette.zoneText)
    fresh.position.copy(old.position)
    fresh.userData.zoneLabel = old.userData.zoneLabel
    old.geometry.dispose(); old.material.map.dispose(); old.material.dispose()
    floorGroup.remove(old)
    floorGroup.add(fresh)
  })
}

export function buildStatusRing(radius) {
  const ring = new THREE.Mesh(new THREE.RingGeometry(radius * 0.9, radius, 64), new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.9, side: THREE.DoubleSide, depthWrite: false }))
  ring.rotation.x = -Math.PI / 2
  ring.position.y = 0.012
  const pulse = ring.clone()
  pulse.material = ring.material.clone()
  pulse.name = 'pulse'
  const heat = new THREE.Mesh(new THREE.CircleGeometry(radius * 2.2, 48), new THREE.MeshBasicMaterial({ map: heatTexture(), transparent: true, depthWrite: false }))
  heat.rotation.x = -Math.PI / 2
  heat.position.y = 0.008
  heat.name = 'heat'
  const g = new THREE.Group()
  g.add(heat, ring, pulse)
  g.userData.ring = ring
  return g
}

let heatTex
function heatTexture() {
  if (heatTex) return heatTex
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const ctx = c.getContext('2d')
  const grd = ctx.createRadialGradient(64, 64, 0, 64, 64, 64)
  grd.addColorStop(0, 'rgba(255,255,255,0.55)')
  grd.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = grd
  ctx.fillRect(0, 0, 128, 128)
  heatTex = new THREE.CanvasTexture(c)
  return heatTex
}

// 状态：正常细光圈；预警呼吸 + 12% 琥珀自发光；告警外扩脉冲 + 28% 红色自发光；离线 35% 透明
export function applyStatus(device, status, palette) {
  const color = new THREE.Color(palette[status])
  const { ringGroup, model } = device
  const ring = ringGroup.userData.ring
  ring.material.color.copy(color)
  ringGroup.getObjectByName('pulse').material.color.copy(color)
  ringGroup.getObjectByName('heat').material.color.copy(color)
  const tint = { warn: 0.07, alarm: 0.2 }[status] || 0
  model.traverse((o) => {
    const m = o.material
    if (!m || !m.userData.role) return
    if (m.userData.role !== 'liquid') { m.emissive.copy(color); m.emissiveIntensity = tint }
    m.transparent = status === 'offline'
    m.opacity = status === 'offline' ? 0.35 : 1
  })
  device.status = status
}

// 每帧：告警脉冲、预警呼吸、热区显隐
export function animateStatus(device, t, showHeat) {
  const pulse = device.ringGroup.getObjectByName('pulse')
  const heat = device.ringGroup.getObjectByName('heat')
  const ring = device.ringGroup.userData.ring
  const s = device.status
  heat.visible = showHeat && (s === 'warn' || s === 'alarm')
  pulse.visible = s === 'alarm'
  if (s === 'alarm') {
    const k = (t % 1.8) / 1.8
    pulse.scale.setScalar(1 + k * 0.9)
    pulse.material.opacity = 0.85 * (1 - k)
  }
  ring.material.opacity = s === 'warn' ? 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * Math.PI * 2 / 2.2)) : s === 'offline' ? 0.5 : 0.9
}
