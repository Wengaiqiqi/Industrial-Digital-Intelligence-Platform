import * as THREE from 'three';

export class DeviceManager {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        this.devices = new Map();
        this.labels = new Map();
        this.dataUpdateInterval = null;
        this.labelUpdateInterval = null;
        this.isLabelsVisible = false;
        
        // CSS样式
        this.injectCSS();
    }

    injectCSS() {
        const style = document.createElement('style');
        style.textContent = `
            .device-label {
                position: absolute;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                pointer-events: none;
                z-index: 1000;
                min-width: 120px;
                backdrop-filter: blur(4px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: opacity 0.3s ease;
            }
            .device-label .label-header {
                font-weight: bold;
                color: #409eff;
                margin-bottom: 4px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-bottom: 2px;
            }
            .device-label .label-item {
                margin: 2px 0;
                display: flex;
                justify-content: space-between;
            }
            .device-label .label-value {
                color: #67c23a;
                font-weight: bold;
            }
            .device-label .label-value.warning {
                color: #e6a23c;
            }
            .device-label .label-value.danger {
                color: #f56c6c;
            }
        `;
        document.head.appendChild(style);
    }

    // 注册设备
    registerDevice(deviceObject, deviceConfig) {
        const deviceId = deviceConfig.id || deviceObject.userData.deviceId || `device_${Date.now()}`;
        
        // 确保设备对象有正确的userData
        if (!deviceObject.userData) {
            deviceObject.userData = {};
        }
        deviceObject.userData.deviceId = deviceId;
        deviceObject.userData.deviceType = deviceConfig.type;
        
        this.devices.set(deviceId, {
            object: deviceObject,
            config: deviceConfig,
            data: {},
            lastUpdate: Date.now()
        });
        
        // 创建数据标签
        this.createDataLabel(deviceId, deviceObject);
        
        console.log(`设备已注册: ${deviceId}`, deviceConfig);
        return deviceId;
    }

    // 创建数据标签
    createDataLabel(deviceId, deviceObject) {
        const labelDiv = document.createElement('div');
        labelDiv.className = 'device-label';
        labelDiv.style.display = 'none';
        
        document.body.appendChild(labelDiv);
        this.labels.set(deviceId, labelDiv);
    }

    // 更新设备数据
    updateDeviceData(deviceId, data) {
        const device = this.devices.get(deviceId);
        if (device) {
            device.data = { ...device.data, ...data };
            device.lastUpdate = Date.now();
            this.updateLabel(deviceId);
            this.updateDeviceVisual(deviceId, data);
        }
    }

    // 批量更新设备数据
    updateMultipleDevices(deviceDataMap) {
        for (const [deviceId, data] of Object.entries(deviceDataMap)) {
            this.updateDeviceData(deviceId, data);
        }
    }

    // 更新标签显示
    updateLabel(deviceId) {
        const device = this.devices.get(deviceId);
        const label = this.labels.get(deviceId);
        
        if (!device || !label || !this.isLabelsVisible) return;

        const position = new THREE.Vector3();
        device.object.getWorldPosition(position);
        
        // 转换为屏幕坐标
        position.project(this.camera);
        
        // 检查是否在视野内
        if (position.z > 1) {
            label.style.display = 'none';
            return;
        }
        
        const x = (position.x * 0.5 + 0.5) * this.renderer.domElement.clientWidth;
        const y = (position.y * -0.5 + 0.5) * this.renderer.domElement.clientHeight;
        
        label.style.left = x + 'px';
        label.style.top = (y - 60) + 'px'; // 偏移到对象上方
        label.style.display = 'block';
        
        // 更新标签内容
        this.updateLabelContent(deviceId);
    }

    // 更新标签内容
    updateLabelContent(deviceId) {
        const device = this.devices.get(deviceId);
        const label = this.labels.get(deviceId);
        
        if (!device || !label) return;

        const config = device.config;
        let content = `<div class="label-header">${config.name || deviceId}</div>`;
        
        // 显示设备数据
        for (const [key, value] of Object.entries(device.data)) {
            const unit = config.units?.[key] || '';
            const thresholds = config.thresholds?.[key];
            
            let valueClass = 'label-value';
            if (thresholds) {
                if (value >= thresholds.danger) {
                    valueClass += ' danger';
                } else if (value >= thresholds.warning) {
                    valueClass += ' warning';
                }
            }
            
            content += `
                <div class="label-item">
                    <span>${this.getParameterDisplayName(key)}:</span>
                    <span class="${valueClass}">${value}${unit}</span>
                </div>
            `;
        }
        
        // 显示最后更新时间
        const timeDiff = Math.floor((Date.now() - device.lastUpdate) / 1000);
        content += `<div class="label-item" style="font-size: 10px; color: #999; margin-top: 4px;">
            <span>更新: ${timeDiff}s前</span>
        </div>`;
        
        label.innerHTML = content;
    }

    // 获取参数显示名称
    getParameterDisplayName(key) {
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
            alarm: '报警'
        };
        return displayNames[key] || key;
    }

    // 更新设备视觉效果
    updateDeviceVisual(deviceId, data) {
        const device = this.devices.get(deviceId);
        if (!device) return;
        
        const config = device.config;
        const object = device.object;
        
        // 根据数据改变颜色
        if (config.colorMapping && data[config.colorMapping.parameter]) {
            const value = data[config.colorMapping.parameter];
            const color = this.getColorByValue(value, config.colorMapping.range);
            this.changeObjectColor(object, color);
        }
        
        // 根据数据旋转（如电机转速）
        if (config.rotation && data[config.rotation.parameter]) {
            const speed = data[config.rotation.parameter];
            object.rotation.y += speed * 0.01;
        }
        
        // 根据液位显示填充效果
        if (config.levelDisplay && data[config.levelDisplay.parameter]) {
            const level = data[config.levelDisplay.parameter];
            this.updateLevelDisplay(object, level, config.levelDisplay.range);
        }
        
        // 闪烁报警
        if (config.alarmFlash && data[config.alarmFlash.parameter]) {
            const isAlarm = data[config.alarmFlash.parameter];
            this.updateAlarmFlash(object, isAlarm);
        }
    }

    // 根据数值获取颜色
    getColorByValue(value, range) {
        const { min, max } = range;
        const ratio = Math.max(0, Math.min(1, (value - min) / (max - min)));
        
        if (ratio < 0.3) {
            // 蓝色到绿色
            return new THREE.Color(0, ratio * 3.33, 1 - ratio);
        } else if (ratio < 0.7) {
            // 绿色到黄色
            const r = (ratio - 0.3) * 2.5;
            return new THREE.Color(r, 1, 0);
        } else {
            // 黄色到红色
            const g = 1 - (ratio - 0.7) * 3.33;
            return new THREE.Color(1, g, 0);
        }
    }

    // 改变对象颜色
    changeObjectColor(object, color) {
        object.traverse((child) => {
            if (child.isMesh && child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(mat => {
                        if (mat.color) mat.color.copy(color);
                    });
                } else {
                    if (child.material.color) child.material.color.copy(color);
                }
            }
        });
    }

    // 更新液位显示
    updateLevelDisplay(object, level, range) {
        const { min, max } = range;
        const ratio = Math.max(0, Math.min(1, (level - min) / (max - min)));
        
        // 简单的液位显示：改变对象的Y轴缩放
        object.traverse((child) => {
            if (child.isMesh && child.userData.isLevelIndicator) {
                child.scale.y = ratio;
            }
        });
    }

    // 更新报警闪烁
    updateAlarmFlash(object, isAlarm) {
        if (isAlarm) {
            const time = Date.now() * 0.005;
            const intensity = Math.sin(time) * 0.5 + 0.5;
            
            object.traverse((child) => {
                if (child.isMesh && child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(mat => {
                            if (mat.emissive) {
                                mat.emissive.setHex(0xff0000 * intensity);
                            }
                        });
                    } else {
                        if (child.material.emissive) {
                            child.material.emissive.setHex(0xff0000 * intensity);
                        }
                    }
                }
            });
        } else {
            object.traverse((child) => {
                if (child.isMesh && child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(mat => {
                            if (mat.emissive) mat.emissive.setHex(0x000000);
                        });
                    } else {
                        if (child.material.emissive) {
                            child.material.emissive.setHex(0x000000);
                        }
                    }
                }
            });
        }
    }

    // 显示设备标签
    showDeviceLabels() {
        this.isLabelsVisible = true;
        this.labels.forEach(label => {
            label.style.opacity = '1';
        });
        
        // 开始定期更新标签位置
        if (!this.labelUpdateInterval) {
            this.labelUpdateInterval = setInterval(() => {
                this.devices.forEach((device, deviceId) => {
                    this.updateLabel(deviceId);
                });
            }, 100);
        }
    }

    // 隐藏设备标签
    hideDeviceLabels() {
        this.isLabelsVisible = false;
        this.labels.forEach(label => {
            label.style.display = 'none';
        });
        
        if (this.labelUpdateInterval) {
            clearInterval(this.labelUpdateInterval);
            this.labelUpdateInterval = null;
        }
    }

    // 开始数据模拟
    startDataSimulation() {
        if (this.dataUpdateInterval) {
            clearInterval(this.dataUpdateInterval);
        }
        
        this.dataUpdateInterval = setInterval(() => {
            this.devices.forEach((device, deviceId) => {
                const mockData = this.generateMockData(device.config.type);
                this.updateDeviceData(deviceId, mockData);
            });
        }, 2000);
        
        console.log('开始数据模拟');
    }

    // 停止数据模拟
    stopDataSimulation() {
        if (this.dataUpdateInterval) {
            clearInterval(this.dataUpdateInterval);
            this.dataUpdateInterval = null;
        }
        console.log('停止数据模拟');
    }

    // 生成模拟数据
    generateMockData(deviceType) {
        const baseTime = Date.now();
        
        switch (deviceType) {
            case 'temperature_sensor':
                return {
                    temperature: (20 + Math.random() * 30 + Math.sin(baseTime * 0.001) * 5).toFixed(1),
                    status: Math.random() > 0.1 ? '正常' : '故障'
                };
            
            case 'pressure_sensor':
                return {
                    pressure: (1 + Math.random() * 4 + Math.sin(baseTime * 0.0005) * 0.5).toFixed(2),
                    status: Math.random() > 0.05 ? '正常' : '超限'
                };
            
            case 'flow_meter':
                return {
                    flow: (50 + Math.random() * 100 + Math.sin(baseTime * 0.0008) * 20).toFixed(1),
                    temperature: (15 + Math.random() * 10).toFixed(1),
                    status: '正常'
                };
            
            case 'fan':
                return {
                    speed: (1000 + Math.random() * 500).toFixed(0),
                    power: (500 + Math.random() * 200).toFixed(1),
                    temperature: (35 + Math.random() * 15).toFixed(1),
                    status: Math.random() > 0.02 ? '运行' : '停止'
                };
            
            case 'servo_motor':
                return {
                    speed: (Math.random() * 0.2 - 0.1), // 用于旋转动画
                    torque: (10 + Math.random() * 20).toFixed(1),
                    temperature: (40 + Math.random() * 20).toFixed(1),
                    position: (Math.random() * 360).toFixed(1),
                    status: '运行'
                };
            
            case 'tank':
                return {
                    level: (Math.random() * 100).toFixed(1),
                    temperature: (20 + Math.random() * 15).toFixed(1),
                    pressure: (0.5 + Math.random() * 2).toFixed(2),
                    status: '正常'
                };
            
            case 'pump':
                return {
                    pressure: (2 + Math.random() * 3).toFixed(1),
                    flow: (80 + Math.random() * 40).toFixed(1),
                    speed: (Math.random() * 0.15), // 用于旋转动画
                    power: (750 + Math.random() * 250).toFixed(0),
                    temperature: (45 + Math.random() * 25).toFixed(1),
                    status: Math.random() > 0.03 ? '运行' : '故障'
                };
            
            default:
                return {
                    value: (Math.random() * 100).toFixed(1),
                    status: '正常'
                };
        }
    }

    // 获取设备信息
    getDeviceInfo(deviceId) {
        return this.devices.get(deviceId);
    }

    // 获取所有设备
    getAllDevices() {
        return Array.from(this.devices.entries()).map(([id, device]) => ({
            id,
            ...device
        }));
    }

    // 移除设备
    removeDevice(deviceId) {
        const device = this.devices.get(deviceId);
        if (device) {
            // 移除标签
            const label = this.labels.get(deviceId);
            if (label) {
                document.body.removeChild(label);
                this.labels.delete(deviceId);
            }
            
            this.devices.delete(deviceId);
            console.log(`设备已移除: ${deviceId}`);
        }
    }

    // 清理所有资源
    dispose() {
        this.stopDataSimulation();
        this.hideDeviceLabels();
        
        // 清理所有标签
        this.labels.forEach(label => {
            if (label.parentNode) {
                document.body.removeChild(label);
            }
        });
        
        this.devices.clear();
        this.labels.clear();
    }
}
