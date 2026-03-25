#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试回测逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.backtest_engine import BacktestEngine
import json

be = BacktestEngine()

# 测试获取未来日期
print("=== 测试 get_future_dates ===")
dates = be.get_future_dates('2025-03-05', 5)
print(f"从2025-03-05开始的5个交易日: {dates}")

# 测试获取股票价格
print("\n=== 测试 fetch_stock_prices ===")
test_code = '000001'  # 平安银行
test_dates = ['2025-03-06', '2025-03-07', '2025-03-10', '2025-03-11', '2025-03-12']
prices = be.fetch_stock_prices(test_code, test_dates)
print(f"股票 {test_code} 的价格数据:")
for d, p in prices.items():
    print(f"  {d}: {p}")

if not prices:
    print("  没有获取到价格数据！")

# 测试完整的交易创建
print("\n=== 测试 _create_trade_with_history ===")
test_stock = {
    'code': '000001',
    'name': '平安银行',
    'open': 10.5,
    'score': 80,
    'reason': '测试'
}
test_report = {
    'momentum_picks': [test_stock],
    'reversal_picks': []
}

trade = be._create_trade_with_history(test_stock, '2025-03-05', test_dates, test_report)
if trade:
    print(f"交易记录:")
    print(f"  代码: {trade['code']}")
    print(f"  买入价: {trade['buy_price']}")
    print(f"  总收益: {trade['total_return']}%")
    print(f"  每日收益:")
    for dr in trade.get('daily_returns', []):
        print(f"    第{dr['day']}天 ({dr['date']}): 价格{dr['price']}, 累计收益{dr['cumulative_return']}%")
else:
    print("  交易创建失败！")
