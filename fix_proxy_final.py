#!/usr/bin/env python3
"""
修复代理问题 - 必须在导入requests之前设置NO_PROXY
"""
import os

# 关键：必须在导入任何网络库之前设置！
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['ALL_PROXY'] = ''
os.environ['all_proxy'] = ''

# 然后设置NO_PROXY
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn'
os.environ['no_proxy'] = 'localhost,127.0.0.1,eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn'

# 现在导入requests
import requests
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("修复代理后的测试")
print("=" * 60)

# 验证代理设置
print(f"\nHTTP_PROXY: '{os.environ.get('HTTP_PROXY')}'")
print(f"NO_PROXY: '{os.environ.get('NO_PROXY')}'")
print(f"\nrequests代理: {requests.utils.getproxies()}")

# 创建session并禁用代理
session = requests.Session()
session.trust_env = False  # 禁用系统代理

print("\n" + "=" * 60)
print("测试1: 使用session.trust_env=False")
print("=" * 60)

url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5'
try:
    resp = session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text[:300]}")
    if resp.status_code == 200:
        print("\n✓ 东财API连接成功！")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")

# 测试2: 使用禁用代理的request
print("\n" + "=" * 60)
print("测试2: 使用proxies=None")
print("=" * 60)

try:
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, proxies={
        'http': None,
        'https': None
    })
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("\n✓ 东财API连接成功！")
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")
