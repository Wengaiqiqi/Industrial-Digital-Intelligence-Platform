"""
模型训练脚本
用于定期训练和更新机器学习模型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_service import MLModelService
from loguru import logger
import schedule
import time
from datetime import datetime

def train_models():
    """训练模型的主函数"""
    logger.info("=" * 50)
    logger.info("开始模型训练任务")
    logger.info(f"训练时间: {datetime.now()}")
    
    try:
        # 创建ML服务实例
        ml_service = MLModelService()
        
        # 训练模型
        results = ml_service.train_models()
        
        # 输出训练结果
        logger.info("模型训练完成:")
        logger.info(f"  异常检测模型: {'成功' if results['anomaly_detector'] else '失败'}")
        logger.info(f"  预测维护模型: {'成功' if results['predictive_model'] else '失败'}")
        
        # 保存训练记录
        training_log = {
            'timestamp': datetime.now().isoformat(),
            'anomaly_detector_success': results['anomaly_detector'],
            'predictive_model_success': results['predictive_model']
        }
        
        # 写入训练日志
        log_path = os.path.join(os.path.dirname(__file__), 'training_log.txt')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{training_log}\\n")
        
        logger.info("模型训练任务完成")
        
    except Exception as e:
        logger.error(f"模型训练失败: {e}")

def run_scheduled_training():
    """运行定时训练"""
    logger.info("启动定时模型训练服务...")
    
    # 设置训练计划
    # 每天凌晨2点训练
    schedule.every().day.at("02:00").do(train_models)
    
    # 每6小时训练一次（开发测试用）
    schedule.every(6).hours.do(train_models)
    
    # 立即执行一次训练
    logger.info("执行初始模型训练...")
    train_models()
    
    # 开始定时任务循环
    logger.info("定时训练服务已启动，等待下次训练...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='机器学习模型训练')
    parser.add_argument('--mode', choices=['once', 'scheduled'], default='once',
                       help='训练模式: once(单次训练) 或 scheduled(定时训练)')
    
    args = parser.parse_args()
    
    if args.mode == 'once':
        # 单次训练
        train_models()
    else:
        # 定时训练
        run_scheduled_training()
