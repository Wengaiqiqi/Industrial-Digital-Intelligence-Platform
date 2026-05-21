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

# 创建Flask应用
app = Flask(__name__)

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "../database/industrial.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'industrial-control-platform-2025'

# 初始化扩展
db = SQLAlchemy(app)
CORS(app)

# MQTT客户端全局变量
mqtt_client = None
latest_device_data = {}  # 存储最新的设备数据

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
        
        # 否则从数据库获取最新数据
        devices = []
        device_names = db.session.query(DeviceStatus.device_name).distinct().all()
        
        for (device_name,) in device_names:
            latest_data = SensorData.query.filter_by(device_name=device_name)\
                .order_by(desc(SensorData.timestamp)).first()
            
            device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
            
            if latest_data:
                device_info = {
                    'device_name': device_name,
                    'value': latest_data.value,
                    'unit': latest_data.unit,
                    'type': latest_data.device_type,
                    'status': device_status.status if device_status else 'unknown',
                    'timestamp': latest_data.to_dict()['timestamp']
                }
                devices.append(device_info)
        
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

@app.route('/api/devices/<device_name>/data', methods=['GET'])
def get_device_data(device_name):
    """获取设备历史数据"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        logger.info(f"获取设备 {device_name} 的历史数据, 时间范围: {hours}小时, 限制: {limit}条")
        
        query = SensorData.query.filter_by(device_name=device_name)
        
        if hours:
            start_time = datetime.now() - timedelta(hours=hours)
            query = query.filter(SensorData.timestamp >= start_time)
        
        data = query.order_by(desc(SensorData.timestamp)).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in data],
            'count': len(data),
            'device_name': device_name,
            'time_range_hours': hours
        })
        
    except Exception as e:
        logger.error(f"获取设备 {device_name} 历史数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_name>/latest', methods=['GET'])
def get_device_latest(device_name):
    """获取设备最新数据"""
    try:
        global latest_device_data
        
        # 优先从缓存获取
        if device_name in latest_device_data:
            return jsonify({
                'success': True,
                'device_name': device_name,
                'data': latest_device_data[device_name]
            })
        
        # 从数据库获取
        latest_data = SensorData.query.filter_by(device_name=device_name)\
            .order_by(desc(SensorData.timestamp)).first()
        
        device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
        
        if latest_data:
            result = {
                'value': latest_data.value,
                'unit': latest_data.unit,
                'type': latest_data.device_type,
                'status': device_status.status if device_status else 'unknown',
                'timestamp': latest_data.to_dict()['timestamp']
            }
            
            return jsonify({
                'success': True,
                'device_name': device_name,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
            
    except Exception as e:
        logger.error(f"获取设备最新数据失败: {e}")
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
        
        # 这里应该实际发送控制命令到设备
        # 目前只是模拟，实际实现需要根据具体的设备通信协议
        logger.info(f"向设备 {device_name} 发送控制命令: {command}={value}")
        
        # 模拟控制成功，更新设备状态
        device.last_update = datetime.now()
        if command == 'set_value' and value is not None:
            device.last_value = float(value)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'设备 {device_name} 控制成功',
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

@app.route('/api/ml/anomaly/<device_name>', methods=['GET'])
def get_anomaly_detection(device_name):
    """获取异常检测结果"""
    try:
        logger.info(f"获取设备 {device_name} 的异常检测结果")
        
        # 获取最近的数据进行异常检测分析
        hours = request.args.get('hours', 24, type=int)
        start_time = datetime.now() - timedelta(hours=hours)
        
        data = SensorData.query.filter(
            SensorData.device_name == device_name,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp).all()
        
        if not data:
            return jsonify({
                'success': True,
                'data': {
                    'device_name': device_name,
                    'anomaly_score': 0.0,
                    'is_anomaly': False,
                    'anomaly_count': 0,
                    'total_points': 0,
                    'message': '暂无数据'
                }
            })
        
        # 简单的异常检测逻辑（实际应用中应使用更复杂的ML算法）
        values = [d.value for d in data]
        anomaly_count = sum(1 for d in data if d.is_anomaly)
        
        # 计算异常率
        anomaly_rate = anomaly_count / len(data) if data else 0
        
        # 计算数据的标准差来评估异常程度
        import statistics
        if len(values) > 1:
            mean_val = statistics.mean(values)
            stdev = statistics.stdev(values)
            latest_value = values[-1] if values else 0
            anomaly_score = abs(latest_value - mean_val) / stdev if stdev > 0 else 0
        else:
            anomaly_score = 0
        
        is_anomaly = anomaly_score > 2.0 or anomaly_rate > 0.1
        
        return jsonify({
            'success': True,
            'data': {
                'device_name': device_name,
                'anomaly_score': round(anomaly_score, 3),
                'is_anomaly': is_anomaly,
                'anomaly_count': anomaly_count,
                'total_points': len(data),
                'anomaly_rate': round(anomaly_rate * 100),
                'analysis_period_hours': hours
            }
        })
        
    except Exception as e:
        logger.error(f"异常检测失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ml/prediction/<device_name>', methods=['GET'])
def get_failure_prediction(device_name):
    """获取故障预测"""
    try:
        logger.info(f"获取设备 {device_name} 的故障预测")
        
        # 获取设备历史数据进行故障预测分析
        hours = request.args.get('hours', 168, type=int)  # 默认7天
        start_time = datetime.now() - timedelta(hours=hours)
        
        data = SensorData.query.filter(
            SensorData.device_name == device_name,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp).all()
        
        device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
        
        if not data:
            return jsonify({
                'success': True,
                'data': {
                    'device_name': device_name,
                    'failure_probability': 0.0,
                    'risk_level': 'low',
                    'predicted_failure_time': None,
                    'recommendation': '暂无足够数据进行预测'
                }
            })
        
        # 简单的故障预测逻辑（实际应用中应使用更复杂的ML模型）
        error_count = device_status.error_count if device_status else 0
        anomaly_count = sum(1 for d in data if d.is_anomaly)
        
        # 计算故障概率
        failure_probability = min((error_count * 0.1 + anomaly_count * 0.05) / len(data), 1.0)
        
        # 确定风险等级
        if failure_probability < 0.2:
            risk_level = 'low'
            recommendation = '设备运行正常，建议按计划维护'
        elif failure_probability < 0.5:
            risk_level = 'medium'
            recommendation = '设备有潜在风险，建议增加检查频率'
        else:
            risk_level = 'high'
            recommendation = '设备故障风险较高，建议立即检查和维护'
        
        # 预测故障时间（简化计算）
        if failure_probability > 0.3:
            days_to_failure = max(1, int(30 * (1 - failure_probability)))
            predicted_failure_time = (datetime.now() + timedelta(days=days_to_failure)).isoformat()
        else:
            predicted_failure_time = None
        
        return jsonify({
            'success': True,
            'data': {
                'device_name': device_name,
                'failure_probability': failure_probability,  # 已经是百分比，直接使用
                'risk_level': risk_level,
                'predicted_failure_time': predicted_failure_time,
                'recommendation': recommendation,
                'analysis_period_hours': hours,
                'data_points_analyzed': len(data)
            }
        })
        
    except Exception as e:
        logger.error(f"故障预测失败: {e}")
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

@app.route('/api/ml/predict/<device_name>', methods=['POST'])
def predict_device_failure(device_name):
    """预测设备故障"""
    try:
        logger.info(f"开始预测设备 {device_name} 故障概率")
        
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
        
        # 获取设备最近数据进行预测
        hours = request.get_json().get('hours', 24) if request.get_json() else 24
        data = ml_service.load_device_data(device_name, hours)
        
        if data.empty:
            return jsonify({
                'success': False,
                'message': f'设备 {device_name} 没有足够的数据进行预测'
            }), 400
        
        # 执行预测
        prediction = ml_service.predict_failure_probability(data)
        
        if prediction:
            return jsonify({
                'success': True,
                'device_name': device_name,
                'prediction': prediction,
                'data_points': len(data),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': '预测模型不可用或预测失败'
            }), 500
            
    except Exception as e:
        logger.error(f"故障预测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '故障预测服务暂时不可用'
        }), 500

@app.route('/api/ml/detect-anomaly/<device_name>', methods=['POST'])
def detect_device_anomaly(device_name):
    """检测设备异常"""
    try:
        logger.info(f"开始检测设备 {device_name} 异常")
        
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
        
        # 获取设备最近数据进行异常检测
        hours = request.get_json().get('hours', 1) if request.get_json() else 1
        data = ml_service.load_device_data(device_name, hours)
        
        if data.empty:
            return jsonify({
                'success': False,
                'message': f'设备 {device_name} 没有足够的数据进行异常检测'
            }), 400
        
        # 执行异常检测
        anomaly_result = ml_service.detect_anomaly(data)
        
        if anomaly_result:
            return jsonify({
                'success': True,
                'device_name': device_name,
                'anomaly_detection': anomaly_result,
                'data_points': len(data),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': '异常检测模型不可用或检测失败'
            }), 500
            
    except Exception as e:
        logger.error(f"异常检测失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '异常检测服务暂时不可用'
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

@app.route('/api/devices/categories', methods=['GET'])
def get_device_categories():
    """获取设备分类信息"""
    try:
        # 获取所有设备的最新数据
        device_names = db.session.query(SensorData.device_name).distinct().all()
        
        categories = {
            'sensors': [],     # 传感器类
            'actuators': [],   # 执行器类
            'indicators': [],  # 指示器类
            'io': []          # IO设备类
        }
        
        for (device_name,) in device_names:
            latest_data = SensorData.query.filter_by(device_name=device_name)\
                .order_by(desc(SensorData.timestamp)).first()
            
            device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
            
            if latest_data:
                device_info = {
                    'name': device_name,
                    'value': latest_data.value,
                    'unit': latest_data.unit,
                    'type': latest_data.device_type,
                    'status': device_status.status if device_status else 'unknown',
                    'timestamp': latest_data.to_dict()['timestamp']
                }
                
                # 根据设备名称分类
                if any(keyword in device_name.lower() for keyword in ['sensor', 'level', 'temperature', 'pressure', 'flow']):
                    categories['sensors'].append(device_info)
                elif any(keyword in device_name.lower() for keyword in ['valve', 'pump', 'motor', 'speed']):
                    categories['actuators'].append(device_info)
                elif any(keyword in device_name.lower() for keyword in ['indicator', 'light', 'alarm']):
                    categories['indicators'].append(device_info)
                elif any(keyword in device_name.lower() for keyword in ['input', 'output', 'stop', 'digital']):
                    categories['io'].append(device_info)
                else:
                    # 默认归类为传感器
                    categories['sensors'].append(device_info)
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total_devices': sum(len(cat) for cat in categories.values())
        })
        
    except Exception as e:
        logger.error(f"获取设备分类失败: {e}")
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
        
        # 删除设备状态记录
        db.session.delete(device)
        
        # 删除所有相关的传感器数据记录
        sensor_data_count = SensorData.query.filter_by(device_name=device_name).count()
        SensorData.query.filter_by(device_name=device_name).delete()
        
        db.session.commit()
        logger.info(f"成功删除设备: {device_name}, 删除了 {sensor_data_count} 条历史数据")
        
        return jsonify({
            'success': True,
            'message': f'设备 {device_name} 删除成功',
            'deleted_records': sensor_data_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除设备失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/devices/<device_name>', methods=['PUT'])
def update_device(device_name):
    """更新设备信息"""
    try:
        data = request.get_json()
        
        # 查找设备
        device = DeviceStatus.query.filter_by(device_name=device_name).first()
        if not device:
            return jsonify({'success': False, 'error': f'设备 {device_name} 不存在'}), 404
        
        # 更新设备信息
        if 'device_type' in data:
            device.device_type = data['device_type']
        if 'unit' in data:
            device.unit = data['unit']
        if 'status' in data:
            device.status = data['status']
        
        device.last_update = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"成功更新设备: {device_name}")
        
        return jsonify({
            'success': True,
            'message': f'设备 {device_name} 更新成功',
            'device': device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新设备失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# MQTT处理函数
def setup_mqtt():
    """设置MQTT客户端"""
    global mqtt_client
    try:
        # 兼容不同版本的paho-mqtt
        try:
            mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except (AttributeError, TypeError):
            mqtt_client = mqtt.Client()
            
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        
        # 尝试连接MQTT代理
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_start()
        logger.info("后端MQTT客户端连接成功")
        
    except Exception as e:
        logger.warning(f"MQTT连接失败: {e}")
        mqtt_client = None

def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    """MQTT连接回调"""
    if rc == 0:
        logger.info("后端MQTT连接成功")
        # 订阅设备数据主题
        client.subscribe("industrial/sensors/data")
        client.subscribe("industrial/device/+")
    else:
        logger.error(f"MQTT连接失败，错误码: {rc}")

def on_mqtt_message(client, userdata, msg):
    """MQTT消息处理"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        if topic == "industrial/sensors/data":
            # 处理完整的设备数据包
            process_device_data_batch(payload)
        elif topic.startswith("industrial/device/"):
            # 处理单个设备数据
            device_name = topic.split('/')[-1]
            process_single_device_data(device_name, payload)
            
    except Exception as e:
        logger.error(f"处理MQTT消息失败: {e}")

def process_device_data_batch(data_packet):
    """处理批量设备数据"""
    global latest_device_data
    
    with app.app_context():
        try:
            timestamp = datetime.fromisoformat(data_packet['timestamp'].replace('Z', '+00:00'))
            devices = data_packet.get('devices', {})
            
            # 更新最新设备数据缓存
            latest_device_data.update(devices)
            
            
            # 批量插入数据库
            sensor_records = []
            device_status_updates = []
            alarm_records = []
            
            for device_name, device_data in devices.items():
                # 准备传感器数据记录
                sensor_record = SensorData(
                    device_name=device_name,
                    device_type=device_data.get('type', 'unknown'),
                    value=device_data['value'],
                    unit=device_data.get('unit', ''),
                    timestamp=timestamp,
                    is_anomaly=device_data.get('alarm', False),
                    status=device_data.get('status', 'normal')
                )
                sensor_records.append(sensor_record)
                  # 更新设备状态
                device_status = DeviceStatus.query.filter_by(device_name=device_name).first()
                if device_status:
                    device_status.last_value = device_data['value']
                    device_status.status = device_data.get('status', 'online')
                    device_status.last_update = timestamp
                    device_status.total_runtime += 2  # 2秒增量
                else:
                    # 创建新设备状态记录
                    device_status = DeviceStatus(
                        device_name=device_name,
                        device_type=device_data.get('type', 'unknown'),
                        status=device_data.get('status', 'online'),
                        last_value=device_data['value'],
                        unit=device_data.get('unit', ''),
                        last_update=timestamp,
                        total_runtime=0
                    )
                    db.session.add(device_status)
                
                # 检查并创建报警记录
                if device_data.get('alarm', False):
                    alarm_record = AlarmRecord(
                        device_name=device_name,
                        alarm_type='threshold_exceeded',
                        severity='warning',
                        message=f"设备 {device_name} 数值异常: {device_data['value']} {device_data.get('unit', '')}",
                        value=device_data['value'],
                        timestamp=timestamp
                    )
                    alarm_records.append(alarm_record)
            
            # 批量提交到数据库
            if sensor_records:
                db.session.add_all(sensor_records)
            if alarm_records:
                db.session.add_all(alarm_records)
            
            db.session.commit()
            logger.debug(f"成功处理 {len(devices)} 个设备的数据")
            
        except Exception as e:
            logger.error(f"批量处理设备数据失败: {e}")
            db.session.rollback()

def process_single_device_data(device_name, device_data):
    """处理单个设备数据"""
    global latest_device_data
    
    # 更新最新设备数据缓存
    latest_device_data[device_name] = device_data

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
    app.run(host='0.0.0.0', port=5055, debug=False, use_reloader=False)
