#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试回测功能
"""
import sys
sys.path.insert(0, '.')
from backend.backtest_engine import BacktestEngine
import time

print('=== Testing Backtest Engine ===')

engine = BacktestEngine()

# 测试3天的回测
start_date = '2025-03-03'
end_date = '2025-03-05'

print(f'\nRunning backtest: {start_date} to {end_date}')
print('This should take about 30-60 seconds...\n')

start = time.time()
result = engine.run_backtest(start_date, end_date)
elapsed = time.time() - start

print(f'\nBacktest completed in {elapsed:.1f}s')

if 'error' in result:
    print(f'Error: {result["error"]}')
else:
    print(f'Trading days: {len(result.get("trading_days", []))}')
    print(f'Daily reports: {len(result.get("daily_reports", []))}')
    print(f'Total trades: {len(result.get("trades", []))}')
    
    summary = result.get('summary', {})
    overall = summary.get('overall', {})
    print(f'\nOverall Stats:')
    print(f'  Avg return: {overall.get("avg_return", 0)}%')
    print(f'  Win rate: {overall.get("win_rate", 0)}%')
    print(f'  Total trades: {summary.get("total_trades", 0)}')

print('\n=== Test Complete ===')
