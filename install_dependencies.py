#!/usr/bin/env python3
"""
工业数智平台 - 依赖安装脚本 (Python版本)
支持Windows、Linux、macOS跨平台安装
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
from typing import List, Optional, Tuple

class DependencyInstaller:
    """依赖安装管理器"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.install_dir = self.script_dir / "所需安装"
        self.platform = platform.system().lower()
        self.python_path = None
        self.node_path = None
        
    def print_header(self):
        """打印脚本头部信息"""
        print("=" * 50)
        print("🏭 工业数智平台 - 依赖安装脚本")
        print("=" * 50)
        print()
        
    def check_python_environment(self) -> bool:
        """检查Python环境"""
        print("[1/6] 🔍 检查Python环境...")
        
        # 尝试当前Python环境
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True, check=True)
            self.python_path = sys.executable
            print(f"✅ 当前Python环境可用: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            pass
            
        # 尝试系统Python
        for python_cmd in ["python", "python3", "py"]:
            try:
                result = subprocess.run([python_cmd, "--version"], 
                                      capture_output=True, text=True, check=True)
                if "Python 3." in result.stdout:
                    self.python_path = python_cmd
                    print(f"✅ 系统Python可用: {result.stdout.strip()}")
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
                
        # 尝试常见的Anaconda路径
        anaconda_paths = self._get_anaconda_paths()
        for path in anaconda_paths:
            if path.exists():
                try:
                    result = subprocess.run([str(path), "--version"], 
                                          capture_output=True, text=True, check=True)
                    self.python_path = str(path)
                    print(f"✅ 找到Python环境: {path}")
                    print(f"   版本: {result.stdout.strip()}")
                    return True
                except subprocess.CalledProcessError:
                    continue
                    
        print("❌ 未找到Python环境！")
        print("💡 请安装Python 3.8+ 或 Anaconda")
        print("   下载地址: https://www.python.org/downloads/")
        print("            https://www.anaconda.com/download/")
        return False
        
    def _get_anaconda_paths(self) -> List[Path]:
        """获取可能的Anaconda路径"""
        paths = []
        if self.platform == "windows":
            base_paths = [
                Path("D:/Anaconda3"),
                Path("C:/Anaconda3"),
                Path.home() / "anaconda3",
                Path("C:/ProgramData/Anaconda3"),
            ]
            for base in base_paths:
                paths.extend([
                    base / "python.exe",
                    base / "envs" / "normal" / "python.exe",
                    base / "envs" / "base" / "python.exe",
                ])
        else:
            base_paths = [
                Path.home() / "anaconda3",
                Path.home() / "miniconda3",
                Path("/opt/anaconda3"),
                Path("/usr/local/anaconda3"),
            ]
            for base in base_paths:
                paths.extend([
                    base / "bin" / "python",
                    base / "envs" / "normal" / "bin" / "python",
                ])
        return paths
        
    def install_python_dependencies(self) -> bool:
        """安装Python依赖"""
        print("\n[2/6] 📦 安装Python依赖...")
        
        # 升级pip
        print("正在升级pip...")
        try:
            subprocess.run([self.python_path, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True)
            print("✅ pip升级完成")
        except subprocess.CalledProcessError:
            print("⚠️ pip升级失败，继续安装依赖...")
            
        # 安装依赖包
        requirements_file = self.script_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt文件不存在！")
            return False
            
        print("正在安装核心依赖包...")
        try:
            subprocess.run([self.python_path, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True)
            print("✅ Python依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ Python依赖安装失败！")
            print("💡 请检查网络连接或使用国内镜像源:")
            print(f"   {self.python_path} -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
            return False
            
    def check_nodejs_environment(self) -> bool:
        """检查Node.js环境"""
        print("\n[3/6] 🟢 检查Node.js环境...")
        
        # 检查Node.js
        try:
            node_result = subprocess.run(["node", "--version"], 
                                       capture_output=True, text=True, check=True)
            npm_result = subprocess.run(["npm", "--version"], 
                                      capture_output=True, text=True, check=True)
            self.node_path = "node"
            print("✅ Node.js环境正常")
            print(f"   Node.js: {node_result.stdout.strip()}")
            print(f"   npm: {npm_result.stdout.strip()}")
            
            # 检查npm配置
            try:
                registry_result = subprocess.run(["npm", "config", "get", "registry"], 
                                               capture_output=True, text=True, check=True)
                print(f"   当前npm源: {registry_result.stdout.strip()}")
                print("💡 如果下载慢，可使用淘宝镜像源:")
                print("   npm config set registry https://registry.npmmirror.com")
            except subprocess.CalledProcessError:
                pass
                
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        print("❌ Node.js未安装！")
        print("\n📁 检查本地安装文件...")
        
        # 查找安装文件
        install_files = self._find_nodejs_installers()
        if install_files:
            print("✅ 找到Node.js安装包:")
            for file in install_files:
                print(f"   {file.name}")
            print("\n💡 请按以下步骤安装:")
            print(f"   1. 打开文件夹: {self.install_dir}")
            print("   2. 运行安装包")
            print("   3. 按照向导完成安装")
            print("   4. 重启命令行窗口")
            print("   5. 重新运行此脚本")
            
            if self.platform == "windows":
                os.startfile(str(self.install_dir))
        else:
            print("❌ 未找到本地安装文件！")
            print("💡 请下载并安装Node.js:")
            print("   1. 访问: https://nodejs.org/")
            print("   2. 下载LTS版本")
            print(f"   3. 将安装包放入: {self.install_dir}")
            
        return False
        
    def _find_nodejs_installers(self) -> List[Path]:
        """查找Node.js安装文件"""
        installers = []
        if self.install_dir.exists():
            if self.platform == "windows":
                installers.extend(self.install_dir.glob("node-v*.msi"))
                installers.extend(self.install_dir.glob("node-v*.exe"))
            elif self.platform == "darwin":  # macOS
                installers.extend(self.install_dir.glob("node-v*.pkg"))
            else:  # Linux
                installers.extend(self.install_dir.glob("node-v*.tar.gz"))
        return installers
        
    def install_frontend_dependencies(self) -> bool:
        """安装前端依赖"""
        print("\n[4/6] 🌐 安装前端依赖...")
        
        frontend_dir = self.script_dir / "frontend"
        if not frontend_dir.exists():
            print("❌ 前端目录不存在！")
            return False
            
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            print("❌ package.json文件不存在！")
            return False
            
        print("正在安装前端包...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ 前端依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败！")
            print("💡 尝试解决方案:")
            print("   1. 清理缓存: npm cache clean --force")
            print("   2. 删除node_modules文件夹")
            print("   3. 重新安装: npm install")
            return False
            
    def check_mqtt_broker(self) -> bool:
        """检查MQTT代理"""
        print("\n[5/6] 📡 检查MQTT代理...")
        
        # 检查Mosquitto
        try:
            result = subprocess.run(["mosquitto", "-h"], 
                                  capture_output=True, text=True, check=True)
            print("✅ Mosquitto已安装")
            # 尝试获取版本信息
            for line in result.stderr.split('\n'):
                if 'version' in line.lower():
                    print(f"   {line.strip()}")
                    break
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        print("⚠️ Mosquitto未安装 (使用内置MQTT代理)")
        
        # 查找Mosquitto安装文件
        mosquitto_files = self._find_mosquitto_installers()
        if mosquitto_files:
            print("\n📁 找到Mosquitto安装包:")
            for file in mosquitto_files:
                print(f"   {file.name}")
            print("\n💡 可选安装Mosquitto获得更好性能:")
            print(f"   1. 打开文件夹: {self.install_dir}")
            print("   2. 运行安装包")
            print("   3. 按照向导完成安装")
            print("   4. 添加到系统PATH环境变量")
            print("\n⏭️ 跳过此步骤，系统将使用内置MQTT代理")
        else:
            print("❌ 未找到Mosquitto安装文件")
            print("💡 可从以下地址下载:")
            print("   https://mosquitto.org/download/")
            print(f"   或将安装包放入: {self.install_dir}")
            print("\n⏭️ 系统将使用内置MQTT代理")
            
        return True  # 内置代理可用，返回True
        
    def _find_mosquitto_installers(self) -> List[Path]:
        """查找Mosquitto安装文件"""
        installers = []
        if self.install_dir.exists():
            if self.platform == "windows":
                installers.extend(self.install_dir.glob("mosquitto-*.exe"))
                installers.extend(self.install_dir.glob("mosquitto-*.msi"))
            elif self.platform == "darwin":  # macOS
                installers.extend(self.install_dir.glob("mosquitto-*.pkg"))
            else:  # Linux
                installers.extend(self.install_dir.glob("mosquitto-*.tar.gz"))
                installers.extend(self.install_dir.glob("mosquitto-*.deb"))
                installers.extend(self.install_dir.glob("mosquitto-*.rpm"))
        return installers
        
    def check_project_integrity(self) -> bool:
        """检查项目文件完整性"""
        print("\n[6/6] 🔧 环境配置检查...")
        print("检查项目文件完整性...")
        
        # 检查关键文件
        critical_files = [
            "backend/app.py",
            "mqtt_broker_embedded.py",
            "start_services.py",
            "requirements.txt",
        ]
        
        missing_files = []
        for file_path in critical_files:
            full_path = self.script_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            print("❌ 缺少关键文件:")
            for file in missing_files:
                print(f"   {file}")
            return False
            
        # 创建必要目录
        dirs_to_create = ["logs", "database"]
        for dir_name in dirs_to_create:
            dir_path = self.script_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            
        print("✅ 项目文件检查完成")
        return True
        
    def print_summary(self, results: dict):
        """打印安装摘要"""
        print("\n" + "=" * 50)
        print("🎉 依赖安装和检查完成！")
        print("=" * 50)
        print("\n📊 环境摘要:")
        
        status_map = {True: "✅", False: "❌"}
        
        print(f"   {status_map[results['python']]} Python环境: {'已配置' if results['python'] else '未配置'}")
        print(f"   {status_map[results['python_deps']]} Python依赖: {'已安装' if results['python_deps'] else '安装失败'}")
        print(f"   {status_map[results['nodejs']]} Node.js环境: {'已配置' if results['nodejs'] else '未配置'}")
        print(f"   {status_map[results['frontend']]} 前端依赖: {'已安装' if results['frontend'] else '安装失败'}")
        print(f"   {status_map[results['mqtt']]} MQTT代理: {'已配置' if results['mqtt'] else '配置失败'}")
        print(f"   {status_map[results['project']]} 项目文件: {'完整' if results['project'] else '不完整'}")
        
        if all(results.values()):
            print("\n🚀 现在可以启动平台:")
            print("   方式1: 运行 python start_services.py")
            if self.platform == "windows":
                print("   方式2: 双击运行 start_services.py")
            print("\n💡 首次运行可能需要防火墙权限确认")
        else:
            print("\n⚠️ 部分组件安装失败，请检查上述错误信息")
            
    def run(self) -> bool:
        """运行安装流程"""
        self.print_header()
        
        results = {
            'python': False,
            'python_deps': False,
            'nodejs': False,
            'frontend': False,
            'mqtt': False,
            'project': False
        }
        
        # 执行安装步骤
        results['python'] = self.check_python_environment()
        if results['python']:
            results['python_deps'] = self.install_python_dependencies()
            
        results['nodejs'] = self.check_nodejs_environment()
        if results['nodejs']:
            results['frontend'] = self.install_frontend_dependencies()
            
        results['mqtt'] = self.check_mqtt_broker()
        results['project'] = self.check_project_integrity()
        
        # 打印摘要
        self.print_summary(results)
        
        return all(results.values())

def main():
    """主函数"""
    try:
        installer = DependencyInstaller()
        success = installer.run()
        
        if not success:
            print("\n按Enter键退出...")
            input()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ 安装过程被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安装过程发生错误: {e}")
        print("\n按Enter键退出...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    main()
