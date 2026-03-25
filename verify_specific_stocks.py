#!/usr/bin/env python3
"""
验证特定股票的收益
使用新浪API直接查询
"""
import sys
sys.path.insert(0, '.')

from core.sina_fetcher import SinaDataFetcher
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=" * 70)
print("3月19日选股收益验证 - 特定股票查询")
print("=" * 70)

# 3月19日选股结果（买入价）
march_19_picks = {
    'momentum': [
        ('301365', '矩阵股份', 28.08),
        ('301196', '唯科科技', 89.99),
        ('300720', '海川智能', 56.85),
        ('300308', '中际旭创', 170.00),
        ('002730', '电光科技', 21.63),
    ],
    'reversal': [
        ('002809', '红墙股份', 12.15),
        ('300900', '广联航空', 35.50),
        ('600410', '华胜天成', 12.80),
        ('300606', '金太阳', 18.50),
        ('605286', '同力日升', 22.30),
    ]
}

# 使用新浪获取器
fetcher = SinaDataFetcher()

# 获取所有股票列表来查询
print("\n获取股票列表...")
stock_list = fetcher.get_stock_list()
print(f"共 {len(stock_list)} 只股票\n")

# 筛选出需要的股票
codes_to_check = [code for strategy, picks in march_19_picks.items() for code, name, _ in picks]
print(f"需要查询 {len(codes_to_check)} 只股票\n")

# 转换为新浪格式
sina_codes = []
for code in codes_to_check:
    prefix = 'sh' if code.startswith('6') else 'sz'
    sina_codes.append(f'{prefix}{code}')

# 分批获取（每次最多200只）
print("获取实时价格...")
all_results = []
for i in range(0, len(sina_codes), 200):
    batch = sina_codes[i:i+200]
    df = fetcher.fetch_tencent_quotes(batch)  # 腾讯接口更详细
    if not df.empty:
        all_results.append(df)

if all_results:
    prices_df = pd.concat(all_results, ignore_index=True)
    prices = dict(zip(prices_df['code'], prices_df['latest']))
    
    print("\n" + "=" * 70)
    print("收益验证结果")
    print("=" * 70)
    
    for strategy, picks in march_19_picks.items():
        print(f"\n【{strategy}】")
        print("-" * 70)
        
        for code, name, buy_price in picks:
            current_price = prices.get(code, 0)
            if current_price > 0:
                return_pct = (current_price - buy_price) / buy_price * 100
                print(f"  {code} {name}: {buy_price:.2f} -> {current_price:.2f} ({return_pct:+.2f}%)")
            else:
                print(f"  {code} {name}: 未找到数据")

print("\n" + "=" * 70)
print("验证完成")
print("=" * 70)
