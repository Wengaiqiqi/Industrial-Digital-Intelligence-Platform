#!/usr/bin/env python3
"""
真实设备MQTT数据发布器
模拟真实工业设备向系统发送数据
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
import math
from datetime import datetime
from loguru import logger

class RealDevicePublisher:
    def __init__(self, mqtt_host="localhost", mqtt_port=1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = None
        self.running = False
        
        # 定义真实设备列表
        self.devices = {
            "temp_sensor_workshop_a": {
                "type": "temperature_sensor",
                "unit": "°C",
                "base_value": 25.0,
                "variance": 3.0,
                "sample_rate": 5
            },
            "pressure_sensor_line_1": {
                "type": "pressure_sensor", 
                "unit": "bar",
                "base_value": 2.5,
                "variance": 0.5,
                "sample_rate": 3
            },
            "flow_meter_pump_1": {
                "type": "flow_meter",
                "unit": "L/min",
                "base_value": 15.0,
                "variance": 2.0,
                "sample_rate": 2
            },
            "vibration_sensor_motor_1": {
                "type": "vibration_sensor",
                "unit": "mm/s",
                "base_value": 1.2,
                "variance": 0.3,
                "sample_rate": 1
            }
        }
    
    def connect_mqtt(self):
        """连接MQTT代理"""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"MQTT连接失败: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("真实设备发布器MQTT连接成功")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning("MQTT连接断开")
    
    def simulate_sensor_reading(self, device_config):
        """模拟真实传感器读数"""
        base = device_config["base_value"]
        variance = device_config["variance"]
        
        # 添加一些真实的物理特征
        # 1. 基础随机变化
        value = base + random.uniform(-variance, variance)
        
        # 2. 模拟一些周期性变化（如温度的日夜变化）
        time_factor = time.time() % 3600  # 1小时周期
        seasonal_change = 0.5 * variance * math.sin(2 * math.pi * time_factor / 3600)
        value += seasonal_change
        
        # 3. 偶尔的异常值（模拟设备故障）
        if random.random() < 0.02:  # 2%概率出现异常
            value += random.choice([-1, 1]) * variance * 2
        
        return round(value, 2)
    
    def publish_device_data(self, device_name, device_config):
        """发布单个设备数据"""
        if not self.client or not self.running:
            return
        
        try:
            # 模拟真实传感器读数
            value = self.simulate_sensor_reading(device_config)
            
            # 构建数据包
            data = {
                "device_name": device_name,
                "device_type": device_config["type"],
                "value": value,
                "unit": device_config["unit"],
                "timestamp": datetime.now().isoformat(),
                "status": "normal" if abs(value - device_config["base_value"]) < device_config["variance"] * 1.5 else "warning"
            }
            
            # 发布到设备专用主题
            topic = f"industrial/device/{device_name}"
            self.client.publish(topic, json.dumps(data))
            
            logger.info(f"发布数据: {device_name} = {value} {device_config['unit']}")
            
        except Exception as e:
            logger.error(f"发布设备数据失败 {device_name}: {e}")
    
    def device_publisher_thread(self, device_name, device_config):
        """设备数据发布线程"""
        while self.running:
            self.publish_device_data(device_name, device_config)
            time.sleep(device_config["sample_rate"])
    
    def start_publishing(self):
        """开始发布所有设备数据"""
        if not self.connect_mqtt():
            return False
        
        self.running = True
        logger.info("开始发布真实设备数据...")
        
        # 为每个设备启动一个发布线程
        threads = []
        for device_name, device_config in self.devices.items():
            thread = threading.Thread(
                target=self.device_publisher_thread,
                args=(device_name, device_config),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            logger.info(f"启动设备 {device_name} 数据发布线程")
        
        return True
    
    def stop_publishing(self):
        """停止发布"""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        logger.info("真实设备数据发布已停止")

def main():
    publisher = RealDevicePublisher()
    
    try:
        if publisher.start_publishing():
            logger.info("真实设备发布器启动成功")
            logger.info("按 Ctrl+C 停止发布")
            
            # 保持运行
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        publisher.stop_publishing()

if __name__ == "__main__":
    main()
