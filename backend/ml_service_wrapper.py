"""
机器学习服务包装器
为后端提供机器学习功能的统一接口
"""

import os
import sys
import importlib.util
from loguru import logger

# 获取ml_service.py的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ml_service_path = os.path.join(os.path.dirname(current_dir), 'ml_models', 'ml_service.py')

# 动态导入ml_service模块
ML_SERVICE_AVAILABLE = False
MLModelService = None
MLAnalysisService = None

try:
    if os.path.exists(ml_service_path):
        # 使用importlib动态导入模块
        spec = importlib.util.spec_from_file_location("ml_service", ml_service_path)
        ml_service_module = importlib.util.module_from_spec(spec)
        
        # 添加ml_models目录到sys.path以便模块内部导入
        ml_models_dir = os.path.dirname(ml_service_path)
        if ml_models_dir not in sys.path:
            sys.path.insert(0, ml_models_dir)
        
        # 执行模块
        spec.loader.exec_module(ml_service_module)
        
        # 获取需要的类
        MLModelService = getattr(ml_service_module, 'MLModelService', None)
        MLAnalysisService = getattr(ml_service_module, 'MLAnalysisService', None)
        
        if MLModelService and MLAnalysisService:
            ML_SERVICE_AVAILABLE = True
            logger.info("机器学习服务导入成功")
        else:
            logger.warning("机器学习服务类未找到")
    else:
        logger.warning(f"ml_service.py 文件不存在: {ml_service_path}")
        
except Exception as e:
    logger.warning(f"机器学习服务导入失败: {e}")

# 如果导入失败，创建占位类
if not ML_SERVICE_AVAILABLE:
    logger.info("使用占位类替代机器学习服务")
    
    class MLModelService:
        def __init__(self):
            pass
        
        def train_models(self):
            return {'anomaly_detector': False, 'predictive_model': False}
        
        def load_device_data(self, device_name, hours):
            import pandas as pd
            return pd.DataFrame()
        
        def predict_failure_probability(self, data):
            return None
        
        def detect_anomaly(self, data):
            return None
    
    class MLAnalysisService:
        def __init__(self):
            pass
        
        def analyze_device_data(self, device_name, hours):
            return {
                'success': False,
                'message': '机器学习服务不可用'
            }

def get_ml_model_service():
    """获取机器学习模型服务实例"""
    if ML_SERVICE_AVAILABLE:
        # 计算正确的数据库路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(os.path.dirname(current_dir), 'database', 'industrial.db')
        return MLModelService(db_path=db_path)
    else:
        return MLModelService()

def get_ml_analysis_service():
    """获取机器学习分析服务实例"""
    return MLAnalysisService()

def is_ml_service_available():
    """检查机器学习服务是否可用"""
    return ML_SERVICE_AVAILABLE
