#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AKShare 接口
"""
import sys
sys.path.insert(0, '.')
import akshare as ak
import time

print('=== Testing AKShare API ===')

# 测试 stock_zh_a_hist 接口
print('\n1. Testing stock_zh_a_hist (000001, 20250305):')
try:
    df = ak.stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20250305",
        end_date="20250305",
        adjust=""
    )
    if not df.empty:
        print(f'   Success: open={df.iloc[0]["开盘"]}, close={df.iloc[0]["收盘"]}')
    else:
        print('   Empty result')
except Exception as e:
    print(f'   Error: {e}')

# 测试 stock_zh_a_hist_tx 接口
print('\n2. Testing stock_zh_a_hist_tx (sh000001, 20250305-20250305):')
try:
    df = ak.stock_zh_a_hist_tx(
        symbol="sh000001",
        start_date="20250305",
        end_date="20250305"
    )
    if not df.empty:
        print(f'   Success: open={df.iloc[0]["open"]}, close={df.iloc[0]["close"]}')
    else:
        print('   Empty result')
except Exception as e:
    print(f'   Error: {e}')

# 测试并发
print('\n3. Testing concurrent calls (3 stocks):')
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_one(code):
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date="20250305",
            end_date="20250305",
            adjust=""
        )
        return code, df is not None and not df.empty
    except Exception as e:
        return code, False

start = time.time()
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(fetch_one, code): code for code in ['000001', '000002', '000333']}
    for future in as_completed(futures):
        code, success = future.result()
        print(f'   {code}: {"Success" if success else "Failed"}')

print(f'   Time: {time.time()-start:.1f}s')

# 测试顺序
print('\n4. Testing sequential calls (3 stocks):')
start = time.time()
for code in ['000001', '000002', '000333']:
    code, success = fetch_one(code)
    print(f'   {code}: {"Success" if success else "Failed"}')
    time.sleep(0.5)  # 延迟

print(f'   Time: {time.time()-start:.1f}s')

print('\n=== Test Complete ===')
