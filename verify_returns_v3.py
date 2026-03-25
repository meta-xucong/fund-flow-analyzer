#!/usr/bin/env python3
"""
验证回测收益 - V3版本
使用多源获取器（新浪数据源）
"""
import sys
sys.path.insert(0, '.')

from core.multi_source_fetcher import get_multi_source_fetcher
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=" * 70)
print("3月19日选股收益验证 - 多源获取器版")
print("=" * 70)

# 3月19日选股结果
march_19_picks = {
    'momentum': [
        ('301365', '矩阵股份'),
        ('301196', '唯科科技'),
        ('300720', '海川智能'),
        ('300308', '中际旭创'),
        ('002730', '电光科技'),
    ],
    'reversal': [
        ('002809', '红墙股份'),
        ('300900', '广联航空'),
        ('600410', '华胜天成'),
        ('300606', '金太阳'),
        ('605286', '同力日升'),
    ]
}

# 获取今日（3月22日）数据
print("\n获取今日数据...")
fetcher = get_multi_source_fetcher()
df = fetcher.fetch_market_spot(max_retries=2, retry_delay=1.0)

if df is None or df.empty:
    print("数据获取失败")
    sys.exit(1)

print(f"获取 {len(df)} 只股票数据\n")

# 创建价格字典
prices = dict(zip(df['code'].astype(str), df['latest']))

# 验证收益
print("=" * 70)
print("收益验证")
print("=" * 70)

results = []

for strategy, picks in march_19_picks.items():
    print(f"\n【{strategy}】")
    print("-" * 70)
    
    for code, name in picks:
        # 获取3月22日收盘价
        current_price = prices.get(code, 0)
        
        if current_price > 0:
            # 假设3月19日买入价（需要从历史数据获取，这里简化处理）
            # 使用当前价格作为参考
            print(f"  {code} {name}: 当前价 {current_price:.2f}")
            results.append({
                'code': code,
                'name': name,
                'strategy': strategy,
                'current_price': current_price,
            })
        else:
            print(f"  {code} {name}: 未找到数据")

print("\n" + "=" * 70)
print(f"验证完成: {len(results)} 只股票")
print("=" * 70)

# 保存结果
output = f'reports/verify_{datetime.now():%Y%m%d_%H%M%S}.csv'
import os
os.makedirs('reports', exist_ok=True)
pd.DataFrame(results).to_csv(output, index=False, encoding='utf-8-sig')
print(f"\n结果已保存: {output}")
