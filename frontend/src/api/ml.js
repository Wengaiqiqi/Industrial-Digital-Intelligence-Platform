// 机器学习分析API
import request from './index'
import axios from 'axios'

// 为ML训练操作创建专门的axios实例（更长超时）
const mlRequest = axios.create({
  baseURL: '/api',
  timeout: 120000, // ML训练需要2分钟超时
  headers: {
    'Content-Type': 'application/json'
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
  },

  // 预测设备故障（使用标准超时）
  predictFailure(deviceName, hours = 24) {
    return request.post(`/ml/predict/${deviceName}`, { hours })
  },

  // 检测设备异常（使用标准超时）
  detectAnomaly(deviceName, hours = 1) {
    return request.post(`/ml/detect-anomaly/${deviceName}`, { hours })
  },

  // 获取异常检测结果（简化版）
  getAnomalyDetection(deviceName, hours = 24) {
    return request.get(`/ml/anomaly/${deviceName}`, { 
      params: { hours } 
    })
  },
  // 获取故障预测结果（简化版）
  getFailurePrediction(deviceName, hours = 168) {
    return request.get(`/ml/prediction/${deviceName}`, { 
      params: { hours } 
    })
  }
}

export default mlAPI
