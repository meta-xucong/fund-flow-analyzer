#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

client = app.test_client()

# 测试 OPTIONS 请求
print('测试 OPTIONS 请求...')
r = client.options('/api/backtest/delete/test-id')
print('状态码:', r.status_code)
print('响应:', r.get_json())
print('CORS Headers:')
print('  Access-Control-Allow-Origin:', r.headers.get('Access-Control-Allow-Origin'))
print('  Access-Control-Allow-Methods:', r.headers.get('Access-Control-Allow-Methods'))

# 测试 DELETE 请求
print('\n测试 DELETE 请求...')
r2 = client.delete('/api/backtest/delete/2025-03-05_2025-03-05')
print('状态码:', r2.status_code)
print('响应:', r2.get_json())
