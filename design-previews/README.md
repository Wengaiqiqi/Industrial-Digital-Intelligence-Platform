# 工业数智平台 · 前端重设计预览

本目录包含 7 个现有前端页面的高保真设计预览。当前仅用于视觉评审，尚未替换 Vue 页面实现。

## 视觉系统

- 色系：Lieflat Charts `porcelain / 青瓷蓝`
- 背景：`#F7F2EB`
- 正文：`#081F5C`
- 数据主色：`#334EAC`
- 数据次级：`#7096D1`、`#BAD6EB`
- 卡片：24px 圆角、无阴影、无渐变，以留白和发丝分隔线组织层级
- 表格：固定行节奏、轻量分隔、状态文字与形状双编码、数值单元格可嵌微型趋势

## 页面清单

1. `01-dashboard-overview.png` — 运行总览
2. `02-device-management.png` — 设备管理
3. `03-alarm-center.png` — 告警中心
4. `04-realtime-monitor.png` — 实时监控
5. `05-historical-data.png` — 历史数据
6. `06-prediction-analysis.png` — 预测分析
7. `07-3d-scene.png` — 三维场景

## Lieflat Charts 选型

- 实时与短周期序列：F2 Hairline Line。相比 F3，当前数据点不超过 30，逐点读取比面积轮廓更诚实；相比 L3，当前不是 90 天级长序列。
- 设备与告警排行：F5 Tick Rows。长中文标签更适合横排；F1 竖排会压缩标签，L2 暗卡和级联结构不适合高频运维页面。
- 星期 × 小时异常量：F10 Dot Heat。数据本体就是周期矩阵，L4/L9 会增加不必要的关系叙事。
- 单值效率：F11 Tick Gauge。效率是单指标进度，不是 F4/L14 所要求的多类别 100% 构成。
- 预测关系：F8 Plumb Scatter。振动与温升是两个连续变量，位置编码比按类目汇总更诚实。

整组预览只使用 `porcelain` 色系，避免跨色系混用。
