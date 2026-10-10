// MQTT数据集成器 
export class MQTTDataIntegrator {
    constructor(deviceDataManager) {
        this.deviceDataManager = deviceDataManager;
        this.deviceBindings = new Map(); // 存储设备ID与MQTT主题的绑定关系
        this.isConnected = false;
        this.pollingInterval = null;
        
        this.initHttpPolling();
    }

    // 初始化HTTP轮询
    initHttpPolling() {
        console.log('MQTT数据集成器启动 - 使用HTTP轮询模式');
        this.isConnected = true;
        
        // 每2秒轮询一次实时数据
        this.pollingInterval = setInterval(() => {
            this.fetchRealtimeData();
        }, 2000);
    }

    // 获取实时数据
    async fetchRealtimeData() {
        try {
            const response = await fetch('/api/devices/realtime');
            if (response.ok) {
                const data = await response.json();
                this.handleDeviceData(data);
            }
        } catch (error) {
            console.warn('获取实时数据失败:', error);
        }
    }

    // 处理设备数据
    handleDeviceData(data) {
        if (!this.deviceDataManager || !data.data) {
            console.log('数据管理器或数据为空:', { deviceDataManager: !!this.deviceDataManager, data: data });
            return;
        }

        console.log('收到设备数据:', data.data);

        // 后端返回的是对象格式，键为设备名称
        if (typeof data.data === 'object' && data.data !== null) {
            Object.entries(data.data).forEach(([deviceName, deviceInfo]) => {
                // 首先尝试精确匹配
                let boundDeviceId = this.findBoundDeviceId(deviceName);
                
                // 如果精确匹配失败，尝试模糊匹配
                if (!boundDeviceId) {
                    boundDeviceId = this.findBoundDeviceByPattern(deviceName);
                }
                
                console.log(`处理设备: ${deviceName}, 绑定到场景设备: ${boundDeviceId}`);
                
                if (boundDeviceId && this.deviceDataManager) {
                    // 添加设备名称到数据中
                    const deviceData = {
                        ...deviceInfo,
                        device_name: deviceName
                    };
                    const formattedData = this.formatDeviceData(deviceData);
                    console.log(`正在更新设备数据: 场景设备${boundDeviceId} <- MQTT设备${deviceName}`, formattedData);
                    this.deviceDataManager.updateDeviceData(boundDeviceId, formattedData);
                    
                    // 验证数据是否已保存
                    const savedData = this.deviceDataManager.getDeviceData(boundDeviceId);
                    console.log(`验证已保存的数据:`, savedData);
                } else if (!boundDeviceId) {
                    // console.log(`MQTT设备 ${deviceName} 未绑定到任何场景设备`);
                }
            });
        } else {
            console.warn('数据格式不正确，期望对象格式:', data.data);
        }
    }

    // 绑定设备
    bindDevice(sceneDeviceId, mqttDeviceId, dataMapping = {}) {
        this.deviceBindings.set(mqttDeviceId, {
            sceneDeviceId: sceneDeviceId,
            dataMapping: dataMapping
        });
        
        console.log(`设备绑定成功: 场景设备${sceneDeviceId} <-> MQTT设备${mqttDeviceId}`);
        console.log('当前所有绑定:', Array.from(this.deviceBindings.entries()));
    }

    // 解绑设备
    unbindDevice(mqttDeviceId) {
        this.deviceBindings.delete(mqttDeviceId);
        console.log(`设备解绑: ${mqttDeviceId}`);
    }

    // 查找绑定的设备ID
    findBoundDeviceId(mqttDeviceId) {
        const binding = this.deviceBindings.get(mqttDeviceId);
        return binding ? binding.sceneDeviceId : null;
    }

    // 根据模式查找绑定的设备ID（用于处理设备名称不完全匹配的情况）
    findBoundDeviceByPattern(mqttDeviceName) {
        // 遍历所有绑定，尝试找到匹配的设备
        for (const [boundMqttId, binding] of this.deviceBindings.entries()) {
            // 方法1: 提取设备基础名称（去掉后缀数字和下划线）
            const boundBaseName = boundMqttId.replace(/_\d+$/, '').replace(/\d+$/, '');
            const dataBaseName = mqttDeviceName.replace(/_\d+$/, '').replace(/\d+$/, '');
            
            // 方法2: 检查是否包含相同的设备类型关键词
            const deviceTypes = ['pressure', 'temperature', 'flow', 'sensor', 'motor', 'fan', 'pump'];
            let typeMatch = false;
            
            for (const type of deviceTypes) {
                if (boundMqttId.includes(type) && mqttDeviceName.includes(type)) {
                    typeMatch = true;
                    break;
                }
            }
            
            // 如果基础名称匹配或设备类型匹配，则认为是同一类设备
            if (boundBaseName === dataBaseName || typeMatch) {
                console.log(`模糊匹配成功: ${mqttDeviceName} -> ${boundMqttId} (场景设备: ${binding.sceneDeviceId})`);
                return binding.sceneDeviceId;
            }
        }
        return null;
    }

    // 格式化设备数据
    formatDeviceData(deviceInfo) {
        // 这里可以根据需要转换数据格式
        // 例如单位转换、数值范围调整等
        const formattedData = {
            value: deviceInfo.value || 0,
            unit: deviceInfo.unit || '',
            type: deviceInfo.type || deviceInfo.device_type || 'unknown',
            status: deviceInfo.status || 'unknown',
            timestamp: deviceInfo.timestamp || new Date().toISOString(),
            device_name: deviceInfo.device_name || ''
        };
        
        return formattedData;
    }

    // 清除所有绑定
    clearAllBindings() {
        this.deviceBindings.clear();
        console.log('已清除所有设备绑定');
    }

    // 销毁实例
    destroy() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.clearAllBindings();
        this.isConnected = false;
        console.log('MQTT数据集成器已销毁');
    }
}
