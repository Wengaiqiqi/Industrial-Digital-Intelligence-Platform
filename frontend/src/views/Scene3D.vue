<template>
  <div class="scene-3d-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <!-- 左侧：操作模式 -->
      <div class="toolbar-section toolbar-left">
        <el-button-group>
          <el-button 
            :type="mode === 'select' ? 'primary' : ''" 
            @click="setMode('select')"
          >选择</el-button>
          <el-button 
            :type="mode === 'rotate' ? 'primary' : ''" 
            @click="setMode('rotate')"
          >旋转</el-button>
          <el-button 
            :type="mode === 'scale' ? 'primary' : ''" 
            @click="setMode('scale')"
          >缩放</el-button>
        </el-button-group>
      </div>
      
      <!-- 中间：场景和模型管理 -->
      <div class="toolbar-section toolbar-center">
        <div class="toolbar-group">
          <el-button @click="saveScene" type="success" size="default">保存场景</el-button>
          <el-button @click="loadScene" size="default">加载场景</el-button>
          <el-button @click="clearScene" type="danger" size="default">清空场景</el-button>
        </div>
        
        <div class="toolbar-group">
          <el-button @click="triggerImportModel" type="primary" size="default">导入模型</el-button>
          <input ref="fileInput" type="file" accept=".gltf,.glb,.obj,.fbx" style="display:none" @change="onModelFileChange" />
          
          <el-dropdown @command="addBuiltInModel">
            <el-button type="info" size="default">
              内置模型<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="pump">工业泵</el-dropdown-item>
                <el-dropdown-item command="tank">储罐</el-dropdown-item>
                <el-dropdown-item command="heat_exchanger">换热器</el-dropdown-item>
                <el-dropdown-item command="valve_gate">闸阀</el-dropdown-item>
                <el-dropdown-item command="valve_ball">球阀</el-dropdown-item>
                <el-dropdown-item command="conveyor">传送带</el-dropdown-item>
                <el-dropdown-item command="factory">工厂场景</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <el-dropdown @command="addDevice">
            <el-button type="success" size="default">
              添加设备<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="temperature_sensor">温度传感器</el-dropdown-item>
                <el-dropdown-item command="pressure_sensor">压力传感器</el-dropdown-item>
                <el-dropdown-item command="flow_meter">流量计</el-dropdown-item>
                <el-dropdown-item command="fan">风扇</el-dropdown-item>
                <el-dropdown-item command="servo_motor">伺服电机</el-dropdown-item>
                <el-dropdown-item command="indicator_light">指示灯</el-dropdown-item>
                <el-dropdown-item command="digital_input">数字输入</el-dropdown-item>
                <el-dropdown-item command="digital_output">数字输出</el-dropdown-item>
                <el-dropdown-item command="pipe">管道</el-dropdown-item>
                <el-dropdown-item command="tank">储罐</el-dropdown-item>
                <el-dropdown-item command="conveyor">传送带</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <el-button @click="openBatchAddDialog" type="warning" size="default">
            批量添加<el-icon class="el-icon--right"><plus /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 右侧：视图设置 -->
      <div class="toolbar-section toolbar-right">
        <el-switch
          v-model="showGrid"
          active-text="显示网格"
          inactive-text="隐藏网格"
          @change="toggleGrid"
        />
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧设备库 -->
      <div class="device-library">
        <el-card class="library-card">
          <template #header>
            <div class="card-header">
              <span>设备库</span>
              <el-input
                v-model="searchText"
                placeholder="搜索设备"
                size="small"
              />
            </div>
          </template>
          
          <el-collapse v-model="activeLibraryCategory">
            <el-collapse-item title="传感器" name="sensors">
              <div class="device-grid">
                <div 
                  class="device-item" 
                  v-for="device in filteredSensors" 
                  :key="device.type"
                  @click="selectDeviceType(device)"
                  @dragstart="onDragStart($event, device)"
                  draggable="true"
                >
                  <div class="device-icon" :style="{backgroundColor: device.color}">
                    {{ device.icon }}
                  </div>
                  <div class="device-name">{{ device.name }}</div>
                </div>
              </div>
            </el-collapse-item>
            
            <el-collapse-item title="执行器" name="actuators">
              <div class="device-grid">
                <div 
                  class="device-item" 
                  v-for="device in filteredActuators" 
                  :key="device.type"
                  @click="selectDeviceType(device)"
                  @dragstart="onDragStart($event, device)"
                  draggable="true"
                >
                  <div class="device-icon" :style="{backgroundColor: device.color}">
                    {{ device.icon }}
                  </div>
                  <div class="device-name">{{ device.name }}</div>
                </div>
              </div>
            </el-collapse-item>
            
            <el-collapse-item title="结构件" name="structures">
              <div class="device-grid">
                <div 
                  class="device-item" 
                  v-for="device in filteredStructures" 
                  :key="device.type"
                  @click="selectDeviceType(device)"
                  @dragstart="onDragStart($event, device)"
                  draggable="true"
                >
                  <div class="device-icon" :style="{backgroundColor: device.color}">
                    {{ device.icon }}
                  </div>
                  <div class="device-name">{{ device.name }}</div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </div>

      <!-- 中间3D视图 -->
      <div class="scene-viewport">
        <div 
          ref="threeContainer" 
          class="three-container"
          @drop="onDrop"
          @dragover="onDragOver"
          @click="onSceneClick"
          @pointerup="onSceneClick"
          @contextmenu="onRightClick"
        ></div>
        
        <!-- 右键菜单 -->
        <div 
          v-if="contextMenu.visible" 
          class="context-menu"
          :style="{
            left: contextMenu.x + 'px',
            top: contextMenu.y + 'px'
          }"
        >
          <div v-if="contextMenu.targetDevice" class="menu-item" @mousedown.prevent="handleBindDevice">
            绑定设备
          </div>
          <div v-if="contextMenu.targetDevice" class="menu-item danger" @mousedown.prevent="handleDeleteDevice">
            删除设备
          </div>
          <div v-if="!contextMenu.targetDevice" class="menu-item" disabled>
            没有选中设备
          </div>
          <div class="menu-item" @mousedown.prevent="hideContextMenu">
            取消
          </div>
        </div>
        
        <!-- 3D视图控制 -->
        <div class="viewport-controls">
          <el-button-group>
            <el-button @click="resetView">重置视图</el-button>
            <el-button @click="fitToScreen">适应屏幕</el-button>
            <el-button @click="toggleWireframe">
              {{ wireframeMode ? '实体模式' : '线框模式' }}
            </el-button>
          </el-button-group>
          
          <div class="view-controls">
            <el-slider
              v-model="cameraDistance"
              :min="5"
              :max="50"
              @input="updateCameraDistance"
              style="width: 100px;"
            />
            <span>距离</span>
          </div>
          
        </div>

      </div>

      <aside class="object-inspector">
        <div class="inspector-title">对象属性</div>
        <template v-if="selectedObject">
          <div class="selected-object-card">
            <div class="selected-object-icon"><el-icon><Setting /></el-icon></div>
            <div>
              <strong>{{ selectedObject.name }}</strong>
              <span>{{ selectedObject.description || selectedObject.deviceType }}</span>
            </div>
            <el-tag size="small">已选择</el-tag>
          </div>

          <div class="inspector-section">
            <div class="inspector-label">位置</div>
            <div class="axis-grid">
              <span>X {{ Number(selectedObject.mesh?.position?.x ?? selectedObject.position?.x ?? 0).toFixed(2) }}</span>
              <span>Y {{ Number(selectedObject.mesh?.position?.y ?? selectedObject.position?.y ?? 0).toFixed(2) }}</span>
              <span>Z {{ Number(selectedObject.mesh?.position?.z ?? selectedObject.position?.z ?? 0).toFixed(2) }}</span>
            </div>
          </div>

          <div class="inspector-section">
            <div class="inspector-label">旋转</div>
            <div class="axis-grid">
              <span>X {{ Number(selectedObject.mesh?.rotation?.x ?? 0).toFixed(2) }}</span>
              <span>Y {{ Number(selectedObject.mesh?.rotation?.y ?? 0).toFixed(2) }}</span>
              <span>Z {{ Number(selectedObject.mesh?.rotation?.z ?? 0).toFixed(2) }}</span>
            </div>
          </div>

          <div class="inspector-section">
            <div class="inspector-label">绑定设备</div>
            <el-button plain class="inspector-action" @click="openDeviceBinding">配置数据绑定</el-button>
          </div>

          <div class="inspector-section live-state">
            <div class="inspector-label">实时状态</div>
            <div class="live-row"><span>运行状态</span><strong>运行中</strong></div>
            <div class="live-row"><span>对象类型</span><strong>{{ selectedObject.deviceType }}</strong></div>
            <div class="live-row"><span>创建时间</span><strong>{{ selectedObject.createTime ? new Date(selectedObject.createTime).toLocaleTimeString() : '--' }}</strong></div>
          </div>
        </template>
        <el-empty v-else description="选择场景对象后查看属性" :image-size="64" />
      </aside>
    </div>
    
    <!-- 底部信息栏 -->
    <div class="status-bar">
      <div class="status-info">
        <span>设备数量: {{ sceneObjects.length }}</span>
        <span>选中: {{ selectedObject ? selectedObject.name : '无' }}</span>
      </div>
      
      <div class="coordinates" v-if="mousePosition">
        <span>X: {{ mousePosition.x.toFixed(2) }}</span>
        <span>Y: {{ mousePosition.y.toFixed(2) }}</span>
        <span>Z: {{ mousePosition.z.toFixed(2) }}</span>
      </div>
    </div>
    
    <!-- 设备绑定对话框 -->
    <el-dialog
      v-model="deviceBindingDialogVisible"
      title="设备绑定"
      width="500px"
    >
      <el-form :model="deviceBindingForm" label-width="100px">
        <el-form-item label="3D设备">
          <el-input v-model="deviceBindingForm.sceneDeviceName" disabled />
        </el-form-item>
        
        <el-form-item label="MQTT设备ID">
          <el-select 
            v-model="deviceBindingForm.mqttDeviceId" 
            placeholder="选择MQTT设备"
            filterable
            style="width: 100%"
          >
            <el-option 
              v-for="device in availableMqttDevices" 
              :key="device.id" 
              :label="`${device.name} (${device.id})`"
              :value="device.id"
            >
              <div class="device-option">
                <div class="device-name">{{ device.name }}</div>
                <div class="device-info">{{ device.id }} - {{ device.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="数据映射">
          <el-input
            v-model="deviceBindingForm.dataMapping"
            type="textarea"
            placeholder="JSON格式的数据映射配置（可选）"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deviceBindingDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDeviceBinding">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 批量添加设备对话框 -->
    <el-dialog
      v-model="batchAddDialogVisible"
      title="批量添加设备"
      width="600px"
    >
      <el-form :model="batchAddForm" label-width="120px">
        <el-form-item label="设备类型">
          <el-select v-model="batchAddForm.deviceType" placeholder="选择设备类型" style="width: 100%">
            <el-option-group label="传感器">
              <el-option 
                v-for="device in deviceLibrary.sensors" 
                :key="device.type" 
                :label="device.name" 
                :value="device.type"
              />
            </el-option-group>
            <el-option-group label="执行器">
              <el-option 
                v-for="device in deviceLibrary.actuators" 
                :key="device.type" 
                :label="device.name" 
                :value="device.type"
              />
            </el-option-group>
            <el-option-group label="结构件">
              <el-option 
                v-for="device in deviceLibrary.structures" 
                :key="device.type" 
                :label="device.name" 
                :value="device.type"
              />
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <el-form-item label="数量">
          <el-input-number v-model="batchAddForm.count" :min="1" :max="20" />
        </el-form-item>
        
        <el-form-item label="排列方式">
          <el-radio-group v-model="batchAddForm.arrangement">
            <el-radio label="grid">网格排列</el-radio>
            <el-radio label="line">直线排列</el-radio>
            <el-radio label="circle">圆形排列</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="间距">
          <el-slider v-model="batchAddForm.spacing" :min="1" :max="5" :step="0.5" />
          <span style="margin-left: 10px;">{{ batchAddForm.spacing }}m</span>
        </el-form-item>
        
        <el-form-item label="命名前缀">
          <el-input v-model="batchAddForm.namePrefix" placeholder="可选，不填则使用默认命名" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchAddDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBatchAdd">确定添加</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Plus } from '@element-plus/icons-vue'

import { ModelLoader } from '../utils/ModelLoader.js'
import { DeviceDataManager } from '../utils/DeviceDataManager.js'
import { MQTTDataIntegrator } from '../utils/MQTTDataIntegrator.js'
import { ModelBuilder } from '../utils/ModelBuilder.js'
// 模型导入相关
const fileInput = ref(null)
let modelLoader = null
let deviceDataManager = null
let mqttDataIntegrator = null

// 设备数据模拟
const deviceDataList = ref([])

const triggerImportModel = () => {
  if (fileInput.value) fileInput.value.value = '';
  fileInput.value && fileInput.value.click();
}

const onModelFileChange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!modelLoader) {
    modelLoader = new ModelLoader(scene);
  }
  try {
    const result = await modelLoader.loadFromFile(file, { x: 0, y: 1, z: 0 }, 1);
    
    // 注册为可监控设备
    if (deviceManager && result.model) {
      const deviceId = deviceManager.registerDevice(result.model, {
        id: `imported_${Date.now()}`,
        name: file.name.split('.')[0],
        type: 'imported_model',
        units: {
          status: '',
          temperature: ' °C'
        }
      });
      
      // 添加到场景对象列表
      const sceneObject = {
        id: deviceId,
        name: file.name.split('.')[0],
        deviceType: 'imported_model',
        mesh: result.model,
        position: { x: 0, y: 1, z: 0 },
        rotation: { x: 0, y: 0, z: 0 },
        scale: 1
      };
      sceneObjects.value.push(sceneObject);
    }
    
    ElMessage.success('模型导入成功');
  } catch (err) {
    ElMessage.error('模型导入失败: ' + err.message);
  }
}

const addBuiltInModel = (modelType) => {
  if (!modelBuilder) {
    ElMessage.error('模型构建器未初始化');
    return;
  }
  
  let model;
  const position = { x: 0, y: 0, z: 0 };
  
  try {
    console.log('开始创建模型:', modelType);
    
    // 获取设备配置
    const deviceConfig = getDeviceConfig(modelType);
    
    switch (modelType) {
      case 'pump':
        model = modelBuilder.createPump(position);
        break;
      case 'tank':
        model = modelBuilder.createTank(position);
        break;
      case 'heat_exchanger':
        model = modelBuilder.createHeatExchanger(position);
        break;
      case 'valve_gate':
        model = modelBuilder.createValve(position, 1, 'gate');
        break;
      case 'valve_ball':
        model = modelBuilder.createValve(position, 1, 'ball');
        break;
      case 'conveyor':
        model = modelBuilder.createConveyor(position, 8);
        break;
      case 'factory':
        model = modelBuilder.createFactory(position);
        break;
      default:
        ElMessage.warning('未知的模型类型');
        return;
    }
    
    console.log('模型创建结果:', model);
    
    if (!model) {
      ElMessage.error('模型创建失败：返回空对象');
      return;
    }
    
    if (model) {
      scene.add(model);
      
      const deviceId = deviceConfig.id;
      
      // 设置mesh的userData
      model.userData = {
        id: deviceId,
        deviceType: modelType,
        name: deviceConfig.name
      }
      
      // 添加到场景对象列表
      const sceneObject = {
        id: deviceId,
        name: deviceConfig.name,
        deviceType: modelType,
        mesh: model,
        position: { ...position },
        rotation: { x: 0, y: 0, z: 0 },
        scale: 1
      };
      sceneObjects.value.push(sceneObject);
      
      // 注册设备并配置数据显示
      if (deviceDataManager) {
        // 注册到设备数据管理器
        deviceDataManager.registerDevice(model, {
          id: deviceId,
          name: deviceConfig.name,
          type: modelType,
          units: deviceConfig.units,
          colorMapping: getDeviceColorMapping(modelType),
          rotation: getDeviceRotationMapping(modelType),
          scale: getDeviceScaleMapping(modelType)
        })
      }
      
      // 选中新创建的对象
      selectObject(sceneObject);
      
      // 调试场景状态
      debugSceneState();
      
      ElMessage.success(`添加${deviceConfig?.name || modelType}成功`);
    }
  } catch (error) {
    console.error('创建模型失败 - 详细错误:', error);
    console.error('错误堆栈:', error.stack);
    ElMessage.error(`创建模型失败: ${error.message}`);
  }
}

const getDeviceConfig = (modelType) => {
  const configs = {
    pump: {
      id: `pump_${Date.now()}`,
      name: '工业泵',
      type: 'pump',
      units: {
        pressure: ' bar',
        flow: ' L/min',
        temperature: ' °C',
        power: ' W',
        speed: ' rpm'
      },
      thresholds: {
        temperature: { warning: 60, danger: 80 },
        pressure: { warning: 8, danger: 10 }
      },
      colorMapping: {
        parameter: 'temperature',
        range: { min: 20, max: 100 }
      },
      rotation: {
        parameter: 'speed'
      }
    },
    tank: {
      id: `tank_${Date.now()}`,
      name: '储罐',
      type: 'tank',
      units: {
        level: ' %',
        temperature: ' °C',
        pressure: ' bar'
      },
      thresholds: {
        level: { warning: 85, danger: 95 },
        pressure: { warning: 3, danger: 4 }
      },
      colorMapping: {
        parameter: 'level',
        range: { min: 0, max: 100 }
      },
      levelDisplay: {
        parameter: 'level',
        range: { min: 0, max: 100 }
      }
    },
    heat_exchanger: {
      id: `hx_${Date.now()}`,
      name: '换热器',
      type: 'heat_exchanger',
      units: {
        inlet_temp: ' °C',
        outlet_temp: ' °C',
        pressure: ' bar',
        flow: ' L/min'
      },
      colorMapping: {
        parameter: 'inlet_temp',
        range: { min: 20, max: 200 }
      }
    },
    valve_gate: {
      id: `valve_${Date.now()}`,
      name: '闸阀',
      type: 'valve',
      units: {
        position: ' %',
        pressure: ' bar'
      }
    },
    valve_ball: {
      id: `valve_${Date.now()}`,
      name: '球阀',
      type: 'valve',
      units: {
        position: ' %',
        pressure: ' bar'
      }
    },
    conveyor: {
      id: `conveyor_${Date.now()}`,
      name: '传送带',
      type: 'conveyor',
      units: {
        speed: ' m/min',
        load: ' %',
        power: ' W'
      }
    },
    factory: {
      id: `factory_${Date.now()}`,
      name: '工厂',
      type: 'factory',
      units: {
        production_rate: ' units/hr',
        efficiency: ' %'
      }
    }
  };
  
  return configs[modelType] || {
    id: `device_${Date.now()}`,
    name: '设备',
    type: modelType,
    units: {}
  };
}

const toggleDeviceLabels = () => {
  if (!deviceManager) return;
  
  if (showLabels.value) {
    deviceManager.showDeviceLabels();
  } else {
    deviceManager.hideDeviceLabels();
  }
}

const getParameterDisplayName = (key) => {
  const displayNames = {
    temperature: '温度',
    pressure: '压力',
    flow: '流量',
    level: '液位',
    speed: '转速',
    voltage: '电压',
    current: '电流',
    power: '功率',
    status: '状态',
    alarm: '报警',
    inlet_temp: '进口温度',
    outlet_temp: '出口温度',
    position: '位置',
    load: '负载',
    torque: '扭矩',
    production_rate: '生产率',
    efficiency: '效率'
  };
  return displayNames[key] || key;
}

const getDeviceStatus = (device) => {
  if (device.data.status) {
    return device.data.status;
  }
  
  // 根据阈值判断状态
  for (const [key, value] of Object.entries(device.data)) {
    const thresholds = device.config.thresholds?.[key];
    if (thresholds && typeof value === 'number') {
      if (value >= thresholds.danger) {
        return '危险';
      } else if (value >= thresholds.warning) {
        return '警告';
      }
    }
  }
  
  return '正常';
}

const getDeviceStatusType = (device) => {
  const status = getDeviceStatus(device);
  switch (status) {
    case '危险':
    case '故障':
      return 'danger';
    case '警告':
    case '超限':
      return 'warning';
    case '正常':
    case '运行':
      return 'success';
    default:
      return 'info';
  }
}

const getParameterValueClass = (device, key, value) => {
  const thresholds = device.config.thresholds?.[key];
  if (thresholds && typeof value === 'number') {
    if (value >= thresholds.danger) {
      return 'value-danger';
    } else if (value >= thresholds.warning) {
      return 'value-warning';
    }
  }
  return 'value-normal';
}

const formatUpdateTime = (timestamp) => {
  if (!timestamp) return '未知';
  const now = Date.now();
  const diff = Math.floor((now - timestamp) / 1000);
  
  if (diff < 60) {
    return `${diff}秒前`;
  } else if (diff < 3600) {
    return `${Math.floor(diff / 60)}分钟前`;
  } else {
    return `${Math.floor(diff / 3600)}小时前`;
  }
}

// 响应式数据
const threeContainer = ref(null)
const mode = ref('select')
const selectedObject = ref(null)
const searchText = ref('')
const activeLibraryCategory = ref(['sensors'])
const showGrid = ref(true)
const wireframeMode = ref(false)
const cameraDistance = ref(20)
const mousePosition = ref(null)

// 设备数据显示相关


// 右键菜单相关
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  targetDevice: null
})

// 设备绑定相关
const deviceBindingDialogVisible = ref(false)
const deviceBindingForm = reactive({
  sceneDeviceId: '',
  sceneDeviceName: '',
  mqttDeviceId: '',
  dataMapping: ''
})

// 批量添加设备相关
const batchAddDialogVisible = ref(false)
const batchAddForm = reactive({
  deviceType: '',
  count: 3,
  arrangement: 'grid',
  spacing: 2,
  namePrefix: ''
})

const availableMqttDevices = ref([
  { id: 'temp_sensor_001', type: 'temperature_sensor', name: '车间A温度传感器', description: '监测车间环境温度' },
  { id: 'pressure_001', type: 'pressure_sensor', name: '主管道压力传感器', description: '监测主管道压力状态' },
  { id: 'flow_meter_001', type: 'flow_meter', name: '进水流量计', description: '测量进水管道流量' },
  { id: 'motor_001', type: 'servo_motor', name: '主驱动电机', description: '设备主要驱动装置' },
  { id: 'tank_level_001', type: 'level_sensor', name: '储罐液位传感器', description: '监测储罐液体高度' },
  { id: 'temp_sensor_002', type: 'temperature_sensor', name: '车间B温度传感器', description: '监测车间B环境温度' },
  { id: 'vibration_001', type: 'vibration_sensor', name: '设备振动传感器', description: '监测设备运行振动' },
  { id: 'humidity_001', type: 'humidity_sensor', name: '环境湿度传感器', description: '监测环境湿度变化' },
  { id: 'valve_001', type: 'valve', name: '主控制阀门', description: '控制主管道流量' },
  { id: 'pump_001', type: 'pump', name: '循环水泵', description: '循环系统水泵设备' }
])

// Three.js 相关变量
let scene, camera, renderer, controls, transformControls, modelBuilder
let raycaster, mouse
let gridHelper, axesHelper
let animationId

// 场景数据
const sceneObjects = ref([])

// 设备库数据
const deviceLibrary = reactive({
  sensors: [
    { type: 'temperature_sensor', name: '温度传感器', icon: '温', color: '#081F5C' },
    { type: 'pressure_sensor', name: '压力传感器', icon: '压', color: '#334EAC' },
    { type: 'flow_meter', name: '流量计', icon: '流', color: '#7096D1' },
  ],
  actuators: [
    { type: 'fan', name: '风扇', icon: '风', color: '#334EAC' },
    { type: 'servo_motor', name: '伺服电机', icon: '伺', color: '#081F5C' },
    { type: 'indicator_light', name: '指示灯', icon: '灯', color: '#BAD6EB' },
    { type: 'digital_input', name: '数字输入', icon: '入', color: '#081F5C' },
    { type: 'digital_output', name: '数字输出', icon: '出', color: '#7096D1' },
  ],
  structures: [
    { type: 'pipe', name: '管道', icon: '管', color: '#7096D1' },
    { type: 'tank', name: '储罐', icon: '罐', color: '#334EAC' },
    { type: 'conveyor', name: '传送带', icon: '传', color: '#081F5C' },
  ]
})

// 计算属性
const filteredSensors = computed(() => {
  return deviceLibrary.sensors.filter(device => 
    device.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const filteredActuators = computed(() => {
  return deviceLibrary.actuators.filter(device => 
    device.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const filteredStructures = computed(() => {
  return deviceLibrary.structures.filter(device => 
    device.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

// 基础功能函数
const initThreeJS = async () => {
  try {
    // 动态导入 Three.js - 修复导入路径
    const THREE = await import('three')
    const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls.js')
    const { TransformControls } = await import('three/examples/jsm/controls/TransformControls.js')
    
    // 检查容器是否存在
    if (!threeContainer.value) {
      throw new Error('3D容器未找到')
    }
    
    // 创建场景
    scene = new THREE.Scene()
    scene.background = null
    
    // 创建相机
    const containerWidth = threeContainer.value.clientWidth || 800
    const containerHeight = threeContainer.value.clientHeight || 600
    
    camera = new THREE.PerspectiveCamera(
      75, 
      containerWidth / containerHeight, 
      0.1, 
      1000
    )
    camera.position.set(20, 20, 20)
    camera.lookAt(0, 0, 0)
    
    // 创建渲染器
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setClearColor(0x000000, 0)
    renderer.setSize(containerWidth, containerHeight)
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    threeContainer.value.appendChild(renderer.domElement)
    
    // 创建控制器
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    
    // 变换控制器
    transformControls = new TransformControls(camera, renderer.domElement)
    transformControls.size = 0.5 
    
    // 设置事件监听
    transformControls.addEventListener('change', () => {
      // 禁用轨道控制器当变换控制器被拖拽时
      if (controls) {
        controls.enabled = !transformControls.dragging
      }
    })
    
    transformControls.addEventListener('mouseDown', () => {
      if (controls) {
        controls.enabled = false
      }
    })
    
    transformControls.addEventListener('mouseUp', () => {
      console.log('TransformControls mouseUp event')
      if (controls) {
        controls.enabled = true
      }
      // 更新位置信息
      updateSelectedObjectPosition()
      
      console.log('MouseUp - selected object:', selectedObject.value?.name)
      console.log('MouseUp - transform controls object:', transformControls.object)
    })
    
    // 默认设置为移动模式
    transformControls.setMode('translate')
    transformControls.setSpace('world')
    scene.add(transformControls)
    
    // 射线投射器
    raycaster = new THREE.Raycaster()
    mouse = new THREE.Vector2()
    
    // 添加光源
    setupLighting(THREE)
    
    // 添加网格和坐标轴
    setupHelpers(THREE)
    
    // 初始化模型构建器
    modelBuilder = new ModelBuilder(scene)
    
    // 开始渲染循环
    animate()
    
    window.THREE = THREE // 全局可用

    // 初始化模型加载器
    modelLoader = new ModelLoader(scene)
    
    // 初始化设备数据管理器
    deviceDataManager = new DeviceDataManager(scene, camera, renderer)
    
    // 初始化MQTT数据集成器
    mqttDataIntegrator = new MQTTDataIntegrator(deviceDataManager)
    
    console.log('3D引擎初始化成功')
    
  } catch (error) {
    console.error('Three.js 初始化失败:', error)
    ElMessage.error(`3D引擎初始化失败: ${error.message}`)
  }
}

// 设置光照
const setupLighting = (THREE) => {
  // 环境光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)
  
  // 平行光
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0)
  directionalLight.position.set(50, 50, 50)
  directionalLight.castShadow = true
  directionalLight.shadow.mapSize.width = 2048
  directionalLight.shadow.mapSize.height = 2048
  scene.add(directionalLight)
}

// 设置辅助对象
const setupHelpers = (THREE) => {
  // 网格
  gridHelper = new THREE.GridHelper(50, 50, 0x7096d1, 0xbad6eb)
  gridHelper.visible = showGrid.value
  scene.add(gridHelper)
  
  // 坐标轴
  axesHelper = new THREE.AxesHelper(5)
  axesHelper.visible = false
  scene.add(axesHelper)
}

// 创建设备3D模型
const createDeviceModel = (deviceType, position = { x: 0, y: 0, z: 0 }) => {
  const THREE = window.THREE
  if (!THREE) return null
  
  let mesh
  
  switch (deviceType) {
    case 'temperature_sensor':
      mesh = createTemperatureSensor(THREE)
      break
    case 'pressure_sensor':
      mesh = createPressureSensor(THREE)
      break
    case 'flow_meter':
      mesh = createFlowMeter(THREE)
      break
    case 'fan':
      mesh = createFan(THREE)
      break
    case 'servo_motor':
      mesh = createServoMotor(THREE)
      break
    case 'indicator_light':
      mesh = createIndicatorLight(THREE)
      break
    case 'digital_input':
      mesh = createDigitalInput(THREE)
      break
    case 'digital_output':
      mesh = createDigitalOutput(THREE)
      break
    case 'pipe':
      mesh = createPipe(THREE)
      break
    case 'tank':
      mesh = createTank(THREE)
      break
    case 'conveyor':
      mesh = createConveyor(THREE)
      break
    default:
      mesh = createDefaultDevice(THREE)
  }
  
  if (mesh) {
    mesh.position.set(position.x, position.y, position.z)
    mesh.castShadow = true
    mesh.receiveShadow = true
    
    // 添加设备标签
    addDeviceLabel(mesh, deviceType)
  }
  
  return mesh
}

// 创建温度传感器模型
const createTemperatureSensor = (THREE) => {
  const group = new THREE.Group()
  
  // 主体
  const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1, 8)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 传感器探头
  const probeGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.4, 6)
  const probeMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const probe = new THREE.Mesh(probeGeometry, probeMaterial)
  probe.position.y = 0.7
  
  group.add(body)
  group.add(probe)
  
  return group
}

// 创建压力传感器模型
const createPressureSensor = (THREE) => {
  const group = new THREE.Group()
  
  // 主体
  const bodyGeometry = new THREE.BoxGeometry(0.8, 0.8, 0.4)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x7096d1 })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 压力接口
  const portGeometry = new THREE.CylinderGeometry(0.15, 0.15, 0.3, 8)
  const portMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const port = new THREE.Mesh(portGeometry, portMaterial)
  port.position.z = 0.35
  port.rotation.x = Math.PI / 2
  
  group.add(body)
  group.add(port)
  
  return group
}

// 创建流量计模型
const createFlowMeter = (THREE) => {
  const group = new THREE.Group()
  
  // 主体环形
  const torusGeometry = new THREE.TorusGeometry(0.6, 0.2, 8, 16)
  const torusMaterial = new THREE.MeshLambertMaterial({ color: 0x7096d1 })
  const torus = new THREE.Mesh(torusGeometry, torusMaterial)
  
  // 显示屏
  const screenGeometry = new THREE.BoxGeometry(0.4, 0.2, 0.1)
  const screenMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const screen = new THREE.Mesh(screenGeometry, screenMaterial)
  screen.position.y = 0.8
  
  group.add(torus)
  group.add(screen)
  
  return group
}

// 创建风扇模型
const createFan = (THREE) => {
  const group = new THREE.Group()
  
  // 风扇外壳
  const housingGeometry = new THREE.CylinderGeometry(1, 1, 0.3, 16)
  const housingMaterial = new THREE.MeshLambertMaterial({ color: 0xbad6eb })
  const housing = new THREE.Mesh(housingGeometry, housingMaterial)
  
  // 风扇叶片
  const bladeGeometry = new THREE.BoxGeometry(0.1, 1.6, 0.05)
  const bladeMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac })
  
  for (let i = 0; i < 4; i++) {
    const blade = new THREE.Mesh(bladeGeometry, bladeMaterial)
    blade.rotation.y = (i * Math.PI) / 2
    blade.position.y = 0.2
    group.add(blade)
  }
  
  group.add(housing)
  
  return group
}

// 创建伺服电机模型
const createServoMotor = (THREE) => {
  const group = new THREE.Group()
  
  // 电机主体
  const bodyGeometry = new THREE.BoxGeometry(1.2, 0.8, 0.8)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 电机轴
  const shaftGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.6, 8)
  const shaftMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial)
  shaft.position.x = 0.7
  shaft.rotation.z = Math.PI / 2
  
  group.add(body)
  group.add(shaft)
  
  return group
}

// 创建指示灯模型
const createIndicatorLight = (THREE) => {
  const group = new THREE.Group()
  
  // 灯体
  const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.3, 0.2, 16)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 灯泡
  const lightGeometry = new THREE.SphereGeometry(0.25, 16, 16)
  const lightMaterial = new THREE.MeshLambertMaterial({ 
    color: 0xbad6eb,
    emissive: 0x081f5c,
    transparent: true,
    opacity: 0.8
  })
  const light = new THREE.Mesh(lightGeometry, lightMaterial)
  light.position.y = 0.2
  
  group.add(body)
  group.add(light)
  
  return group
}

// 创建数字输入模型
const createDigitalInput = (THREE) => {
  const group = new THREE.Group()
  
  const bodyGeometry = new THREE.BoxGeometry(0.6, 0.3, 0.3)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 输入端口
  const portGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.2, 8)
  const portMaterial = new THREE.MeshLambertMaterial({ color: 0x7096d1 })
  
  for (let i = 0; i < 3; i++) {
    const port = new THREE.Mesh(portGeometry, portMaterial)
    port.position.x = (i - 1) * 0.15
    port.position.z = 0.25
    port.rotation.x = Math.PI / 2
    group.add(port)
  }
  
  group.add(body)
  return group
}

// 创建数字输出模型
const createDigitalOutput = (THREE) => {
  const group = new THREE.Group()
  
  const bodyGeometry = new THREE.BoxGeometry(0.6, 0.3, 0.3)
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac })
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
  
  // 输出端口
  const portGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.2, 8)
  const portMaterial = new THREE.MeshLambertMaterial({ color: 0xbad6eb })
  
  for (let i = 0; i < 3; i++) {
    const port = new THREE.Mesh(portGeometry, portMaterial)
    port.position.x = (i - 1) * 0.15
    port.position.z = 0.25
    port.rotation.x = Math.PI / 2
    group.add(port)
  }
  
  group.add(body)
  return group
}

// 创建管道模型
const createPipe = (THREE) => {
  const geometry = new THREE.CylinderGeometry(0.2, 0.2, 5, 16)
  const material = new THREE.MeshLambertMaterial({ color: 0x7096d1 })
  const pipe = new THREE.Mesh(geometry, material)
  pipe.rotation.z = Math.PI / 2
  
  return pipe
}

// 创建储罐模型
const createTank = (THREE) => {
  const group = new THREE.Group()
  
  // 罐体
  const tankGeometry = new THREE.CylinderGeometry(2, 2, 3, 16)
  const tankMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac, transparent: true, opacity: 0.8 })
  const tank = new THREE.Mesh(tankGeometry, tankMaterial)
  
  // 液位指示
  const liquidGeometry = new THREE.CylinderGeometry(1.9, 1.9, 1.8, 16)
  const liquidMaterial = new THREE.MeshLambertMaterial({ color: 0xbad6eb, transparent: true, opacity: 0.6 })
  const liquid = new THREE.Mesh(liquidGeometry, liquidMaterial)
  liquid.position.y = -0.6
  
  group.add(tank)
  group.add(liquid)
  
  return group
}

// 创建传送带模型
const createConveyor = (THREE) => {
  const group = new THREE.Group()
  
  // 传送带主体
  const beltGeometry = new THREE.BoxGeometry(5, 0.2, 1)
  const beltMaterial = new THREE.MeshLambertMaterial({ color: 0x334eac })
  const belt = new THREE.Mesh(beltGeometry, beltMaterial)
  
  // 滚筒
  const drumGeometry = new THREE.CylinderGeometry(0.2, 0.2, 1.2, 8)
  const drumMaterial = new THREE.MeshLambertMaterial({ color: 0x081f5c })
  
  const drum1 = new THREE.Mesh(drumGeometry, drumMaterial)
  drum1.position.x = -2.4
  drum1.position.y = 0.2
  drum1.rotation.z = Math.PI / 2
  
  const drum2 = new THREE.Mesh(drumGeometry, drumMaterial)
  drum2.position.x = 2.4
  drum2.position.y = 0.2
  drum2.rotation.z = Math.PI / 2
  
  group.add(belt)
  group.add(drum1)
  group.add(drum2)
  
  return group
}

// 创建默认设备模型
const createDefaultDevice = (THREE) => {
  const geometry = new THREE.BoxGeometry(1, 1, 1)
  const material = new THREE.MeshLambertMaterial({ color: 0x7096d1 })
  return new THREE.Mesh(geometry, material)
}

// 添加设备标签
const addDeviceLabel = (mesh, deviceType) => {
  // 这里可以添加文字标签的逻辑
  // 暂时留空，以后可以扩展
}

// 模式和操作相关函数
const setMode = (newMode) => {
  mode.value = newMode
  
  if (selectedObject.value && selectedObject.value.mesh && transformControls) {
    switch (newMode) {
      case 'rotate':
        transformControls.setMode('rotate')
        break
      case 'scale':
        transformControls.setMode('scale')
        break
      case 'select':
      default:
        transformControls.setMode('translate')
    }
  }
}

const addDevice = (deviceType) => {
  const deviceInfo = [...deviceLibrary.sensors, ...deviceLibrary.actuators, ...deviceLibrary.structures]
    .find(d => d.type === deviceType)
  
  if (!deviceInfo) {
    ElMessage.error('未找到设备类型信息')
    return
  }
  
  // 生成智能位置（避免设备重叠）
  const position = getSmartPosition()
  
  // 生成唯一设备ID和名称
  const deviceId = `${deviceType}_${Date.now()}`
  const deviceCount = sceneObjects.value.filter(obj => obj.deviceType === deviceType).length
  const deviceName = `${deviceInfo.name}_${String(deviceCount + 1).padStart(2, '0')}`
  
  const mesh = createDeviceModel(deviceType, position)
  if (!mesh) {
    ElMessage.error('创建设备模型失败')
    return
  }
  
  // 设置设备属性
  mesh.userData = {
    id: deviceId,
    deviceType: deviceType,
    name: deviceName,
    createTime: new Date().toISOString(),
    status: 'normal'
  }
  
  // 添加到场景
  scene.add(mesh)
  
  // 创建场景对象
  const sceneObject = {
    id: deviceId,
    name: deviceName,
    deviceType: deviceType,
    mesh: mesh,
    position: { ...position },
    rotation: { x: 0, y: 0, z: 0 },
    scale: 1,
    createTime: mesh.userData.createTime,
    description: getDeviceDescription(deviceType)
  }
  
  sceneObjects.value.push(sceneObject)
  
  // 注册设备到数据管理器
  if (deviceDataManager) {
    const deviceConfig = getExtendedDeviceConfig(deviceType, deviceId, deviceName)
    deviceDataManager.registerDevice(mesh, deviceConfig)
  }
  
  // 添加创建动画
  addDeviceAnimation(mesh)
  
  // 选中新创建的设备
  selectObject(sceneObject)
  
  ElMessage.success(`成功添加 ${deviceInfo.name}: ${deviceName}`)
}

const selectObject = (object) => {
  console.log('selectObject called:', object?.name)
  console.log('Current selectedObject:', selectedObject.value?.name)
  console.log('TransformControls state:', {
    exists: !!transformControls,
    dragging: transformControls?.dragging,
    attached: !!transformControls?.object
  })
  
  // 如果TransformControls正在拖拽中，不进行选择操作
  if (transformControls && transformControls.dragging) {
    console.log('TransformControls is dragging, ignoring selection')
    return
  }
  
  selectedObject.value = object
  
  // 强制分离当前控制器
  if (transformControls) {
    console.log('Detaching transform controls')
    transformControls.detach()
    transformControls.visible = false
  }
  
  if (object && object.mesh && transformControls) {
    console.log('Attaching to mesh:', object.mesh)
    console.log('Mesh position:', object.mesh.position)
    
    // 确保对象可见且活跃
    object.mesh.visible = true
    
    // 强制更新变换矩阵
    object.mesh.updateMatrixWorld(true)
    
    // 附着变换控制器
    transformControls.attach(object.mesh)
    transformControls.visible = true
    
    // 设置模式
    transformControls.setMode('translate')
    transformControls.setSpace('world')
    
    console.log('Transform controls attached and configured')
    console.log('TransformControls object after attach:', transformControls.object)
  } else if (!object) {
    console.log('Deselecting object')
    if (transformControls) {
      transformControls.visible = false
    }
  }
}

// 智能定位功能 - 避免设备重叠
const getSmartPosition = () => {
  const gridSize = 2 // 网格间距
  const maxAttempts = 100 // 最大尝试次数
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // 生成螺旋式位置
    const ring = Math.floor(attempt / 8) + 1
    const angle = (attempt % 8) * (Math.PI / 4)
    
    const x = ring * gridSize * Math.cos(angle)
    const z = ring * gridSize * Math.sin(angle)
    const y = 1
    
    const position = { x, y, z }
    
    // 检查是否与现有设备冲突
    if (isPositionFree(position)) {
      return position
    }
  }
  
  // 如果都冲突，返回随机位置
  return {
    x: (Math.random() - 0.5) * 20,
    y: 1,
    z: (Math.random() - 0.5) * 20
  }
}

// 检查位置是否空闲
const isPositionFree = (position, minDistance = 1.5) => {
  return !sceneObjects.value.some(obj => {
    const distance = Math.sqrt(
      Math.pow(obj.position.x - position.x, 2) +
      Math.pow(obj.position.z - position.z, 2)
    )
    return distance < minDistance
  })
}

// 获取设备描述
const getDeviceDescription = (deviceType) => {
  const descriptions = {
    'temperature_sensor': '用于测量环境或设备温度的传感器',
    'pressure_sensor': '用于测量压力值的传感器设备',
    'flow_meter': '用于测量流体流量的计量设备',
    'fan': '用于通风或散热的风扇设备',
    'servo_motor': '高精度控制的伺服电机',
    'indicator_light': '状态指示灯，显示设备运行状态',
    'digital_input': '数字输入模块，接收数字信号',
    'digital_output': '数字输出模块，输出数字信号',
    'pipe': '用于流体传输的管道',
    'tank': '用于储存液体或气体的储罐',
    'conveyor': '用于物料传输的传送带'
  }
  return descriptions[deviceType] || '工业设备'
}

// 获取扩展设备配置
const getExtendedDeviceConfig = (deviceType, deviceId, deviceName) => {
  return {
    id: deviceId,
    name: deviceName,
    type: deviceType,
    units: getDeviceUnits(deviceType),
    colorMapping: getDeviceColorMapping(deviceType),
    rotation: getDeviceRotationMapping(deviceType),
    scale: getDeviceScaleMapping(deviceType),
    thresholds: getDeviceThresholds(deviceType),
    defaultValues: getDeviceDefaultValues(deviceType)
  }
}

// 获取设备阈值配置
const getDeviceThresholds = (deviceType) => {
  const thresholds = {
    'temperature_sensor': {
      temperature: { warning: 60, danger: 80, unit: '°C' }
    },
    'pressure_sensor': {
      pressure: { warning: 8, danger: 10, unit: 'bar' }
    },
    'flow_meter': {
      flow: { warning: 80, danger: 95, unit: 'L/min' }
    },
    'tank': {
      level: { warning: 85, danger: 95, unit: '%' },
      temperature: { warning: 50, danger: 70, unit: '°C' }
    }
  }
  return thresholds[deviceType] || {}
}

// 获取设备默认值
const getDeviceDefaultValues = (deviceType) => {
  const defaults = {
    'temperature_sensor': { temperature: 25 },
    'pressure_sensor': { pressure: 1.0 },
    'flow_meter': { flow: 50 },
    'fan': { speed: 1200, power: 100 },
    'servo_motor': { speed: 1800, torque: 50, temperature: 45 },
    'tank': { level: 60, temperature: 30 },
    'indicator_light': { status: 'on', brightness: 80 }
  }
  return defaults[deviceType] || {}
}

// 添加设备创建动画
const addDeviceAnimation = (mesh) => {
  if (!mesh) return
  
  // 保存原始缩放
  const originalScale = { x: mesh.scale.x, y: mesh.scale.y, z: mesh.scale.z }
  
  // 从0开始缩放
  mesh.scale.set(0, 0, 0)
  
  // 创建缩放动画
  const startTime = Date.now()
  const duration = 500 // 500ms动画
  
  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    // 使用easeOutBack缓动函数
    const easeProgress = 1 - Math.pow(1 - progress, 3)
    
    mesh.scale.set(
      originalScale.x * easeProgress,
      originalScale.y * easeProgress,
      originalScale.z * easeProgress
    )
    
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  
  requestAnimationFrame(animate)
}

const selectDeviceType = (device) => {
  addDevice(device.type)
}

// 获取设备单位配置
const getDeviceUnits = (deviceType) => {
  const units = {
    'temperature_sensor': { temperature: ' °C' },
    'pressure_sensor': { pressure: ' bar' },
    'flow_meter': { flow: ' L/min' },
    'servo_motor': { speed: ' RPM', temperature: ' °C' },
    'tank': { level: ' %', temperature: ' °C' },
    'fan': { speed: ' RPM' }
  }
  return units[deviceType] || {}
}

// 获取设备颜色映射配置
const getDeviceColorMapping = (deviceType) => {
  const mappings = {
    'temperature_sensor': { parameter: 'temperature', range: { min: 0, max: 100 } },
    'pressure_sensor': { parameter: 'pressure', range: { min: 0, max: 10 } },
    'tank': { parameter: 'level', range: { min: 0, max: 100 } }
  }
  return mappings[deviceType] || null
}

// 获取设备旋转映射配置
const getDeviceRotationMapping = (deviceType) => {
  const mappings = {
    'servo_motor': { parameter: 'speed' },
    'fan': { parameter: 'speed' }
  }
  return mappings[deviceType] || null
}

// 获取设备缩放映射配置
const getDeviceScaleMapping = (deviceType) => {
  const mappings = {
    'tank': { parameter: 'level', range: { min: 0, max: 100 } }
  }
  return mappings[deviceType] || null
}

// 事件处理函数
const onSceneClick = (event) => {
  if (!raycaster || !camera) return
  
  // 如果是拖拽事件，不处理选择
  if (transformControls && transformControls.dragging) {
    console.log('Transform controls dragging, ignoring click')
    return
  }
  
  const rect = threeContainer.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  raycaster.setFromCamera(mouse, camera)
  
  const objects = sceneObjects.value.map(obj => obj.mesh)
  const intersects = raycaster.intersectObjects(objects, true)
  
  if (intersects.length > 0) {
    const selectedMesh = intersects[0].object
    console.log('Clicked mesh:', selectedMesh)
    console.log('Available scene objects:', sceneObjects.value.map(obj => ({ name: obj.name, mesh: obj.mesh })))
    
    // 查找对应的场景对象，可能需要向上遍历父对象
    let sceneObject = null
    let currentObject = selectedMesh
    
    // 向上遍历查找对应的场景对象
    while (currentObject && !sceneObject) {
      sceneObject = sceneObjects.value.find(obj => obj.mesh === currentObject)
      if (!sceneObject) {
        currentObject = currentObject.parent
      }
    }
    
    console.log('Found scene object:', sceneObject)
    
    if (sceneObject) {
      console.log('Selecting object from click:', sceneObject.name)
      selectObject(sceneObject)
      debugSceneState()
    } else {
      console.log('No scene object found for clicked mesh')
    }
  } else {
    // 只在没有任何TransformControls处于活动状态时才取消选择
    if (!transformControls || !transformControls.object) {
      selectObject(null)
    }
  }
  
  const point = intersects.length > 0 ? intersects[0].point : null
  if (point) {
    mousePosition.value = { x: point.x, y: point.y, z: point.z }
  }
  
  // 隐藏右键菜单
  contextMenu.visible = false
}

// 右键菜单处理
const onRightClick = (event) => {
  console.log('=== 右键点击事件触发 ===')
  console.log('事件对象:', event)
  event.preventDefault()
  event.stopPropagation()
  
  console.log('raycaster:', raycaster)
  console.log('camera:', camera)
  console.log('threeContainer.value:', threeContainer.value)
  console.log('sceneObjects.value.length:', sceneObjects.value.length)
  
  if (!raycaster || !camera) {
    console.log('raycaster 或 camera 未初始化')
    return
  }
  
  if (!threeContainer.value) {
    console.log('threeContainer 未初始化')
    return
  }
  
  const rect = threeContainer.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  console.log('鼠标坐标:', { x: mouse.x, y: mouse.y })
  
  raycaster.setFromCamera(mouse, camera)
  
  const objects = sceneObjects.value.map(obj => obj.mesh)
  console.log('场景对象数量:', objects.length)
  
  const intersects = raycaster.intersectObjects(objects)
  console.log('检测到交集:', intersects.length)
  
  if (intersects.length > 0) {
    const selectedMesh = intersects[0].object
    console.log('选中的mesh:', selectedMesh)
    console.log('selectedMesh.parent:', selectedMesh.parent)
    console.log('selectedMesh.uuid:', selectedMesh.uuid)
    
    // 尝试通过mesh本身或其父对象查找场景对象
    let sceneObject = sceneObjects.value.find(obj => obj.mesh === selectedMesh)
    
    if (!sceneObject && selectedMesh.parent) {
      // 如果mesh是Group的子对象，尝试通过父对象查找
      sceneObject = sceneObjects.value.find(obj => obj.mesh === selectedMesh.parent)
      console.log('通过父对象查找到的场景对象:', sceneObject)
    }
    
    if (!sceneObject) {
      // 如果还是找不到，尝试遍历所有场景对象的子对象
      for (let obj of sceneObjects.value) {
        if (obj.mesh && obj.mesh.children) {
          for (let child of obj.mesh.children) {
            if (child === selectedMesh) {
              sceneObject = obj
              console.log('通过子对象遍历找到的场景对象:', sceneObject)
              break
            }
          }
        }
        if (sceneObject) break
      }
    }
    
    console.log('最终选中的场景对象:', sceneObject)
    
    if (sceneObject) {
      // 显示右键菜单
      contextMenu.visible = true
      contextMenu.x = event.clientX
      contextMenu.y = event.clientY
      contextMenu.targetDevice = sceneObject
      
      console.log('右键菜单位置:', { x: contextMenu.x, y: contextMenu.y })
      console.log('设置目标设备:', contextMenu.targetDevice)
      
      // 同时选中设备
      selectObject(sceneObject)
    } else {
      console.log('未找到场景对象')
      contextMenu.visible = false
    }
  } else {
    console.log('没有检测到设备')
    // 即使没有设备也显示右键菜单（只显示取消选项）
    contextMenu.visible = true
    contextMenu.x = event.clientX
    contextMenu.y = event.clientY
    contextMenu.targetDevice = null
    console.log('显示通用右键菜单')
  }
  
  console.log('=== 右键点击事件处理完成 ===')
}

const hideContextMenu = () => {
  contextMenu.visible = false
}

const openDeviceBinding = () => {
  console.log('openDeviceBinding 被调用')
  if (contextMenu.targetDevice) {
    console.log('目标设备:', contextMenu.targetDevice)
    const device = contextMenu.targetDevice
    deviceBindingForm.sceneDeviceId = device.id
    deviceBindingForm.sceneDeviceName = device.name
    deviceBindingForm.mqttDeviceId = ''
    deviceBindingForm.dataMapping = ''
    
    // 使用nextTick确保对话框能正常显示
    nextTick(() => {
      deviceBindingDialogVisible.value = true
      console.log('设备绑定对话框已显示:', deviceBindingDialogVisible.value)
    })
  } else {
    console.error('没有找到目标设备')
    ElMessage.error('没有找到目标设备')
  }
}

// 处理绑定设备点击
const handleBindDevice = (event) => {
  event.preventDefault()
  event.stopPropagation()
  
  console.log('=== handleBindDevice 开始 ===')
  console.log('contextMenu.targetDevice:', contextMenu.targetDevice)
  
  // 保存目标设备引用，防止被清空
  const targetDevice = contextMenu.targetDevice
  
  if (targetDevice) {
    console.log('目标设备存在，执行绑定操作:', targetDevice)
    
    // 立即设置表单数据
    deviceBindingForm.sceneDeviceId = targetDevice.id
    deviceBindingForm.sceneDeviceName = targetDevice.name
    deviceBindingForm.mqttDeviceId = ''
    deviceBindingForm.dataMapping = ''
    
    // 隐藏菜单
    contextMenu.visible = false
    
    // 显示对话框
    deviceBindingDialogVisible.value = true
    console.log('设备绑定对话框已显示')
  } else {
    console.error('contextMenu.targetDevice 为空或未定义')
    ElMessage.error('未选中目标设备，无法绑定')
    contextMenu.visible = false
  }
  console.log('=== handleBindDevice 结束 ===')
}

// 处理删除设备点击
const handleDeleteDevice = (event) => {
  event.preventDefault()
  event.stopPropagation()
  
  console.log('=== handleDeleteDevice 开始 ===')
  console.log('contextMenu.targetDevice:', contextMenu.targetDevice)
  
  // 保存目标设备引用，防止被清空
  const targetDevice = contextMenu.targetDevice
  
  if (targetDevice) {
    console.log('目标设备存在，执行删除操作:', targetDevice)
    
    // 设置选中对象
    selectedObject.value = targetDevice
    
    // 隐藏菜单
    contextMenu.visible = false
    
    // 执行删除
    deleteSelected()
    console.log('删除操作已执行')
  } else {
    console.error('contextMenu.targetDevice 为空或未定义')
    ElMessage.error('未选中目标设备，无法删除')
    contextMenu.visible = false
  }
  console.log('=== handleDeleteDevice 结束 ===')
}

const deleteContextDevice = () => {
  console.log('deleteContextDevice 被调用')
  if (contextMenu.targetDevice) {
    console.log('删除设备:', contextMenu.targetDevice)
    selectedObject.value = contextMenu.targetDevice
    
    // 立即执行删除操作
    deleteSelected()
    console.log('删除操作已执行')
  } else {
    console.error('没有找到要删除的设备')
    ElMessage.error('没有找到要删除的设备')
  }
}

const onDragStart = (event, device) => {
  event.dataTransfer.setData('device-type', device.type)
}

const onDragOver = (event) => {
  event.preventDefault()
}

const onDrop = (event) => {
  event.preventDefault()
  const deviceType = event.dataTransfer.getData('device-type')
  
  if (deviceType && raycaster && camera) {
    const rect = threeContainer.value.getBoundingClientRect()
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
    
    raycaster.setFromCamera(mouse, camera)
    
    const THREE = window.THREE
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0)
    const intersectPoint = new THREE.Vector3()
    raycaster.ray.intersectPlane(plane, intersectPoint)
    
    // 检查位置是否合适
    const targetPosition = { 
      x: Math.round(intersectPoint.x), 
      y: 1, 
      z: Math.round(intersectPoint.z) 
    }
    
    // 检查是否与现有设备冲突
    if (!isPositionFree(targetPosition, 1.2)) {
      ElMessage.warning('此位置太靠近其他设备，请选择其他位置')
      return
    }
    
    const deviceInfo = [...deviceLibrary.sensors, ...deviceLibrary.actuators, ...deviceLibrary.structures]
      .find(d => d.type === deviceType)
    
    if (deviceInfo) {
      // 使用改进的添加设备函数
      addDeviceAtPosition(deviceType, targetPosition)
    }
  }
}

// 在指定位置添加设备
const addDeviceAtPosition = (deviceType, position) => {
  const deviceInfo = [...deviceLibrary.sensors, ...deviceLibrary.actuators, ...deviceLibrary.structures]
    .find(d => d.type === deviceType)
  
  if (!deviceInfo) {
    ElMessage.error('未找到设备类型信息')
    return
  }
  
  // 生成唯一设备ID和名称
  const deviceId = `${deviceType}_${Date.now()}`
  const deviceCount = sceneObjects.value.filter(obj => obj.deviceType === deviceType).length
  const deviceName = `${deviceInfo.name}_${String(deviceCount + 1).padStart(2, '0')}`
  
  const mesh = createDeviceModel(deviceType, position)
  if (!mesh) {
    ElMessage.error('创建设备模型失败')
    return
  }
  
  // 设置设备属性
  mesh.userData = {
    id: deviceId,
    deviceType: deviceType,
    name: deviceName,
    createTime: new Date().toISOString(),
    status: 'normal'
  }
  
  // 添加到场景
  scene.add(mesh)
  
  // 创建场景对象
  const sceneObject = {
    id: deviceId,
    name: deviceName,
    deviceType: deviceType,
    mesh: mesh,
    position: { ...position },
    rotation: { x: 0, y: 0, z: 0 },
    scale: 1,
    createTime: mesh.userData.createTime,
    description: getDeviceDescription(deviceType)
  }
  
  sceneObjects.value.push(sceneObject)
  
  // 注册设备到数据管理器
  if (deviceDataManager) {
    const deviceConfig = getExtendedDeviceConfig(deviceType, deviceId, deviceName)
    deviceDataManager.registerDevice(mesh, deviceConfig)
  }
  
  // 添加创建动画
  addDeviceAnimation(mesh)
  
  // 选中新创建的设备
  selectObject(sceneObject)
  
  ElMessage.success(`在 (${position.x.toFixed(1)}, ${position.z.toFixed(1)}) 添加 ${deviceInfo.name}: ${deviceName}`)
}// 连接功能
const startConnection = () => {
  ElMessage.info('连接功能已移除')
}

// 设备总览相关方法
const openDeviceBindingById = (deviceId) => {
  const device = sceneObjects.value.find(obj => obj.id === deviceId)
  if (device) {
    deviceBindingForm.sceneDeviceId = deviceId
    deviceBindingForm.sceneDeviceName = device.name
    deviceBindingForm.mqttDeviceId = ''
    deviceBindingForm.dataMapping = ''
    deviceBindingDialogVisible.value = true
  }
}

const confirmDeviceBinding = () => {
  if (!deviceBindingForm.mqttDeviceId) {
    ElMessage.warning('请选择MQTT设备')
    return
  }
  
  if (mqttDataIntegrator) {
    let dataMapping = {}
    if (deviceBindingForm.dataMapping) {
      try {
        dataMapping = JSON.parse(deviceBindingForm.dataMapping)
      } catch (e) {
        ElMessage.error('数据映射格式错误，请使用正确的JSON格式')
        return
      }
    }
    
    mqttDataIntegrator.bindDevice(
      deviceBindingForm.sceneDeviceId,
      deviceBindingForm.mqttDeviceId,
      dataMapping
    )
    
    // 保存绑定信息到设备对象
    const deviceObj = sceneObjects.value.find(obj => obj.id === deviceBindingForm.sceneDeviceId)
    console.log('找到的设备对象:', deviceObj)
    console.log('绑定的MQTT设备ID:', deviceBindingForm.mqttDeviceId)
    
    if (deviceObj) {
      deviceObj.mqttDeviceId = deviceBindingForm.mqttDeviceId
      deviceObj.dataMapping = dataMapping
      console.log('设备绑定信息已保存:', {
        sceneDeviceId: deviceObj.id,
        mqttDeviceId: deviceObj.mqttDeviceId,
        dataMapping: deviceObj.dataMapping
      })
    } else {
      console.error('未找到设备对象:', deviceBindingForm.sceneDeviceId)
    }
    
    // 绑定成功后立即获取一次数据
    setTimeout(() => {
      mqttDataIntegrator.fetchRealtimeData()
    }, 500)
    
    ElMessage.success(`设备绑定成功: ${deviceBindingForm.sceneDeviceName} -> ${getMqttDeviceName(deviceBindingForm.mqttDeviceId)}`)
    deviceBindingDialogVisible.value = false
  } else {
    ElMessage.error('MQTT数据集成器未初始化')
  }
}

// 获取MQTT设备的中文名称
const getMqttDeviceName = (deviceId) => {
  const device = availableMqttDevices.value.find(d => d.id === deviceId)
  return device ? device.name : deviceId
}

// 批量添加设备功能
const openBatchAddDialog = () => {
  batchAddDialogVisible.value = true
}

const confirmBatchAdd = () => {
  if (!batchAddForm.deviceType) {
    ElMessage.warning('请选择设备类型')
    return
  }
  
  const positions = generateBatchPositions(
    batchAddForm.count,
    batchAddForm.arrangement,
    batchAddForm.spacing
  )
  
  const deviceInfo = [...deviceLibrary.sensors, ...deviceLibrary.actuators, ...deviceLibrary.structures]
    .find(d => d.type === batchAddForm.deviceType)
  
  if (!deviceInfo) {
    ElMessage.error('未找到设备类型信息')
    return
  }
  
  let successCount = 0
  
  positions.forEach((position, index) => {
    try {
      const deviceId = `${batchAddForm.deviceType}_${Date.now()}_${index}`
      let deviceName
      
      if (batchAddForm.namePrefix) {
        deviceName = `${batchAddForm.namePrefix}_${String(index + 1).padStart(2, '0')}`
      } else {
        const deviceCount = sceneObjects.value.filter(obj => obj.deviceType === batchAddForm.deviceType).length
        deviceName = `${deviceInfo.name}_${String(deviceCount + index + 1).padStart(2, '0')}`
      }
      
      const mesh = createDeviceModel(batchAddForm.deviceType, position)
      if (!mesh) return
      
      mesh.userData = {
        id: deviceId,
        deviceType: batchAddForm.deviceType,
        name: deviceName,
        createTime: new Date().toISOString(),
        status: 'normal'
      }
      
      scene.add(mesh)
      
      const sceneObject = {
        id: deviceId,
        name: deviceName,
        deviceType: batchAddForm.deviceType,
        mesh: mesh,
        position: { ...position },
        rotation: { x: 0, y: 0, z: 0 },
        scale: 1,
        createTime: mesh.userData.createTime,
        description: getDeviceDescription(batchAddForm.deviceType)
      }
      
      sceneObjects.value.push(sceneObject)
      
      // 注册设备到数据管理器
      if (deviceDataManager) {
        const deviceConfig = getExtendedDeviceConfig(batchAddForm.deviceType, deviceId, deviceName)
        deviceDataManager.registerDevice(mesh, deviceConfig)
      }
      
      // 添加创建动画（延迟执行以避免卡顿）
      setTimeout(() => {
        addDeviceAnimation(mesh)
      }, index * 100)
      
      successCount++
    } catch (error) {
      console.error('批量添加设备失败:', error)
    }
  })
  
  batchAddDialogVisible.value = false
  ElMessage.success(`成功批量添加 ${successCount} 个 ${deviceInfo.name}`)
  
  // 重置表单
  batchAddForm.deviceType = ''
  batchAddForm.count = 3
  batchAddForm.arrangement = 'grid'
  batchAddForm.spacing = 2
  batchAddForm.namePrefix = ''
}

// 生成批量添加的位置
const generateBatchPositions = (count, arrangement, spacing) => {
  const positions = []
  
  switch (arrangement) {
    case 'grid':
      const cols = Math.ceil(Math.sqrt(count))
      const rows = Math.ceil(count / cols)
      
      for (let i = 0; i < count; i++) {
        const row = Math.floor(i / cols)
        const col = i % cols
        
        positions.push({
          x: (col - (cols - 1) / 2) * spacing,
          y: 1,
          z: (row - (rows - 1) / 2) * spacing
        })
      }
      break
      
    case 'line':
      for (let i = 0; i < count; i++) {
        positions.push({
          x: (i - (count - 1) / 2) * spacing,
          y: 1,
          z: 0
        })
      }
      break
      
    case 'circle':
      const radius = (count * spacing) / (2 * Math.PI)
      
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * 2 * Math.PI
        
        positions.push({
          x: radius * Math.cos(angle),
          y: 1,
          z: radius * Math.sin(angle)
        })
      }
      break
  }
  
  return positions
}

// 场景管理
const saveScene = async () => {
  try {
    const sceneData = {
      objects: sceneObjects.value.map(obj => ({
        id: obj.id,
        name: obj.name,
        deviceType: obj.deviceType,
        position: obj.position,
        rotation: obj.rotation,
        scale: obj.scale
      }))
    }
    
    localStorage.setItem('industrial_3d_scene', JSON.stringify(sceneData))
    ElMessage.success('场景保存成功')
  } catch (error) {
    console.error('保存场景失败:', error)
    ElMessage.error('保存场景失败')
  }
}

const loadScene = async () => {
  try {
    const savedData = localStorage.getItem('industrial_3d_scene')
    if (!savedData) {
      ElMessage.warning('没有找到保存的场景')
      return
    }
    
    const sceneData = JSON.parse(savedData)
    clearScene(false)
    
    sceneData.objects.forEach(objData => {
      const mesh = createDeviceModel(objData.deviceType, objData.position)
      if (!mesh) return
      
      mesh.userData = {
        id: objData.id,
        deviceType: objData.deviceType,
        name: objData.name
      }
      
      const THREE = window.THREE
      mesh.rotation.set(
        THREE.MathUtils.degToRad(objData.rotation.x),
        THREE.MathUtils.degToRad(objData.rotation.y),
        THREE.MathUtils.degToRad(objData.rotation.z)
      )
      mesh.scale.set(objData.scale, objData.scale, objData.scale)
      
      scene.add(mesh)
      
      const sceneObject = {
        ...objData,
        mesh: mesh
      }
      
      sceneObjects.value.push(sceneObject)
    })
    
    ElMessage.success('场景加载成功')
  } catch (error) {
    console.error('加载场景失败:', error)
    ElMessage.error('加载场景失败')
  }
}

const clearScene = (showConfirm = true) => {
  const doCleanup = () => {
    // 清除所有设备对象
    sceneObjects.value.forEach(obj => {
      if (obj.mesh && obj.mesh.parent) {
        scene.remove(obj.mesh)
        
        // 清理几何体和材质
        if (obj.mesh.geometry) {
          obj.mesh.geometry.dispose()
        }
        if (obj.mesh.material) {
          if (Array.isArray(obj.mesh.material)) {
            obj.mesh.material.forEach(mat => mat.dispose())
          } else {
            obj.mesh.material.dispose()
          }
        }
      }
    })
    sceneObjects.value = []  // 立即清空数组
    
    // 清除选中状态
    selectedObject.value = null
    if (transformControls) {
      transformControls.detach()
    }
    
    // 清除设备数据管理器中的数据
    if (deviceDataManager) {
      deviceDataManager.devices.clear()
      deviceDataManager.deviceData.clear()
      deviceDataManager.hideTooltip()
    }
    
    // 清除MQTT数据集成器中的绑定
    if (mqttDataIntegrator) {
      mqttDataIntegrator.clearAllBindings()
    }
    
    // 立即清空设备数据列表显示
    deviceDataList.value = []
    
    // 立即重新渲染场景
    if (renderer && scene && camera) {
      renderer.render(scene, camera)
    }
    
    // 延迟一点时间后自动刷新页面，确保清空操作完成
    setTimeout(() => {
      window.location.reload()
    }, 500)
    
    ElMessage.success('场景已清空，正在刷新页面...')
  }

  if (showConfirm) {
    ElMessageBox.confirm('确定要清空整个场景吗？这将删除所有设备和连接。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(doCleanup).catch(() => {})
  } else {
    doCleanup()
  }
}

const deleteSelected = () => {
  if (!selectedObject.value) {
    ElMessage.warning('请先选择要删除的设备')
    return
  }
  
  ElMessageBox.confirm(`确定要删除设备 "${selectedObject.value.name}" 吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    console.log('开始删除设备:', selectedObject.value)
    
    const objIndex = sceneObjects.value.findIndex(obj => obj.id === selectedObject.value.id)
    console.log('找到设备索引:', objIndex)
    
    if (objIndex >= 0) {
      const deviceToDelete = sceneObjects.value[objIndex]
      
      // 从场景中移除网格对象
      if (deviceToDelete.mesh) {
        scene.remove(deviceToDelete.mesh)
        console.log('已从场景移除网格对象')
      }
      
      // 如果有绑定的MQTT数据，清除绑定
      if (mqttDataIntegrator && deviceToDelete.mqttDeviceId) {
        mqttDataIntegrator.unbindDevice(deviceToDelete.mqttDeviceId)
        console.log('已清除MQTT绑定')
      }
      
      // 从数组中移除
      sceneObjects.value.splice(objIndex, 1)
      
      // 清除选中状态和变换控制器
      selectedObject.value = null
      if (transformControls) {
        transformControls.detach()
      }
      
      // 清除设备数据管理器中的数据
      if (deviceDataManager) {
        deviceDataManager.removeDevice(deviceToDelete.id)
      }
      
      console.log('设备删除完成')
      ElMessage.success('设备已删除')
    } else {
      console.error('未找到要删除的设备')
      ElMessage.error('未找到要删除的设备')
    }
  }).catch(() => {
    console.log('取消删除')
  })
}

// 视图控制
const resetView = () => {
  if (camera && controls) {
    camera.position.set(20, 20, 20)
    camera.lookAt(0, 0, 0)
    controls.reset()
  }
}

const fitToScreen = () => {
  if (sceneObjects.value.length === 0 || !camera || !controls) return
  
  const THREE = window.THREE
  const box = new THREE.Box3()
  sceneObjects.value.forEach(obj => {
    box.expandByObject(obj.mesh)
  })
  
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z)
  const fov = camera.fov * (Math.PI / 180)
  const distance = Math.abs(maxDim / Math.sin(fov / 2))
  
  camera.position.copy(center)
  camera.position.z += distance * 1.5
  camera.lookAt(center)
  controls.target.copy(center)
}

const toggleWireframe = () => {
  wireframeMode.value = !wireframeMode.value
  
  sceneObjects.value.forEach(obj => {
    obj.mesh.material.wireframe = wireframeMode.value
  })
}

const toggleGrid = () => {
  if (gridHelper) {
    gridHelper.visible = showGrid.value
  }
}

const updateCameraDistance = () => {
  if (!camera || !controls) return
  
  const THREE = window.THREE
  const direction = new THREE.Vector3()
  camera.getWorldDirection(direction)
  const target = controls.target
  
  camera.position.copy(target).add(direction.multiplyScalar(-cameraDistance.value))
}

// 更新选中对象位置信息
const updateSelectedObjectPosition = () => {
  if (selectedObject.value && selectedObject.value.mesh) {
    selectedObject.value.position.x = selectedObject.value.mesh.position.x
    selectedObject.value.position.y = selectedObject.value.mesh.position.y
    selectedObject.value.position.z = selectedObject.value.mesh.position.z
    
    const THREE = window.THREE
    selectedObject.value.rotation.x = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.x)
    selectedObject.value.rotation.y = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.y)
    selectedObject.value.rotation.z = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.z)
  }
}

// 调试函数
const debugSceneState = () => {
  console.log('=== Scene Debug Info ===')
  console.log('Scene objects count:', sceneObjects.value.length)
  console.log('Selected object:', selectedObject.value?.name)
  console.log('TransformControls:', {
    exists: !!transformControls,
    visible: transformControls?.visible,
    object: transformControls?.object?.name || transformControls?.object,
    dragging: transformControls?.dragging
  })
  sceneObjects.value.forEach((obj, index) => {
    console.log(`Object ${index}:`, {
      name: obj.name,
      id: obj.id,
      mesh: obj.mesh,
      position: obj.mesh?.position
    })
  })
  console.log('========================')
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  if (controls) {
    controls.update()
  }
  
  // 更新模型动画（如GLTF动画）
  if (scene) {
    scene.traverse((child) => {
      if (child.userData.mixer) {
        child.userData.mixer.update(0.016); // 假设60fps
      }
    });
  }
  
  // 更新设备动画
  sceneObjects.value.forEach(obj => {
    if (obj.mesh && obj.mesh.userData) {
      const userData = obj.mesh.userData;
      const time = Date.now() * 0.001; // 时间因子
      
      // 泵的旋转动画
      if (userData.type === 'pump' && userData.rotatingParts) {
        userData.rotatingParts.forEach(part => {
          if (part) {
            part.rotation.y += 0.1; // 旋转速度
          }
        });
      }
      
      // 传送带移动动画
      if (userData.type === 'conveyor' && userData.movingParts) {
        userData.movingParts.forEach(part => {
          if (part && part.material && part.material.map) {
            part.material.map.offset.x = (time * 0.5) % 1; // 纹理滚动
          }
        });
        
        // 滚筒旋转
        if (userData.rotatingParts) {
          userData.rotatingParts.forEach(part => {
            if (part) {
              part.rotation.x += 0.05;
            }
          });
        }
      }
      
      // 储罐液位动画
      if (userData.type === 'tank' && userData.liquidLevel) {
        const liquidLevel = userData.liquidLevel;
        // 模拟液位波动
        const waveHeight = Math.sin(time * 2) * 0.1;
        liquidLevel.scale.y = 0.6 + waveHeight;
      }
    }
  });
  
  // 更新选中对象的属性
  if (selectedObject.value && selectedObject.value.mesh) {
    selectedObject.value.position.x = selectedObject.value.mesh.position.x
    selectedObject.value.position.y = selectedObject.value.mesh.position.y
    selectedObject.value.position.z = selectedObject.value.mesh.position.z
    
    const THREE = window.THREE
    selectedObject.value.rotation.x = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.x)
    selectedObject.value.rotation.y = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.y)
    selectedObject.value.rotation.z = THREE.MathUtils.radToDeg(selectedObject.value.mesh.rotation.z)
  }
  
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

// 窗口大小调整
const handleResize = () => {
  if (!threeContainer.value || !camera || !renderer) return
  
  const width = threeContainer.value.clientWidth
  const height = threeContainer.value.clientHeight
  
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  
  renderer.setSize(width, height)
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initThreeJS()
    window.addEventListener('resize', handleResize)
    
    // 添加全局点击事件来隐藏右键菜单
    document.addEventListener('mousedown', (event) => {
      const contextMenuElement = document.querySelector('.context-menu')
      if (contextMenu.visible && (!contextMenuElement || !contextMenuElement.contains(event.target))) {
        contextMenu.visible = false
      }
    })
  })
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  
  window.removeEventListener('resize', handleResize)
  
  // 清理设备数据管理器
  if (deviceDataManager) {
    deviceDataManager.dispose()
  }
  
  // 清理MQTT数据集成器
  if (mqttDataIntegrator) {
    mqttDataIntegrator.destroy()
  }
  
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped>
.scene-3d-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #F7F2EB;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #BAD6EB;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  flex-wrap: wrap;
  gap: 15px;
  min-height: 60px;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
}

.toolbar-left {
  flex: 0 0 auto;
}

.toolbar-center {
  flex: 1;
  justify-content: center;
  gap: 20px;
}

.toolbar-right {
  flex: 0 0 auto;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.device-library {
  width: 280px;
  background: white;
  border-right: 1px solid #BAD6EB;
  overflow-y: auto;
}

.library-card {
  height: 100%;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
  padding: 8px 0;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  background: #F7F2EB;
}

.device-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 2px solid #BAD6EB;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #F7F2EB;
}

.device-item:hover {
  border-color: #334EAC;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-bottom: 8px;
  color: white;
}

.device-name {
  font-size: 12px;
  text-align: center;
  color: #334EAC;
  font-weight: 500;
}

.scene-viewport {
  flex: 1;
  position: relative;
  background-color: #e8edf0;
}

.three-container {
  width: 100%;
  height: 100%;
  cursor: crosshair;
}

.three-container :deep(canvas) {
  opacity: .42;
  mix-blend-mode: multiply;
}

.viewport-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.view-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.device-data-panel {
  max-height: 400px;
  overflow-y: auto;
}

.device-list {
  max-height: 350px;
  overflow-y: auto;
}

.device-item-data {
  border: 1px solid #BAD6EB;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #F7F2EB;
  transition: all 0.3s ease;
}

.device-item-data:hover {
  background: #F7F2EB;
  border-color: #334EAC;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #BAD6EB;
}

.device-name {
  font-weight: 600;
  color: #081F5C;
  font-size: 14px;
}

.device-parameters {
  margin-bottom: 8px;
}

.parameter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 4px 0;
  font-size: 12px;
}

.parameter-name {
  color: #334EAC;
  font-weight: 500;
}

.parameter-value {
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

.parameter-value.value-normal {
  color: #7096D1;
}

.parameter-value.value-warning {
  color: #7096D1;
}

.parameter-value.value-danger {
  color: #081F5C;
}

.device-time {
  font-size: 10px;
  color: #7096D1;
  text-align: right;
  border-top: 1px solid #BAD6EB;
  padding-top: 4px;
  margin-top: 6px;
}

.no-devices {
  text-align: center;
  color: #7096D1;
  padding: 40px 20px;
  font-size: 14px;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #081F5C;
  color: white;
  font-size: 12px;
}

.status-info {
  display: flex;
  gap: 20px;
}

.coordinates {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .device-library {
    width: 240px;
  }
  
  .properties-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .device-library {
    width: 100%;
    height: 200px;
  }
  
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 10px 15px;
  }
  
  .toolbar-section {
    width: 100%;
    justify-content: center;
  }
  
  .toolbar-center {
    flex-direction: column;
    gap: 10px;
  }
  
  .toolbar-group {
    justify-content: center;
    flex-wrap: wrap;
  }
}

/* 拖拽样式 */
.device-item[draggable="true"] {
  user-select: none;
}

.device-item:active {
  opacity: 0.7;
}

/* 加载动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.loading {
  animation: pulse 1.5s infinite;
}

/* 选中状态 */
.device-item.selected {
  border-color: #334EAC;
  background: #F7F2EB;
}

/* 工具提示 */
.viewport-controls .el-button {
  font-size: 12px;
}

/* 滚动条样式 */
.device-library::-webkit-scrollbar {
  width: 6px;
}

.device-library::-webkit-scrollbar-thumb {
  background: #BAD6EB;
  border-radius: 3px;
}

.device-library::-webkit-scrollbar-thumb:hover {
  background: #7096D1;
}

/* 设备悬停提示样式 */
.device-tooltip {
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #BAD6EB;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 150px;
  backdrop-filter: blur(10px);
}

.menu-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  color: #334EAC;
  font-size: 14px;
  border-bottom: 1px solid #F7F2EB;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: #F7F2EB;
  color: #334EAC;
}

.menu-item:active {
  background: #BAD6EB;
}

.menu-item.danger {
  color: #081F5C;
}

.menu-item.danger:hover {
  background: #F7F2EB;
  color: #081F5C;
}

.device-option {
  line-height: 1.2;
}

.device-name {
  font-weight: 500;
  color: #081F5C;
  margin-bottom: 2px;
}

.device-info {
  font-size: 12px;
  color: #7096D1;
}

/* 设备数据覆盖面板样式 */
.device-data-overlay {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: 70vh;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #BAD6EB;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-size: 14px;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.overlay-header {
  background: #334EAC;
  color: white;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid #BAD6EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-btn {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.overlay-content {
  max-height: calc(70vh - 60px);
  overflow-y: auto;
  padding: 8px;
}

.device-card {
  margin-bottom: 12px;
  border: 1px solid #F7F2EB;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.device-card:hover {
  border-color: #334EAC;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  transform: translateY(-1px);
}

.device-card.selected {
  border-color: #334EAC;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.device-header {
  background: #F7F2EB;
  padding: 10px 12px;
  border-bottom: 1px solid #F7F2EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-name {
  font-weight: 600;
  color: #081F5C;
  font-size: 14px;
}

.device-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-normal {
  background: #F7F2EB;
  color: #081F5C;
  border: 1px solid #BAD6EB;
}

.status-warning {
  background: #F7F2EB;
  color: #7096D1;
  border: 1px solid #BAD6EB;
}

.status-error {
  background: #F7F2EB;
  color: #081F5C;
  border: 1px solid #BAD6EB;
}

.status-offline {
  background: #F7F2EB;
  color: #334EAC;
  border: 1px solid #BAD6EB;
}

.device-data {
  padding: 12px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #F7F2EB;
}

.data-row:last-child {
  border-bottom: none;
}

.data-label {
  color: #334EAC;
  font-size: 12px;
  font-weight: 500;
}

.data-value {
  color: #081F5C;
  font-weight: 600;
  font-size: 13px;
}

.data-value.anomaly {
  color: #081F5C;
  animation: pulse 2s infinite;
}

.data-timestamp {
  color: #7096D1;
  font-size: 11px;
  margin-top: 8px;
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid #F7F2EB;
}

.no-data {
  text-align: center;
  color: #7096D1;
  padding: 24px;
  font-style: italic;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 滚动条样式 */
.overlay-content::-webkit-scrollbar {
  width: 6px;
}

.overlay-content::-webkit-scrollbar-track {
  background: #F7F2EB;
  border-radius: 3px;
}

.overlay-content::-webkit-scrollbar-thumb {
  background: #BAD6EB;
  border-radius: 3px;
}

.overlay-content::-webkit-scrollbar-thumb:hover {
  background: #7096D1;
}

/* 设备数据覆盖面板样式 */
.device-data-overlay {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: 70vh;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #BAD6EB;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-size: 14px;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.overlay-header {
  background: #334EAC;
  color: white;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 16px;
  border-bottom: 1px solid #BAD6EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-btn {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.overlay-content {
  max-height: calc(70vh - 60px);
  overflow-y: auto;
  padding: 8px;
}

.device-card {
  margin-bottom: 12px;
  border: 1px solid #F7F2EB;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.device-card:hover {
  border-color: #334EAC;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  transform: translateY(-1px);
}

.device-card.selected {
  border-color: #334EAC;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.device-header {
  background: #F7F2EB;
  padding: 10px 12px;
  border-bottom: 1px solid #F7F2EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-name {
  font-weight: 600;
  color: #081F5C;
  font-size: 14px;
}

.device-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-normal {
  background: #F7F2EB;
  color: #081F5C;
  border: 1px solid #BAD6EB;
}

.status-warning {
  background: #F7F2EB;
  color: #7096D1;
  border: 1px solid #BAD6EB;
}

.status-error {
  background: #F7F2EB;
  color: #081F5C;
  border: 1px solid #BAD6EB;
}

.status-offline {
  background: #F7F2EB;
  color: #334EAC;
  border: 1px solid #BAD6EB;
}

.device-data {
  padding: 12px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #F7F2EB;
}

.data-row:last-child {
  border-bottom: none;
}

.data-label {
  color: #334EAC;
  font-size: 12px;
  font-weight: 500;
}

.data-value {
  color: #081F5C;
  font-weight: 600;
  font-size: 13px;
}

.data-value.anomaly {
  color: #081F5C;
  animation: pulse 2s infinite;
}

.data-timestamp {
  color: #7096D1;
  font-size: 11px;
  margin-top: 8px;
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid #F7F2EB;
}

.no-data {
  text-align: center;
  color: #7096D1;
  padding: 24px;
  font-style: italic;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 滚动条样式 */
.overlay-content::-webkit-scrollbar {
  width: 6px;
}

.overlay-content::-webkit-scrollbar-track {
  background: #F7F2EB;
  border-radius: 3px;
}

.overlay-content::-webkit-scrollbar-thumb {
  background: #BAD6EB;
  border-radius: 3px;
}

.overlay-content::-webkit-scrollbar-thumb:hover {
  background: #7096D1;
}
</style>
