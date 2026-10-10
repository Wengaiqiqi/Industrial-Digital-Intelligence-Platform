"""
Modbus TCP服务器
模拟PLC设备，支持Modbus TCP协议通信
"""

from pymodbus.server import StartTcpServer
# ModbusDeviceIdentification在新版本中可能不可用，使用可选导入
try:
    from pymodbus import ModbusDeviceIdentification
except ImportError:
    try:
        from pymodbus.device import ModbusDeviceIdentification
    except ImportError:
        ModbusDeviceIdentification = None
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
import threading
import time
import random
from loguru import logger

class ModbusPLCSimulator:
    """Modbus PLC仿真器"""
    
    def __init__(self, host='localhost', port=5020):
        self.host = host
        self.port = port
        self.running = False
        
        # 创建数据存储
        # 线圈（Coils）- 数字输出
        coils = ModbusSequentialDataBlock(0, [0] * 100)
        
        # 离散输入（Discrete Inputs）- 数字输入
        discrete_inputs = ModbusSequentialDataBlock(0, [0] * 100)
        
        # 输入寄存器（Input Registers）- 模拟输入
        input_registers = ModbusSequentialDataBlock(0, [0] * 100)
        
        # 保持寄存器（Holding Registers）- 模拟输出
        holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
        
        # zero_mode=True：请求地址 0 就是数据块地址 0，与下面注释里的寄存器地址一致
        store = ModbusSlaveContext(
            di=discrete_inputs,     # 离散输入
            co=coils,               # 线圈
            hr=holding_registers,   # 保持寄存器
            ir=input_registers,     # 输入寄存器
            zero_mode=True
        )
        
        # 创建服务器上下文，使用单一上下文模式
        self.context = ModbusServerContext(slaves=store, single=True)
        
        # 保存数据块引用以便后续使用
        self.discrete_inputs = discrete_inputs
        self.coils = coils
        self.holding_registers = holding_registers
        self.input_registers = input_registers
        
        # 设备标识（如果可用）
        if ModbusDeviceIdentification:
            identity = ModbusDeviceIdentification()
            identity.VendorName = 'Industrial Simulator'
            identity.ProductCode = 'PLC-SIM'
            identity.VendorUrl = 'http://localhost'
            identity.ProductName = 'PLC Simulator'
            identity.ModelName = 'PLC-SIM-001'
            identity.MajorMinorRevision = '1.0'
            self.identity = identity
        else:
            self.identity = None
            logger.warning("ModbusDeviceIdentification不可用，跳过设备标识设置")
        
        logger.info(f"Modbus PLC仿真器初始化完成 - {host}:{port}")
    
    def update_registers(self):
        """更新寄存器数据"""
        while self.running:
            try:
                # 直接使用保存的数据块引用
                # 模拟传感器数据写入输入寄存器
                # 地址0-9: 温度传感器数据 (放大100倍存储)
                temp1 = int((25 + random.uniform(-5, 5)) * 100)
                temp2 = int((30 + random.uniform(-5, 5)) * 100)
                self.input_registers.setValues(0, [temp1])
                self.input_registers.setValues(1, [temp2])
                
                # 地址10-19: 压力传感器数据 (放大100倍存储)
                pressure = int((1.0 + random.uniform(-0.2, 0.2)) * 100)
                self.input_registers.setValues(10, [pressure])
                
                # 地址20-29: 流量数据 (放大10倍存储)
                flow = int((50 + random.uniform(-10, 10)) * 10)
                self.input_registers.setValues(20, [flow])
                
                # 模拟数字输入状态
                # 地址0-9: 限位开关、按钮等
                for i in range(10):
                    if random.random() < 0.1:  # 10%概率改变状态
                        current_value = self.discrete_inputs.getValues(i, 1)[0]
                        self.discrete_inputs.setValues(i, [1 - current_value])
                
                # 读取保持寄存器中的设定值
                # 地址0-9: 风扇转速设定值
                fan_speed_setpoint = self.holding_registers.getValues(0, 1)[0]
                
                # 地址10-19: 伺服电机位置设定值
                servo_position_setpoint = self.holding_registers.getValues(10, 1)[0]
                
                # 模拟执行器响应，写入输入寄存器
                # 实际转速逐渐接近设定转速
                current_speed = self.input_registers.getValues(30, 1)[0]
                speed_diff = fan_speed_setpoint - current_speed
                new_speed = current_speed + int(speed_diff * 0.1)
                self.input_registers.setValues(30, [new_speed])
                
                # 实际位置逐渐接近设定位置
                current_position = self.input_registers.getValues(40, 1)[0]
                position_diff = servo_position_setpoint - current_position
                new_position = current_position + int(position_diff * 0.1)
                self.input_registers.setValues(40, [new_position])
                
                time.sleep(1)  # 1秒更新一次
                
            except Exception as e:
                logger.error(f"Modbus寄存器更新错误: {e}")
                time.sleep(1)
    
    def start_server(self):
        """启动Modbus服务器"""
        self.running = True
        
        # 启动寄存器更新线程
        update_thread = threading.Thread(target=self.update_registers)
        update_thread.daemon = True
        update_thread.start()
        
        logger.info(f"启动Modbus TCP服务器: {self.host}:{self.port}")
        
        try:
            # 启动TCP服务器
            StartTcpServer(
                context=self.context,
                identity=self.identity,
                address=(self.host, self.port)
            )
        except Exception as e:
            logger.error(f"Modbus服务器启动失败: {e}")
    
    def stop_server(self):
        """停止Modbus服务器"""
        self.running = False
        logger.info("Modbus服务器已停止")

if __name__ == "__main__":
    # 启动Modbus PLC仿真器
    plc_simulator = ModbusPLCSimulator()
    
    try:
        logger.info("Modbus PLC仿真器启动中...")
        plc_simulator.start_server()
    except KeyboardInterrupt:
        logger.info("接收到停止信号")
        plc_simulator.stop_server()
