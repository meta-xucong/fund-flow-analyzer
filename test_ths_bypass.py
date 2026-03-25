#!/usr/bin/env python3
"""
测试同花顺反爬虫突破方案
"""
import os
os.environ['NO_PROXY'] = '10jqka.com.cn,q.10jqka.com.cn,localhost,127.0.0.1'

import requests
import json
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("同花顺反爬虫突破测试")
print("=" * 60)

# 测试1: 直接HTTP请求
print("\n[测试1] 直接HTTP请求")
url = 'http://q.10jqka.com.cn/api.php?t=indexflash&page=1&per_page=20'
try:
    resp = requests.get(url, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
    print(f"Preview: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试2: 带浏览器Headers
print("\n[测试2] 带浏览器Headers")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'http://q.10jqka.com.cn/',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'keep-alive',
}
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Preview: {resp.text[:300]}")
    
    # 尝试解析JSON
    try:
        data = resp.json()
        print(f"JSON解析成功: {len(data)} keys")
    except:
        print("不是JSON格式")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试3: 带Cookie
print("\n[测试3] 带Cookie（模拟已登录用户）")
cookies = {
    'v': 'A4y1C1PoW1P9PdFPJ9PoWP9PoW9BciWucCwXcvKcv8P9P8oW9Po',  # 模拟cookie
}
try:
    session = requests.Session()
    # 先访问主页获取cookie
    session.get('http://q.10jqka.com.cn/', headers=headers, timeout=5)
    
    resp = session.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Preview: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试4: AKShare的stock_zh_a_spot实际调用的URL
print("\n[测试4] AKShare实际调用分析")
try:
    import akshare as ak
    # 检查AKShare源码使用的URL
    import inspect
    source = inspect.getsource(ak.stock_zh_a_spot)
    # 查找URL
    import re
    urls = re.findall(r'https?://[^\s\'\"]+', source)
    print(f"AKShare使用的URLs: {list(set(urls))[:5]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
