#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

client = app.test_client()

# 先获取记录
r1 = client.get('/api/backtest/results')
data = r1.get_json()
print('记录数:', len(data.get('data', [])))

# 获取第一个ID
if data.get('data'):
    result_id = data['data'][0]['id']
    print('测试ID:', result_id)
    
    # 删除
    r2 = client.delete(f'/api/backtest/delete/{result_id}')
    print('删除状态码:', r2.status_code)
    print('删除响应:', r2.get_json())
