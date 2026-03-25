#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端服务器启动脚本 - 确保正确的工作目录
"""
import http.server
import socketserver
import os
import sys
import webbrowser
import time
import threading

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(SCRIPT_DIR, 'frontend')
PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

print("=" * 60)
print("Fund Flow App - Frontend Server")
print("=" * 60)
print(f"\nServing from: {FRONTEND_DIR}")
print(f"Port: {PORT}")
print(f"URL: http://localhost:{PORT}")
print("\nPress Ctrl+C to stop\n")

# 验证文件存在
index_file = os.path.join(FRONTEND_DIR, 'index.html')
if not os.path.exists(index_file):
    print(f"ERROR: index.html not found at {index_file}")
    sys.exit(1)

print(f"✓ index.html found")
print(f"✓ Starting server...\n")

# 自动打开浏览器
def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")
    print("Browser opened automatically")

threading.Thread(target=open_browser, daemon=True).start()

# 启动服务器
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
