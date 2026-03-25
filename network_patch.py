# -*- coding: utf-8 -*-
"""
网络环境修复模块 - 强制绕过Clash代理
"""
import os

# 清除所有代理环境变量
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ[k] = ''

# 方法1: 修改requests默认行为
import requests

# 创建不读取环境变量的session
class NoProxySession(requests.Session):
    def __init__(self):
        super().__init__()
        self.trust_env = False  # 不读取环境变量
        self.proxies = {}       # 空代理

# 替换默认session
original_session = requests.Session
requests.Session = NoProxySession

# 方法2: 修改urllib3
import urllib3
from urllib3.util.connection import create_connection as original_create_connection

def create_connection_patched(address, timeout=None, source_address=None, socket_options=None):
    """强制直接连接，不走代理"""
    import socket
    host, port = address
    sock = socket.create_connection(address, timeout, source_address)
    return sock

# 应用补丁
urllib3.util.connection.create_connection = create_connection_patched

print("[OK] 网络补丁已应用 - Python将直接连接，绕过Clash")
