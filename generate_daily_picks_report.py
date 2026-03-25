#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成每日选股推荐报告

展示每个交易日的选股结果和推荐理由
"""
import pandas as pd
from datetime import datetime

# 读取回测结果
df = pd.read_csv('reports/march_backtest_demo_20260322.csv', encoding='utf-8-sig')

# 按日期分组
dates = sorted(df['date'].unique())

report = []
report.append("=" * 100)
report.append("每日选股推荐报告 (3月1日 - 3月21日)")
report.append("=" * 100)
report.append("")
report.append("说明：")
report.append("  - 本报告展示每个交易日的选股推荐结果")
report.append("  - 选股时间：每日9:25开盘前")
report.append("  - 持有策略：买入后持有5个交易日")
report.append("  - 数据来源：腾讯实时API (今日) + 模拟数据 (历史)")
report.append("")

for date in dates:
    day_data = df[df['date'] == date].sort_values('total_return', ascending=False)
    
    report.append("=" * 100)
    report.append(f"【{date}】选股推荐")
    report.append("=" * 100)
    report.append("")
    
    # 动量策略
    momentum = day_data[day_data['strategy'] == '动量']
    if len(momentum) > 0:
        report.append(f"  >> 动量策略 (选中 {len(momentum)} 只)")
        report.append("  " + "-" * 90)
        for idx, row in momentum.iterrows():
            report.append(f"  {row['code']:>8} {row['name']:<10} | 买入价: {row['buy_price']:>7.2f} | {row['entry_signal']}")
        report.append("")
    
    # 反转策略
    reversal = day_data[day_data['strategy'] == '反转']
    if len(reversal) > 0:
        report.append(f"  >> 反转策略 (选中 {len(reversal)} 只)")
        report.append("  " + "-" * 90)
        for idx, row in reversal.iterrows():
            report.append(f"  {row['code']:>8} {row['name']:<10} | 买入价: {row['buy_price']:>7.2f} | {row['entry_signal']}")
        report.append("")
    
    # 当日统计
    report.append(f"  当日推荐股票总数: {len(day_data)} 只")
    report.append(f"  预期平均收益: {day_data['total_return'].mean():.2f}%")
    report.append("")

# 汇总
report.append("=" * 100)
report.append("汇总统计")
report.append("=" * 100)
report.append("")
report.append(f"  回测期间: {dates[0]} 至 {dates[-1]} (共{len(dates)}个交易日)")
report.append(f"  总推荐次数: {len(df)} 次")
report.append(f"  动量策略: {len(df[df['strategy'] == '动量'])} 次")
report.append(f"  反转策略: {len(df[df['strategy'] == '反转'])} 次")
report.append(f"  平均持有收益: {df['total_return'].mean():.2f}%")
report.append(f"  胜率: {(df['total_return'] > 0).mean() * 100:.1f}%")
report.append("")

# 表现最佳的股票
report.append("=" * 100)
report.append("表现最佳推荐 (Top 10)")
report.append("=" * 100)
report.append("")
top10 = df.nlargest(10, 'total_return')[['date', 'code', 'name', 'strategy', 'buy_price', 'total_return']]
for idx, row in top10.iterrows():
    report.append(f"  {row['date']} | {row['code']:>8} {row['name']:<10} | {row['strategy']:<6} | 收益: {row['total_return']:>5.2f}%")
report.append("")

report.append("=" * 100)

# 保存报告
report_text = "\n".join(report)
with open('reports/daily_stock_picks_march.txt', 'w', encoding='utf-8') as f:
    f.write(report_text)

print(report_text)
print("\n报告已保存: reports/daily_stock_picks_march.txt")
