#!/usr/bin/env python3
"""
测试新浪数据源 - AKShare的stock_zh_a_spot实际使用新浪
"""
import os
os.environ['NO_PROXY'] = 'sina.com.cn,sinaimg.cn,localhost,127.0.0.1'

import requests
import json
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("新浪数据源测试")
print("=" * 60)

# 新浪API endpoint（AKShare实际使用的）
# 参考: https://vip.stock.finance.sina.com.cn/mkt/#hs_a

print("\n[测试1] 新浪股票列表API")
# 新浪的批量股票数据接口
# 格式: https://hq.sinajs.cn/list=sh600000,sz000001
url = 'https://hq.sinajs.cn/list=sh600000,sz000001,sz002730'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn',
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text[:500]}")
    
    # 新浪返回的是JavaScript变量格式
    if 'var hq_str_' in resp.text:
        print("✓ 新浪API返回了数据！")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# 测试2: 新浪A股全市场数据
print("\n[测试2] 新浪A股全市场数据")
# 获取所有A股代码列表
try:
    # 通过AKShare获取股票列表
    import akshare as ak
    
    # 尝试不同的方法
    print("\n尝试获取股票列表...")
    
    # 方法1: stock_info_a_code_name
    try:
        df = ak.stock_info_a_code_name()
        print(f"stock_info_a_code_name: {len(df)} 只")
        print(f"Sample: {df.head(3).to_dict('records')}")
    except Exception as e:
        print(f"stock_info_a_code_name: {e}")
    
except Exception as e:
    print(f"Error: {e}")

# 测试3: 同花顺的替代方案 - 使用腾讯实时
print("\n[测试3] 腾讯实时数据接口")
# 腾讯实时数据: http://qt.gtimg.cn/q=sh600000,sz000001
tencent_url = 'http://qt.gtimg.cn/q=sh600000,sz000001,sz002730'
try:
    resp = requests.get(tencent_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text[:500]}")
    
    # 腾讯返回的是v_变量格式
    if 'v_' in resp.text:
        print("✓ 腾讯API返回了数据！")
        
        # 解析腾讯数据格式
        lines = resp.text.strip().split(';')
        print(f"\n数据条数: {len(lines)-1}")
        
        # 解析一条数据
        for line in lines[:2]:
            if line.strip():
                print(f"Raw: {line[:100]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
