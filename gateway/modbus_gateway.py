#!/usr/bin/env python3
"""
Modbus TCP 采集网关
按 config/platform.json 中设备的 "modbus" 映射轮询 PLC，把读数按平台约定发布到 MQTT；
同时订阅控制主题，把 set_value 命令写回 PLC 寄存器/线圈。

设备映射示例:
  "plc_temperature_1": {"type": "sensor", "unit": "°C", "alarm_min": 18, "alarm_max": 85,
    "modbus": {"connection": "plc1", "table": "input", "address": 0, "datatype": "uint16", "scale": 0.01,
               "write": {"table": "holding", "address": 0, "datatype": "uint16", "scale": 1}}}
  table: holding / input（寄存器）, coil / discrete（位）
  datatype: uint16 / int16 / uint32 / int32 / float32；32 位类型可设 "word_order": "little"
  读数 = 原始值 × scale + offset；写入时反算
"""

import json
import os
import struct
import sys
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from loguru import logger
from pymodbus.client import ModbusTcpClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from platform_config import CONFIG, create_mqtt_client, mqtt_address

REGISTER_COUNT = {'uint16': 1, 'int16': 1, 'uint32': 2, 'int32': 2, 'float32': 2}
STRUCT_FMT = {'uint16': '>H', 'int16': '>h', 'uint32': '>I', 'int32': '>i', 'float32': '>f'}


def decode_registers(registers, datatype, word_order):
    if word_order == 'little':
        registers = list(reversed(registers))
    raw = b''.join(struct.pack('>H', r & 0xFFFF) for r in registers)
    return struct.unpack(STRUCT_FMT[datatype], raw)[0]


def encode_registers(value, datatype, word_order):
    if datatype != 'float32':
        value = int(round(value))
    raw = struct.pack(STRUCT_FMT[datatype], value)
    registers = [struct.unpack('>H', raw[i:i + 2])[0] for i in range(0, len(raw), 2)]
    return list(reversed(registers)) if word_order == 'little' else registers


class PointError(Exception):
    """PLC 返回了异常响应（地址不存在等）：只影响这个点位，不用断开连接"""


class Connection:
    """一个 PLC 连接；断线后下个周期自动重连。pymodbus 同步客户端不是线程安全的，读写都加锁"""

    def __init__(self, name, cfg):
        self.name = name
        self.unit = int(cfg.get('unit', 1))
        self.client = ModbusTcpClient(cfg['host'], port=int(cfg.get('port', 502)), timeout=float(cfg.get('timeout', 3)))
        self.lock = threading.Lock()
        self.ok = None

    def ensure(self):
        if self.client.connected:
            return True
        connected = self.client.connect()
        if connected != self.ok:
            (logger.info if connected else logger.warning)(f"PLC {self.name} {'已连接' if connected else '连接失败，稍后重试'}")
        self.ok = connected
        return connected

    def read(self, m):
        table, address = m.get('table', 'holding'), int(m['address'])
        datatype = m.get('datatype', 'uint16')
        with self.lock:
            if not self.ensure():
                return None
            if table in ('coil', 'discrete'):
                fn = self.client.read_coils if table == 'coil' else self.client.read_discrete_inputs
                rr = fn(address, 1, slave=self.unit)
                if rr.isError():
                    raise PointError(rr)
                return float(rr.bits[0])
            fn = self.client.read_input_registers if table == 'input' else self.client.read_holding_registers
            rr = fn(address, REGISTER_COUNT[datatype], slave=self.unit)
            if rr.isError():
                raise PointError(rr)
            raw = decode_registers(rr.registers, datatype, m.get('word_order', 'big'))
            return raw * float(m.get('scale', 1)) + float(m.get('offset', 0))

    def write(self, w, value):
        table, address = w.get('table', 'holding'), int(w['address'])
        with self.lock:
            if not self.ensure():
                raise IOError(f'PLC {self.name} 未连接')
            if table == 'coil':
                rr = self.client.write_coil(address, bool(value), slave=self.unit)
            elif table == 'holding':
                raw = (float(value) - float(w.get('offset', 0))) / float(w.get('scale', 1))
                registers = encode_registers(raw, w.get('datatype', 'uint16'), w.get('word_order', 'big'))
                rr = self.client.write_registers(address, registers, slave=self.unit)
            else:
                raise ValueError(f'表 {table} 不可写')
            if rr.isError():
                raise IOError(rr)

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


class ModbusGateway:
    def __init__(self):
        modbus_cfg = CONFIG.get('modbus', {})
        self.interval = float(modbus_cfg.get('poll_interval_seconds', 2))
        self.connections = {name: Connection(name, c) for name, c in modbus_cfg.get('connections', {}).items()}
        self.devices = {name: d for name, d in CONFIG['devices'].items()
                        if isinstance(d.get('modbus'), dict) and d['modbus'].get('connection') in self.connections}
        self.mqtt_cfg = CONFIG['mqtt']
        self.client = create_mqtt_client('modbus-gateway', mqtt)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Modbus 网关 MQTT 连接成功")
            client.subscribe(f"{self.mqtt_cfg['topic_control_prefix']}/+", qos=1)
        else:
            logger.error(f"Modbus 网关 MQTT 连接失败，错误码: {rc}")

    def on_message(self, client, userdata, msg):
        device_name = msg.topic.rsplit('/', 1)[-1]
        device = self.devices.get(device_name)
        if not device:
            return  # 不是本网关管理的设备
        try:
            cmd = json.loads(msg.payload.decode('utf-8'))
            write = device['modbus'].get('write')
            if cmd.get('command') != 'set_value' or not write:
                logger.warning(f"设备 {device_name} 不支持命令 {cmd.get('command')}")
                return
            self.connections[device['modbus']['connection']].write(write, float(cmd['value']))
            logger.info(f"已写入 PLC: {device_name} = {cmd['value']}")
        except Exception as e:
            logger.error(f"写入 PLC 失败 ({device_name}): {e}")

    def poll_once(self):
        readings = {}
        for name, device in self.devices.items():
            conn = self.connections[device['modbus']['connection']]
            try:
                value = conn.read(device['modbus'])
            except PointError as e:
                logger.warning(f"读取 {name} 失败: {e}")
                continue
            except Exception as e:
                logger.warning(f"读取 {name} 失败，断开重连: {e}")
                conn.close()
                continue
            if value is None:
                continue
            readings[name] = {
                'value': round(value, 6),
                'unit': device.get('unit', ''),
                'type': device.get('type', 'unknown'),
            }
        if readings:
            packet = {'timestamp': datetime.now().astimezone().isoformat(), 'source': 'modbus-gateway', 'devices': readings}
            self.client.publish(self.mqtt_cfg['topic_batch'], json.dumps(packet, ensure_ascii=False), qos=1)

    def run(self):
        if not self.devices:
            logger.warning("config/platform.json 里没有配置 modbus 映射的设备，网关退出")
            return
        host, port, keepalive = mqtt_address()
        self.client.connect_async(host, port, keepalive)
        self.client.loop_start()
        logger.info(f"Modbus 网关启动：{len(self.devices)} 个点位，{len(self.connections)} 个 PLC，周期 {self.interval}s")
        try:
            while True:
                started = time.time()
                self.poll_once()
                time.sleep(max(0.1, self.interval - (time.time() - started)))
        except KeyboardInterrupt:
            logger.info("Modbus 网关停止")
        finally:
            self.client.loop_stop()
            for conn in self.connections.values():
                conn.close()


if __name__ == '__main__':
    ModbusGateway().run()
