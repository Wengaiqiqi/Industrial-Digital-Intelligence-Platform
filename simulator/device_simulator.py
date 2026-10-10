# filepath: e:\daima\comp\prode\new\simulator\device_simulator.py
"""
工业设备仿真器
模拟风扇、温度传感器、伺服电机、指示灯、IO设备、PLC等工业设备
通过MQTT发布设备数据（Modbus TCP 由 modbus_server.py 提供）
"""

import random
import time
import threading
import json
import math
from datetime import datetime
import paho.mqtt.client as mqtt
from loguru import logger

class IndustrialDeviceSimulator:
    """工业设备仿真器主类"""
    
    def __init__(self):
        self.devices = {
            # 温度传感器
            'temperature_sensor_1': {
                'value': 25.0,
                'unit': '°C',
                'range': (20, 80),
                'type': 'sensor',
                'status': 'online',
                'alarm_threshold': {'min': 18, 'max': 85}
            },
            'temperature_sensor_2': {
                'value': 30.0,
                'unit': '°C',
                'range': (20, 80),
                'type': 'sensor',
                'status': 'online',
                'alarm_threshold': {'min': 18, 'max': 85}
            },
            # 风扇设备
            'fan_1': {
                'value': 1000,
                'unit': 'RPM',
                'range': (0, 3000),
                'type': 'actuator',
                'status': 'online',
                'power_consumption': 150  # W
            },
            'fan_2': {
                'value': 1200,
                'unit': 'RPM',
                'range': (0, 3000),
                'type': 'actuator',
                'status': 'online',
                'power_consumption': 180  # W
            },
            # 伺服电机
            'servo_motor_1': {
                'value': 0,
                'unit': '°',
                'range': (0, 360),
                'type': 'actuator',
                'status': 'online',
                'torque': 5.2  # Nm
            },
            'servo_motor_2': {
                'value': 180,
                'unit': '°',
                'range': (0, 360),
                'type': 'actuator',
                'status': 'online',
                'torque': 7.8  # Nm
            },
            # 压力传感器
            'pressure_sensor_1': {
                'value': 1.0,
                'unit': 'bar',
                'range': (0.5, 5.0),
                'type': 'sensor',
                'status': 'online',
                'alarm_threshold': {'min': 0.3, 'max': 5.5}
            },
            # 流量计
            'flow_meter_1': {
                'value': 50.0,
                'unit': 'L/min',
                'range': (0, 100),
                'type': 'sensor',
                'status': 'online',
                'alarm_threshold': {'min': 5, 'max': 95}
            },
            # 指示灯
            'indicator_light_1': {
                'value': 1,  # 0:关闭, 1:绿色, 2:黄色, 3:红色
                'unit': 'state',
                'range': (0, 3),
                'type': 'indicator',
                'status': 'online'
            },
            # IO设备
            'digital_input_1': {
                'value': 0,  # 0或1
                'unit': 'digital',
                'range': (0, 1),
                'type': 'io',
                'status': 'online'
            },
            'digital_output_1': {
                'value': 0,  # 0或1
                'unit': 'digital',
                'range': (0, 1),
                'type': 'io',
                'status': 'online'
            }
        }
        
        self.running = True
        self.anomaly_mode = False  # 异常模式，用于测试
        self.production_line_status = 'running'  # running, stopped, maintenance
        
        # MQTT客户端
        self.mqtt_client = None
        self.setup_mqtt()
        
        logger.info("工业设备仿真器初始化完成")
        
    def setup_mqtt(self):
        """设置MQTT客户端"""
        try:
            # 兼容不同版本的paho-mqtt
            try:
                self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            except (AttributeError, TypeError):
                self.mqtt_client = mqtt.Client()
                
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # 尝试连接MQTT代理
            try:
                self.mqtt_client.connect("localhost", 1883, 60)
                self.mqtt_client.loop_start()
                logger.info("设备模拟器MQTT客户端连接成功")
            except Exception as e:
                logger.warning(f"MQTT连接失败: {e}")
                logger.info("将在离线模式下运行，不使用MQTT通信")
                self.mqtt_client = None
                
        except Exception as e:
            logger.error(f"MQTT设置失败: {e}")
            self.mqtt_client = None
    
    def on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT连接回调"""
        if rc == 0:
            logger.info("设备模拟器MQTT连接成功")
            # 订阅控制主题
            client.subscribe("industrial/control/+")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """MQTT消息回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            device_name = topic.split('/')[-1]
            
            if device_name in self.devices:
                # 处理设备控制命令
                if 'command' in payload:
                    self.handle_device_command(device_name, payload)
                    
        except Exception as e:
            logger.error(f"处理MQTT消息失败: {e}")
    
    def handle_device_command(self, device_name, command_data):
        """处理设备控制命令"""
        device = self.devices.get(device_name)
        if not device:
            return
            
        command = command_data.get('command')
        value = command_data.get('value')
        
        if command == 'set_value':
            min_val, max_val = device['range']
            if min_val <= value <= max_val:
                device['value'] = value
                logger.info(f"设备 {device_name} 值设置为: {value}")
        
        elif command == 'set_status':
            if value in ['online', 'offline', 'maintenance']:
                device['status'] = value
                logger.info(f"设备 {device_name} 状态设置为: {value}")
    
    def simulate_device_data(self):
        """模拟设备数据变化"""
        while self.running:
            try:
                for device_name, device in self.devices.items():
                    if device['status'] != 'online':
                        continue
                    
                    current_value = device['value']
                    device_type = device['type']
                    min_val, max_val = device['range']
                    
                    # 根据设备类型进行不同的模拟
                    if device_type == 'sensor':
                        # 传感器数据模拟
                        new_value = self.simulate_sensor_data(device_name, current_value, min_val, max_val)
                    elif device_type == 'actuator':
                        # 执行器数据模拟
                        new_value = self.simulate_actuator_data(device_name, current_value, min_val, max_val)
                    elif device_type == 'indicator':
                        # 指示灯状态模拟
                        new_value = self.simulate_indicator_data(device_name, current_value)
                    elif device_type == 'io':
                        # IO设备模拟
                        new_value = self.simulate_io_data(device_name, current_value)
                    else:
                        new_value = current_value
                    
                    # 更新设备值
                    device['value'] = new_value
                    device['last_update'] = datetime.now()
                
                # 发布数据到MQTT
                self.publish_device_data()
                
                time.sleep(2)  # 2秒更新一次
                
            except Exception as e:
                logger.error(f"设备数据模拟错误: {e}")
                time.sleep(1)
    
    def simulate_sensor_data(self, device_name, current_value, min_val, max_val):
        """模拟传感器数据"""
        # 正常波动 ±3%
        normal_variation = current_value * random.uniform(-0.03, 0.03)
        new_value = current_value + normal_variation
        
        # 温度传感器特殊逻辑
        if 'temperature' in device_name:
            # 模拟环境温度变化和设备发热
            time_factor = time.time() % 3600  # 1小时周期
            seasonal_variation = 5 * math.sin(time_factor / 3600 * 2 * math.pi)
            new_value += seasonal_variation * 0.1
            
            # 如果风扇运行，温度会降低
            fan_cooling_effect = 0
            for fan_name, fan_device in self.devices.items():
                if 'fan' in fan_name and fan_device['status'] == 'online':
                    fan_cooling_effect += fan_device['value'] * 0.001  # 风扇转速影响
            
            new_value -= fan_cooling_effect
        
        # 异常模式
        if self.anomaly_mode and random.random() < 0.1:  # 10%概率产生异常
            anomaly_factor = random.uniform(1.3, 2.0)
            new_value = current_value * anomaly_factor
        
        # 确保在合理范围内
        return max(min_val, min(max_val, new_value))
    
    def simulate_actuator_data(self, device_name, current_value, min_val, max_val):
        """模拟执行器数据"""
        # 执行器通常有目标值，模拟到达目标值的过程
        if 'fan' in device_name:
            # 风扇转速模拟
            target_speed = getattr(self, f'{device_name}_target', current_value)
            speed_diff = target_speed - current_value
            new_value = current_value + speed_diff * 0.1  # 逐渐到达目标转速
            
        elif 'servo' in device_name:
            # 伺服电机位置模拟
            # 模拟周期性运动
            time_factor = time.time() % 60  # 60秒周期
            new_value = 180 + 90 * math.sin(time_factor / 60 * 2 * math.pi)
            
        else:
            new_value = current_value
        
        return max(min_val, min(max_val, new_value))
    
    def simulate_indicator_data(self, device_name, current_value):
        """模拟指示灯状态"""
        # 根据系统状态设置指示灯
        if self.production_line_status == 'running':
            return 1  # 绿色
        elif self.production_line_status == 'maintenance':
            return 2  # 黄色
        else:
            return 3  # 红色
    
    def simulate_io_data(self, device_name, current_value):
        """模拟IO设备数据"""
        # 数字IO随机变化，模拟开关状态
        if random.random() < 0.1:  # 10%概率改变状态
            return 1 - current_value  # 0变1，1变0
        return current_value
    
    def publish_device_data(self):
        """发布设备数据到MQTT"""
        try:
            # 构建完整的数据包
            data_packet = {
                'timestamp': datetime.now().isoformat(),
                'production_line_status': self.production_line_status,
                'devices': {}
            }
            
            for device_name, device in self.devices.items():
                data_packet['devices'][device_name] = {
                    'value': device['value'],
                    'unit': device['unit'],
                    'type': device['type'],
                    'status': device['status'],
                    'timestamp': device.get('last_update', datetime.now()).isoformat()
                }
                
                # 检查报警条件
                if 'alarm_threshold' in device:
                    alarm_status = self.check_alarm(device)
                    data_packet['devices'][device_name]['alarm'] = alarm_status
            
            # 发布到MQTT（如果连接可用）
            if self.mqtt_client:
                self.mqtt_client.publish(
                    "industrial/sensors/data", 
                    json.dumps(data_packet, ensure_ascii=False)
                )
                
                # 单独发布每个设备的数据
                for device_name, device_data in data_packet['devices'].items():
                    self.mqtt_client.publish(
                        f"industrial/device/{device_name}",
                        json.dumps(device_data, ensure_ascii=False)
                    )
            else:
                # 如果MQTT不可用，输出到日志（用于调试）
                logger.debug(f"设备数据更新: {len(data_packet['devices'])} 个设备")
                
        except Exception as e:
            logger.error(f"发布数据失败: {e}")
    
    def check_alarm(self, device):
        """检查设备报警状态"""
        if 'alarm_threshold' not in device:
            return False
            
        value = device['value']
        threshold = device['alarm_threshold']
        
        if value < threshold['min'] or value > threshold['max']:
            return True
        return False
    
    def get_device_data(self):
        """获取当前所有设备数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'production_line_status': self.production_line_status,
            'devices': self.devices.copy()
        }
    
    def set_anomaly_mode(self, enabled):
        """设置异常模式"""
        self.anomaly_mode = enabled
        logger.info(f"异常模式: {'开启' if enabled else '关闭'}")
    
    def set_production_status(self, status):
        """设置生产线状态"""
        if status in ['running', 'stopped', 'maintenance']:
            self.production_line_status = status
            logger.info(f"生产线状态设置为: {status}")
    
    def start_simulation(self):
        """启动仿真"""
        logger.info("启动工业设备仿真...")
        self.running = True
        
        # 启动数据模拟线程
        simulation_thread = threading.Thread(target=self.simulate_device_data)
        simulation_thread.daemon = True
        simulation_thread.start()
        
        logger.info("工业设备仿真已启动")
        return simulation_thread
    
    def stop_simulation(self):
        """停止仿真"""
        logger.info("停止工业设备仿真...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

if __name__ == "__main__":
    # 启动仿真器
    simulator = IndustrialDeviceSimulator()
    simulation_thread = simulator.start_simulation()
    
    try:
        logger.info("工业设备仿真器运行中... 按 Ctrl+C 停止")
        while True:
            # 每30秒输出一次设备状态
            time.sleep(30)
            data = simulator.get_device_data()
            logger.info("=== 设备状态概览 ===")
            for device_name, device in data['devices'].items():
                logger.info(f"{device_name}: {device['value']:.2f} {device['unit']} - {device['status']}")
            
    except KeyboardInterrupt:
        logger.info("接收到停止信号")
        simulator.stop_simulation()
        logger.info("仿真器已停止")
