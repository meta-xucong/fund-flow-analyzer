#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版HTTP服务器 - 用于测试前端
"""
import http.server
import socketserver
import os
import webbrowser
import threading
import time

PORT = 8080
DIRECTORY = "frontend"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

print("=" * 60)
print("Fund Flow App - 前端测试服务器")
print("=" * 60)
print(f"\n启动目录: {DIRECTORY}")
print(f"访问地址: http://localhost:{PORT}")
print("\n正在启动...")

def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")
    print("\n已自动打开浏览器")

# 在后台打开浏览器
threading.Thread(target=open_browser, daemon=True).start()

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"\n服务已启动: http://localhost:{PORT}")
    print("按 Ctrl+C 停止服务\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务已停止")
