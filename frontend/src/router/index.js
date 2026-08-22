import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '运行总览' }
  },  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/DeviceManagement.vue'),
    meta: { title: '设备管理' }
  },
  {
    path: '/alarms',
    name: 'Alarms',
    component: () => import('../views/AlarmManagement.vue'),
    meta: { title: '告警中心' }
  },
  {
    path: '/3d-scene',
    name: '3DScene',
    component: () => import('../views/Scene3D.vue'),
    meta: { title: '三维场景' }
  },  {
    path: '/prediction',
    name: 'Prediction',
    component: () => import('../views/PredictionAnalysis.vue'),
    meta: { title: '预测分析' }
  },  {
    path: '/realtime-monitor',
    name: 'RealtimeMonitor',
    component: () => import('../views/RealtimeMonitor.vue'),
    meta: { title: '实时监控' }
  },
  {
    path: '/historical-data',
    name: 'HistoricalData',
    component: () => import('../views/HistoricalData.vue'),
    meta: { title: '历史数据' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 工业数智平台` : '工业数智平台'
  next()
})

export default router
