# -*- coding: utf-8 -*-
"""
测试AKShare所有可用的A股数据源
"""
import os
import sys
import time

# 保持Clash代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

import akshare as ak
import requests

print("=" * 80)
print("AKShare数据源测试")
print("=" * 80)

# 测试股票代码
test_code = '002730'
test_symbol = 'sh600519'  # 茅台，用于港股/美股接口

results = []

# 1. stock_zh_a_spot - 同花顺/新浪数据源（默认）
print("\n[1] Testing stock_zh_a_spot (Tonghuashun/Sina)...")
try:
    df = ak.stock_zh_a_spot()
    print(f"    SUCCESS: Got {len(df)} stocks")
    results.append(('stock_zh_a_spot', '同花顺/新浪', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_spot', '同花顺/新浪', False, 0))

time.sleep(1)

# 2. stock_zh_a_spot_em - 东方财富
print("\n[2] Testing stock_zh_a_spot_em (East Money)...")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"    SUCCESS: Got {len(df)} stocks")
    results.append(('stock_zh_a_spot_em', '东方财富', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_spot_em', '东方财富', False, 0))

time.sleep(1)

# 3. stock_zh_a_hist - 历史数据（东财）
print("\n[3] Testing stock_zh_a_hist (Historical - East Money)...")
try:
    df = ak.stock_zh_a_hist(symbol=test_code, period='daily', start_date='20260319', end_date='20260320')
    print(f"    SUCCESS: Got {len(df)} records")
    results.append(('stock_zh_a_hist', '历史数据-东财', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_hist', '历史数据-东财', False, 0))

time.sleep(1)

# 4. stock_zh_a_hist_tx - 腾讯历史数据
print("\n[4] Testing stock_zh_a_hist_tx (Tencent Historical)...")
try:
    df = ak.stock_zh_a_hist_tx(symbol=test_code, start_date='20260319', end_date='20260320')
    print(f"    SUCCESS: Got {len(df)} records")
    results.append(('stock_zh_a_hist_tx', '腾讯历史', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_hist_tx', '腾讯历史', False, 0))

time.sleep(1)

# 5. stock_zh_a_minute - 分钟数据
print("\n[5] Testing stock_zh_a_minute (Minute Data)...")
try:
    df = ak.stock_zh_a_minute(symbol=test_code, period='1', adjust='')
    print(f"    SUCCESS: Got {len(df)} records")
    results.append(('stock_zh_a_minute', '分钟数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_minute', '分钟数据', False, 0))

time.sleep(1)

# 6. stock_zh_a_new - 新股数据
print("\n[6] Testing stock_zh_a_new (New Stocks)...")
try:
    df = ak.stock_zh_a_new()
    print(f"    SUCCESS: Got {len(df)} stocks")
    results.append(('stock_zh_a_new', '新股数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_new', '新股数据', False, 0))

time.sleep(1)

# 7. stock_zh_a_daily - 日频数据
print("\n[7] Testing stock_zh_a_daily (Daily Data)...")
try:
    df = ak.stock_zh_a_daily(symbol=test_symbol, adjust='')
    print(f"    SUCCESS: Got {len(df)} records")
    results.append(('stock_zh_a_daily', '日频数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_a_daily', '日频数据', False, 0))

time.sleep(1)

# 8. stock_hk_spot - 港股数据（测试代理是否工作）
print("\n[8] Testing stock_hk_spot (Hong Kong Stocks)...")
try:
    df = ak.stock_hk_spot()
    print(f"    SUCCESS: Got {len(df)} stocks")
    results.append(('stock_hk_spot', '港股数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_hk_spot', '港股数据', False, 0))

time.sleep(1)

# 9. stock_us_spot - 美股数据
print("\n[9] Testing stock_us_spot (US Stocks)...")
try:
    df = ak.stock_us_spot()
    print(f"    SUCCESS: Got {len(df)} stocks")
    results.append(('stock_us_spot', '美股数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_us_spot', '美股数据', False, 0))

time.sleep(1)

# 10. stock_zh_index_spot_em - 指数数据
print("\n[10] Testing stock_zh_index_spot_em (Index)...")
try:
    df = ak.stock_zh_index_spot_em()
    print(f"    SUCCESS: Got {len(df)} indices")
    results.append(('stock_zh_index_spot_em', 'A股指数', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_zh_index_spot_em', 'A股指数', False, 0))

time.sleep(1)

# 11. stock_sector_spot - 板块数据
print("\n[11] Testing stock_sector_spot (Sector)...")
try:
    df = ak.stock_sector_spot()
    print(f"    SUCCESS: Got {len(df)} sectors")
    results.append(('stock_sector_spot', '板块数据', True, len(df)))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_sector_spot', '板块数据', False, 0))

time.sleep(1)

# 12. stock_individual_spot_xq - 雪球数据
print("\n[12] Testing stock_individual_spot_xq (Xueqiu)...")
try:
    df = ak.stock_individual_spot_xq(symbol='SH600519')
    print(f"    SUCCESS: Got data")
    results.append(('stock_individual_spot_xq', '雪球个股', True, 1))
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {str(e)[:50]}")
    results.append(('stock_individual_spot_xq', '雪球个股', False, 0))

# 汇总
print("\n" + "=" * 80)
print("测试结果汇总")
print("=" * 80)
print(f"{'函数名':<30} {'数据源':<15} {'状态':<8} {'数据量'}")
print("-" * 80)

success_count = 0
for func, source, status, count in results:
    status_str = "✓ 可用" if status else "✗ 失败"
    print(f"{func:<30} {source:<15} {status_str:<8} {count}")
    if status:
        success_count += 1

print("-" * 80)
print(f"总计: {success_count}/{len(results)} 个数据源可用")
print("=" * 80)

# 推荐
print("\n推荐使用的数据源:")
for func, source, status, count in results:
    if status and count > 100:  # 数据量大于100的
        print(f"  - {source} ({func}): {count} 条数据")
