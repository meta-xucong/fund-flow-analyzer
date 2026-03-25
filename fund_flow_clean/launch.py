#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘前资金流向分析系统 - 启动器（带端口检测）
"""
import os
import sys
import time
import subprocess
import socket
import signal
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 获取EXE所在目录
def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# 设置工作目录
exe_dir = get_executable_dir()
os.chdir(exe_dir)

# 添加项目路径
sys.path.insert(0, exe_dir)

def check_port(port=5000):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def kill_port_process_safe(port=5000):
    """
    安全地关闭占用端口的进程（不会杀死自身进程）
    """
    import psutil
    
    my_pid = os.getpid()
    killed = []
    
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    # 确保不杀死自身进程
                    if proc.pid != my_pid:
                        proc.terminate()
                        killed.append(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        # 等待进程终止
        if killed:
            time.sleep(1)
            
        return len(killed) > 0
    except Exception as e:
        print(f"[!] 清理端口时出错: {e}")
        return False

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
    
    print("[*] 依赖检查通过")
    return True

def signal_handler(sig, frame):
    """信号处理器"""
    print('\n[*] 收到关闭信号，正在退出...')
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    port = 5000
    
    # 检查端口
    if check_port(port):
        print(f"[!] 端口 {port} 已被占用")
        response = input(f"[*] 是否终止占用端口 {port} 的进程? (y/n): ")
        if response.lower() == 'y':
            print(f"[*] 正在释放端口 {port}...")
            if kill_port_process_safe(port):
                print(f"[*] 端口 {port} 已释放")
            if check_port(port):
                print(f"[!] 无法释放端口 {port}，请手动关闭占用进程")
                return 1
        else:
            print("[!] 端口被占用，无法启动服务")
            return 1
    
    # 创建必要的目录
    for dir_name in ['database', 'reports/daily', 'reports/backtest', 'logs']:
        os.makedirs(dir_name, exist_ok=True)
    
    print(f"[*] 启动服务...")
    print(f"[*] URL: http://localhost:{port}")
    print("\n" + "="*60)
    print("服务已启动!")
    print("="*60)
    print(f"\n访问地址: http://localhost:{port}")
    print("\n按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    # 启动服务器（直接导入运行）
    try:
        from integrated_server import app
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            threaded=True, 
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n[*] 正在停止服务...")
        kill_port_process_safe(port)
        print("[*] 再见!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
