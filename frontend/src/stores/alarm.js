import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { alarmAPI } from '../api'

export const useAlarmStore = defineStore('alarm', () => {
  const alarms = ref([])
  const loading = ref(false)
  const lastUpdate = ref(null)
  
  // 未读报警数量
  const unreadCount = computed(() => {
    return alarms.value.filter(alarm => !alarm.acknowledged).length
  })
  // 最近24小时的报警
  const recentAlarms = computed(() => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    
    return alarms.value.filter(alarm => 
      new Date(alarm.timestamp) > yesterday
    )
  })
  
  // 获取报警列表
  async function fetchAlarms(params = {}) {
    loading.value = true
    try {
      const response = await alarmAPI.getAlarms(params)
      alarms.value = response.data || []
      lastUpdate.value = new Date()
    } catch (error) {
      console.error('获取报警记录失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  // 确认报警
  async function acknowledgeAlarm(alarmId, user = 'admin') {
    try {
      await alarmAPI.acknowledgeAlarm(alarmId, user)
      
      // 更新本地状态
      const alarm = alarms.value.find(a => a.id === alarmId)
      if (alarm) {
        alarm.acknowledged = true
        alarm.ack_user = user
        alarm.ack_time = new Date().toISOString()
      }
      
      return true
    } catch (error) {
      console.error('确认报警失败:', error)
      return false
    }
  }
  
  // 批量确认报警
  async function acknowledgeMultipleAlarms(alarmIds, user = 'admin') {
    const results = await Promise.allSettled(
      alarmIds.map(id => acknowledgeAlarm(id, user))
    )
    
    const successCount = results.filter(r => r.status === 'fulfilled' && r.value).length
    return successCount
  }
  
  return {
    alarms,
    loading,
    lastUpdate,
    unreadCount,
    recentAlarms,
    fetchAlarms,
    acknowledgeAlarm,
    acknowledgeMultipleAlarms
  }
})
