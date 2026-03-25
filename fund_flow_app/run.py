#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版启动脚本
"""
import os
import sys
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("Fund Flow Analysis System")
    print("=" * 60)
    
    # 创建目录
    os.makedirs('database', exist_ok=True)
    os.makedirs('reports/daily', exist_ok=True)
    os.makedirs('reports/backtest', exist_ok=True)
    
    # 导入并启动
    try:
        from backend.app import app
        print("\nStarting server...")
        print("URL: http://localhost:5000")
        print("\nPress Ctrl+C to stop\n")
        
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
