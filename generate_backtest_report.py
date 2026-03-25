#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成回测报告
"""
import pandas as pd
from datetime import datetime

# 读取结果
df = pd.read_csv('reports/march_backtest_demo_20260322.csv', encoding='utf-8-sig')

report = []
report.append("=" * 80)
report.append("3月回测演示结果汇总")
report.append("=" * 80)
report.append("")
report.append("回测参数:")
report.append("  - 时间范围: 2025-03-03 至 2025-03-21 (15个交易日)")
report.append("  - 股票池: 沪深A股前2000只")
report.append("  - 选股策略: 动量策略 + 反转策略")
report.append("  - 持有期: 5个交易日")
report.append("")
report.append("-" * 80)
report.append("总体统计")
report.append("-" * 80)
report.append(f"  总交易次数:     {len(df)} 笔")
report.append(f"  动量策略:       {len(df[df.strategy == '动量'])} 笔")
report.append(f"  反转策略:       {len(df[df.strategy == '反转'])} 笔")
report.append("")
report.append(f"  平均收益率:     {df.total_return.mean():.2f}%")
report.append(f"  收益率中位数:   {df.total_return.median():.2f}%")
report.append(f"  最高收益:       {df.total_return.max():.2f}%")
report.append(f"  最低收益:       {df.total_return.min():.2f}%")
report.append(f"  胜率:           {(df.total_return > 0).mean() * 100:.1f}%")
report.append("")

# 策略对比
report.append("-" * 80)
report.append("策略表现对比")
report.append("-" * 80)
momentum = df[df.strategy == '动量']
reversal = df[df.strategy == '反转']
report.append(f"  动量策略: 平均收益 {momentum.total_return.mean():.2f}%, 胜率 {(momentum.total_return > 0).mean() * 100:.1f}%")
report.append(f"  反转策略: 平均收益 {reversal.total_return.mean():.2f}%, 胜率 {(reversal.total_return > 0).mean() * 100:.1f}%")
report.append("")

# 每日统计
report.append("-" * 80)
report.append("每日平均收益")
report.append("-" * 80)
daily = df.groupby('date').total_return.mean()
for date, ret in daily.items():
    count = len(df[df.date == date])
    report.append(f"  {date}: {ret:>6.2f}% ({count}笔)")
report.append("")

# 显示交易明细
report.append("-" * 80)
report.append("交易明细 (前20笔)")
report.append("-" * 80)
display = df[['date', 'code', 'name', 'strategy', 'buy_price', 'total_return']].head(20)
report.append(display.to_string(index=False))
report.append("")
report.append("=" * 80)
report.append("说明:")
report.append("  - 今日9:25数据为真实数据 (来自腾讯API)")
report.append("  - 历史数据为基于今日数据生成的模拟数据")
report.append("  - 收益率为模拟计算，仅用于验证回测逻辑")
report.append("  - 实际回测需要获取真实历史日线数据")
report.append("=" * 80)

# 保存报告
report_text = "\n".join(report)
with open('reports/march_backtest_report.txt', 'w', encoding='utf-8') as f:
    f.write(report_text)

print(report_text)
print("\n报告已保存: reports/march_backtest_report.txt")
