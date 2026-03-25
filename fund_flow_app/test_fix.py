#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的数据获取功能
"""
import sys
sys.path.insert(0, '.')
from backend.data_fetcher import DataFetcher
import time

print('=== Testing Historical Data Fetch ===')
fetcher = DataFetcher()

# 测试单只股票获取
print('\n1. Testing single stock fetch (000001, 2025-03-05):')
stock_list = fetcher.get_stock_list()
result = fetcher._fetch_single_stock_hist('000001', '2025-03-05', stock_list)
if result:
    print(f'   Success: {result["name"]} close={result["latest"]}')
else:
    print('   Failed')

# 测试批量获取
print('\n2. Testing batch fetch (2025-03-05, sample_size=20):')
start = time.time()
df = fetcher.fetch_historical_data('2025-03-05', sample_size=20)
elapsed = time.time() - start
if not df.empty:
    print(f'   Success: Got {len(df)} stocks in {elapsed:.1f}s')
    print(f'   First stock: {df.iloc[0]["name"]}')
else:
    print(f'   Failed, took {elapsed:.1f}s')

print('\n=== Test Complete ===')
