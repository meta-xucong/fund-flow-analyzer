#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算每日选股收益率

比较今日数据（买入）和次日数据（卖出）
"""
import os
import sys
sys.path.insert(0, '.')

os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,localhost,127.0.0.1'

import pandas as pd
import json
import glob
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_daily_returns():
    """
    计算所有可计算的日期的收益率
    """
    print("=" * 70)
    print("每日选股收益率计算")
    print("=" * 70)
    
    # 查找所有选股记录
    picks_files = sorted(glob.glob('reports/daily/picks_*.json'))
    
    if len(picks_files) < 2:
        print("\n数据不足，需要至少2天的数据才能计算收益")
        print(f"当前有 {len(picks_files)} 天数据")
        print("\n请明天再次运行 daily_collector.py")
        return
    
    results = []
    
    # 遍历每对连续的日期
    for i in range(len(picks_files) - 1):
        buy_file = picks_files[i]
        sell_file = picks_files[i + 1]
        
        # 提取日期
        buy_date = os.path.basename(buy_file).replace('picks_', '').replace('.json', '')
        sell_date = os.path.basename(sell_file).replace('picks_', '').replace('.json', '')
        
        print(f"\n计算 {buy_date} -> {sell_date} 的收益...")
        
        # 读取选股记录
        with open(buy_file, 'r', encoding='utf-8') as f:
            buy_data = json.load(f)
        
        # 读取次日数据文件
        sell_csv = f'data/daily/market_{sell_date}.csv'
        if not os.path.exists(sell_csv):
            logger.warning(f"  找不到 {sell_csv}，跳过")
            continue
        
        sell_df = pd.read_csv(sell_csv)
        sell_prices = dict(zip(sell_df['code'].astype(str), sell_df['latest']))
        
        # 计算每个策略的收益
        for strategy in ['momentum', 'reversal']:
            picks = buy_data.get(strategy, [])
            
            for pick in picks:
                code = str(pick['code'])
                buy_price = pick['price']
                sell_price = sell_prices.get(code, 0)
                
                if buy_price > 0 and sell_price > 0:
                    return_pct = (sell_price - buy_price) / buy_price * 100
                    
                    results.append({
                        'buy_date': buy_date,
                        'sell_date': sell_date,
                        'strategy': strategy,
                        'code': code,
                        'name': pick.get('name', ''),
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'return_pct': return_pct,
                    })
    
    if not results:
        print("\n没有可计算的收益数据")
        return
    
    # 生成报告
    df = pd.DataFrame(results)
    generate_report(df)


def generate_report(df):
    """生成回测报告"""
    print("\n" + "=" * 70)
    print("回测报告")
    print("=" * 70)
    
    # 总体统计
    total = len(df)
    avg_return = df['return_pct'].mean()
    win_rate = (df['return_pct'] > 0).mean() * 100
    
    print(f"\n【总体统计】")
    print(f"  总交易次数: {total}")
    print(f"  平均收益率: {avg_return:.2f}%")
    print(f"  胜率: {win_rate:.1f}%")
    
    # 按策略统计
    print(f"\n【按策略统计】")
    for strategy in ['momentum', 'reversal']:
        s_df = df[df['strategy'] == strategy]
        if s_df.empty:
            continue
        
        win_count = (s_df['return_pct'] > 0).sum()
        total_count = len(s_df)
        
        print(f"\n  {strategy.upper()}:")
        print(f"    交易次数: {total_count}")
        print(f"    胜率: {win_count}/{total_count} ({win_count/total_count*100:.1f}%)")
        print(f"    平均收益: {s_df['return_pct'].mean():.2f}%")
        print(f"    中位数收益: {s_df['return_pct'].median():.2f}%")
    
    # 每日详细表格
    print(f"\n【每日详细收益表】")
    print("-" * 70)
    
    for date in sorted(df['buy_date'].unique()):
        date_df = df[df['buy_date'] == date]
        print(f"\n{buy_date} 买入 -> {date_df['sell_date'].iloc[0]} 卖出:")
        print(f"{'代码':<10} {'名称':<12} {'策略':<10} {'买入价':<10} {'卖出价':<10} {'收益率':<10}")
        print("-" * 70)
        
        for _, row in date_df.iterrows():
            print(f"{row['code']:<10} {row['name']:<12} {row['strategy']:<10} "
                  f"{row['buy_price']:<10.2f} {row['sell_price']:<10.2f} {row['return_pct']:>+8.2f}%")
        
        # 当日统计
        day_return = date_df['return_pct'].mean()
        day_win = (date_df['return_pct'] > 0).sum()
        day_total = len(date_df)
        print(f"\n  当日平均收益: {day_return:+.2f}% | 胜率: {day_win}/{day_total}")
    
    # 保存结果
    os.makedirs('reports', exist_ok=True)
    output = f'reports/returns_{datetime.now():%Y%m%d_%H%M%S}.csv'
    df.to_csv(output, index=False, encoding='utf-8-sig')
    print(f"\n详细结果已保存: {output}")
    print("=" * 70)


if __name__ == "__main__":
    calculate_daily_returns()
