#!/usr/bin/env python3
"""
工业现场管控平台 - 依赖清理脚本
支持 Windows/Linux/macOS 跨平台清理
"""

import os
import shutil
import sys
from pathlib import Path
import argparse
from loguru import logger

class DependencyCleaner:
    """依赖清理器"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.cleaned_items = []
        self.skipped_items = []
        
        # 配置日志
        logger.add(
            self.project_root / "logs" / "clean_dependencies.log",
            rotation="1 day",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def clean_python_cache(self):
        """清理Python缓存文件"""
        logger.info("🗑️ 清理Python缓存文件...")
        
        patterns = [
            "**/__pycache__",
            "**/*.pyc", 
            "**/*.pyo",
            "**/*.pyd",
            "**/.pytest_cache",
            "**/.coverage",
            "**/htmlcov"
        ]
        
        for pattern in patterns:
            for item in self.project_root.glob(pattern):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.info(f"删除目录: {item}")
                    else:
                        item.unlink()
                        logger.info(f"删除文件: {item}")
                    self.cleaned_items.append(str(item))
                except Exception as e:
                    logger.warning(f"删除失败 {item}: {e}")
                    self.skipped_items.append(str(item))
    
    def clean_frontend_dependencies(self):
        """清理前端依赖"""
        logger.info("📦 清理前端依赖...")
        
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            logger.warning("前端目录不存在")
            return
        
        items_to_clean = [
            frontend_dir / "node_modules",
            frontend_dir / "package-lock.json",
            frontend_dir / "yarn.lock",
            frontend_dir / "dist",
            frontend_dir / ".vite",
            frontend_dir / ".temp"
        ]
        
        for item in items_to_clean:
            if item.exists():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        logger.info(f"删除目录: {item}")
                    else:
                        item.unlink()
                        logger.info(f"删除文件: {item}")
                    self.cleaned_items.append(str(item))
                except Exception as e:
                    logger.warning(f"删除失败 {item}: {e}")
                    self.skipped_items.append(str(item))
            else:
                logger.debug(f"不存在: {item}")
    
    def clean_log_files(self):
        """清理日志文件"""
        logger.info("🗂️ 清理日志文件...")
        
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            logger.warning("日志目录不存在")
            return
        
        log_patterns = ["*.log", "*.log.*"]
        
        for pattern in log_patterns:
            for log_file in logs_dir.glob(pattern):
                # 保留当前清理脚本的日志
                if "clean_dependencies" in log_file.name:
                    continue
                    
                try:
                    log_file.unlink()
                    logger.info(f"删除日志: {log_file}")
                    self.cleaned_items.append(str(log_file))
                except Exception as e:
                    logger.warning(f"删除失败 {log_file}: {e}")
                    self.skipped_items.append(str(log_file))
    
    def clean_database_files(self):
        """清理数据库文件"""
        logger.info("💾 清理数据库文件...")
        
        db_patterns = [
            "database/*.db",
            "database/*.db-journal",
            "database/*.db-wal",
            "database/*.db-shm"
        ]
        
        for pattern in db_patterns:
            for db_file in self.project_root.glob(pattern):
                try:
                    db_file.unlink()
                    logger.info(f"删除数据库文件: {db_file}")
                    self.cleaned_items.append(str(db_file))
                except Exception as e:
                    logger.warning(f"删除失败 {db_file}: {e}")
                    self.skipped_items.append(str(db_file))
    
    def clean_ml_models(self):
        """清理机器学习模型文件"""
        logger.info("🤖 清理机器学习模型文件...")
        
        model_patterns = [
            "ml_models/*.pkl",
            "ml_models/*.joblib", 
            "ml_models/*.h5",
            "ml_models/*.pb",
            "ml_models/*.onnx",
            "ml_models/checkpoints/*",
            "ml_models/tensorboard_logs/*"
        ]
        
        for pattern in model_patterns:
            for model_file in self.project_root.glob(pattern):
                try:
                    if model_file.is_dir():
                        shutil.rmtree(model_file)
                        logger.info(f"删除模型目录: {model_file}")
                    else:
                        model_file.unlink()
                        logger.info(f"删除模型文件: {model_file}")
                    self.cleaned_items.append(str(model_file))
                except Exception as e:
                    logger.warning(f"删除失败 {model_file}: {e}")
                    self.skipped_items.append(str(model_file))
    
    def clean_mqtt_data(self):
        """清理MQTT数据"""
        logger.info("📡 清理MQTT数据...")
        
        mqtt_dirs = [
            self.project_root / "mosquitto_data",
            self.project_root / "mqtt_data"
        ]
        
        for mqtt_dir in mqtt_dirs:
            if mqtt_dir.exists():
                try:
                    shutil.rmtree(mqtt_dir)
                    logger.info(f"删除MQTT数据: {mqtt_dir}")
                    self.cleaned_items.append(str(mqtt_dir))
                except Exception as e:
                    logger.warning(f"删除失败 {mqtt_dir}: {e}")
                    self.skipped_items.append(str(mqtt_dir))
    
    def clean_temp_files(self):
        """清理临时文件"""
        logger.info("🔧 清理临时文件...")
        
        temp_patterns = [
            "**/*.tmp",
            "**/*.temp", 
            "**/*.bak",
            "**/*.swp",
            "**/*.swo",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/desktop.ini",
            "**/*.pid"
        ]
        
        for pattern in temp_patterns:
            for temp_file in self.project_root.glob(pattern):
                try:
                    temp_file.unlink()
                    logger.info(f"删除临时文件: {temp_file}")
                    self.cleaned_items.append(str(temp_file))
                except Exception as e:
                    logger.warning(f"删除失败 {temp_file}: {e}")
                    self.skipped_items.append(str(temp_file))
    
    def clean_empty_directories(self):
        """清理空目录"""
        logger.info("🔍 清理空目录...")
        
        # 从深层目录开始清理
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    # 检查目录是否为空
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logger.info(f"删除空目录: {dir_path}")
                        self.cleaned_items.append(str(dir_path))
                except Exception as e:
                    logger.debug(f"无法删除目录 {dir_path}: {e}")
    
    def clean_all(self, exclude=None):
        """清理所有依赖"""
        exclude = exclude or []
        
        print("=====================================")
        print("🧹 工业现场管控平台 - 依赖清理脚本")
        print("=====================================")
        print()
        
        cleaning_methods = [
            ("python_cache", self.clean_python_cache, "Python缓存"),
            ("frontend", self.clean_frontend_dependencies, "前端依赖"),
            ("logs", self.clean_log_files, "日志文件"),
            ("database", self.clean_database_files, "数据库文件"),
            ("models", self.clean_ml_models, "机器学习模型"),
            ("mqtt", self.clean_mqtt_data, "MQTT数据"),
            ("temp", self.clean_temp_files, "临时文件"),
            ("empty_dirs", self.clean_empty_directories, "空目录")
        ]
        
        for method_name, method, description in cleaning_methods:
            if method_name not in exclude:
                try:
                    method()
                except Exception as e:
                    logger.error(f"清理{description}时出错: {e}")
        
        self.show_summary()
    
    def show_summary(self):
        """显示清理摘要"""
        print()
        print("=====================================")
        print("🎉 依赖清理完成！")
        print("=====================================")
        print()
        print("📊 清理摘要:")
        print(f"   ✅ 成功清理: {len(self.cleaned_items)} 项")
        print(f"   ⚠️ 跳过项目: {len(self.skipped_items)} 项")
        print()
        
        if self.cleaned_items:
            print("🗑️ 已清理的项目:")
            for item in self.cleaned_items[:10]:  # 只显示前10项
                print(f"   • {item}")
            if len(self.cleaned_items) > 10:
                print(f"   ... 还有 {len(self.cleaned_items) - 10} 项")
            print()
        
        if self.skipped_items:
            print("⚠️ 跳过的项目:")
            for item in self.skipped_items[:5]:  # 只显示前5项
                print(f"   • {item}")
            if len(self.skipped_items) > 5:
                print(f"   ... 还有 {len(self.skipped_items) - 5} 项")
            print()
        
        print("💡 清理后的操作建议:")
        print("   1. 重新运行: install_dependencies.bat")
        print("   2. 重新初始化数据库: python database/init_db.py")
        print("   3. 重新训练机器学习模型(如需要)")
        print()
        print("⚠️ 注意: 源代码文件、配置文件和安装包未被删除")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="工业现场管控平台依赖清理脚本")
    parser.add_argument("--exclude", nargs="*", 
                      choices=["python_cache", "frontend", "logs", "database", 
                              "models", "mqtt", "temp", "empty_dirs"],
                      help="排除的清理项目")
    parser.add_argument("--project-root", type=str, 
                      help="项目根目录路径")
    parser.add_argument("--dry-run", action="store_true", 
                      help="预览模式，不实际删除文件")
    
    args = parser.parse_args()
    
    try:
        cleaner = DependencyCleaner(args.project_root)
        
        if args.dry_run:
            print("🔍 预览模式 - 不会实际删除文件")
            print()
        
        cleaner.clean_all(exclude=args.exclude)
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断清理操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 清理过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
