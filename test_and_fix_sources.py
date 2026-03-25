# -*- coding: utf-8 -*-
"""
测试并修复各种数据源
"""
import os
import sys
import time
import json

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

import akshare as ak
import requests
import pandas as pd

print("=" * 80)
print("数据源修复测试")
print("=" * 80)

results = []

# 1. 测试腾讯历史数据 stock_zh_a_hist_tx
print("\n[1] Testing stock_zh_a_hist_tx (Tencent Historical)")
print("-" * 60)
try:
    # 原始调用方式
    print("Method 1: Original API call")
    df = ak.stock_zh_a_hist_tx(symbol='002730', start_date='20260319', end_date='20260320')
    print(f"  SUCCESS: {len(df)} records")
    results.append(('stock_zh_a_hist_tx', 'OK', len(df)))
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {str(e)[:100]}")
    
    # 尝试修复：使用不同的symbol格式
    print("\nMethod 2: Try different symbol format")
    try:
        df = ak.stock_zh_a_hist_tx(symbol='sz002730', start_date='20260319', end_date='20260320')
        print(f"  SUCCESS: {len(df)} records")
        results.append(('stock_zh_a_hist_tx', 'Fixed', len(df)))
    except Exception as e2:
        print(f"  FAILED: {e2}")
        results.append(('stock_zh_a_hist_tx', 'Failed', 0))

time.sleep(1)

# 2. 测试分钟数据 stock_zh_a_minute
print("\n[2] Testing stock_zh_a_minute (Minute Data)")
print("-" * 60)
try:
    print("Method 1: period='1'")
    df = ak.stock_zh_a_minute(symbol='002730', period='1', adjust='')
    print(f"  SUCCESS: {len(df)} records")
    if len(df) > 0:
        print(f"  Columns: {list(df.columns)}")
        print(f"  Sample: {df.head(2).to_string()}")
    results.append(('stock_zh_a_minute', 'OK', len(df)))
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {str(e)[:100]}")
    
    # 尝试修复：使用不同的period参数
    print("\nMethod 2: Try period='5'")
    try:
        df = ak.stock_zh_a_minute(symbol='002730', period='5', adjust='')
        print(f"  SUCCESS: {len(df)} records")
        results.append(('stock_zh_a_minute', 'Fixed', len(df)))
    except Exception as e2:
        print(f"  FAILED: {e2}")
        results.append(('stock_zh_a_minute', 'Failed', 0))

time.sleep(1)

# 3. 测试港股 stock_hk_spot
print("\n[3] Testing stock_hk_spot (Hong Kong)")
print("-" * 60)
try:
    print("Method 1: Direct API call")
    df = ak.stock_hk_spot()
    print(f"  SUCCESS: {len(df)} records")
    results.append(('stock_hk_spot', 'OK', len(df)))
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {str(e)[:100]}")
    
    # 尝试修复：使用_em版本
    print("\nMethod 2: Try stock_hk_spot_em")
    try:
        df = ak.stock_hk_spot_em()
        print(f"  SUCCESS: {len(df)} records")
        results.append(('stock_hk_spot_em', 'Fixed', len(df)))
    except Exception as e2:
        print(f"  FAILED: {e2}")
        results.append(('stock_hk_spot', 'Failed', 0))

time.sleep(1)

# 4. 测试美股 stock_us_spot (限制请求数量)
print("\n[4] Testing stock_us_spot (US Stocks)")
print("-" * 60)
try:
    print("Method 1: Direct API call (limit 10 stocks)")
    # 这个API很慢，我们设置超时
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("API call timeout")
    
    # Windows doesn't support signal.SIGALRM, use alternative
    start_time = time.time()
    df = ak.stock_us_spot()
    elapsed = time.time() - start_time
    print(f"  SUCCESS: {len(df)} records in {elapsed:.1f}s")
    results.append(('stock_us_spot', 'OK', len(df)))
except Exception as e:
    print(f"  FAILED: {type(e).__name__}: {str(e)[:100]}")
    results.append(('stock_us_spot', 'Timeout/Failed', 0))

time.sleep(1)

# 5. 测试其他可能的API
print("\n[5] Testing alternative APIs")
print("-" * 60)

# 测试雪球API
print("\n5.1 stock_individual_spot_xq (Xueqiu)")
try:
    df = ak.stock_individual_spot_xq(symbol='SH600519')
    print(f"  SUCCESS: Got data")
    print(f"  Data: {df.head().to_string()}")
    results.append(('stock_individual_spot_xq', 'OK', 1))
except Exception as e:
    print(f"  FAILED: {e}")
    results.append(('stock_individual_spot_xq', 'Failed', 0))

# 测试指数API
print("\n5.2 stock_zh_index_spot_em (A股指数)")
try:
    df = ak.stock_zh_index_spot_em()
    print(f"  SUCCESS: {len(df)} indices")
    results.append(('stock_zh_index_spot_em', 'OK', len(df)))
except Exception as e:
    print(f"  FAILED: {e}")
    results.append(('stock_zh_index_spot_em', 'Failed', 0))

# 测试新浪直接API
print("\n5.3 Sina Direct API (hq.sinajs.cn)")
try:
    url = 'https://hq.sinajs.cn/list=sh600519,sz002730'
    headers = {'Referer': 'https://finance.sina.com.cn'}
    r = requests.get(url, headers=headers, timeout=10)
    print(f"  SUCCESS: Status {r.status_code}")
    print(f"  Data: {r.text[:100]}...")
    results.append(('sina_direct', 'OK', 1))
except Exception as e:
    print(f"  FAILED: {e}")
    results.append(('sina_direct', 'Failed', 0))

# 汇总
print("\n" + "=" * 80)
print("修复测试结果汇总")
print("=" * 80)
print(f"{'数据源':<30} {'状态':<15} {'数据量'}")
print("-" * 80)
for name, status, count in results:
    print(f"{name:<30} {status:<15} {count}")

# 分类
print("\n" + "=" * 80)
print("分类结果")
print("=" * 80)

working = [r for r in results if r[1] == 'OK']
fixed = [r for r in results if r[1] == 'Fixed']
failed = [r for r in results if r[1] in ['Failed', 'Timeout/Failed']]

print(f"\n✅ 正常工作 ({len(working)}):")
for name, status, count in working:
    print(f"  - {name}: {count}")

if fixed:
    print(f"\n🔧 修复后可用 ({len(fixed)}):")
    for name, status, count in fixed:
        print(f"  - {name}: {count}")

if failed:
    print(f"\n❌ 无法修复 ({len(failed)}):")
    for name, status, count in failed:
        print(f"  - {name}")
