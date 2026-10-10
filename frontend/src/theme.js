import { ref, watchEffect } from 'vue'

const KEY = 'idp-theme'
const stored = (() => { try { return localStorage.getItem(KEY) } catch { return null } })()

// 深色为默认主题；html.dark 同时驱动 Element Plus 的暗色变量
export const theme = ref(stored === 'light' ? 'light' : 'dark')

watchEffect(() => {
  document.documentElement.classList.toggle('dark', theme.value === 'dark')
  try { localStorage.setItem(KEY, theme.value) } catch { /* 隐私模式下忽略 */ }
})

export const toggleTheme = () => { theme.value = theme.value === 'dark' ? 'light' : 'dark' }

// 画布类图表（ECharts / Three.js）读不到 CSS 变量，取当前计算值
export const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()
