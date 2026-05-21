import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { deviceAPI } from '../api'

export const useDeviceStore = defineStore('device', () => {  const devices = ref([])
  const loading = ref(false)
  const lastUpdate = ref(null)
  const startTime = ref(Date.now()) // 记录启动时间
  const deviceStartTimes = ref({}) // 记录每个设备的启动时间
  
  // 设备状态统计
  const deviceStats = computed(() => {
    const stats = {
      total: devices.value.length,
      online: 0,
      offline: 0,
      warning: 0,
      error: 0
    }
    
    devices.value.forEach(device => {
      switch (device.status) {
        case 'online':
          stats.online++
          break
        case 'offline':
          stats.offline++
          break
        case 'warning':
          stats.warning++
          break
        case 'error':
          stats.error++
          break
      }
    })
    
    return stats
  })
  
  // 计算设备运行时间
  function calculateDeviceRuntime(deviceName) {
    const deviceStartTime = deviceStartTimes.value[deviceName] || startTime.value
    return Math.floor((Date.now() - deviceStartTime) / 1000)
  }
  
  // 格式化运行时间
  function formatRuntime(seconds) {
    if (!seconds || seconds < 0) return '0秒'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    } else {
      return `${secs}秒`
    }
  }  // 获取设备列表
  async function fetchDevices() {
    loading.value = true
    try {
      const response = await deviceAPI.getDevicesStatus()
      const fetchedDevices = response.data || []
      
      // 为新设备设置启动时间
      fetchedDevices.forEach(device => {
        if (!deviceStartTimes.value[device.device_name]) {
          deviceStartTimes.value[device.device_name] = Date.now()
        }
        // 计算实时运行时间
        device.total_runtime = calculateDeviceRuntime(device.device_name)
      })
      
      devices.value = fetchedDevices
      lastUpdate.value = new Date()
    } catch (error) {
      console.error('获取设备状态失败:', error)
    } finally {
      loading.value = false
    }
  }
    // 获取实时设备数据
  async function fetchRealtimeDevices() {
    loading.value = true
    try {
      const response = await deviceAPI.getRealtimeDevices()
      if (response.success && response.data) {
        // 如果返回的是对象格式，转换为数组
        if (Array.isArray(response.data)) {
          devices.value = response.data        } else {
          // 如果是对象格式，转换为数组并添加必要的字段
          devices.value = Object.keys(response.data).map(deviceName => {
            // 为新设备设置启动时间
            if (!deviceStartTimes.value[deviceName]) {
              deviceStartTimes.value[deviceName] = Date.now()
            }
            
            return {
              device_name: deviceName,
              device_type: response.data[deviceName].type || 'unknown',
              current_value: response.data[deviceName].value,
              last_value: response.data[deviceName].value,
              unit: response.data[deviceName].unit || '',
              status: response.data[deviceName].status || 'online',
              last_update: response.data[deviceName].timestamp || new Date().toISOString(),
              location: '产线A',
              total_runtime: calculateDeviceRuntime(deviceName), // 使用计算函数
              error_count: 0
            }
          })
        }
        lastUpdate.value = new Date()
      }
    } catch (error) {
      console.error('获取实时设备数据失败:', error)
      // 如果实时API失败，回退到状态API
      await fetchDevices()
    } finally {
      loading.value = false
    }
  }
  
  // 根据名称获取设备
  function getDeviceByName(deviceName) {
    return devices.value.find(device => device.device_name === deviceName)
  }
  
  // 更新设备状态
  function updateDeviceStatus(deviceName, status) {
    const device = getDeviceByName(deviceName)
    if (device) {
      device.status = status
      device.last_update = new Date().toISOString()
    }
  }
  
  // 控制设备
  async function controlDevice(deviceName, command, value) {
    try {
      await deviceAPI.controlDevice(deviceName, command, value)
      // 控制成功后，可以更新本地状态或重新获取数据
      return true
    } catch (error) {
      console.error('设备控制失败:', error)
      return false
    }
  }

  // 添加设备
  async function addDevice(deviceData) {
    try {
      const response = await deviceAPI.addDevice(deviceData)
      if (response.success) {
        // 添加成功后，更新本地设备列表
        const newDevice = {
          ...deviceData,
          last_update: new Date().toISOString(),
          total_runtime: 0,
          error_count: 0
        }
        
        // 设置设备启动时间
        deviceStartTimes.value[deviceData.device_name] = Date.now()
        
        devices.value.push(newDevice)
        return true
      }
      return false
    } catch (error) {
      console.error('添加设备失败:', error)
      throw error
    }
  }

  // 删除设备
  async function deleteDevice(deviceName) {
    try {
      const response = await deviceAPI.deleteDevice(deviceName)
      if (response.success) {
        // 从本地列表中移除
        const index = devices.value.findIndex(d => d.device_name === deviceName)
        if (index > -1) {
          devices.value.splice(index, 1)
        }
        // 移除启动时间记录
        delete deviceStartTimes.value[deviceName]
        return true
      }
      return false
    } catch (error) {
      console.error('删除设备失败:', error)
      throw error
    }
  }  return {
    devices,
    loading,
    lastUpdate,
    startTime,
    deviceStartTimes,
    deviceStats,
    fetchDevices,
    fetchRealtimeDevices,
    getDeviceByName,
    updateDeviceStatus,
    controlDevice,
    addDevice,
    deleteDevice,
    calculateDeviceRuntime,
    formatRuntime
  }
})
