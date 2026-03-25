#!/usr/bin/env python3
"""
稳定性对比测试

对比 fixed_fetcher vs ultra_stable_fetcher
"""
import os
os.environ['NO_PROXY'] = '*'

import sys
sys.path.insert(0, '.')

import time
import logging

logging.basicConfig(level=logging.WARNING)

print("=" * 70)
print("稳定性对比测试")
print("=" * 70)

# 测试参数
TEST_CODES = ['sh600000', 'sz000001', 'sz002730', 'sh601318', 'sz000858'] * 4  # 20只
NUM_ITERATIONS = 3

print(f"\n测试参数:")
print(f"  股票数量: {len(TEST_CODES)} 只")
print(f"  测试轮次: {NUM_ITERATIONS} 轮")
print(f"  总请求数: {len(TEST_CODES) * NUM_ITERATIONS} 次")

results = {}

# ========== 测试1: 终极稳定版 ==========
print("\n" + "-" * 70)
print("[测试1] 终极稳定版 (ultra_stable_fetcher)")
print("-" * 70)

from core.ultra_stable_fetcher import get_ultra_stable_fetcher

fetcher1 = get_ultra_stable_fetcher()
start_time = time.time()
success_count = 0
fail_count = 0

for i in range(NUM_ITERATIONS):
    print(f"  第{i+1}轮...", end=' ', flush=True)
    try:
        df = fetcher1.fetch_tencent_realtime(TEST_CODES)
        if not df.empty:
            success_count += 1
            print(f"OK ({len(df)}只)")
        else:
            fail_count += 1
            print("FAIL (empty)")
    except Exception as e:
        fail_count += 1
        print(f"FAIL ({e})")
    
    # 统计信息
    stats = fetcher1.get_stats()

elapsed1 = time.time() - start_time
results['ultra_stable'] = {
    'success': success_count,
    'fail': fail_count,
    'time': elapsed1,
    'avg_delay': stats.get('average_delay', 'N/A'),
}

print(f"\n  结果: {success_count}/{NUM_ITERATIONS} 成功, {elapsed1:.2f}秒")
print(f"  平均延迟: {stats.get('average_delay', 'N/A')}")

# ========== 测试2: 修复版 (普通重试) ==========
print("\n" + "-" * 70)
print("[测试2] 修复版 (fixed_fetcher)")
print("-" * 70)

from core.fixed_fetcher import FixedDataFetcher

fetcher2 = FixedDataFetcher()
start_time = time.time()
success_count = 0
fail_count = 0

for i in range(NUM_ITERATIONS):
    print(f"  第{i+1}轮...", end=' ', flush=True)
    try:
        df = fetcher2.stock_zh_a_spot_tx_fixed()  # 获取所有，取前20只
        if not df.empty:
            success_count += 1
            print(f"OK ({len(df)}只)")
        else:
            fail_count += 1
            print("FAIL (empty)")
    except Exception as e:
        fail_count += 1
        print(f"FAIL ({e})")

elapsed2 = time.time() - start_time
results['fixed'] = {
    'success': success_count,
    'fail': fail_count,
    'time': elapsed2,
}

print(f"\n  结果: {success_count}/{NUM_ITERATIONS} 成功, {elapsed2:.2f}秒")

# ========== 汇总 ==========
print("\n" + "=" * 70)
print("对比汇总")
print("=" * 70)

print(f"\n{'指标':<25} {'终极稳定版':<20} {'修复版':<20}")
print("-" * 70)

us = results['ultra_stable']
fx = results['fixed']

print(f"{'成功率':<25} {us['success']/NUM_ITERATIONS*100:>6.1f}%{'':<12} {fx['success']/NUM_ITERATIONS*100:>6.1f}%")
print(f"{'总耗时':<25} {us['time']:>6.2f}s{'':<12} {fx['time']:>6.2f}s")
print(f"{'平均延迟':<25} {us.get('avg_delay', 'N/A'):>10}{'':<8} {'N/A':>10}")

print("\n" + "=" * 70)

# 建议
print("\n[建议]")
if us['success'] >= fx['success']:
    print("[OK] 终极稳定版成功率更高，推荐用于生产环境")
else:
    print("[?] 两者成功率相当")

if us['time'] <= fx['time'] * 1.2:
    print("[OK] 终极稳定版速度可接受")
else:
    print("[WARN] 终极稳定版较慢，但稳定性更好")

print("=" * 70)
