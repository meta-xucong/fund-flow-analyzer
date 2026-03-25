# -*- coding: utf-8 -*-
"""
过去3天回测分析报告
验证25分钟模式(9:25开盘价买入) vs 30分钟模式(收盘价)
"""
import os
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

import akshare as ak
import pandas as pd
from datetime import datetime

print("=" * 80)
print("过去3天(2026-03-17至2026-03-19)回测分析报告")
print("=" * 80)

# 定义选股结果 (基于3月20日报告)
momentum_picks = {
    '002730': '电光科技',
    '300565': '科信技术',
    '002756': '永兴材料',
    '002487': '大金重工',
    '000973': '佛塑科技'
}

reversal_picks = {
    '002208': '合肥城建',
    '600589': '大位科技',
    '600610': '中毅达',
    '300961': '深水海纳',
    '300201': '海伦哲'
}

def analyze_stock(code, name, strategy, date):
    """分析单只股票在指定日期的表现"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period='daily', 
                                start_date=date.replace('-', ''), 
                                end_date=date.replace('-', ''))
        if len(df) == 0:
            return None
        
        row = df.iloc[0]
        open_price = row['开盘']
        close_price = row['收盘']
        high_price = row['最高']
        low_price = row['最低']
        prev_close = row['收盘'] / (1 + row['涨跌幅']/100)
        
        # 计算关键指标
        day_return = (close_price - open_price) / open_price * 100
        max_return = (high_price - open_price) / open_price * 100
        min_return = (low_price - open_price) / open_price * 100
        gap = (open_price - prev_close) / prev_close * 100
        
        return {
            'code': code,
            'name': name,
            'date': date,
            'strategy': strategy,
            'open': open_price,
            'close': close_price,
            'high': high_price,
            'low': low_price,
            'gap': gap,  # 开盘跳空
            'day_return': day_return,  # 开盘买入到收盘收益
            'max_return': max_return,  # 开盘买入到最高收益
            'min_return': min_return,  # 开盘买入到最低回撤
            'day_change': row['涨跌幅']  # 当日涨跌幅
        }
    except Exception as e:
        print(f"  获取{code}数据失败: {e}")
        return None

# 分析日期
dates = ['2026-03-17', '2026-03-18', '2026-03-19']

print("\n" + "=" * 80)
print("一、逐日回测分析")
print("=" * 80)

all_results = []

for date in dates:
    print(f"\n【{date}】")
    print("-" * 80)
    
    # 动量策略回测
    print("\n  动量策略 (追涨):")
    for code, name in momentum_picks.items():
        result = analyze_stock(code, name, 'momentum', date)
        if result:
            all_results.append(result)
            signal = "✓" if result['day_return'] > 0 else "✗"
            print(f"    {signal} {code} {name}: 开盘{result['open']:.2f} → 收盘{result['close']:.2f} "
                  f"收益{result['day_return']:+.2f}% (最高{result['max_return']:+.2f}%)")
    
    # 反转策略回测
    print("\n  反转策略 (抄底):")
    for code, name in reversal_picks.items():
        result = analyze_stock(code, name, 'reversal', date)
        if result:
            all_results.append(result)
            signal = "✓" if result['day_return'] > 0 else "✗"
            print(f"    {signal} {code} {name}: 开盘{result['open']:.2f} → 收盘{result['close']:.2f} "
                  f"收益{result['day_return']:+.2f}% (最高{result['max_return']:+.2f}%)")

# 汇总统计
print("\n" + "=" * 80)
print("二、汇总统计")
print("=" * 80)

df_results = pd.DataFrame(all_results)

if len(df_results) > 0:
    # 按策略统计
    for strategy in ['momentum', 'reversal']:
        strategy_df = df_results[df_results['strategy'] == strategy]
        if len(strategy_df) == 0:
            continue
            
        win_count = (strategy_df['day_return'] > 0).sum()
        total_count = len(strategy_df)
        win_rate = win_count / total_count * 100
        avg_return = strategy_df['day_return'].mean()
        max_profit = strategy_df['day_return'].max()
        max_loss = strategy_df['day_return'].min()
        avg_max_return = strategy_df['max_return'].mean()
        
        strategy_name = "动量策略" if strategy == 'momentum' else "反转策略"
        print(f"\n{strategy_name}:")
        print(f"  总次数: {total_count}")
        print(f"  盈利次数: {win_count} ({win_rate:.1f}%)")
        print(f"  平均收益: {avg_return:+.2f}%")
        print(f"  最大盈利: {max_profit:+.2f}%")
        print(f"  最大亏损: {max_loss:+.2f}%")
        print(f"  平均盘中最高收益: {avg_max_return:+.2f}%")
    
    # 总体统计
    print("\n总体表现:")
    win_count = (df_results['day_return'] > 0).sum()
    total_count = len(df_results)
    win_rate = win_count / total_count * 100
    avg_return = df_results['day_return'].mean()
    
    print(f"  总选股次数: {total_count}")
    print(f"  总体胜率: {win_rate:.1f}%")
    print(f"  平均收益: {avg_return:+.2f}%")
    
    # 最佳/最差表现
    best = df_results.loc[df_results['day_return'].idxmax()]
    worst = df_results.loc[df_results['day_return'].idxmin()]
    
    print(f"\n最佳表现: {best['code']} {best['name']} ({best['date']}) 收益 {best['day_return']:+.2f}%")
    print(f"最差表现: {worst['code']} {worst['name']} ({worst['date']}) 收益 {worst['day_return']:+.2f}%")

print("\n" + "=" * 80)
print("三、逐股详细回测")
print("=" * 80)

# 按股票分组展示
for code in list(momentum_picks.keys()) + list(reversal_picks.keys()):
    stock_df = df_results[df_results['code'] == code]
    if len(stock_df) == 0:
        continue
    
    name = stock_df.iloc[0]['name']
    strategy = stock_df.iloc[0]['strategy']
    
    print(f"\n{code} {name} ({'动量' if strategy == 'momentum' else '反转'}策略):")
    for _, row in stock_df.iterrows():
        print(f"  {row['date']}: 开盘{row['open']:.2f} → 收盘{row['close']:.2f} "
              f"收益{row['day_return']:+.2f}% | 盘中最高{row['max_return']:+.2f}% 最低{row['min_return']:+.2f}%")
    
    avg_return = stock_df['day_return'].mean()
    print(f"  平均收益: {avg_return:+.2f}%")

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)
