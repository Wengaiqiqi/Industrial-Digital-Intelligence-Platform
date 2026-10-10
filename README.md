# 工业数智平台

一个面向工业生产现场的综合管控与可视化平台，集成设备实时监控、报警管理、历史数据分析、机器学习预测、3D 场景展示、MQTT 数据通信和 Modbus TCP 仿真能力。项目适合作为工业互联网、智能制造、数字孪生、设备运维预测等方向的课程设计、毕业设计或作品集项目。

## 项目概览

本项目模拟典型工业现场的数据采集与管控流程：设备仿真器持续生成温度、压力、流量、风机、电机、PLC 等设备数据，通过 MQTT 发送到后端服务；后端负责数据入库、状态维护、报警判断和 API 输出；前端以仪表盘、实时监控、3D 场景、历史数据和预测分析等页面展示系统运行状态。

项目同时提供内置 MQTT Broker 和 Modbus TCP PLC 仿真器，不依赖真实工业设备即可完整运行演示。

## 核心功能

- 实时设备监控：展示设备在线状态、实时数值、报警状态、运行趋势等信息。
- 工业数据采集：模拟多类工业设备的数据变化，并支持通过 MQTT 分发数据。
- 智能报警管理：根据设备阈值自动生成报警记录，支持报警查看和确认。
- 历史数据分析：按时间范围查询、统计和导出历史传感器数据。
- 机器学习分析：提供异常检测、故障预测、模型训练和设备健康分析接口。
- 预测性维护：基于 scikit-learn 与 TensorFlow/LSTM 进行设备风险预测。
- 3D 场景可视化：使用 Three.js 构建工业现场三维设备场景。
- Modbus TCP 仿真：提供 PLC 寄存器、线圈、输入寄存器等仿真数据。
- 一键安装与启动：提供 Windows 批处理脚本自动创建 Python 3.11 环境并启动服务。

## 技术栈

### 前端

- Vue 3
- Vite
- Element Plus
- Pinia
- Vue Router
- ECharts
- Three.js
- Axios
- Sass

### 后端

- Python 3.11
- Flask
- Flask-SQLAlchemy
- Flask-CORS
- SQLite
- Loguru
- pandas / numpy

### 工业通信与仿真

- paho-mqtt
- 内置轻量 MQTT Broker
- pymodbus
- Modbus TCP Server

### 机器学习

- scikit-learn
- TensorFlow
- IsolationForest
- RandomForestRegressor
- LSTM
- joblib / pickle 模型持久化

## 系统架构

```text
┌──────────────────────────┐
│        Vue 前端           │
│ Dashboard / 3D / ML / 报警 │
└─────────────┬────────────┘
              │ HTTP / API Proxy
              ▼
┌──────────────────────────┐
│       Flask 后端 API       │
│ 数据查询 / 报警 / 设备控制   │
└───────┬───────────┬──────┘
        │           │
        │ SQLite    │ MQTT
        ▼           ▼
┌──────────────┐  ┌──────────────────┐
│  数据库       │  │ 内置 MQTT Broker  │
│ industrial.db│  │ 127.0.0.1:1883    │
└──────────────┘  └────────┬─────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │ 工业设备仿真器     │
                  │ 传感器 / 电机 / PLC │
                  └──────────────────┘

┌──────────────────────────┐
│   Modbus TCP PLC 仿真器    │
│        localhost:5020      │
└──────────────────────────┘
```

## 目录结构

```text
.
├── backend/                     # Flask 后端服务
│   ├── app.py                   # REST API、数据库模型、MQTT 数据处理
│   └── ml_service_wrapper.py    # 机器学习服务封装
├── frontend/                    # Vue 3 前端项目
│   ├── src/
│   │   ├── api/                 # API 请求封装
│   │   ├── components/          # 通用组件
│   │   ├── router/              # 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── utils/               # 3D、设备、MQTT 数据工具
│   │   └── views/               # 页面视图
│   ├── package.json
│   └── vite.config.js
├── simulator/                   # 工业设备与 Modbus 仿真
│   ├── device_simulator.py      # 设备数据仿真器
│   └── modbus_server.py         # Modbus TCP PLC 仿真器
├── ml_models/                   # 机器学习服务与模型文件
│   ├── ml_service.py
│   ├── train_model.py
│   ├── anomaly_detector.pkl
│   └── predictive_maintenance.pkl
├── database/                    # SQLite 数据库与初始化脚本
│   ├── init_db.py
│   └── industrial.db
├── logs/                        # 运行日志
├── mqtt_broker_embedded.py      # 内置轻量 MQTT Broker
├── install_dependencies.bat     # Windows 一键安装依赖
├── start_services.bat           # Windows 一键启动平台
├── start_services.py            # 服务管理器
├── requirements.txt             # Python 依赖
└── README.md
```

## 快速开始

### 环境要求

- Windows 10/11
- Anaconda 或 Miniconda
- Node.js 16 或以上版本
- 推荐 Python 3.10 / 3.11

本项目当前锁定依赖更适合 Python 3.10/3.11。不要直接使用 Python 3.13 安装旧版 pandas、numpy、TensorFlow，否则可能触发源码编译失败。

### 1. 安装依赖

双击运行：

```bat
install_dependencies.bat
```

脚本会自动：

- 创建项目本地 Python 3.11 环境 `.conda-py311`
- 安装 Python 后端依赖
- 安装前端 npm 依赖
- 检查关键项目文件
- 创建 `logs` 和 `database` 目录

### 2. 启动服务

双击运行：

```bat
start_services.bat
```

启动后会打开多个服务窗口，包括：

- MQTT Broker
- Flask 后端 API
- 工业设备仿真器
- Modbus TCP 仿真器
- Vue 前端服务

### 3. 访问系统

- 前端页面：http://localhost:5173
- 后端 API：http://localhost:5055
- 健康检查：http://localhost:5055/api/health
- MQTT Broker：127.0.0.1:1883
- Modbus TCP：localhost:5020

## 手动启动方式

如果不使用批处理脚本，也可以手动启动：

```bat
.conda-py311\python.exe mqtt_broker_embedded.py
```

```bat
cd backend
..\.conda-py311\python.exe app.py
```

```bat
cd simulator
..\.conda-py311\python.exe device_simulator.py
```

```bat
cd simulator
..\.conda-py311\python.exe modbus_server.py
```

```bat
cd gateway
..\.conda-py311\python.exe modbus_gateway.py
```

```bat
cd frontend
npm run dev
```

注意：上面的后端、仿真器命令在 Windows 下执行时，请根据实际命令行环境调整 Python 路径。推荐优先使用 `start_services.bat`。

## API 概览

### 系统健康

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 后端健康检查 |

### 设备数据

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/devices/realtime` | 获取实时设备数据 |
| GET | `/api/devices/status` | 获取设备状态列表 |
| GET | `/api/devices/<device_name>/history` | 查询设备历史数据 |
| GET | `/api/devices/<device_name>/statistics` | 获取设备统计信息 |
| POST | `/api/devices` | 新增设备 |
| DELETE | `/api/devices/<device_name>` | 删除设备 |
| POST | `/api/control/device` | 发送设备控制命令 |

### 报警管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/alarms` | 查询报警记录 |
| POST | `/api/alarms/<alarm_id>/acknowledge` | 确认报警 |

### 统计与历史数据

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/statistics/dashboard` | 仪表盘统计数据 |
| POST | `/api/historical-data` | 查询历史数据 |
| POST | `/api/export-historical-data` | 导出历史数据 |

### 机器学习

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/ml/analyze/<device_name>` | 综合分析设备状态 |
| POST | `/api/ml/train` | 训练机器学习模型 |

## 页面功能

- 仪表盘：设备总览、关键指标、实时趋势、报警概览。
- 实时监控：按设备查看实时状态、数据变化和设备详情。
- 设备管理：设备新增、编辑、删除、分类管理。
- 报警管理：报警记录查询、状态筛选、报警确认。
- 历史数据：时间范围查询、数据统计、导出分析。
- 预测分析：模型训练、异常检测、故障预测、健康评估。
- 3D 场景：工业现场设备三维可视化展示。

## 数据模型说明

后端主要包含三类核心数据：

- `SensorData`：传感器采样数据，包括设备名称、类型、数值、单位、时间戳等。
- `DeviceStatus`：设备状态信息，包括在线状态、当前值、报警等级、最后更新时间等。
- `AlarmRecord`：报警记录，包括报警类型、严重程度、确认状态、触发时间等。

SQLite 数据库默认位于：

```text
database/industrial.db
```

## 机器学习说明

系统内置两类主要模型：

- 异常检测模型：基于 IsolationForest 判断设备数据是否偏离正常范围。
- 预测性维护模型：基于随机森林和 LSTM 思路预测设备故障风险。

当数据库中真实数据不足时，系统会生成合成训练数据用于演示模型训练流程。实际生产环境中可以替换为真实设备采集数据。

## MQTT 与 Modbus 说明

### MQTT

项目提供内置轻量 MQTT Broker，默认监听：

```text
127.0.0.1:1883
```

主要主题：

```text
industrial/sensors/data
industrial/device/<device_name>
industrial/control/<device_name>
```

连接地址、账号密码、TLS、主题都在 `config/platform.json` 的 `mqtt` 段配置，断线会自动重连。

### 接入真实设备

`config/platform.json` 是唯一的配置入口，可以配置 MQTT 代理、设备阈值、离线超时、接口令牌，以及 Modbus 寄存器映射。

- 能发 MQTT 的设备或网关：按约定格式发到 `industrial/device/<设备名>` 或 `industrial/sensors/data`。
- Modbus TCP 的 PLC：配置寄存器映射后，由 `gateway/modbus_gateway.py` 轮询并转发，控制指令会写回 PLC。

报文格式、阈值报警、离线判断、控制下发和令牌的完整说明见 [docs/接入真实设备.md](docs/接入真实设备.md)。

### Modbus TCP

Modbus PLC 仿真器默认监听：

```text
localhost:5020
```

用于模拟：

- Coils
- Discrete Inputs
- Input Registers
- Holding Registers

## 常见问题

### 1. pandas、numpy 或 TensorFlow 安装失败

请确认不要使用 Python 3.13。推荐运行：

```bat
install_dependencies.bat
```

脚本会创建 `.conda-py311` 环境并使用 Python 3.11 安装依赖。

### 2. 前端提示 Request failed with status code 404

请确认后端实际运行在 `5055` 端口，并重新启动前端服务：

```text
http://localhost:5055/api/health
```

如果健康检查不是 200，请先关闭旧的后端窗口，再重新运行 `start_services.bat`。

### 3. MQTT 连接失败

请确认 `mqtt_broker_embedded.py` 已先启动，并监听 `127.0.0.1:1883`。使用一键启动脚本时，MQTT Broker 会最先启动。

### 4. 端口冲突

默认端口：

| 服务 | 端口 |
| --- | --- |
| 前端 Vite | 5173 |
| 后端 Flask | 5055 |
| MQTT Broker | 1883 |
| Modbus TCP | 5020 |

如果端口被占用，请关闭旧服务窗口，或修改对应配置文件中的端口。

## 上传 GitHub 前建议

建议不要上传以下内容：

```text
.conda-py311/
frontend/node_modules/
frontend/dist/
logs/
__pycache__/
*.pyc
database/*.db
ml_models/*.pkl
ml_models/*.h5
```

可以保留模型文件和数据库样例用于演示，但如果仓库体积较大，建议改为在 Release 中提供。

## 项目亮点

- 覆盖工业现场平台的完整业务链路：采集、传输、存储、监控、报警、分析、预测。
- 不依赖真实硬件，内置设备仿真、MQTT Broker 和 Modbus TCP Server。
- 前后端分离，结构清晰，便于扩展为真实工业网关或数字孪生平台。
- 集成机器学习预测分析能力，适合展示智能运维和预测性维护场景。
- 提供一键安装和一键启动脚本，降低 Windows 环境部署成本。

## 后续优化方向

- 增加用户登录、角色权限和操作审计。
- 将 SQLite 替换为 PostgreSQL 或 TimescaleDB。
- 引入 WebSocket 或 Socket.IO 推送实时数据。
- 支持 OPC UA 数据接入。
- 增加 Docker Compose 部署方案。
- 增加单元测试、接口测试和前端 E2E 测试。
- 将 3D 场景与实时设备状态深度绑定，实现更完整的数字孪生展示。

## License

本项目可作为学习、课程设计和作品集项目使用。若用于商业或生产环境，请根据实际需求补充安全、认证、监控和部署能力。
