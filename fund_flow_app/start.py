#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘前资金流向分析系统 - 启动脚本
"""
import os
import sys
import webbrowser
import time
import threading

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           盘前资金流向分析系统 v1.0.0                            ║
║                                                                  ║
║   Pre-market Fund Flow Analysis System                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

功能:
  [1] 每日9:25自动推送分析报告
  [2] 自定义日期范围历史回测
  [3] 苹果风格磨砂玻璃UI界面

正在启动服务...
"""
    print(banner)

def check_dependencies():
    """检查依赖"""
    print("[*] 检查依赖...")
    required = ['flask', 'pandas', 'akshare', 'requests']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"[!] 缺少依赖: {', '.join(missing)}")
        print(f"[*] 请运行: pip install -r requirements.txt")
        return False
    
    print("[*] 依赖检查通过 ✓")
    return True

def start_backend():
    """启动后端服务"""
    print("[*] 启动后端服务...")
    print("[*] API地址: http://localhost:5000")
    
    # 使用 integrated_server.py 而不是 backend/app.py
    def run_flask():
        import subprocess
        import atexit
        
        # 使用subprocess启动服务器，这样更容易管理
        proc = subprocess.Popen(
            [sys.executable, '-c', '''
import sys
sys.path.insert(0, ".")
from integrated_server import app
app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)
'''],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        # 注册退出时清理
        def cleanup():
            print("\n[*] 正在终止后端进程...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
            print("[*] 后端进程已终止")
        
        atexit.register(cleanup)
        
        # 等待进程结束
        try:
            proc.wait()
        except KeyboardInterrupt:
            cleanup()
    
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    
    return thread

def open_browser():
    """打开浏览器"""
    time.sleep(2)  # 等待服务启动
    url = 'http://localhost:5000'
    
    # 获取前端文件路径
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend', 'index.html')
    
    if os.path.exists(frontend_path):
        # 如果前端文件存在，直接打开本地文件
        webbrowser.open(f'file://{os.path.abspath(frontend_path)}')
        print(f"[*] 已打开浏览器")
    else:
        webbrowser.open(url)
        print(f"[*] 已打开浏览器: {url}")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 创建必要的目录
    os.makedirs('database', exist_ok=True)
    os.makedirs('reports/daily', exist_ok=True)
    os.makedirs('reports/backtest', exist_ok=True)
    
    # 启动后端
    backend_thread = start_backend()
    
    # 打开浏览器
    open_browser()
    
    print("\n" + "="*60)
    print("服务已启动!")
    print("="*60)
    print("\n访问地址:")
    print("  - Web界面: http://localhost:5000 或自动打开的浏览器窗口")
    print("  - API文档: http://localhost:5000/api")
    print("\n按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    try:
        # 保持程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[*] 正在停止服务...")
        print("[*] 再见!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
