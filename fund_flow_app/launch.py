#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘前资金流向分析系统 - 启动器
"""
import os
import sys
import time
import socket
import signal
import warnings
import psutil
import webbrowser
import threading

# 忽略警告
warnings.filterwarnings('ignore')

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = get_script_dir()
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

def check_port(port=5000):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def kill_port_process_safe(port=5000):
    """安全地关闭占用端口的进程"""
    my_pid = os.getpid()
    killed = []
    
    try:
        for conn in psutil.net_connections():
            if hasattr(conn, 'laddr') and conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid)
                    if proc.pid != my_pid:
                        proc.terminate()
                        killed.append(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        if killed:
            time.sleep(1)
            for pid in killed:
                try:
                    p = psutil.Process(pid)
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
        
        return len(killed) > 0
    except Exception as e:
        print(f"[!] 清理端口时出错: {e}")
        return False

def print_banner():
    print("""
============================================================
          盘前资金流向分析系统 v1.0.0
============================================================

功能:
  [1] 每日9:25自动推送分析报告
  [2] 自定义日期范围历史回测
  [3] 苹果风格磨砂玻璃UI界面

============================================================
""")

def main():
    print_banner()
    
    port = 5000
    
    # 检查端口
    if check_port(port):
        print(f"[!] 端口 {port} 已被占用")
        response = input(f"[*] 是否终止占用端口 {port} 的进程? (y/n): ")
        if response.lower() == 'y':
            print(f"[*] 正在释放端口 {port}...")
            if kill_port_process_safe(port):
                print(f"[*] 端口 {port} 已释放")
            time.sleep(1)
            if check_port(port):
                print(f"[!] 无法释放端口 {port}")
                return 1
        else:
            print("[!] 端口被占用，无法启动服务")
            return 1
    
    # 创建必要的目录
    for dir_name in ['database', 'reports/daily', 'reports/backtest', 'logs']:
        os.makedirs(dir_name, exist_ok=True)
    
    print(f"[*] 启动服务...")
    print(f"[*] URL: http://localhost:{port}")
    print("\n============================================================")
    print("服务已启动!")
    print("============================================================")
    print(f"\n访问地址: http://localhost:{port}")
    print("\n按 Ctrl+C 停止服务")
    print("============================================================\n")
    
    # 延迟2秒后自动打开浏览器
    def open_browser():
        time.sleep(2)
        url = f"http://localhost:{port}"
        print(f"[*] 正在打开浏览器: {url}")
        webbrowser.open(url)
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 直接导入并运行服务器
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
    finally:
        # 确保端口被释放
        kill_port_process_safe(port)
        print("[*] 再见!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
