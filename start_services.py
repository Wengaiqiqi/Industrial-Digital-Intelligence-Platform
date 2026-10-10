#!/usr/bin/env python3
"""
一键启动脚本
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
from loguru import logger

class WindowsServiceManager:
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        self.has_node = False
        
        # 设置控制台编码
        os.system('chcp 65001 >nul')
        
    def check_dependencies(self):
        """检查依赖环境"""
        logger.info("🔍 检查系统依赖...")
        
        # 检查Python
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            logger.info(f"✅ Python版本: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"❌ Python检查失败: {e}")
            return False
            
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            logger.info(f"✅ Node.js版本: {result.stdout.strip()}")
            self.has_node = True
        except Exception:
            logger.warning("⚠️ Node.js未安装，前端将无法启动")
            self.has_node = False
            
        # 检查关键Python依赖
        logger.info("🔍 检查Python依赖包...")
        try:
            import pymodbus
            logger.info(f"✅ pymodbus版本: {pymodbus.__version__}")
        except ImportError:
            logger.error("❌ pymodbus未安装，请运行: pip install pymodbus")
            return False
            
        try:
            import paho.mqtt.client as mqtt
            logger.info("✅ paho-mqtt已安装")
        except ImportError:
            logger.error("❌ paho-mqtt未安装，请运行: pip install paho-mqtt")
            return False
            
        # 检查关键文件
        required_files = [
            'backend/app.py',
            'simulator/device_simulator.py',
            'simulator/modbus_server.py',
            'ml_models/ml_service.py'
        ]
        
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                logger.error(f"❌ 关键文件不存在: {file_path}")
                return False
            else:
                logger.info(f"✅ 文件检查通过: {file_path}")
                
        return True
    
    def start_service(self, name, cmd, cwd=None, delay=2, retry_count=1):
        """启动服务"""
        for attempt in range(retry_count + 1):
            try:
                if cwd is None:
                    cwd = self.base_dir
                
                if attempt > 0:
                    logger.info(f"🔄 重试启动{name} (第{attempt + 1}次尝试)...")
                else:
                    logger.info(f"🚀 启动{name}...")
                
                # 创建PowerShell命令
                cwd_for_ps = str(cwd).replace("'", "''")
                cmdline = subprocess.list2cmdline([str(part) for part in cmd])
                ps_cmd = f"Set-Location -LiteralPath '{cwd_for_ps}'; {cmdline}"
                
                # 启动新的PowerShell窗口
                process = subprocess.Popen([
                    'powershell', '-NoExit', '-Command', ps_cmd
                ], cwd=cwd)
                
                self.processes.append({'name': name, 'process': process})
                logger.info(f"✅ {name}启动成功 (PID: {process.pid})")
                time.sleep(delay)
                return True
                
            except Exception as e:
                logger.error(f"❌ 启动{name}失败 (尝试{attempt + 1}/{retry_count + 1}): {e}")
                if attempt < retry_count:
                    time.sleep(2)
                
        return False
    
    def start_all_services(self):
        """启动所有服务"""
        print("=" * 60)
        print("🚀 工业现场管控平台 - 一键启动")
        print("=" * 60)

        # config/platform.json 的 start 段决定是否启动内置代理和模拟器；接真实设备时关掉它们
        sys.path.insert(0, str(self.base_dir))
        from platform_config import CONFIG
        start_cfg = CONFIG.get('start', {})
        py = sys.executable
        services = []
        if start_cfg.get('embedded_broker', True):
            services.append({'name': 'MQTT代理服务', 'cmd': [py, 'mqtt_broker_embedded.py'], 'cwd': self.base_dir, 'delay': 2})
        services.append({'name': '后端服务', 'cmd': [py, 'app.py'], 'cwd': self.base_dir / 'backend', 'delay': 3})
        if start_cfg.get('device_simulator', True):
            services.append({'name': '设备模拟器', 'cmd': [py, 'device_simulator.py'], 'cwd': self.base_dir / 'simulator', 'delay': 2})
        if start_cfg.get('modbus_simulator', True):
            services.append({'name': 'Modbus服务器', 'cmd': [py, 'modbus_server.py'], 'cwd': self.base_dir / 'simulator', 'delay': 2, 'retry_count': 2})
        if CONFIG.get('modbus', {}).get('enabled'):
            services.append({'name': 'Modbus采集网关', 'cmd': [py, 'modbus_gateway.py'], 'cwd': self.base_dir / 'gateway', 'delay': 2})
        
        # 启动Python服务
        success_count = 0
        for service in services:
            retry_count = service.get('retry_count', 1)
            success = self.start_service(
                service['name'],
                service['cmd'],
                service['cwd'],
                service['delay'],
                retry_count
            )
            if success:
                success_count += 1
            else:
                logger.warning(f"⚠️ {service['name']}启动失败，继续启动其他服务")
        
        # 启动前端服务
        if self.has_node:
            frontend_dir = self.base_dir / 'frontend'
            vite_path = frontend_dir / 'node_modules' / '.bin' / 'vite.cmd'
            
            if vite_path.exists():
                success = self.start_service(
                    '前端服务', 
                    ['cmd', '/c', 'node_modules\\.bin\\vite.cmd', '--host', '0.0.0.0', '--port', '5173'], 
                    frontend_dir, 
                    3
                )
                if success:
                    success_count += 1
            else:
                logger.warning("⚠️ 前端依赖未安装，请运行: npm install")
                print("   💡 在 frontend 文件夹中运行: npm install")
        else:
            logger.warning("⚠️ Node.js未安装，跳过前端启动")
        
        print("=" * 60)
        print(f"✅ 启动完成！成功启动 {success_count} 个服务")
        print("=" * 60)
        
        self.show_info()
    
    def show_info(self):
        """显示访问信息"""
        print("\n🎉 工业现场管控平台启动成功！")
        print("\n📍 访问地址：")
        print("   🌐 前端界面: http://localhost:5173")
        print("   🔧 后端API:  http://localhost:5055")
        print("   ❤️  健康检查: http://localhost:5055/api/health")
        print("\n📊 系统功能：")
        print("   ✅ 实时设备监控")
        print("   ✅ 数据采集与存储")
        print("   ✅ 智能报警管理")
        print("   ✅ 机器学习预测")
        print("   ✅ Modbus通信协议")
        print("   ✅ 3D场景可视化")
        print("\n💡 使用提示：")
        print("   • 所有服务在独立窗口中运行")
        print("   • 可在任务栏查看各服务状态")
        print("   • 关闭服务窗口即可停止对应服务")
        print("   • 按 Ctrl+C 退出此管理器")
        
        # 等待服务完全启动
        print("\n⏰ 等待服务完全启动...")
        for i in range(5, 0, -1):
            print(f"   {i}秒后自动打开浏览器...")
            time.sleep(1)
        
        # 自动打开浏览器
        try:
            webbrowser.open('http://localhost:5173')
            logger.info("✅ 已自动打开浏览器")
        except Exception as e:
            logger.warning(f"⚠️ 无法自动打开浏览器: {e}")
            print("   请手动访问: http://localhost:5173")
    
    def monitor_services(self):
        """监控服务状态"""
        print("\n🔍 服务监控模式 (按 Ctrl+C 退出)")
        print("-" * 40)
        
        try:
            while True:
                time.sleep(10)
                running_count = 0
                
                for service in self.processes:
                    try:
                        if service['process'].poll() is None:
                            running_count += 1
                        else:
                            logger.warning(f"⚠️ {service['name']} 已停止运行")
                    except Exception:
                        pass
                
                logger.info(f"📊 当前运行中的服务: {running_count}/{len(self.processes)}")
                
        except KeyboardInterrupt:
            logger.info("📴 收到退出信号...")
        except Exception as e:
            logger.error(f"❌ 监控过程中出错: {e}")
    
    def run(self):
        """主运行函数"""
        try:
            print("🎯 工业现场管控平台服务管理器")
            print("=" * 60)
            
            # 检查依赖
            if not self.check_dependencies():
                print("\n❌ 依赖检查失败，请解决上述问题后重试")
                input("按回车键退出...")
                return False
            
            print("\n✅ 依赖检查通过，开始启动服务...")
            time.sleep(2)
            
            # 启动所有服务
            self.start_all_services()
            
            # 监控服务状态
            self.monitor_services()
                
        except KeyboardInterrupt:
            logger.info("📴 用户中断启动...")
        except Exception as e:
            logger.error(f"❌ 启动过程中出错: {e}")
        finally:
            print("\n👋 感谢使用工业现场管控平台！")

def main():
    """主函数"""
    # 配置日志
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "service_manager.log", 
        rotation="1 day",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    manager = WindowsServiceManager()
    manager.run()

if __name__ == "__main__":
    main()
