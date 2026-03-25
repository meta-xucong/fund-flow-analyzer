#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口检测和清理工具
"""
import sys
import subprocess
import os

def check_port(port=5000):
    """检查端口是否被占用"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0  # 0 表示端口被占用
    except Exception as e:
        print(f"[!] 检查端口时出错: {e}")
        return False

def kill_process_on_port(port=5000):
    """关闭占用指定端口的进程"""
    print(f"[*] 查找占用端口 {port} 的进程...")
    
    try:
        if sys.platform == 'win32':
            # Windows: 使用 netstat 查找 PID
            result = subprocess.run(
                ['netstat', '-ano', '|', 'findstr', f':{port}'],
                capture_output=True, text=True, shell=True
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                pids = set()
                for line in lines:
                    if f':{port}' in line and ('LISTENING' in line or 'ESTABLISHED' in line):
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            if pid.isdigit():
                                pids.add(pid)
                
                if pids:
                    print(f"[*] 发现占用进程 PID: {', '.join(pids)}")
                    for pid in pids:
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], check=False, capture_output=True)
                            print(f"[*] 已终止进程 PID {pid}")
                        except Exception as e:
                            print(f"[!] 终止进程 {pid} 失败: {e}")
                    return True
                else:
                    print(f"[*] 未找到占用端口 {port} 的进程")
                    return False
            else:
                print(f"[*] 端口 {port} 未被占用")
                return False
        else:
            # Linux/Mac: 使用 lsof
            result = subprocess.run(
                ['lsof', '-ti', f'tcp:{port}'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout:
                pids = result.stdout.strip().split('\n')
                print(f"[*] 发现占用进程 PID: {', '.join(pids)}")
                for pid in pids:
                    try:
                        os.kill(int(pid), 9)
                        print(f"[*] 已终止进程 PID {pid}")
                    except Exception as e:
                        print(f"[!] 终止进程 {pid} 失败: {e}")
                return True
            else:
                print(f"[*] 端口 {port} 未被占用")
                return False
                
    except Exception as e:
        print(f"[!] 清理端口时出错: {e}")
        return False

def main():
    """主函数"""
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print(f"[*] 检查端口 {port}...")
    
    if check_port(port):
        print(f"[!] 端口 {port} 已被占用")
        response = input(f"[*] 是否终止占用端口 {port} 的进程? (y/n): ")
        if response.lower() == 'y':
            if kill_process_on_port(port):
                print(f"[OK] 端口 {port} 已释放")
            else:
                print(f"[!] 无法释放端口 {port}")
        else:
            print("[*] 操作已取消")
    else:
        print(f"[*] 端口 {port} 未被占用，可以启动服务")

if __name__ == '__main__':
    main()
