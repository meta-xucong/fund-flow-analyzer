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

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_port(port=5000):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def kill_port_process(port=5000):
    """关闭占用端口的进程"""
    try:
        if sys.platform == 'win32':
            # 查找占用端口的Python进程
            result = subprocess.run(
                f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /F /PID %a 2>nul',
                shell=True, capture_output=True
            )
        else:
            result = subprocess.run(
                f"lsof -ti tcp:{port} | xargs kill -9 2>/dev/null",
                shell=True, capture_output=True
            )
        time.sleep(1)  # 等待进程终止
        return True
    except:
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

def main():
    """主函数"""
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
            kill_port_process(port)
            if check_port(port):
                print(f"[!] 无法释放端口 {port}，请手动关闭占用进程")
                return 1
            print(f"[*] 端口 {port} 已释放 ✓")
        else:
            print("[!] 端口被占用，无法启动服务")
            return 1
    
    # 创建必要的目录
    os.makedirs('database', exist_ok=True)
    os.makedirs('reports/daily', exist_ok=True)
    os.makedirs('reports/backtest', exist_ok=True)
    
    print(f"[*] 启动服务...")
    print(f"[*] URL: http://localhost:{port}")
    print("\n" + "="*60)
    print("服务已启动!")
    print("="*60)
    print(f"\n访问地址: http://localhost:{port}")
    print("\n按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    # 启动服务器
    try:
        subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'integrated_server.py')
        ])
    except KeyboardInterrupt:
        print("\n\n[*] 正在停止服务...")
        # 确保端口被释放
        kill_port_process(port)
        print("[*] 再见!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
