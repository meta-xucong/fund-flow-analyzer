#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试删除功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用 Flask 测试客户端
from backend.app import app

client = app.test_client()

# 1. 先获取列表
print('1. 获取回测列表...')
r = client.get('/api/backtest/results')
print(f'   状态码: {r.status_code}')
data = r.get_json()

if data.get('success') and len(data.get('data', [])) > 0:
    item = data['data'][0]
    result_id = item['id']
    print(f'   找到记录: {result_id}')
    
    # 2. 测试删除
    print(f'\n2. 删除记录: {result_id}...')
    r2 = client.delete(f'/api/backtest/delete/{result_id}')
    print(f'   状态码: {r2.status_code}')
    print(f'   响应: {r2.get_json()}')
    
    # 3. 再次获取列表
    print(f'\n3. 再次获取列表确认...')
    r3 = client.get('/api/backtest/results')
    data3 = r3.get_json()
    remaining = len(data3.get('data', []))
    print(f'   剩余记录数: {remaining}')
else:
    print('   没有记录可删除')
