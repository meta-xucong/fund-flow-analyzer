#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯接口
"""
import sys
sys.path.insert(0, '.')
import akshare as ak

print('=== Testing stock_zh_a_hist_tx API ===')

# 测试获取个股（平安银行）
print('\n1. Testing 000001 (sz000001):')
try:
    df = ak.stock_zh_a_hist_tx(
        symbol="sz000001",
        start_date="20250305",
        end_date="20250305"
    )
    if not df.empty:
        print(f'   Success: {df.iloc[0].to_dict()}')
    else:
        print('   Empty result')
except Exception as e:
    print(f'   Error: {e}')

# 测试获取个股（万科A）
print('\n2. Testing 000002 (sz000002):')
try:
    df = ak.stock_zh_a_hist_tx(
        symbol="sz000002",
        start_date="20250305",
        end_date="20250305"
    )
    if not df.empty:
        print(f'   Success: name={df.iloc[0].get("name", "N/A")}, close={df.iloc[0]["close"]}')
    else:
        print('   Empty result')
except Exception as e:
    print(f'   Error: {e}')

# 测试获取沪市股票
print('\n3. Testing 600000 (sh600000):')
try:
    df = ak.stock_zh_a_hist_tx(
        symbol="sh600000",
        start_date="20250305",
        end_date="20250305"
    )
    if not df.empty:
        print(f'   Success: name={df.iloc[0].get("name", "N/A")}, close={df.iloc[0]["close"]}')
    else:
        print('   Empty result')
except Exception as e:
    print(f'   Error: {e}')

print('\n=== Test Complete ===')
