#!/usr/bin/env python3
"""
快速测试修复后的数据源
"""
import os
os.environ['NO_PROXY'] = '*'

import sys
sys.path.insert(0, '.')

from core.fixed_fetcher import FixedDataFetcher
import logging

logging.basicConfig(level=logging.WARNING)  # 减少日志输出

print("=" * 70)
print("修复后的A股数据源快速测试")
print("=" * 70)

fetcher = FixedDataFetcher()
results = []

# 测试1: 腾讯实时 (修复)
print("\n[1] 腾讯实时 (修复 stock_zh_a_spot_tx)...")
try:
    df = fetcher.stock_zh_a_spot_tx_fixed()
    count = len(df) if df is not None else 0
    status = "OK" if count > 0 else "Empty"
    results.append(("腾讯实时", count > 0, count))
    print(f"    [{status}]: {count} rows")
    if count > 0:
        print(f"    示例: {df.iloc[0]['code']} {df.iloc[0]['name']} {df.iloc[0]['latest']}")
except Exception as e:
    results.append(("腾讯实时", False, 0))
    print(f"    [FAIL]: {e}")

# 测试2: 腾讯历史 (优化)
print("\n[2] 腾讯历史 (优化 stock_zh_a_hist_tx)...")
try:
    df = fetcher.stock_zh_a_hist_tx_fixed('sz000001')
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("腾讯历史", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("腾讯历史", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试3: 新浪日线 (优化)
print("\n[3] 新浪日线 (优化 stock_zh_a_daily)...")
try:
    df = fetcher.stock_zh_a_daily_fixed('sh600000', '20250320', '20250321')
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("新浪日线", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("新浪日线", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试4: 股票列表
print("\n[4] 股票列表 (stock_info_a_code_name)...")
try:
    df = fetcher.stock_info_a_code_name()
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("股票列表", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("股票列表", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试5: 异动数据
print("\n[5] 异动数据 (stock_changes_em)...")
try:
    df = fetcher.stock_changes_em_fixed()
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("异动数据", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("异动数据", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试6: 个股资金
print("\n[6] 个股资金 (stock_individual_fund_flow)...")
try:
    df = fetcher.stock_individual_fund_flow_fixed('600000', 'sh')
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("个股资金", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("个股资金", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试7: 新股 (修复)
print("\n[7] 新股 (修复 stock_zh_a_new)...")
try:
    df = fetcher.stock_zh_a_new_fixed()
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("新股", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("新股", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试8: 龙虎榜 (修复)
print("\n[8] 龙虎榜 (修复 stock_lhb_detail_daily_sina)...")
try:
    df = fetcher.stock_lhb_detail_daily_sina_fixed('20250320')
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("龙虎榜", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("龙虎榜", False, 0))
    print(f"    ✗ FAIL: {e}")

# 测试9: 新浪实时 (修复)
print("\n[9] 新浪实时 (修复 stock_zh_a_spot)...")
print("    Testing... (may take 30s)")
try:
    df = fetcher.stock_zh_a_spot_fixed()
    count = len(df) if df is not None else 0
    status = "✓ OK" if count > 0 else "✗ Empty"
    results.append(("新浪实时", count > 0, count))
    print(f"    {status}: {count} rows")
except Exception as e:
    results.append(("新浪实时", False, 0))
    print(f"    ✗ FAIL: {e}")

# 汇总
print("\n" + "=" * 70)
print("修复结果汇总")
print("=" * 70)

ok_count = sum(1 for _, ok, _ in results if ok)
total = len(results)

for name, ok, count in results:
    symbol = "[OK]" if ok else "[FAIL]"
    print(f"{symbol} {name:<20} {count:>6} rows")

print("-" * 70)
print(f"可用数据源: {ok_count}/{total}")
print("=" * 70)
