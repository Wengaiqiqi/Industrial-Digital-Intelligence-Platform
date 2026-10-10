"""
机器学习服务包装器
为后端提供机器学习功能的统一接口
"""

import os
import sys
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_models'))

try:
    from ml_service import MLModelService, MLAnalysisService
    ML_SERVICE_AVAILABLE = True
    logger.info("机器学习服务导入成功")
except Exception as e:
    ML_SERVICE_AVAILABLE = False
    logger.warning(f"机器学习服务导入失败: {e}")


def get_ml_model_service():
    """获取机器学习模型服务实例"""
    return MLModelService()

def get_ml_analysis_service():
    """获取机器学习分析服务实例"""
    return MLAnalysisService()

def is_ml_service_available():
    """检查机器学习服务是否可用"""
    return ML_SERVICE_AVAILABLE
