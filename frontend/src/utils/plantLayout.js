// LINE-01 演示产线：设备布局（单位 m，Y 向上，场景中心为原点）与数据点位绑定。
// 阈值与模拟器 simulator/device_simulator.py 中的 alarm_threshold / range 保持一致。

export const ZONES = [
  { id: 'A', name: 'A 原料区', x: [-7.5, -3], z: [-5, 2] },
  { id: 'B', name: 'B 反应区', x: [-2.5, 1.5], z: [-5, 2] },
  { id: 'C', name: 'C 冷却区', x: [2, 7.5], z: [-5, -0.75] },
  { id: 'D', name: 'D 包装线', x: [2, 7.5], z: [-0.25, 5] },
  { id: 'E', name: 'E 控制室', x: [-7.5, -3], z: [2.5, 5] }
]

// model: plantModels.js 中的模型类型；mqtt: 后端 /api/devices/realtime 的设备名
export const DEVICES = [
  { id: 'TT101', tag: 'TT-101', name: '原料罐温度', kind: '温度传感器', zone: 'A 原料区', loc: 'T-101 罐壁 · 高 2.5 m', mqtt: 'temperature_sensor_1', unit: '°C', range: [18, 85], alarm: [18, 85], model: 'tank', pos: [-6, 0, -3.25], sensorAt: [0, 2.5, 1.05] },
  { id: 'PT101', tag: 'PT-101', name: '泵出口压力', kind: '压力传感器', zone: 'A 原料区', loc: 'P-101 出口管段', mqtt: 'pressure_sensor_1', unit: 'bar', range: [0.3, 5.5], alarm: [0.3, 5.5], model: 'gauge', pos: [-2.25, 0.6, -2.0] },
  { id: 'TT201', tag: 'TT-201', name: '反应釜温度', kind: '温度传感器', zone: 'B 反应区', loc: 'R-201 夹套出口', mqtt: 'temperature_sensor_2', unit: '°C', range: [18, 85], alarm: [18, 85], model: 'reactor', pos: [-0.5, 0, -2.75], sensorAt: [0, 2.6, 1.35] },
  { id: 'FT101', tag: 'FT-101', name: '冷却回路流量', kind: '流量计', zone: 'C 冷却区', loc: 'R-201 → FAN-01 回路', mqtt: 'flow_meter_1', unit: 'L/min', range: [5, 95], alarm: [5, 95], model: 'flowMeter', pos: [2, 1.75, -3.2], rot: [0, Math.PI / 2, 0] },
  { id: 'FAN01', tag: 'FAN-01', name: '冷却风机 1', kind: '风机', zone: 'C 冷却区', loc: '冷却单元 1 顶部', mqtt: 'fan_1', unit: 'RPM', range: [0, 3000], model: 'coolingUnit', pos: [3.375, 0, -3.625] },
  { id: 'FAN02', tag: 'FAN-02', name: '冷却风机 2', kind: '风机', zone: 'C 冷却区', loc: '冷却单元 2 顶部', mqtt: 'fan_2', unit: 'RPM', range: [0, 3000], model: 'coolingUnit', pos: [6.125, 0, -3.625] },
  { id: 'M1', tag: 'M-1', name: '装箱机械臂 1', kind: '伺服电机', zone: 'D 包装线', loc: 'C-301 工位 1', mqtt: 'servo_motor_1', unit: '°', range: [0, 360], model: 'robotArm', pos: [3.75, 0, 4.125] },
  { id: 'M2', tag: 'M-2', name: '装箱机械臂 2', kind: '伺服电机', zone: 'D 包装线', loc: 'C-301 工位 2', mqtt: 'servo_motor_2', unit: '°', range: [0, 360], model: 'robotArm', pos: [6.5, 0, 4.125] },
  { id: 'PLC', tag: 'PLC-01', name: '控制柜 I/O', kind: '数字输入 / 输出', zone: 'E 控制室', loc: 'PLC-01 柜门模块', mqtt: ['digital_input_1', 'digital_output_1'], unit: '', range: [0, 1], special: 'io', model: 'cabinet', pos: [-5.875, 0, 3.425] },
  { id: 'L1', tag: 'L-1', name: '状态塔灯', kind: '指示灯', zone: 'E 控制室', loc: 'PLC-01 柜顶', mqtt: 'indicator_light_1', unit: '', range: [0, 3], special: 'lamp', model: 'stackLight', pos: [-5.875, 2.75, 3.425] }
]

// 无数据点位的工艺结构
export const STRUCTURES = [
  { id: 'T102', tag: 'T-102', name: '原料罐 2', model: 'tank', pos: [-6, 0, -0.25], level: 0.45 },
  { id: 'P101', tag: 'P-101', name: '进料泵', model: 'pump', pos: [-3.625, 0, -1.325] },
  { id: 'C301', tag: 'C-301', name: '传送带', model: 'conveyor', pos: [5, 0, 2.55] }
]

export const PIPES = [
  [[-5, 0.6, -3.25], [-4.5, 0.6, -3.25], [-4.5, 0.6, -1.325], [-4.25, 0.6, -1.325]],
  [[-5, 0.6, -0.25], [-4.5, 0.6, -0.25], [-4.5, 0.6, -1.325]],
  [[-3, 0.6, -1.325], [-2.25, 0.6, -1.325], [-2.25, 0.6, -2.75], [-1.8, 0.6, -2.75]],
  [[0.8, 1.75, -2.75], [2, 1.75, -2.75], [2, 1.75, -3.625], [2.5, 1.75, -3.625]],
  [[4.25, 1, -3.625], [5.25, 1, -3.625]],
  [[6.125, 1, -2.75], [6.125, 1, -0.75], [3, 1, -0.75], [3, 1, 2.55], [3, 0.85, 2.55]]
]

export const STATUS_LABEL = { ok: '正常', warn: '预警', alarm: '告警', offline: '离线' }

const STALE_MS = 15000

// 读数 → 状态：越限告警；距上下限 8% 以内预警；超时或上报离线为离线
export function deviceStatus(dev, reading) {
  if (!reading || reading.status === 'offline' || Date.now() - reading.receivedAt > STALE_MS) return 'offline'
  if (dev.special === 'lamp') return ['ok', 'ok', 'warn', 'alarm'][reading.value] || 'ok'
  if (reading.alarm) return 'alarm'
  if (!dev.alarm) return 'ok'
  const [min, max] = dev.alarm
  const v = reading.value
  if (v < min || v > max) return 'alarm'
  const margin = (max - min) * 0.08
  return v < min + margin || v > max - margin ? 'warn' : 'ok'
}

export function formatValue(dev, reading) {
  if (!reading) return '—'
  if (dev.special === 'io') return `DI ${reading.di ?? '—'} · DO ${reading.do ?? '—'}`
  if (dev.special === 'lamp') return ['熄灭', '运行', '预警', '故障'][reading.value] ?? String(reading.value)
  const v = Number(reading.value)
  const text = Math.abs(v) >= 100 ? Math.round(v).toLocaleString('en-US') : v.toFixed(Math.abs(v) < 10 ? 2 : 1)
  const unit = dev.unit ?? reading.unit
  return unit ? `${text}${unit === '°' ? '' : ' '}${unit}` : text
}

// 后端返回 { 设备名: { value, unit, status, alarm, timestamp } }；取出某个对象绑定点位的读数
export function readingFor(dev, raw, now = Date.now()) {
  if (Array.isArray(dev.mqtt)) {
    const [di, dout] = dev.mqtt.map((k) => raw[k])
    return di || dout ? { di: di?.value, do: dout?.value, value: di?.value ?? 0, status: di?.status ?? dout?.status, timestamp: di?.timestamp ?? dout?.timestamp, receivedAt: now } : null
  }
  const r = raw[dev.mqtt]
  return r ? { ...r, value: Number(r.value), receivedAt: now } : null
}
