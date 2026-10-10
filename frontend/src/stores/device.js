import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deviceAPI } from '../api'

// 设备台账（/api/devices/status）与控制、增删；实时读数见 composables/useLine.js
export const useDeviceStore = defineStore('device', () => {
  const devices = ref([])

  async function fetchDevices() {
    try {
      const response = await deviceAPI.getDevicesStatus()
      devices.value = response.data || []
    } catch (error) {
      console.error('获取设备状态失败:', error)
    }
  }

  function formatRuntime(seconds) {
    if (!seconds || seconds < 0) return '0 秒'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours} 小时 ${minutes} 分钟`
    return minutes > 0 ? `${minutes} 分钟 ${seconds % 60} 秒` : `${seconds} 秒`
  }

  async function controlDevice(deviceName, command, value) {
    try {
      await deviceAPI.controlDevice(deviceName, command, value)
      return true
    } catch (error) {
      console.error('设备控制失败:', error)
      return false
    }
  }

  async function addDevice(deviceData) {
    const response = await deviceAPI.addDevice(deviceData)
    return !!response.success
  }

  async function deleteDevice(deviceName) {
    const response = await deviceAPI.deleteDevice(deviceName)
    if (response.success) devices.value = devices.value.filter((d) => d.device_name !== deviceName)
    return !!response.success
  }

  return { devices, fetchDevices, formatRuntime, controlDevice, addDevice, deleteDevice }
})
