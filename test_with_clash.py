#!/usr/bin/env python3
"""
在Clash开启的情况下测试绕过代理的方案
"""
import os

# 方案1: 清除所有代理环境变量
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ALL_PROXY', None)

# 设置NO_PROXY
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com'
os.environ['no_proxy'] = 'localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com'

import requests
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("Clash开启时的绕过测试")
print("=" * 60)

# 检查当前代理设置
print(f"\n当前代理设置:")
print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
print(f"  http_proxy: {os.environ.get('http_proxy', 'Not set')}")
print(f"  NO_PROXY: {os.environ.get('NO_PROXY', 'Not set')}")

# 方案1: 使用session，trust_env=False
print("\n" + "=" * 60)
print("[方案1] session.trust_env = False")
print("=" * 60)

session = requests.Session()
session.trust_env = False  # 禁用环境变量中的代理设置

url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5'
try:
    resp = session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Content: {resp.text[:200]}")
        print("\n✓ 成功！session.trust_env = False 可以绕过Clash")
    else:
        print(f"Unexpected status: {resp.status_code}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")

# 方案2: 显式设置proxies=None
print("\n" + "=" * 60)
print("[方案2] 显式设置 proxies=None")
print("=" * 60)

try:
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, proxies={
        'http': None,
        'https': None
    })
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Content: {resp.text[:200]}")
        print("\n✓ 成功！proxies=None 可以绕过Clash")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")

# 方案3: 使用urllib直接请求（绕过requests）
print("\n" + "=" * 60)
print("[方案3] 使用urllib（绕过requests）")
print("=" * 60)

import urllib.request
import ssl

try:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    # 创建opener，不设置代理
    opener = urllib.request.build_opener()
    resp = opener.open(req, timeout=10)
    data = resp.read().decode('utf-8')
    print(f"Status: {resp.status}")
    print(f"Content: {data[:200]}")
    print("\n✓ 成功！urllib 可以绕过Clash")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 60)
