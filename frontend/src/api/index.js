import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000, // 增加到30秒，支持ML训练操作
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 2xx 范围内的状态码都会触发该函数
    const { data } = response
    
    if (data.success === false) {
      ElMessage.error(data.error || '请求失败')
      return Promise.reject(new Error(data.error || '请求失败'))
    }
    
    return data
  },
  error => {
    // 超出 2xx 范围的状态码都会触发该函数
    const message = error.response?.data?.error || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API接口定义
export const deviceAPI = {
  // 获取所有设备状态
  getDevicesStatus() {
    return api.get('/devices/status')
  },
  
  // 获取实时设备数据
  getRealtimeDevices() {
    return api.get('/devices/realtime')
  },
  
  // 获取设备历史数据（新端点）
  getDeviceHistory(deviceName, hours = 24, limit = 1000) {
    return api.get(`/devices/${deviceName}/history`, {
      params: { hours, limit }
    })
  },
  
  // 控制设备
  controlDevice(deviceName, command, value) {
    return api.post('/control/device', {
      device_name: deviceName,
      command,
      value
    })
  },

  // 添加设备
  addDevice(deviceData) {
    return api.post('/devices', deviceData)
  },

  // 删除设备
  deleteDevice(deviceName) {
    return api.delete(`/devices/${deviceName}`)
  }
}

export const alarmAPI = {
  // 获取报警记录
  getAlarms(params = {}) {
    return api.get('/alarms', { params })
  },
  
  // 确认报警
  acknowledgeAlarm(alarmId, user = 'admin') {
    return api.post(`/alarms/${alarmId}/acknowledge`, { user })
  }
}

export const historicalAPI = {
  // 获取历史数据
  getHistoricalData(startTime, endTime) {
    return api.post('/historical-data', {
      start_time: startTime,
      end_time: endTime
    })
  },

  // 导出历史数据
  exportHistoricalData(startTime, endTime) {
    return api.post('/export-historical-data', {
      start_time: startTime,
      end_time: endTime
    }, {
      responseType: 'blob'
    })
  }
}

export default api
