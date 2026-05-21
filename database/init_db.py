"""
数据库初始化脚本
创建工业现场管控平台所需的数据库表结构
"""

import sqlite3
import os
from datetime import datetime
from loguru import logger

def create_database(db_path):
    """创建数据库和表结构"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建传感器数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name VARCHAR(100) NOT NULL,
            device_type VARCHAR(50) NOT NULL,
            value REAL NOT NULL,
            unit VARCHAR(20) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_anomaly BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'normal'
        )
        ''')
        
        # 创建设备状态表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name VARCHAR(100) NOT NULL UNIQUE,
            device_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            last_value REAL,
            unit VARCHAR(20),
            last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_runtime INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        )
        ''')
        
        # 创建报警记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarm_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name VARCHAR(100) NOT NULL,
            alarm_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            value REAL,
            threshold REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT FALSE,
            ack_user VARCHAR(100),
            ack_time DATETIME
        )
        ''')
        
        # 创建生产统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS production_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_runtime INTEGER DEFAULT 0,
            downtime INTEGER DEFAULT 0,
            production_count INTEGER DEFAULT 0,
            defect_count INTEGER DEFAULT 0,
            efficiency REAL DEFAULT 0.0,
            energy_consumption REAL DEFAULT 0.0
        )
        ''')
        
        # 创建用户操作日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name VARCHAR(100),
            operation VARCHAR(100) NOT NULL,
            target_device VARCHAR(100),
            parameters TEXT,
            result VARCHAR(50),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建系统配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key VARCHAR(100) NOT NULL UNIQUE,
            config_value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_data_device_time ON sensor_data(device_name, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alarm_records_time ON alarm_records(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alarm_records_device ON alarm_records(device_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_time ON operation_logs(timestamp)')
        
        # 插入初始设备状态数据
        devices = [
            ('temperature_sensor_1', 'sensor', 'online', 25.0, '°C'),
            ('temperature_sensor_2', 'sensor', 'online', 30.0, '°C'),
            ('fan_1', 'actuator', 'online', 1000.0, 'RPM'),
            ('fan_2', 'actuator', 'online', 1200.0, 'RPM'),
            ('servo_motor_1', 'actuator', 'online', 0.0, '°'),
            ('servo_motor_2', 'actuator', 'online', 180.0, '°'),
            ('pressure_sensor_1', 'sensor', 'online', 1.0, 'bar'),
            ('flow_meter_1', 'sensor', 'online', 50.0, 'L/min'),
            ('indicator_light_1', 'indicator', 'online', 1.0, 'state'),
            ('digital_input_1', 'io', 'online', 0.0, 'digital'),
            ('digital_output_1', 'io', 'online', 0.0, 'digital')
        ]
        
        cursor.execute('SELECT COUNT(*) FROM device_status')
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
            INSERT INTO device_status (device_name, device_type, status, last_value, unit)
            VALUES (?, ?, ?, ?, ?)
            ''', devices)
            logger.info("初始设备状态数据已插入")
        
        # 插入系统配置
        configs = [
            ('data_retention_days', '90', '数据保留天数'),
            ('alarm_threshold_temperature_high', '80', '温度高报警阈值'),
            ('alarm_threshold_temperature_low', '5', '温度低报警阈值'),
            ('alarm_threshold_pressure_high', '5.0', '压力高报警阈值'),
            ('alarm_threshold_pressure_low', '0.3', '压力低报警阈值'),
            ('model_retrain_interval_hours', '24', '模型重训练间隔（小时）'),
            ('mqtt_broker_host', 'localhost', 'MQTT代理主机'),
            ('mqtt_broker_port', '1883', 'MQTT代理端口'),
            ('system_name', '工业数智平台', '系统名称'),
            ('system_version', '1.0.0', '系统版本')
        ]
        
        for config_key, config_value, description in configs:
            cursor.execute('''
            INSERT OR IGNORE INTO system_config (config_key, config_value, description)
            VALUES (?, ?, ?)
            ''', (config_key, config_value, description))
        
        # 提交事务
        conn.commit()
        logger.info(f"数据库初始化完成: {db_path}")
        
        # 显示表统计信息
        tables = ['sensor_data', 'device_status', 'alarm_records', 'production_stats', 'operation_logs', 'system_config']
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count} 条记录")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def insert_sample_data(db_path):
    """插入示例数据"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 插入示例传感器数据
        from datetime import timedelta
        import random
        
        base_time = datetime.now() - timedelta(hours=24)
        
        sample_data = []
        devices = [
            ('temperature_sensor_1', 'sensor', '°C', 25.0, 5.0),
            ('temperature_sensor_2', 'sensor', '°C', 30.0, 5.0),
            ('pressure_sensor_1', 'sensor', 'bar', 1.0, 0.2),
            ('flow_meter_1', 'sensor', 'L/min', 50.0, 10.0)
        ]
        
        for i in range(288):  # 24小时，每5分钟一个数据点
            timestamp = base_time + timedelta(minutes=i * 5)
            
            for device_name, device_type, unit, base_value, variation in devices:
                value = base_value + random.uniform(-variation, variation)
                is_anomaly = random.random() < 0.05  # 5%概率异常
                
                if is_anomaly:
                    value *= random.uniform(1.5, 2.0)
                
                sample_data.append((
                    device_name, device_type, value, unit,
                    timestamp.strftime('%Y-%m-%d %H:%M:%S'), is_anomaly
                ))
        
        cursor.executemany('''
        INSERT INTO sensor_data (device_name, device_type, value, unit, timestamp, is_anomaly)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        # 插入示例报警记录
        alarm_data = [
            ('temperature_sensor_1', 'threshold', 'high', '温度过高报警', 85.0, 80.0),
            ('pressure_sensor_1', 'threshold', 'medium', '压力异常', 4.8, 5.0),
            ('fan_1', 'offline', 'critical', '风扇离线', None, None)
        ]
        
        for device_name, alarm_type, severity, message, value, threshold in alarm_data:
            cursor.execute('''
            INSERT INTO alarm_records (device_name, alarm_type, severity, message, value, threshold)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (device_name, alarm_type, severity, message, value, threshold))
        
        conn.commit()
        conn.close()
        
        logger.info("示例数据插入完成")
        return True
        
    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")
        return False

def main():
    """主函数"""
    db_path = os.path.join(os.path.dirname(__file__), 'industrial.db')
    
    logger.info("开始初始化工业现场管控平台数据库...")
    
    # 创建数据库
    if create_database(db_path):
        logger.info("数据库结构创建成功")
        
        # 插入示例数据
        if insert_sample_data(db_path):
            logger.info("数据库初始化完全成功")
        else:
            logger.warning("示例数据插入失败，但数据库结构已创建")
    else:
        logger.error("数据库初始化失败")

if __name__ == "__main__":
    main()
