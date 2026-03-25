# -*- coding: utf-8 -*-
"""
修复数据源 - 强制使用新浪API（绕过东财）
"""
import os

# 恢复Clash代理（让Kimi能联网）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

import akshare as ak
import requests
import pandas as pd
from datetime import datetime

def get_stock_hist_sina(symbol, start_date, end_date):
    """
    使用新浪数据源获取股票历史数据
    
    新浪API格式: https://quotes.sina.cn/cn/api/quotes.php?symbol=sh600000&dpc=1
    """
    # 转换代码格式
    if symbol.startswith('6'):
        code = f"sh{symbol}"
    else:
        code = f"sz{symbol}"
    
    # 使用新浪日K线API
    url = f"https://quotes.sina.cn/cn/api/quotes.php"
    params = {
        'symbol': code,
        'dpc': 1,
    }
    headers = {
        'Referer': 'https://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
    }
    
    try:
        # 先尝试AKShare的新浪接口
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        print(f"AKShare failed: {e}, trying direct Sina API...")
        return None

def test_data_sources():
    """测试数据源可用性"""
    print("=" * 60)
    print("Testing Data Sources")
    print("=" * 60)
    
    test_stock = '002730'
    
    # 测试1: AKShare新浪接口
    print("\n1. Testing AKShare stock_zh_a_hist (Sina)...")
    try:
        df = ak.stock_zh_a_hist(symbol=test_stock, period="daily", 
                                start_date="20260319", end_date="20260320")
        print(f"   SUCCESS: Got {len(df)} records")
        print(df[['日期', '开盘', '收盘']].to_string())
    except Exception as e:
        print(f"   FAILED: {type(e).__name__}")
    
    # 测试2: 新浪实时行情
    print("\n2. Testing Sina Realtime API...")
    try:
        url = 'https://hq.sinajs.cn/list=sz002730'
        r = requests.get(url, headers={'Referer': 'https://finance.sina.com.cn'}, timeout=10)
        print(f"   SUCCESS: Status {r.status_code}")
        print(f"   Data: {r.text[:80]}...")
    except Exception as e:
        print(f"   FAILED: {type(e).__name__}")

if __name__ == '__main__':
    test_data_sources()
