#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试 CORS 头
from backend.app import app

client = app.test_client()

# 测试 OPTIONS 请求
print('测试 OPTIONS 请求...')
r = client.options('/api/backtest/delete/test-id')
print('状态码:', r.status_code)
print('CORS Headers:')
print('  Access-Control-Allow-Origin:', r.headers.get('Access-Control-Allow-Origin'))
print('  Access-Control-Allow-Methods:', r.headers.get('Access-Control-Allow-Methods'))

# 获取一个真实ID
print('\n获取回测列表...')
r2 = client.get('/api/backtest/results')
data = r2.get_json()
print('记录数:', len(data.get('data', [])))

if data.get('data'):
    result_id = data['data'][0]['id']
    print('测试ID:', result_id)
    
    # 测试 DELETE
    print('\n测试 DELETE 请求...')
    r3 = client.delete(f'/api/backtest/delete/{result_id}')
    print('状态码:', r3.status_code)
    print('响应:', r3.get_json())
