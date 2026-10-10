#!/usr/bin/env python3
"""
工业现场管控平台后端服务
实现数据采集、存储、分析和API接口
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import threading
import os
import sys
from loguru import logger
import pandas as pd
from sqlalchemy import desc
import hmac
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from platform_config import CONFIG, create_mqtt_client, mqtt_address, parse_timestamp

# 创建Flask应用
app = Flask(__name__)

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "../database/industrial.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# MQTT 线程、离线检测线程和接口线程会同时写库，等待锁而不是立即报 database is locked
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# 初始化扩展
db = SQLAlchemy(app)
CORS(app, origins=CONFIG.get('cors_origins', '*'))

# MQTT客户端全局变量
mqtt_client = None
mqtt_connected = False
latest_device_data = {}  # 存储最新的设备数据
alarm_active = {}  # 设备当前是否处于越限状态，只在进入越限时记一次报警
DEVICE_CONFIG = CONFIG.get('devices', {})
OFFLINE_TIMEOUT = int(CONFIG.get('offline_timeout_seconds', 30))
API_TOKEN = CONFIG.get('api_token') or ''


@app.before_request
def check_api_token():
    """配置了 api_token 时，除健康检查外的接口都需要令牌（请求头 X-API-Token 或 Authorization: Bearer）"""
    if not API_TOKEN or request.method == 'OPTIONS' or request.path == '/api/health':
        return None
    token = request.headers.get('X-API-Token', '')
    auth = request.headers.get('Authorization', '')
    if not token and auth.startswith('Bearer '):
        token = auth[7:]
    if not hmac.compare_digest(token, API_TOKEN):
        return jsonify({'success': False, 'error': '未授权：缺少或错误的 API 令牌'}), 401
    return None

# 数据模型
class SensorData(db.Model):
    """传感器数据表"""
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False, index=True)
    device_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_anomaly = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='normal')
    
    def to_dict(self):
        timestamp_str = None
        if self.timestamp:
            if isinstance(self.timestamp, str):
                timestamp_str = self.timestamp
            else:
                timestamp_str = self.timestamp.isoformat()
        
        return {
            'id': self.id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': timestamp_str,
            'is_anomaly': self.is_anomaly,
            'status': self.status
        }

class DeviceStatus(db.Model):
    """设备状态表"""
    __tablename__ = 'device_status'
    
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False, unique=True)
    device_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    last_value = db.Column(db.Float)
    unit = db.Column(db.String(20))
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    total_runtime = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        last_update_str = None
        if self.last_update:
            if isinstance(self.last_update, str):
                last_update_str = self.last_update
            else:
                last_update_str = self.last_update.isoformat()
        
        return {
            'device_name': self.device_name,
            'device_type': self.device_type,
            'status': self.status,
            'last_value': self.last_value,
            'unit': self.unit,
            'last_update': last_update_str,
            'total_runtime': self.total_runtime,
            'error_count': self.error_count
        }

class AlarmRecord(db.Model):
    """报警记录表"""
    __tablename__ = 'alarm_records'
    
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False, index=True)
    alarm_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    value = db.Column(db.Float)
    threshold = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    acknowledged = db.Column(db.Boolean, default=False)
    ack_user = db.Column(db.String(100))
    ack_time = db.Column(db.DateTime)
    
    def to_dict(self):
        timestamp_str = None
        if self.timestamp:
            if isinstance(self.timestamp, str):
                timestamp_str = self.timestamp
            else:
                timestamp_str = self.timestamp.isoformat()
        
        ack_time_str = None
        if self.ack_time:
            if isinstance(self.ack_time, str):
                ack_time_str = self.ack_time
            else:
                ack_time_str = self.ack_time.isoformat()
        
        return {
            'id': self.id,
            'device_name': self.device_name,
            'alarm_type': self.alarm_type,
            'severity': self.severity,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': timestamp_str,
            'acknowledged': self.acknowledged,
            'ack_user': self.ack_user,
            'ack_time': ack_time_str
        }

# 实时数据API
@app.route('/api/devices/realtime', methods=['GET'])
def get_realtime_devices():
    """获取实时设备数据"""
    try:
        global latest_device_data
        
        # 如果有缓存的实时数据，直接返回
        if latest_device_data:
            return jsonify({
                'success': True,
                'data': latest_device_data,
                'timestamp': datetime.now().isoformat()
            })
        
        # 否则从数据库获取最新数据（与缓存同样按设备名返回）
        devices = {}
        device_names = db.session.query(DeviceStatus.device_name).distinct().all()
        
        for (device_name,) in device_names:
            latest_data = SensorData.query.filter_by(device_name=device_name)\
                .order_by(desc(SensorData.timestamp)).first()
            
            device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
            
            if latest_data:
                devices[device_name] = {
                    'value': latest_data.value,
                    'unit': latest_data.unit,
                    'type': latest_data.device_type,
                    'status': device_status.status if device_status else 'unknown',
                    'timestamp': latest_data.to_dict()['timestamp']
                }
        
        return jsonify({
            'success': True,
            'data': devices,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取实时设备数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_name>/history', methods=['GET'])
def get_device_history(device_name):
    """获取设备历史数据"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        query = SensorData.query.filter_by(device_name=device_name)
        
        if hours:
            start_time = datetime.now() - timedelta(hours=hours)
            query = query.filter(SensorData.timestamp >= start_time)
        
        history_data = query.order_by(desc(SensorData.timestamp)).limit(limit).all()
        
        return jsonify({
            'success': True,
            'device_name': device_name,
            'data': [item.to_dict() for item in history_data],
            'count': len(history_data)
        })
        
    except Exception as e:
        logger.error(f"获取设备历史数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API路由
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/devices/status', methods=['GET'])
def get_devices_status():
    """获取所有设备状态"""
    try:
        logger.info("开始获取设备状态...")
        devices = DeviceStatus.query.all()
        logger.info(f"找到 {len(devices)} 个设备")
        
        device_list = []
        for device in devices:
            try:
                device_dict = device.to_dict()
                device_list.append(device_dict)
            except Exception as e:
                logger.error(f"转换设备 {device.device_name} 数据失败: {e}")
                continue
        
        return jsonify({
            'success': True,
            'data': device_list,
            'count': len(device_list)
        })
    except Exception as e:
        logger.error(f"获取设备状态失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alarms', methods=['GET'])
def get_alarms():
    """获取报警记录"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        query = AlarmRecord.query
        
        if hours:
            start_time = datetime.now() - timedelta(hours=hours)
            query = query.filter(AlarmRecord.timestamp >= start_time)
        
        alarms = query.order_by(desc(AlarmRecord.timestamp)).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [alarm.to_dict() for alarm in alarms],
            'count': len(alarms)
        })
    except Exception as e:
        logger.error(f"获取报警记录失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics/dashboard', methods=['GET'])
def get_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        logger.info("开始获取仪表板统计数据...")
        
        # 设备状态统计
        total_devices = DeviceStatus.query.count()
        online_devices = DeviceStatus.query.filter_by(status='online').count()
        offline_devices = DeviceStatus.query.filter_by(status='offline').count()
        warning_devices = DeviceStatus.query.filter_by(status='warning').count()
        
        # 最近24小时报警统计
        last_24h = datetime.now() - timedelta(hours=24)
        recent_alarms = AlarmRecord.query.filter(AlarmRecord.timestamp >= last_24h).count()
        unack_alarms = AlarmRecord.query.filter(
            AlarmRecord.timestamp >= last_24h,
            AlarmRecord.acknowledged == False
        ).count()
        
        # 数据点统计
        total_data_points = SensorData.query.count()
        recent_data_points = SensorData.query.filter(SensorData.timestamp >= last_24h).count()
        
        result = {
            'success': True,
            'data': {
                'devices': {
                    'total': total_devices,
                    'online': online_devices,
                    'offline': offline_devices,
                    'warning': warning_devices
                },
                'alarms': {
                    'recent_24h': recent_alarms,
                    'unacknowledged': unack_alarms
                },
                'data_points': {
                    'total': total_data_points,
                    'recent_24h': recent_data_points
                },
                'system_health': 'good' if offline_devices == 0 else 'warning'
            }
        }
        
        logger.info("仪表板统计数据获取成功")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/device', methods=['POST'])
def control_device():
    """控制设备"""
    try:
        data = request.get_json()
        device_name = data.get('device_name')
        command = data.get('command')
        value = data.get('value')
        
        logger.info(f"控制设备: {device_name}, 命令: {command}, 值: {value}")
        
        # 检查设备是否存在
        device = DeviceStatus.query.filter_by(device_name=device_name).first()
        if not device:
            return jsonify({'success': False, 'error': '设备不存在'}), 404
        
        # 检查设备是否在线
        if device.status == 'offline':
            return jsonify({'success': False, 'error': '设备离线，无法控制'}), 400
        
        if command not in ('set_value', 'set_status'):
            return jsonify({'success': False, 'error': f'不支持的命令: {command}'}), 400
        if command == 'set_value':
            try:
                value = float(value)
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': 'set_value 需要数值'}), 400

        # 通过 MQTT 下发到 <topic_control_prefix>/<设备名>，由设备、网关或 Modbus 网关执行。
        # 设备的实际值以之后上报的数据为准，这里不直接改库。
        if not mqtt_client or not mqtt_connected:
            return jsonify({'success': False, 'error': 'MQTT 未连接，控制命令无法下发'}), 503
        topic = f"{CONFIG['mqtt']['topic_control_prefix']}/{device_name}"
        payload = json.dumps({'command': command, 'value': value, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)
        info = mqtt_client.publish(topic, payload, qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            return jsonify({'success': False, 'error': f'控制命令发送失败 (rc={info.rc})'}), 502
        logger.info(f"已下发控制命令 {topic}: {command}={value}")

        return jsonify({
            'success': True,
            'message': f'控制命令已下发到设备 {device_name}',
            'command': command,
            'value': value
        })
        
    except Exception as e:
        logger.error(f"设备控制失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alarms/<int:alarm_id>/acknowledge', methods=['POST'])
def acknowledge_alarm(alarm_id):
    """确认报警"""
    try:
        data = request.get_json()
        user = data.get('user', 'admin')
        
        logger.info(f"确认报警 {alarm_id}, 用户: {user}")
        
        alarm = AlarmRecord.query.get(alarm_id)
        if not alarm:
            return jsonify({'success': False, 'error': '报警记录不存在'}), 404
        
        if alarm.acknowledged:
            return jsonify({'success': False, 'error': '报警已经确认过了'}), 400
        
        alarm.acknowledged = True
        alarm.ack_user = user
        alarm.ack_time = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'报警 {alarm_id} 已确认',
            'ack_user': user,
            'ack_time': alarm.ack_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"确认报警失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 机器学习分析相关API
@app.route('/api/ml/analyze/<device_name>', methods=['POST'])
def analyze_device_ml(device_name):
    """对指定设备进行机器学习分析"""
    try:
        # 获取分析参数
        data = request.get_json() or {}
        hours = data.get('hours', 24)  # 默认分析最近24小时数据
        
        logger.info(f"开始对设备 {device_name} 进行机器学习分析，时间范围: {hours}小时")        # 导入机器学习服务
        from ml_service_wrapper import get_ml_analysis_service, is_ml_service_available
        
        if not is_ml_service_available():
            return jsonify({
                'success': False,
                'error': '机器学习服务不可用',
                'message': '请确保机器学习模型已正确安装和配置'
            }), 500
        
        # 创建分析服务实例
        ml_analysis = get_ml_analysis_service()
        
        # 执行分析
        result = ml_analysis.analyze_device_data(device_name, hours)
        
        if result['success']:
            logger.info(f"设备 {device_name} 分析完成")
            return jsonify(result)
        else:
            logger.warning(f"设备 {device_name} 分析失败: {result.get('message', '未知错误')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"机器学习分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '机器学习分析服务暂时不可用'
        }), 500

@app.route('/api/ml/train', methods=['POST'])
def train_ml_models():
    """训练机器学习模型"""
    try:
        logger.info("开始训练机器学习模型")
        
        # 获取请求参数
        data = request.get_json() or {}
        device_name = data.get('device_name', 'all')
        hours = data.get('hours', 168)  # 默认7天
        
        logger.info(f"训练参数 - 设备: {device_name}, 时间范围: {hours}小时")
        
        # 导入机器学习服务
        from ml_service_wrapper import get_ml_model_service, is_ml_service_available
        
        if not is_ml_service_available():
            return jsonify({
                'success': False,
                'error': '机器学习服务不可用',
                'message': '请确保机器学习模型已正确安装和配置'
            }), 500
          # 创建ML服务实例
        ml_service = get_ml_model_service()
          # 训练模型（传递设备和时间参数）
        results = ml_service.train_models(device_name=device_name, hours=hours)
          # 检查训练是否成功
        training_success = results.get('overall_success', False)
        
        if training_success:
            response_data = {
                'success': True,
                'results': results,
                'data_points': results.get('data_points', 0),
                'devices_count': results.get('devices_count', 0),
                'accuracy': results.get('overall_accuracy', 0),  # 已经是百分比，直接使用
                'anomaly_accuracy': results.get('anomaly_accuracy', 0),  # 已经是百分比，直接使用
                'predictive_score': results.get('predictive_score', 0),  # 已经是百分比，直接使用
                'message': '模型训练完成',
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"训练成功响应: {response_data}")
            return jsonify(response_data)
        else:            # 训练失败但没有抛出异常
            error_msg = f"模型训练未能成功完成 - 异常检测: {results.get('anomaly_detector', False)}, 预测模型: {results.get('predictive_model', False)}"
            logger.warning(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg,
                'results': results,
                'message': '模型训练未完全成功'
            }), 400
        
    except Exception as e:
        logger.error(f"模型训练失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '模型训练失败'
        }), 500

# 历史数据分析API
@app.route('/api/historical-data', methods=['POST'])
def get_historical_data():
    """获取历史数据分析"""
    try:
        data = request.get_json()
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        # 如果没有指定时间范围，默认获取最近24小时的数据
        if not start_time_str or not end_time_str:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
        else:
            # 处理时区转换：前端发送的是UTC时间，需要转换为本地时间
            import pytz
            try:
                # 解析UTC时间
                start_utc = datetime.fromisoformat(start_time_str.replace('Z', ''))
                end_utc = datetime.fromisoformat(end_time_str.replace('Z', ''))
                
                # 如果时间字符串包含时区信息，直接使用
                if start_time_str.endswith('Z') or '+' in start_time_str:
                    utc_tz = pytz.UTC
                    local_tz = pytz.timezone('Asia/Shanghai')  # 中国时区
                    
                    # 将UTC时间转换为本地时间
                    start_utc_aware = utc_tz.localize(start_utc)
                    end_utc_aware = utc_tz.localize(end_utc)
                    
                    start_time = start_utc_aware.astimezone(local_tz).replace(tzinfo=None)
                    end_time = end_utc_aware.astimezone(local_tz).replace(tzinfo=None)
                else:
                    # 如果没有时区信息，当作本地时间处理
                    start_time = start_utc
                    end_time = end_utc
            except Exception as e:
                logger.warning(f"时区转换失败，使用原始时间: {e}")
                start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', ''))
        
        logger.info(f"获取历史数据，时间范围: {start_time} - {end_time}")
        
        # 查询时间范围内的所有数据
        query = SensorData.query.filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).order_by(SensorData.timestamp.desc())
        
        historical_data = query.all()
        
        # 按设备分组数据
        device_data = {}
        for record in historical_data:
            device_name = record.device_name
            if device_name not in device_data:
                device_data[device_name] = []
            device_data[device_name].append(record.to_dict())
        
        # 计算每个设备的统计信息
        device_statistics = {}
        for device_name, records in device_data.items():
            if records:
                values = [r['value'] for r in records]
                device_statistics[device_name] = {
                    'name': device_name,
                    'recordCount': len(records),
                    'lastValue': values[0] if values else 0,
                    'avgValue': sum(values) / len(values) if values else 0,
                    'maxValue': max(values) if values else 0,
                    'minValue': min(values) if values else 0,
                    'unit': records[0]['unit'] if records else '',
                    'type': records[0]['device_type'] if records else '',
                    'status': 'online',
                    'timestamps': [r['timestamp'] for r in records[-20:]],  # 最近20个时间点
                    'values': values[-20:] if len(values) >= 20 else values  # 最近20个值
                }
        
        return jsonify({
            'success': True,
            'data': list(device_statistics.values()),
            'total_records': len(historical_data),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-historical-data', methods=['POST'])
def export_historical_data():
    """导出历史数据为CSV"""
    try:
        data = request.get_json()
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        if not start_time_str or not end_time_str:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
        else:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', ''))
        
        # 查询数据
        query = SensorData.query.filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).order_by(SensorData.timestamp.desc())
        
        historical_data = query.all()
        
        # 创建CSV内容
        csv_lines = ['设备名称,设备类型,数值,单位,时间戳,异常标记,状态']
        
        for record in historical_data:
            line = f"{record.device_name},{record.device_type},{record.value},{record.unit},{record.timestamp},{record.is_anomaly},{record.status}"
            csv_lines.append(line)
        
        csv_content = '\n'.join(csv_lines)
        
        # 返回CSV数据
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=historical_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        logger.error(f"导出历史数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_name>/statistics', methods=['GET'])
def get_device_statistics(device_name):
    """获取设备详细统计信息"""
    try:
        hours = request.args.get('hours', 24, type=int)
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 获取设备数据
        data = SensorData.query.filter(
            SensorData.device_name == device_name,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp).all()
        
        if not data:
            return jsonify({
                'success': True,
                'device_name': device_name,
                'statistics': {
                    'recordCount': 0,
                    'avgValue': 0,
                    'maxValue': 0,
                    'minValue': 0,
                    'stdValue': 0,
                    'lastValue': 0,
                    'unit': '',
                    'anomalyCount': 0
                }
            })
        
        values = [d.value for d in data]
        anomaly_count = sum(1 for d in data if d.is_anomaly)
        
        # 计算统计信息
        import statistics
        stats = {
            'recordCount': len(data),
            'avgValue': statistics.mean(values),
            'maxValue': max(values),
            'minValue': min(values),
            'stdValue': statistics.stdev(values) if len(values) > 1 else 0,
            'lastValue': values[-1] if values else 0,
            'unit': data[0].unit if data else '',
            'anomalyCount': anomaly_count,
            'anomalyRate': round((anomaly_count / len(data)) * 100) if data else 0
        }
        
        return jsonify({
            'success': True,
            'device_name': device_name,
            'statistics': stats,
            'analysis_period_hours': hours
        })
        
    except Exception as e:
        logger.error(f"获取设备统计信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices', methods=['POST'])
def add_device():
    """添加新设备"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['device_name', 'device_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        device_name = data['device_name']
        device_type = data['device_type']
        
        # 检查设备是否已存在
        existing_device = DeviceStatus.query.filter_by(device_name=device_name).first()
        if existing_device:
            return jsonify({'success': False, 'error': f'设备 {device_name} 已存在'}), 400
        
        # 创建新设备状态记录
        new_device = DeviceStatus(
            device_name=device_name,
            device_type=device_type,
            status='offline',
            last_value=data.get('initial_value', 0.0),
            unit=data.get('unit', ''),
            last_update=datetime.utcnow(),
            total_runtime=0,
            error_count=0
        )
        
        db.session.add(new_device)
        
        # 如果有初始数据，也添加传感器数据记录
        if 'initial_value' in data:
            initial_data = SensorData(
                device_name=device_name,
                device_type=device_type,
                value=data['initial_value'],
                unit=data.get('unit', ''),
                timestamp=datetime.utcnow(),
                status='normal'
            )
            db.session.add(initial_data)
        
        db.session.commit()
        logger.info(f"成功添加设备: {device_name}")
        
        return jsonify({
            'success': True,
            'message': f'设备 {device_name} 添加成功',
            'device': new_device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加设备失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    """删除设备"""
    try:
        # 查找设备
        device = DeviceStatus.query.filter_by(device_name=device_name).first()
        if not device:
            return jsonify({'success': False, 'error': f'设备 {device_name} 不存在'}), 404
        
        # 只删除设备状态记录；历史数据保留，供追溯和模型训练使用（与前端提示一致）。
        # 设备若仍在上报，下一条数据会重新登记它。
        db.session.delete(device)
        db.session.commit()
        latest_device_data.pop(device_name, None)
        alarm_active.pop(device_name, None)
        logger.info(f"成功删除设备: {device_name}（历史数据已保留）")

        return jsonify({
            'success': True,
            'message': f'设备 {device_name} 删除成功',
            'deleted_records': 0
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除设备失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# MQTT处理函数
# 接入约定（详见 docs/接入真实设备.md）：
#   批量：<topic_batch>            {"timestamp": ..., "devices": {"设备名": {"value": 1.2, "unit": "...", ...}}}
#   单台：<topic_device_prefix>/设备名  {"value": 1.2, ...}，或直接是一个数字
#   控制：<topic_control_prefix>/设备名 {"command": "set_value", "value": 1500}（后端发布）
DEVICE_STATUSES = ('online', 'offline', 'warning', 'maintenance')
last_seen = {}  # 设备最近一次收到数据的本机时间，用于离线判断（不受设备时钟偏差影响）


def setup_mqtt():
    """按配置连接 MQTT 代理；连不上会在后台持续重试，断线自动重连"""
    global mqtt_client
    mqtt_client = create_mqtt_client('backend', mqtt)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_disconnect = on_mqtt_disconnect
    mqtt_client.on_message = on_mqtt_message
    host, port, keepalive = mqtt_address()
    mqtt_client.connect_async(host, port, keepalive)
    mqtt_client.loop_start()
    logger.info(f"正在连接 MQTT 代理 {host}:{port}（连不上会自动重试）")


def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    """MQTT连接回调"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        logger.info("后端MQTT连接成功")
        mqtt_cfg = CONFIG['mqtt']
        client.subscribe(mqtt_cfg['topic_batch'], qos=1)
        client.subscribe(f"{mqtt_cfg['topic_device_prefix']}/+", qos=1)
    elif rc in (4, 5):
        logger.error(f"MQTT 认证失败（错误码 {rc}），请检查 config/platform.json 或 MQTT_USERNAME / MQTT_PASSWORD")
    else:
        logger.error(f"MQTT连接失败，错误码: {rc}")


def on_mqtt_disconnect(client, userdata, rc, *args):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        logger.warning(f"MQTT 连接断开（rc={rc}），正在自动重连...")


def decode_payload(raw_bytes):
    """JSON 优先；纯数字文本也接受"""
    text = raw_bytes.decode('utf-8', errors='replace').strip()
    try:
        return json.loads(text)
    except ValueError:
        return float(text)


def on_mqtt_message(client, userdata, msg):
    """MQTT消息处理"""
    try:
        mqtt_cfg = CONFIG['mqtt']
        topic = msg.topic
        payload = decode_payload(msg.payload)

        if topic == mqtt_cfg['topic_batch']:
            if not isinstance(payload, dict) or not isinstance(payload.get('devices'), dict):
                logger.warning(f"忽略格式错误的批量报文: {topic}")
                return
            ingest_readings(payload['devices'], payload.get('timestamp'))
        elif topic.startswith(mqtt_cfg['topic_device_prefix'] + '/'):
            device_name = topic[len(mqtt_cfg['topic_device_prefix']) + 1:]
            ingest_readings({device_name: payload}, None)

    except Exception as e:
        logger.error(f"处理MQTT消息失败 ({msg.topic}): {e}")


def normalize_value(value):
    """把上报值转成有限的浮点数；布尔量转 0/1；无效返回 None"""
    if isinstance(value, bool):
        return float(value)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if value == value and abs(value) != float('inf') else None


def ingest_readings(readings, packet_timestamp):
    """入库、更新设备状态、按阈值报警。逐台校验，坏数据只丢弃那一台。"""
    with app.app_context():
        try:
            received_at = datetime.now()
            packet_ts = parse_timestamp(packet_timestamp) if packet_timestamp is not None else received_at
            stored = 0

            for device_name, data in readings.items():
                if not isinstance(device_name, str) or not device_name or len(device_name) > 100 or '/' in device_name:
                    logger.warning(f"忽略非法设备名: {device_name!r}")
                    continue
                if not isinstance(data, dict):
                    data = {'value': data}
                value = normalize_value(data.get('value'))
                if value is None:
                    logger.warning(f"忽略设备 {device_name} 的无效数值: {data.get('value')!r}")
                    continue

                cfg = DEVICE_CONFIG.get(device_name, {})
                timestamp = parse_timestamp(data['timestamp']) if data.get('timestamp') is not None else packet_ts
                device_type = str(data.get('type') or cfg.get('type') or 'unknown')[:50]
                unit = str(data.get('unit') or cfg.get('unit') or '')[:20]

                # 报警以后端配置的阈值为准；设备自带的 alarm 标志也认
                alarm_min, alarm_max = cfg.get('alarm_min'), cfg.get('alarm_max')
                below = alarm_min is not None and value < alarm_min
                above = alarm_max is not None and value > alarm_max
                alarming = below or above or bool(data.get('alarm'))
                reported = data.get('status')
                status = 'warning' if alarming else (reported if reported in DEVICE_STATUSES else 'online')

                db.session.add(SensorData(
                    device_name=device_name,
                    device_type=device_type,
                    value=value,
                    unit=unit,
                    timestamp=timestamp,
                    is_anomaly=alarming,
                    status='alarm' if alarming else 'normal'
                ))

                device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
                if device_status:
                    # 运行时长按真实的上报间隔累加；断线期间不计
                    if device_status.status != 'offline' and device_status.last_update:
                        delta = (timestamp - device_status.last_update).total_seconds()
                        if 0 < delta <= OFFLINE_TIMEOUT:
                            device_status.total_runtime = (device_status.total_runtime or 0) + int(round(delta))
                    device_status.last_value = value
                    device_status.status = status
                    device_status.last_update = timestamp
                    device_status.unit = unit or device_status.unit
                    if device_status.device_type == 'unknown' and device_type != 'unknown':
                        device_status.device_type = device_type
                else:
                    db.session.add(DeviceStatus(
                        device_name=device_name,
                        device_type=device_type,
                        status=status,
                        last_value=value,
                        unit=unit,
                        last_update=timestamp,
                        total_runtime=0
                    ))

                # 只在进入越限状态时记一条报警，避免持续越限时每个周期都刷屏
                if alarming and not alarm_active.get(device_name):
                    threshold = alarm_max if above else alarm_min if below else None
                    detail = f"高于上限 {alarm_max}" if above else f"低于下限 {alarm_min}" if below else "设备上报报警"
                    db.session.add(AlarmRecord(
                        device_name=device_name,
                        alarm_type='threshold_exceeded',
                        severity='warning',
                        message=f"设备 {device_name} 数值异常: {value:g} {unit}（{detail}）",
                        value=value,
                        threshold=threshold,
                        timestamp=timestamp
                    ))
                alarm_active[device_name] = alarming

                last_seen[device_name] = received_at
                latest_device_data[device_name] = {
                    'value': value,
                    'unit': unit,
                    'type': device_type,
                    'status': status,
                    'alarm': alarming,
                    'timestamp': timestamp.isoformat()
                }
                stored += 1

            db.session.commit()
            if stored:
                logger.debug(f"成功处理 {stored} 个设备的数据")

        except Exception as e:
            logger.error(f"处理设备数据失败: {e}")
            db.session.rollback()


def watch_devices():
    """后台线程：超过 offline_timeout_seconds 没有数据的设备标为离线并报警；按 retention_days 清理旧数据"""
    retention_days = int(CONFIG.get('retention_days', 0) or 0)
    last_cleanup = 0.0
    while True:
        time.sleep(5)
        with app.app_context():
            try:
                now = datetime.now()
                cutoff = now - timedelta(seconds=OFFLINE_TIMEOUT)
                for device in DeviceStatus.query.filter(DeviceStatus.status != 'offline').all():
                    seen = last_seen.get(device.device_name) or device.last_update
                    if seen and seen >= cutoff:
                        continue
                    device.status = 'offline'
                    alarm_active.pop(device.device_name, None)
                    if device.device_name in latest_device_data:
                        latest_device_data[device.device_name]['status'] = 'offline'
                    db.session.add(AlarmRecord(
                        device_name=device.device_name,
                        alarm_type='device_offline',
                        severity='critical',
                        message=f"设备 {device.device_name} 已离线：超过 {OFFLINE_TIMEOUT} 秒没有收到数据",
                        timestamp=now
                    ))
                    logger.warning(f"设备 {device.device_name} 离线")

                if retention_days > 0 and time.time() - last_cleanup > 3600:
                    last_cleanup = time.time()
                    deleted = SensorData.query.filter(SensorData.timestamp < now - timedelta(days=retention_days)).delete()
                    if deleted:
                        logger.info(f"已清理 {deleted} 条超过 {retention_days} 天的历史数据")

                db.session.commit()
            except Exception as e:
                logger.error(f"设备状态巡检失败: {e}")
                db.session.rollback()

# 数据库初始化
def init_database():
    """初始化数据库"""
    try:
        db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        os.makedirs(db_dir, exist_ok=True)
        
        with app.app_context():
            db.create_all()
            logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

if __name__ == "__main__":
    init_database()
    logger.info("启动工业现场管控平台后端服务...")
    setup_mqtt()  # 启动MQTT客户端
    threading.Thread(target=watch_devices, daemon=True, name='device-watchdog').start()
    app.run(host='0.0.0.0', port=5055, debug=False, use_reloader=False)
