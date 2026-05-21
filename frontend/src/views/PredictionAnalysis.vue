<template>
  <div class="prediction-analysis">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>预测分析</h2>
      <p>基于机器学习的设备故障预测和异常检测</p>
    </div>

    <!-- 智能ML分析组件 -->
    <MLAnalysis />
  </div>
</template>

<script>
import MLAnalysis from '@/components/MLAnalysis.vue'

export default {
  name: 'PredictionAnalysis',
  components: {
    MLAnalysis
  }
}
</script>

<style scoped>
.prediction-analysis {
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 16px;
}
</style>
