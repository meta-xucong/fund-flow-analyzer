# -*- coding: utf-8 -*-
"""
验证3月19日选股在3月20日的收益表现
买入时间：3月19日 9:30（开盘价）
卖出时间：3月20日 9:30（开盘价）- 隔夜收益
"""
import os
import sys

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        del os.environ[k]

import akshare as ak
import pandas as pd
import time

print("=" * 80)
print("3月19日选股收益验证")
print("买入: 3月19日 9:30开盘价 | 卖出: 3月20日 9:30开盘价")
print("=" * 80)

# 3月19日选股结果
momentum_picks = [
    ('301365', '矩阵股份'),
    ('301196', '唯科科技'),
    ('300720', '海川智能'),
    ('300308', '中际旭创'),
    ('002730', '电光科技'),
]

reversal_picks = [
    ('002809', '红墙股份'),
    ('300900', '广联航空'),
    ('600410', '华胜天成'),
    ('300606', '金太阳'),
    ('605286', '同力天启'),
]

def get_stock_data(code, name):
    """获取股票3月19日和20日的数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period='daily', 
                                start_date='20260319', end_date='20260320')
        if len(df) >= 2:
            # 3月19日数据（买入日）
            day1 = df[df['日期'] == '2026-03-19'].iloc[0]
            # 3月20日数据（卖出日）
            day2 = df[df['日期'] == '2026-03-20'].iloc[0]
            
            return {
                'code': code,
                'name': name,
                'buy_date': '2026-03-19',
                'buy_price': day1['开盘'],  # 9:30开盘价买入
                'buy_close': day1['收盘'],
                'buy_high': day1['最高'],
                'buy_low': day1['最低'],
                'buy_change': day1['涨跌幅'],
                'sell_date': '2026-03-20',
                'sell_price': day2['开盘'],  # 次日9:30开盘价卖出
                'sell_close': day2['收盘'],
                'sell_high': day2['最高'],
                'sell_change': day2['涨跌幅'],
            }
    except Exception as e:
        print(f"  获取{code}失败: {e}")
    return None

results = []

# 验证动量策略
print("\n【动量策略 - 追涨】")
print("-" * 80)

for code, name in momentum_picks:
    print(f"正在获取 {name}({code})...")
    data = get_stock_data(code, name)
    if data:
        # 计算隔夜收益
        overnight_return = (data['sell_price'] - data['buy_price']) / data['buy_price'] * 100
        # 计算当日收盘收益（如果当天卖出）
        day_return = (data['buy_close'] - data['buy_price']) / data['buy_price'] * 100
        # 计算次日最高收益
        max_return = (data['sell_high'] - data['buy_price']) / data['buy_price'] * 100
        
        data['overnight_return'] = overnight_return
        data['day_return'] = day_return
        data['max_return'] = max_return
        results.append(data)
        
        signal = "✓" if overnight_return > 0 else "✗"
        print(f"  {signal} {name}: 买入{data['buy_price']:.2f} → 次日开盘{data['sell_price']:.2f} "
              f"隔夜收益: {overnight_return:+.2f}%")
        print(f"     当日收盘收益: {day_return:+.2f}% | 次日最高可获: {max_return:+.2f}%")
    else:
        print(f"  ✗ {name}: 无数据")
    time.sleep(0.5)

# 验证反转策略
print("\n【反转策略 - 抄底】")
print("-" * 80)

for code, name in reversal_picks:
    print(f"正在获取 {name}({code})...")
    data = get_stock_data(code, name)
    if data:
        overnight_return = (data['sell_price'] - data['buy_price']) / data['buy_price'] * 100
        day_return = (data['buy_close'] - data['buy_price']) / data['buy_price'] * 100
        max_return = (data['sell_high'] - data['buy_price']) / data['buy_price'] * 100
        
        data['overnight_return'] = overnight_return
        data['day_return'] = day_return
        data['max_return'] = max_return
        results.append(data)
        
        signal = "✓" if overnight_return > 0 else "✗"
        print(f"  {signal} {name}: 买入{data['buy_price']:.2f} → 次日开盘{data['sell_price']:.2f} "
              f"隔夜收益: {overnight_return:+.2f}%")
        print(f"     当日收盘收益: {day_return:+.2f}% | 次日最高可获: {max_return:+.2f}%")
    else:
        print(f"  ✗ {name}: 无数据")
    time.sleep(0.5)

# 汇总统计
print("\n" + "=" * 80)
print("汇总统计")
print("=" * 80)

if results:
    df = pd.DataFrame(results)
    
    # 区分策略
    momentum_df = df[df['code'].isin([c for c, _ in momentum_picks])]
    reversal_df = df[df['code'].isin([c for c, _ in reversal_picks])]
    
    print("\n【动量策略】")
    if len(momentum_df) > 0:
        win = (momentum_df['overnight_return'] > 0).sum()
        total = len(momentum_df)
        avg = momentum_df['overnight_return'].mean()
        best = momentum_df.loc[momentum_df['overnight_return'].idxmax()]
        worst = momentum_df.loc[momentum_df['overnight_return'].idxmin()]
        
        print(f"  统计: {win}/{total} 盈利 ({win/total*100:.1f}%)")
        print(f"  平均隔夜收益: {avg:+.2f}%")
        print(f"  最佳: {best['name']} {best['overnight_return']:+.2f}%")
        print(f"  最差: {worst['name']} {worst['overnight_return']:+.2f}%")
    
    print("\n【反转策略】")
    if len(reversal_df) > 0:
        win = (reversal_df['overnight_return'] > 0).sum()
        total = len(reversal_df)
        avg = reversal_df['overnight_return'].mean()
        best = reversal_df.loc[reversal_df['overnight_return'].idxmax()]
        worst = reversal_df.loc[reversal_df['overnight_return'].idxmin()]
        
        print(f"  统计: {win}/{total} 盈利 ({win/total*100:.1f}%)")
        print(f"  平均隔夜收益: {avg:+.2f}%")
        print(f"  最佳: {best['name']} {best['overnight_return']:+.2f}%")
        print(f"  最差: {worst['name']} {worst['overnight_return']:+.2f}%")
    
    print("\n【总体表现】")
    win = (df['overnight_return'] > 0).sum()
    total = len(df)
    avg = df['overnight_return'].mean()
    
    print(f"  总交易次数: {total}")
    print(f"  盈利次数: {win} ({win/total*100:.1f}%)")
    print(f"  平均收益: {avg:+.2f}%")
    print(f"  总收益率（等权）: {df['overnight_return'].sum():+.2f}%")

print("\n" + "=" * 80)
