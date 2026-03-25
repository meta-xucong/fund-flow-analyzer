#!/usr/bin/env python3
"""Test fixed data sources"""
import os
os.environ['NO_PROXY'] = '*'

import sys
sys.path.insert(0, '.')

from core.fixed_fetcher import FixedDataFetcher
import logging

logging.basicConfig(level=logging.WARNING)

print("=" * 70)
print("Fixed Data Sources Test")
print("=" * 70)

fetcher = FixedDataFetcher()
results = []

# Test 1: Tencent Real-time
print("\n[1] Tencent Real-time (fixed)...")
try:
    df = fetcher.stock_zh_a_spot_tx_fixed()
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Tencent Real-time", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
    if count > 0:
        print(f"    Sample: {df.iloc[0]['code']} {df.iloc[0]['name']} @ {df.iloc[0]['latest']}")
except Exception as e:
    results.append(("Tencent Real-time", False, 0))
    print(f"    [FAIL]: {e}")

# Test 2: Tencent History
print("\n[2] Tencent History (optimized)...")
try:
    df = fetcher.stock_zh_a_hist_tx_fixed('sz000001')
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Tencent History", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Tencent History", False, 0))
    print(f"    [FAIL]: {e}")

# Test 3: Sina Daily
print("\n[3] Sina Daily (optimized)...")
try:
    df = fetcher.stock_zh_a_daily_fixed('sh600000', '20250320', '20250321')
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Sina Daily", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Sina Daily", False, 0))
    print(f"    [FAIL]: {e}")

# Test 4: Stock List
print("\n[4] Stock List...")
try:
    df = fetcher.stock_info_a_code_name()
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Stock List", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Stock List", False, 0))
    print(f"    [FAIL]: {e}")

# Test 5: Abnormal Data
print("\n[5] Abnormal Data...")
try:
    df = fetcher.stock_changes_em_fixed()
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Abnormal Data", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Abnormal Data", False, 0))
    print(f"    [FAIL]: {e}")

# Test 6: Individual Fund Flow
print("\n[6] Individual Fund Flow...")
try:
    df = fetcher.stock_individual_fund_flow_fixed('600000', 'sh')
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Fund Flow", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Fund Flow", False, 0))
    print(f"    [FAIL]: {e}")

# Test 7: New Stocks (fixed)
print("\n[7] New Stocks (fixed)...")
try:
    df = fetcher.stock_zh_a_new_fixed()
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("New Stocks", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("New Stocks", False, 0))
    print(f"    [FAIL]: {e}")

# Test 8: Dragon/Tiger List (fixed)
print("\n[8] Dragon/Tiger List (fixed)...")
try:
    df = fetcher.stock_lhb_detail_daily_sina_fixed('20250320')
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Dragon/Tiger", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Dragon/Tiger", False, 0))
    print(f"    [FAIL]: {e}")

# Test 9: Sina Real-time (fixed)
print("\n[9] Sina Real-time (fixed - takes 30s)...")
try:
    df = fetcher.stock_zh_a_spot_fixed()
    count = len(df) if df is not None else 0
    ok = count > 0
    results.append(("Sina Real-time", ok, count))
    print(f"    [{'OK' if ok else 'FAIL'}]: {count} rows")
except Exception as e:
    results.append(("Sina Real-time", False, 0))
    print(f"    [FAIL]: {e}")

# Summary
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)

ok_count = sum(1 for _, ok, _ in results if ok)
total = len(results)

for name, ok, count in results:
    symbol = "[OK]" if ok else "[FAIL]"
    print(f"{symbol} {name:<25} {count:>6} rows")

print("-" * 70)
print(f"Available: {ok_count}/{total} sources")
print("=" * 70)

# List available sources
print("\n[Available A-Share Data Sources]:")
available = [(name, count) for name, ok, count in results if ok]
for i, (name, count) in enumerate(available, 1):
    print(f"  {i}. {name} ({count} rows)")
