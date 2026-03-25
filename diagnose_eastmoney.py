#!/usr/bin/env python3
"""
诊断东财API连接问题
"""
import os
os.environ['NO_PROXY'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com'

import requests
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("东财API诊断")
print("=" * 60)

# 东财历史数据API的实际URL
# 参考: https://push2his.eastmoney.com/api/qt/stock/kline/get
url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
params = {
    'fields1': 'f1,f2,f3,f4,f5,f6',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
    'ut': '7eea3edcaed734bea9cbfc24409ed989',
    'klt': '101',  # 日线
    'fqt': '1',    # 前复权
    'secid': '0.000001',  # 平安银行
    'beg': '20250319',
    'end': '20250319',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://quote.eastmoney.com/',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

print(f"\n[测试1] 直接请求东财API")
print(f"URL: {url}")
print(f"Params: {params}")

try:
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试2: 不带headers
print(f"\n[测试2] 不带headers")
try:
    resp = requests.get(url, params=params, timeout=10)
    print(f"Status: {resp.status_code}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试3: 检查是否被IP封禁 - 使用不同的User-Agent
print(f"\n[测试3] 使用不同User-Agent")
headers_v2 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Referer': 'https://quote.eastmoney.com/',
}
try:
    resp = requests.get(url, params=params, headers=headers_v2, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content preview: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试4: 检查TCP连接问题
print(f"\n[测试4] 检查DNS和连接")
import socket
try:
    ip = socket.gethostbyname('push2his.eastmoney.com')
    print(f"push2his.eastmoney.com IP: {ip}")
except Exception as e:
    print(f"DNS Error: {e}")

print("\n" + "=" * 60)
