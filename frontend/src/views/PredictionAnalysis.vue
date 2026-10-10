<template>
  <div class="prediction-analysis">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>预测分析</h2>
      <p>基于机器学习识别异常趋势与潜在故障</p>
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
  color: var(--ink);
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: var(--data-2);
  font-size: 16px;
}
</style>
