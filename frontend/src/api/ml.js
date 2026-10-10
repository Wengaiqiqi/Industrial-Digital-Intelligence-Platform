// 机器学习分析API
import request, { API_TOKEN } from './index'
import axios from 'axios'

// 为ML训练操作创建专门的axios实例（更长超时）
const mlRequest = axios.create({
  baseURL: '/api',
  timeout: 120000, // ML训练需要2分钟超时
  headers: {
    'Content-Type': 'application/json',
    ...(API_TOKEN && { 'X-API-Token': API_TOKEN })
  }
})

export const mlAPI = {  // 训练机器学习模型（使用更长超时）
  async trainModels(deviceName = 'all', hours = 168) {
    try {
      const response = await mlRequest.post('/ml/train', { 
        device_name: deviceName,
        hours: hours
      })
      console.log('ML API 原始响应:', response) // 调试日志
      return response.data // 返回响应数据而不是整个响应对象
    } catch (error) {
      console.error('ML API 训练请求失败:', error)
      throw error
    }
  },

  // 分析指定设备（使用标准超时）
  analyzeDevice(deviceName, hours = 24) {
    return request.post(`/ml/analyze/${deviceName}`, { hours })
  }
}

export default mlAPI
