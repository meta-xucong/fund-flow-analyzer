#!/usr/bin/env python3
"""测试今日报告API"""
import requests

print('[*] Testing today report API...')

try:
    resp = requests.get('http://localhost:5000/api/daily-report/today', timeout=60)
    print(f'Status: {resp.status_code}')
    data = resp.json()
    
    if data.get('success'):
        result = data['data']
        is_open = result.get('is_market_open', True)
        
        if is_open:
            meta = result.get('meta', {})
            print(f"OK - Market open! Data date: {meta.get('data_date', 'unknown')}")
            print(f"Data source: {meta.get('data_source', 'unknown')}")
            momentum = len(result.get('momentum_picks', []))
            reversal = len(result.get('reversal_picks', []))
            print(f"Stocks: momentum={momentum}, reversal={reversal}")
        else:
            print(f"INFO - Market closed: {result.get('message', 'Today is closed')}")
    else:
        print(f"FAILED: {data.get('message')}")
        print(f"Error type: {data.get('error_type', 'unknown')}")
        
except Exception as e:
    print(f"ERROR: {e}")
