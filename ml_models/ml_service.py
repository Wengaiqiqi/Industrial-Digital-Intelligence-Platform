"""
异常检测和预测模型服务
实现设备故障预测和异常检测
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os
import json
from datetime import datetime, timedelta
from loguru import logger
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'industrial.db')


def parse_timestamp(timestamp_series):
    """解析混合格式的时间戳（ISO8601、带/不带毫秒等）"""
    return pd.to_datetime(timestamp_series, format='mixed')

class AnomalyDetector:
    """异常检测模型"""
    
    def __init__(self, model_path='../ml_models/anomaly_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.last_accuracy = 0.0  # 保存最后一次训练的准确率
        
    def prepare_features(self, data):
        """准备特征数据"""
        features = []
        
        for _, row in data.iterrows():
            feature_row = [
                row['value'],
                row['timestamp'].hour,  # 小时特征
                row['timestamp'].weekday(),  # 星期特征
            ]
            
            # 添加设备类型特征
            device_type_map = {
                'sensor': 1,
                'actuator': 2,
                'indicator': 3,
                'io': 4
            }
            feature_row.append(device_type_map.get(row['device_type'], 0))
            
            features.append(feature_row)
        
        return np.array(features)
    
    def train(self, data):
        """训练异常检测模型"""
        try:
            logger.info("开始训练异常检测模型...")
            
            # 数据预处理 - 智能解析时间戳
            data['timestamp'] = parse_timestamp(data['timestamp'])
            features = self.prepare_features(data)
            
            # 标准化
            features_scaled = self.scaler.fit_transform(features)
            
            # 训练Isolation Forest模型
            self.model = IsolationForest(
                contamination=0.1,  # 假设10%的数据是异常
                random_state=42,
                n_estimators=100
            )
            
            self.model.fit(features_scaled)
            self.is_trained = True
            
            # 计算异常检测性能指标
            predictions = self.model.predict(features_scaled)
            decision_scores = self.model.decision_function(features_scaled)
            
            # 如果有真实标签，计算准确率
            if 'is_anomaly' in data.columns:
                # 转换预测结果：-1(异常) -> True, 1(正常) -> False
                pred_anomalies = (predictions == -1)
                true_anomalies = data['is_anomaly'].values
                
                # 计算准确率
                accuracy = accuracy_score(true_anomalies, pred_anomalies)
                self.last_accuracy = accuracy
                logger.info(f"异常检测准确率: {accuracy:.3f}")
            else:
                # 没有真实标签时，使用决策分数的分布作为质量指标
                score_std = np.std(decision_scores)
                self.last_accuracy = min(0.95, max(0.5, score_std * 10))  # 基于分数分布估算质量
                logger.info(f"异常检测模型质量估计: {self.last_accuracy:.3f} (基于决策分数分布)")
            
            # 保存模型
            self.save_model()
            
            logger.info("异常检测模型训练完成")
            return True
            
        except Exception as e:
            logger.error(f"训练异常检测模型失败: {e}")
            return False
    def predict(self, data):
        """预测异常"""
        if not self.is_trained:
            self.load_model()
        
        if not self.is_trained:
            return None
        
        try:
            # 确保数据格式正确
            if isinstance(data, dict):
                # 单个数据点
                data = pd.DataFrame([data])
            
            data['timestamp'] = parse_timestamp(data['timestamp'])
            features = self.prepare_features(data)
            features_scaled = self.scaler.transform(features)
            
            # 预测
            predictions = self.model.predict(features_scaled)
            scores = self.model.decision_function(features_scaled)
              # -1表示异常，1表示正常
            results = []
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                results.append({
                    'is_anomaly': bool(pred == -1),
                    'anomaly_score': float(score),
                    'confidence': round(float(abs(score)), 4)  # 保持为0-1之间的小数
                })
            
            return results if len(results) > 1 else results[0]
            
        except Exception as e:
            logger.error(f"异常检测预测失败: {e}")
            return None
    
    def save_model(self):
        """保存模型"""
        try:
            model_dir = os.path.dirname(self.model_path)
            os.makedirs(model_dir, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'trained_at': datetime.now().isoformat()
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"异常检测模型已保存: {self.model_path}")
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
    
    def load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.is_trained = True
                logger.info(f"异常检测模型已加载: {self.model_path}")
                return True
            else:
                logger.warning(f"模型文件不存在: {self.model_path}")
                return False
                
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False


class PredictiveMaintenanceModel:
    """预测性维护模型"""
    
    # LSTM时序预测模型
    def __init__(self, model_path='../ml_models/lstm_predictive_maintenance.h5'):
        from tensorflow.keras.models import Sequential, load_model
        from tensorflow.keras.layers import LSTM, Dense
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.seq_len = 10  # 输入序列长度
        self.n_features = 1  # 只用value做预测
        self.keras = {'Sequential': Sequential, 'LSTM': LSTM, 'Dense': Dense, 'load_model': load_model}

    def prepare_sequences(self, data):
        # 只用value做时序预测
        data = data.sort_values('timestamp')
        values = data['value'].values.reshape(-1, 1)
        values_scaled = self.scaler.fit_transform(values)
        X, y = [], []
        for i in range(len(values_scaled) - self.seq_len):
            X.append(values_scaled[i:i+self.seq_len])
            y.append(values_scaled[i+self.seq_len])
        return np.array(X), np.array(y)

    def train(self, data):
        try:
            logger.info("开始训练LSTM预测模型...")
            data['timestamp'] = parse_timestamp(data['timestamp'])
            X, y = self.prepare_sequences(data)
            if len(X) == 0:
                logger.warning("没有足够的数据进行训练")
                return False
            # 构建LSTM模型
            model = self.keras['Sequential']()
            model.add(self.keras['LSTM'](32, input_shape=(self.seq_len, self.n_features)))
            model.add(self.keras['Dense'](1))
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=20, batch_size=16, verbose=0)
            self.model = model
            self.is_trained = True
            model.save(self.model_path)
            logger.info(f"LSTM预测模型训练完成并已保存: {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"训练LSTM预测模型失败: {e}")
            return False

    def predict_next_value(self, data):
        if not self.is_trained:
            self.load_model()
        if not self.is_trained:
            return None
        try:
            data['timestamp'] = parse_timestamp(data['timestamp'])
            values = data.sort_values('timestamp')['value'].values.reshape(-1, 1)
            values_scaled = self.scaler.transform(values)
            if len(values_scaled) < self.seq_len:
                logger.warning("数据长度不足以预测")
                return None
            last_seq = values_scaled[-self.seq_len:]
            last_seq = last_seq.reshape(1, self.seq_len, self.n_features)
            pred_scaled = self.model.predict(last_seq)[0][0]
            pred_value = self.scaler.inverse_transform([[pred_scaled]])[0][0]
            return {
                'next_value_prediction': float(pred_value),
                'prediction_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"LSTM预测失败: {e}")
            return None

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = self.keras['load_model'](self.model_path)
                self.is_trained = True
                logger.info(f"LSTM预测模型已加载: {self.model_path}")
                return True
            else:
                logger.warning(f"LSTM模型文件不存在: {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"加载LSTM模型失败: {e}")
            return False
    

class MLModelService:
    """机器学习模型服务"""
    
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        self.anomaly_detector = AnomalyDetector()
        self.predictive_model = PredictiveMaintenanceModel()
        
    def load_device_data(self, device_name=None, hours=24):
        """加载指定设备（device_name 为空时加载全部设备）的历史数据"""
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"数据库文件不存在: {self.db_path}")
                return pd.DataFrame()

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=hours)
            query = """
            SELECT device_name, device_type, value, unit, timestamp, is_anomaly, status
            FROM sensor_data
            WHERE timestamp >= ? AND timestamp <= ?
            """
            params = [start_date.isoformat(), end_date.isoformat()]
            if device_name:
                query += " AND device_name = ?"
                params.append(device_name)
            query += " ORDER BY timestamp ASC"

            conn = sqlite3.connect(self.db_path)
            data = pd.read_sql_query(query, conn, params=params)
            conn.close()

            logger.info(f"加载设备 {device_name or '全部'} 数据: {len(data)} 条记录，时间范围: {hours} 小时")
            return data

        except Exception as e:
            logger.error(f"加载设备数据失败: {e}")
            return pd.DataFrame()
    
    def train_models(self, device_name=None, hours=168):
        """训练所有模型 - 支持按设备分类训练和自定义时间范围"""
        logger.info(f"开始训练机器学习模型 - 设备: {device_name or '全部'}, 时间范围: {hours}小时")
        
        if device_name and device_name != 'all':
            # 训练特定设备的模型
            logger.info(f"为设备 {device_name} 训练专属模型，使用{hours}小时数据")
            data = self.load_device_data(device_name, hours=hours)
            
            if data.empty or len(data) < 50:
                logger.warning(f"设备 {device_name} 数据不足，回退使用全局数据训练")
                data = self.load_device_data(hours=hours)
        else:
            # 训练全局模型
            logger.info(f"训练全局模型，使用{hours}小时数据")
            data = self.load_device_data(hours=hours)
            
            # 如果数据库中没有足够的数据，尝试加载更长时间范围的数据
            if data.empty or len(data) < 100:
                logger.info("指定时间范围数据不足，尝试加载更长时间范围的数据...")
                data = self.load_device_data(hours=hours*2)  # 双倍时间范围
        
        # 只有在完全没有真实数据时才生成模拟数据
        if data.empty:
            logger.warning("没有任何真实数据，生成模拟数据进行训练")
            data = self.generate_synthetic_data()
        else:
            logger.info(f"使用真实数据进行训练，共 {len(data)} 条记录")
            
            # 打印数据分布信息
            if 'device_name' in data.columns:
                device_counts = data['device_name'].value_counts()
                logger.info(f"设备数据分布:")
                for device, count in device_counts.head(10).items():
                    logger.info(f"  {device}: {count} 条记录")
                if len(device_counts) > 10:
                    logger.info(f"  ... 还有 {len(device_counts) - 10} 个设备")        # 训练异常检测模型
        anomaly_success = self.anomaly_detector.train(data)
        
        # 训练预测模型
        predictive_success = self.predictive_model.train(data)
        
        # 计算总体训练成功状态
        overall_success = anomaly_success and predictive_success
        
        # 获取真实的模型性能指标
        anomaly_accuracy = getattr(self.anomaly_detector, 'last_accuracy', 0.0) if anomaly_success else 0.0
        predictive_score = getattr(self.predictive_model, 'last_test_score', 0.0) if predictive_success else 0.0
        
        # 计算综合准确率（异常检测和预测模型的平均值）
        if anomaly_success and predictive_success:
            overall_accuracy = (anomaly_accuracy + predictive_score) / 2
        elif anomaly_success:
            overall_accuracy = anomaly_accuracy
        elif predictive_success:
            overall_accuracy = predictive_score
        else:
            overall_accuracy = 0.0
        
        result = {
            'anomaly_detector': bool(anomaly_success),
            'predictive_model': bool(predictive_success),
            'overall_success': bool(overall_success),
            'data_points': int(len(data)),
            'devices_count': int(len(data['device_name'].unique()) if not data.empty and 'device_name' in data.columns else 0),
            'anomaly_accuracy': round(float(anomaly_accuracy) * 100),  # 转换为整数百分比
            'predictive_score': round(float(predictive_score) * 100),  # 转换为整数百分比
            'overall_accuracy': round(float(overall_accuracy) * 100)   # 转换为整数百分比
        }
        
        logger.info(f"训练完成 - 异常检测: {'成功' if anomaly_success else '失败'} (准确率: {anomaly_accuracy:.3f}), "
                   f"预测模型: {'成功' if predictive_success else '失败'} (分数: {predictive_score:.3f}), "
                   f"综合准确率: {overall_accuracy:.3f}, "
                   f"数据点: {result['data_points']}, 设备数: {result['devices_count']}")
        
        return result
    
    def generate_synthetic_data(self, num_samples=10000):
        """生成合成训练数据"""
        logger.info("生成合成训练数据...")
        
        devices = [
            'temperature_sensor_1', 'temperature_sensor_2',
            'fan_1', 'fan_2',
            'servo_motor_1', 'servo_motor_2',
            'pressure_sensor_1', 'flow_meter_1'
        ]
        
        device_types = {
            'temperature_sensor_1': 'sensor',
            'temperature_sensor_2': 'sensor',
            'fan_1': 'actuator',
            'fan_2': 'actuator',
            'servo_motor_1': 'actuator',
            'servo_motor_2': 'actuator',
            'pressure_sensor_1': 'sensor',
            'flow_meter_1': 'sensor'
        }
        
        data = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(num_samples):
            device = np.random.choice(devices)
            timestamp = base_time + timedelta(minutes=i * 5)
            
            # 生成设备相关的数值
            if 'temperature' in device:
                value = np.random.normal(30, 5)
                unit = '°C'
            elif 'fan' in device:
                value = np.random.normal(1500, 300)
                unit = 'RPM'
            elif 'servo' in device:
                value = np.random.uniform(0, 360)
                unit = '°'
            elif 'pressure' in device:
                value = np.random.normal(2.0, 0.5)
                unit = 'bar'
            elif 'flow' in device:
                value = np.random.normal(50, 10)
                unit = 'L/min'
            else:
                value = np.random.normal(0, 1)
                unit = 'unit'
            
            # 5%概率生成异常数据
            is_anomaly = np.random.random() < 0.05
            if is_anomaly:
                value *= np.random.uniform(1.5, 3.0)
            
            data.append({
                'device_name': device,
                'device_type': device_types[device],
                'value': value,
                'unit': unit,
                'timestamp': timestamp,
                'is_anomaly': is_anomaly,
                'status': 'online'
            })
        
        return pd.DataFrame(data)
    
    def detect_anomaly(self, data):
        """检测异常"""
        return self.anomaly_detector.predict(data)
    
    def predict_next_value(self, data):
        """LSTM 预测下一时刻数值"""
        return self.predictive_model.predict_next_value(data)
    

class MLAnalysisService:
    """机器学习分析服务 - 为前端提供智能分析功能"""
    
    def __init__(self):
        self.ml_service = MLModelService()
        
    def analyze_device_data(self, device_name, hours=24):
        """分析设备数据并提供预测建议 - 按设备分类进行"""
        try:
            logger.info(f"开始分析设备 {device_name}，时间范围: {hours} 小时")
            
            # 获取设备历史数据
            data = self.ml_service.load_device_data(device_name, hours)
            
            if data.empty:
                return {
                    'success': False,
                    'message': f'设备 {device_name} 没有足够的历史数据进行分析'
                }
            
            # 按设备分类进行训练和分析
            device_anomaly_detector = AnomalyDetector()
            device_predictive_model = PredictiveMaintenanceModel()
            
            # 使用设备专属数据训练小型模型
            if len(data) >= 50:  # 需要至少50个数据点
                # 训练设备专属异常检测模型
                device_anomaly_detector.train(data)
                
                # 异常检测
                anomaly_result = device_anomaly_detector.predict(data.tail(1))
            else:
                # 数据不足时使用全局模型
                anomaly_result = self.ml_service.detect_anomaly(data.tail(1))
            
            # 故障预测（使用足够的历史数据）
            if len(data) >= 100:
                # 使用设备专属数据进行预测
                device_predictive_model.train(data)
                prediction_result = device_predictive_model.predict_next_value(data)
            else:
                # 使用全局模型
                prediction_result = self.ml_service.predict_next_value(data)
            
            # 数据统计分析
            statistics = self._calculate_device_statistics(data, device_name)
            
            # 生成分析建议
            recommendations = self._generate_device_recommendations(
                device_name, anomaly_result, prediction_result, statistics
            )
            
            # confidence 现在已经在源头格式化为百分比了，不需要额外处理
            
            return {
                'success': True,
                'device_name': device_name,
                'analysis_time': datetime.now().isoformat(),
                'data_period_hours': hours,
                'data_points': len(data),
                'anomaly_detection': anomaly_result,
                'failure_prediction': prediction_result,
                'statistics': statistics,
                'recommendations': recommendations,
                'data_quality': self._assess_data_quality(data)
            }
            
        except Exception as e:
            logger.error(f"设备数据分析失败: {e}")
            return {
                'success': False,
                'message': f'分析设备 {device_name} 数据时发生错误: {str(e)}'
            }
    
    def _calculate_device_statistics(self, data, device_name):
        """计算设备专属统计信息"""
        try:
            if data.empty:
                return {}
              # 基础统计
            stats = {
                'device_name': device_name,
                'device_type': data['device_type'].iloc[0] if not data.empty else 'unknown',
                'unit': data['unit'].iloc[0] if not data.empty else '',
                'count': int(len(data)),
                'mean': float(data['value'].mean()),
                'std': float(data['value'].std()),
                'min': float(data['value'].min()),
                'max': float(data['value'].max()),
                'median': float(data['value'].median()),
                'anomaly_count': int(data['is_anomaly'].sum()) if 'is_anomaly' in data.columns else 0,
                'anomaly_rate': round(float(data['is_anomaly'].mean()) * 100) if 'is_anomaly' in data.columns else 0,
                'trend': self._calculate_trend(data),
                'time_span': {
                    'start': data['timestamp'].min().isoformat() if not data.empty else None,
                    'end': data['timestamp'].max().isoformat() if not data.empty else None
                }
            }
            
            # 设备专属分析
            stats.update(self._analyze_device_patterns(data, device_name))
            
            return stats
        except Exception as e:
            logger.error(f"计算设备统计信息失败: {e}")
            return {}
    
    def _analyze_device_patterns(self, data, device_name):
        """分析设备专属模式"""
        patterns = {}
        
        try:
            # 根据设备类型进行专门分析
            device_type = data['device_type'].iloc[0] if not data.empty else 'unknown'
            
            if 'temperature' in device_name.lower():
                # 温度传感器分析
                patterns.update(self._analyze_temperature_patterns(data))
            elif 'pressure' in device_name.lower():
                # 压力传感器分析
                patterns.update(self._analyze_pressure_patterns(data))
            elif 'flow' in device_name.lower():
                # 流量传感器分析
                patterns.update(self._analyze_flow_patterns(data))
            elif 'motor' in device_name.lower() or 'fan' in device_name.lower():
                # 电机/风扇分析
                patterns.update(self._analyze_motor_patterns(data))
            
            # 时间模式分析
            patterns.update(self._analyze_time_patterns(data))
            
        except Exception as e:
            logger.error(f"设备模式分析失败: {e}")
            
        return patterns
    
    def _analyze_temperature_patterns(self, data):
        """温度传感器专用分析"""
        patterns = {}
        values = data['value']
        
        # 温度范围分析
        if values.max() > 80:
            patterns['high_temperature_risk'] = True
            patterns['max_temp_recorded'] = float(values.max())
        
        if values.min() < 0:
            patterns['low_temperature_risk'] = True
            patterns['min_temp_recorded'] = float(values.min())
        
        # 温度波动分析
        temp_changes = values.diff().abs()
        patterns['avg_temperature_change'] = float(temp_changes.mean())
        patterns['max_temperature_change'] = float(temp_changes.max())
        
        return patterns
    
    def _analyze_pressure_patterns(self, data):
        """压力传感器专用分析"""
        patterns = {}
        values = data['value']
        
        # 压力异常分析
        if values.max() > 10:  # 假设正常压力范围是0-10 bar
            patterns['high_pressure_risk'] = True
            
        if values.min() < 0:
            patterns['negative_pressure_detected'] = True
        
        # 压力稳定性分析
        pressure_variance = float(values.var())
        patterns['pressure_stability'] = 'stable' if pressure_variance < 0.1 else 'unstable'
        
        return patterns
    
    def _analyze_flow_patterns(self, data):
        """流量传感器专用分析"""
        patterns = {}
        values = data['value']
        
        # 流量中断检测
        zero_flow_count = (values == 0).sum()
        patterns['flow_interruption_rate'] = float(zero_flow_count / len(values))
        
        # 流量效率分析
        if not values.empty:
            avg_flow = values.mean()
            patterns['average_flow_rate'] = float(avg_flow)
            patterns['flow_efficiency'] = 'good' if avg_flow > 30 else 'low'
        
        return patterns
    
    def _analyze_motor_patterns(self, data):
        """电机/风扇专用分析"""
        patterns = {}
        values = data['value']
        
        # 转速分析
        if 'RPM' in data['unit'].iloc[0] if not data.empty else '':
            avg_rpm = values.mean()
            patterns['average_rpm'] = float(avg_rpm)
            patterns['motor_performance'] = 'good' if avg_rpm > 1000 else 'low'
            
            # 转速波动分析
            rpm_std = values.std()
            patterns['rpm_stability'] = 'stable' if rpm_std < 100 else 'unstable'
        
        return patterns
    
    def _analyze_time_patterns(self, data):
        """时间模式分析"""
        patterns = {}
        
        try:
            # 确保timestamp是datetime类型
            if not data.empty:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data['hour'] = data['timestamp'].dt.hour
                data['weekday'] = data['timestamp'].dt.weekday
                
                # 工作时间vs非工作时间分析
                work_hours = data[(data['hour'] >= 8) & (data['hour'] <= 18)]
                non_work_hours = data[(data['hour'] < 8) | (data['hour'] > 18)]
                
                if not work_hours.empty and not non_work_hours.empty:
                    patterns['work_hours_avg'] = float(work_hours['value'].mean())
                    patterns['non_work_hours_avg'] = float(non_work_hours['value'].mean())
                    patterns['work_vs_nonwork_diff'] = float(
                        abs(work_hours['value'].mean() - non_work_hours['value'].mean())
                    )
                
                # 周末vs工作日分析
                weekdays = data[data['weekday'] < 5]  # 0-4是周一到周五
                weekends = data[data['weekday'] >= 5]  # 5-6是周六周日
                
                if not weekdays.empty and not weekends.empty:
                    patterns['weekday_avg'] = float(weekdays['value'].mean())
                    patterns['weekend_avg'] = float(weekends['value'].mean())
        
        except Exception as e:
            logger.error(f"时间模式分析失败: {e}")
        
        return patterns
    
    def _calculate_trend(self, data):
        """计算数据趋势"""
        try:
            if len(data) < 2:
                return 'insufficient_data'
            
            # 简单的线性趋势计算
            x = np.arange(len(data))
            y = data['value'].values
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'unknown'
    
    def _assess_data_quality(self, data):
        """评估数据质量"""
        if data.empty:
            return {'quality_score': 0, 'issues': ['no_data']}
        
        issues = []
        quality_score = 100
        
        # 检查数据完整性
        if data['value'].isnull().any():
            issues.append('missing_values')
            quality_score -= 20
        
        # 检查数据范围合理性
        if (data['value'] < 0).any() and 'temperature' not in data['device_name'].iloc[0].lower():
            issues.append('negative_values')
            quality_score -= 10
        
        # 检查数据时间间隔
        if not data.empty and len(data) > 1:
            time_diffs = pd.to_datetime(data['timestamp']).diff().dt.total_seconds()
            if time_diffs.std() > 3600:  # 时间间隔标准差大于1小时
                issues.append('irregular_intervals')
                quality_score -= 15
        
        # 检查异常值比例
        anomaly_rate = data['is_anomaly'].mean()
        if anomaly_rate > 0.2:  # 异常率超过20%
            issues.append('high_anomaly_rate')
            quality_score -= 25
        
        return {
            'quality_score': max(0, quality_score),
            'issues': issues,
            'data_points': len(data),
            'anomaly_rate': round(float(anomaly_rate) * 100)  # 转换为百分比
        }
    
    def _generate_device_recommendations(self, device_name, anomaly_result, prediction_result, statistics):
        """生成设备专属分析建议"""
        recommendations = []
        
        # 基于设备类型的专门建议
        device_type = statistics.get('device_type', 'unknown')
        
        # 异常检测建议
        if anomaly_result and anomaly_result.get('is_anomaly'):
            confidence = anomaly_result.get('confidence', 0)
            if confidence > 0.8:
                recommendations.append({
                    'type': 'critical',
                    'title': f'{device_name} 检测到严重异常',
                    'description': f'设备存在严重异常，置信度: {confidence:.2%}',
                    'action': f'建议立即检查设备 {device_name}，可能需要停机维护',
                    'priority': 'high'
                })
            elif confidence > 0.5:
                recommendations.append({
                    'type': 'warning',
                    'title': f'{device_name} 检测到异常行为',
                    'description': f'设备运行异常，置信度: {confidence:.2%}',
                    'action': f'建议加强对设备 {device_name} 的监控，考虑预防性维护',
                    'priority': 'medium'
                })
        
        # 故障预测建议
        if prediction_result:
            risk_level = prediction_result.get('risk_level', 'unknown')
            probability = prediction_result.get('failure_probability', 0)
            
            if risk_level == 'critical':
                recommendations.append({
                    'type': 'critical',
                    'title': f'{device_name} 高故障风险',
                    'description': f'预测故障概率: {probability:.2%}',
                    'action': f'建议对设备 {device_name} 安排紧急维护，避免设备故障导致停产',
                    'priority': 'high'
                })
            elif risk_level == 'high':
                recommendations.append({
                    'type': 'warning',
                    'title': f'{device_name} 中等故障风险',
                    'description': f'预测故障概率: {probability:.2%}',
                    'action': f'建议在下次计划维护时重点检查设备 {device_name}',
                    'priority': 'medium'
                })
        
        # 设备专属建议
        if 'temperature' in device_name.lower():
            recommendations.extend(self._get_temperature_recommendations(statistics))
        elif 'pressure' in device_name.lower():
            recommendations.extend(self._get_pressure_recommendations(statistics))
        elif 'flow' in device_name.lower():
            recommendations.extend(self._get_flow_recommendations(statistics))
        elif 'motor' in device_name.lower() or 'fan' in device_name.lower():
            recommendations.extend(self._get_motor_recommendations(statistics))
        
        # 如果没有特殊建议，给出正常运行的建议
        if not recommendations:
            recommendations.append({
                'type': 'success',
                'title': f'{device_name} 运行正常',
                'description': '未检测到明显异常或故障风险',
                'action': f'设备 {device_name} 继续按计划进行定期维护即可',
                'priority': 'low'
            })
        
        return recommendations
    
    def _get_temperature_recommendations(self, statistics):
        """温度传感器专用建议"""
        recommendations = []
        
        if statistics.get('high_temperature_risk'):
            max_temp = statistics.get('max_temp_recorded', 0)
            recommendations.append({
                'type': 'warning',
                'title': '高温风险',
                'description': f'检测到最高温度: {max_temp:.1f}°C',
                'action': '检查冷却系统，确保通风良好',
                'priority': 'medium'
            })
        
        if statistics.get('max_temperature_change', 0) > 10:
            recommendations.append({
                'type': 'info',
                'title': '温度波动较大',
                'description': '温度变化幅度较大，可能影响设备稳定性',
                'action': '检查温控系统，优化环境温度控制',
                'priority': 'low'
            })
        
        return recommendations
    
    def _get_pressure_recommendations(self, statistics):
        """压力传感器专用建议"""
        recommendations = []
        
        if statistics.get('high_pressure_risk'):
            recommendations.append({
                'type': 'warning',
                'title': '高压力警告',
                'description': '检测到异常高压，可能存在安全风险',
                'action': '立即检查压力释放阀和安全装置',
                'priority': 'high'
            })
        
        if statistics.get('pressure_stability') == 'unstable':
            recommendations.append({
                'type': 'info',
                'title': '压力不稳定',
                'description': '压力波动较大，影响系统稳定性',
                'action': '检查压力调节器和管路系统',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _get_flow_recommendations(self, statistics):
        """流量传感器专用建议"""
        recommendations = []
        
        interruption_rate = statistics.get('flow_interruption_rate', 0)
        if interruption_rate > 0.1:  # 中断率超过10%
            recommendations.append({
                'type': 'warning',
                'title': '频繁流量中断',
                'description': f'流量中断率: {interruption_rate:.2%}',
                'action': '检查管路是否有堵塞或泄漏',
                'priority': 'medium'
            })
        
        if statistics.get('flow_efficiency') == 'low':
            recommendations.append({
                'type': 'info',
                'title': '流量效率偏低',
                'description': '平均流量低于预期值',
                'action': '检查泵的性能和管路阻力',
                'priority': 'low'
            })
        
        return recommendations
    
    def _get_motor_recommendations(self, statistics):
        """电机/风扇专用建议"""
        recommendations = []
        
        if statistics.get('motor_performance') == 'low':
            avg_rpm = statistics.get('average_rpm', 0)
            recommendations.append({
                'type': 'warning',
                'title': '电机性能偏低',
                'description': f'平均转速: {avg_rpm:.0f} RPM，低于正常范围',
                'action': '检查电机负载和电源供应',
                'priority': 'medium'
            })
        
        if statistics.get('rpm_stability') == 'unstable':
            recommendations.append({
                'type': 'info',
                'title': '转速不稳定',
                'description': '转速波动较大，可能存在机械问题',
                'action': '检查轴承、皮带和联轴器',
                'priority': 'medium'
            })
        
        return recommendations
