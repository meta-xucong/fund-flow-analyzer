#!/usr/bin/env python3
"""
测试所有AKShare数据源
"""
import os
os.environ['NO_PROXY'] = '*'

import akshare as ak
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("AKShare全数据源测试")
print("=" * 70)

def test_source(name, desc, func):
    """测试单个数据源"""
    try:
        df = func()
        count = len(df) if df is not None else 0
        status = "OK" if count > 0 else "Empty"
        return f"{name:<30} {desc:<20} {status:>6} ({count} rows)"
    except Exception as e:
        err = type(e).__name__
        if 'Proxy' in str(e) or 'proxy' in str(e).lower():
            err = "PROXY_BLOCKED"
        elif 'Connection' in str(e):
            err = "CONN_ERROR"
        elif 'JSON' in str(e) or 'json' in str(e).lower():
            err = "JSON_ERROR"
        return f"{name:<30} {desc:<20} FAIL   ({err})"

# A股实时行情
print("\n【A股实时行情】")
print("-" * 70)
print(test_source("stock_zh_a_spot_em", "东财实时", lambda: ak.stock_zh_a_spot_em()))
print(test_source("stock_zh_a_spot", "同花顺/新浪", lambda: ak.stock_zh_a_spot()))
print(test_source("stock_zh_a_spot_tx", "腾讯实时", lambda: ak.stock_zh_a_spot_tx()))

# A股历史数据
print("\n【A股历史数据】")
print("-" * 70)
print(test_source("stock_zh_a_hist", "东财历史", lambda: ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20250320', end_date='20250321')))
print(test_source("stock_zh_a_hist_tx", "腾讯历史", lambda: ak.stock_zh_a_hist_tx(symbol='sz000001')))
print(test_source("stock_zh_a_daily", "新浪日线", lambda: ak.stock_zh_a_daily(symbol='sh600000', start_date='20250320', end_date='20250321')))

# 其他A股数据
print("\n【其他A股数据】")
print("-" * 70)
print(test_source("stock_zh_a_new", "新股", lambda: ak.stock_zh_a_new()))
print(test_source("stock_info_a_code_name", "股票列表", lambda: ak.stock_info_a_code_name()))
print(test_source("stock_changes_em", "异动数据", lambda: ak.stock_changes_em()))

# 港股/美股
print("\n【港股/美股】")
print("-" * 70)
print(test_source("stock_hk_spot_em", "港股实时", lambda: ak.stock_hk_spot_em()))
print(test_source("stock_us_spot_em", "美股实时", lambda: ak.stock_us_spot_em()))

# 资金流向
print("\n【资金流向】")
print("-" * 70)
print(test_source("stock_individual_fund_flow", "个股资金", lambda: ak.stock_individual_fund_flow(stock="600000", market="sh")))
print(test_source("stock_sector_fund_flow_rank", "板块资金", lambda: ak.stock_sector_fund_flow_rank()))

# 龙虎榜
print("\n【龙虎榜】")
print("-" * 70)
print(test_source("stock_lhb_detail_daily_sina", "龙虎榜", lambda: ak.stock_lhb_detail_daily_sina(start_date="20250320", end_date="20250320")))

print("\n" + "=" * 70)
