#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller运行时钩子 - 设置环境和安全检查
"""
import os
import sys
import signal
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 设置环境变量
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1'
os.environ['TQDM_DISABLE'] = '1'
os.environ['FLASK_ENV'] = 'production'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'  # 禁用Flask重载

def get_executable_dir():
    """获取EXE所在目录"""
    if getattr(sys, 'frozen', False):
        # 运行在EXE中
        return os.path.dirname(sys.executable)
    else:
        # 运行在Python中
        return os.path.dirname(os.path.abspath(__file__))

# 设置工作目录
exe_dir = get_executable_dir()
os.chdir(exe_dir)

# 创建必要的目录
for dir_name in ['database', 'reports', 'logs']:
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

# 处理信号
def signal_handler(sig, frame):
    """信号处理器"""
    print('\n[*] 收到关闭信号，正在退出...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("[*] 运行时环境初始化完成")
