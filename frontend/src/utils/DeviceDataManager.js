import * as THREE from 'three';

export class DeviceDataManager {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        this.devices = new Map();
        this.hoveredDevice = null;
        this.tooltipElement = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.deviceData = new Map(); // 存储从MQTT获取的设备数据
        
        this.initTooltip();
        this.bindEvents();
    }

    // 初始化悬停提示框
    initTooltip() {
        this.tooltipElement = document.createElement('div');
        this.tooltipElement.className = 'device-tooltip';
        this.tooltipElement.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 12px;
            line-height: 1.4;
            pointer-events: none;
            z-index: 10000;
            display: none;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        `;
        document.body.appendChild(this.tooltipElement);
    }

    // 绑定鼠标事件
    bindEvents() {
        this.renderer.domElement.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.renderer.domElement.addEventListener('mouseleave', this.onMouseLeave.bind(this));
    }

    // 鼠标移动事件
    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        const deviceObjects = Array.from(this.devices.values()).map(device => device.object);
        const intersects = this.raycaster.intersectObjects(deviceObjects, true);

        if (intersects.length > 0) {
            const intersectedObject = intersects[0].object;
            let deviceObject = intersectedObject;
            
            // 找到设备根对象
            while (deviceObject.parent && !deviceObject.userData.deviceId) {
                deviceObject = deviceObject.parent;
            }

            if (deviceObject.userData.deviceId) {
                const deviceId = deviceObject.userData.deviceId;
                
                if (this.hoveredDevice !== deviceId) {
                    this.hoveredDevice = deviceId;
                    this.showTooltip(deviceId, event.clientX, event.clientY);
                } else {
                    // 更新位置
                    this.updateTooltipPosition(event.clientX, event.clientY);
                }
            }
        } else {
            this.hideTooltip();
        }
    }

    // 鼠标离开事件
    onMouseLeave() {
        this.hideTooltip();
    }

    // 显示悬停提示
    showTooltip(deviceId, x, y) {
        const device = this.devices.get(deviceId);
        if (!device) return;

        const data = this.deviceData.get(deviceId) || {};
        
        let content = `<div style="font-weight: bold; margin-bottom: 8px;">${device.config.name || deviceId}</div>`;
        content += `<div style="color: #ccc; margin-bottom: 8px;">类型: ${device.config.type}</div>`;
        
        if (Object.keys(data).length > 0) {
            content += '<div style="border-top: 1px solid #444; padding-top: 8px; margin-top: 8px;">';
            for (const [key, value] of Object.entries(data)) {
                const unit = device.config.units?.[key] || '';
                content += `<div>${key}: <span style="color: #4CAF50;">${value}${unit}</span></div>`;
            }
            content += '</div>';
        } else {
            content += '<div style="color: #999; font-style: italic;">暂无数据</div>';
        }

        this.tooltipElement.innerHTML = content;
        this.tooltipElement.style.display = 'block';
        this.updateTooltipPosition(x, y);
    }

    // 更新提示框位置
    updateTooltipPosition(x, y) {
        const offset = 15;
        this.tooltipElement.style.left = (x + offset) + 'px';
        this.tooltipElement.style.top = (y + offset) + 'px';
    }

    // 隐藏悬停提示
    hideTooltip() {
        this.hoveredDevice = null;
        this.tooltipElement.style.display = 'none';
    }

    // 注册设备
    registerDevice(deviceObject, deviceConfig) {
        const deviceId = deviceConfig.id || deviceObject.userData.deviceId;
        this.devices.set(deviceId, {
            object: deviceObject,
            config: deviceConfig
        });
        
        // 确保设备对象有正确的userData
        deviceObject.userData.deviceId = deviceId;
        
        return deviceId;
    }

    // 更新设备数据
    updateDeviceData(deviceId, data) {
        this.deviceData.set(deviceId, data);
        
        // 如果当前正在悬停这个设备，更新显示
        if (this.hoveredDevice === deviceId) {
            const device = this.devices.get(deviceId);
            if (device) {
                this.updateDeviceVisual(deviceId, data);
            }
        }
    }

    // 根据数据更新设备视觉效果
    updateDeviceVisual(deviceId, data) {
        const device = this.devices.get(deviceId);
        if (!device) return;

        const config = device.config;
        const object = device.object;

        // 根据数据改变颜色
        if (config.colorMapping && data[config.colorMapping.parameter]) {
            const value = parseFloat(data[config.colorMapping.parameter]);
            const color = this.getColorByValue(value, config.colorMapping.range);
            this.changeObjectColor(object, color);
        }

        // 根据数据旋转（如电机转速）
        if (config.rotation && data[config.rotation.parameter]) {
            const speed = parseFloat(data[config.rotation.parameter]);
            if (!isNaN(speed)) {
                object.rotation.y += speed * 0.01;
            }
        }

        // 根据数据缩放（如液位）
        if (config.scale && data[config.scale.parameter]) {
            const level = parseFloat(data[config.scale.parameter]);
            if (!isNaN(level) && config.scale.range) {
                const { min, max } = config.scale.range;
                const ratio = Math.max(0, Math.min(1, (level - min) / (max - min)));
                object.scale.y = 0.1 + ratio * 0.9; // 保持最小10%的高度
            }
        }
    }

    // 根据数值获取颜色
    getColorByValue(value, range) {
        const { min, max } = range;
        const ratio = Math.max(0, Math.min(1, (value - min) / (max - min)));
        
        if (ratio < 0.3) {
            // 绿色 (正常)
            return new THREE.Color(0x4CAF50);
        } else if (ratio < 0.7) {
            // 黄色 (警告)
            return new THREE.Color(0xFFC107);
        } else {
            // 红色 (危险)
            return new THREE.Color(0xF44336);
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

    // 获取设备数据
    getDeviceData(deviceId) {
        return this.deviceData.get(deviceId) || null;
    }

    // 移除设备
    removeDevice(deviceId) {
        this.devices.delete(deviceId);
        this.deviceData.delete(deviceId);
        if (this.hoveredDevice === deviceId) {
            this.hideTooltip();
        }
    }

    // 获取所有设备列表
    getAllDevices() {
        return Array.from(this.devices.entries()).map(([id, device]) => ({
            id,
            name: device.config.name || id,
            type: device.config.type,
            data: this.deviceData.get(id) || {}
        }));
    }

    // 清理资源
    dispose() {
        if (this.tooltipElement) {
            document.body.removeChild(this.tooltipElement);
        }
        this.renderer.domElement.removeEventListener('mousemove', this.onMouseMove);
        this.renderer.domElement.removeEventListener('mouseleave', this.onMouseLeave);
    }
}
