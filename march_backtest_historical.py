#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3月历史回测 - 基于已有历史报告

利用之前保存的3月19日、20日选股数据
和今日（3月22日）的价格计算收益
"""
import os
import sys
sys.path.insert(0, '.')

os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,localhost,127.0.0.1'

import pandas as pd
import json
from datetime import datetime
from core.sina_fetcher import SinaDataFetcher


def load_historical_picks():
    """加载历史选股数据"""
    historical_data = {}
    
    # 加载3月19日选股
    mar19_file = 'reports/daily/report_2026-03-19.json'
    if os.path.exists(mar19_file):
        with open(mar19_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        picks = []
        for strategy in ['momentum', 'reversal']:
            for p in data.get('stock_picks', {}).get(strategy, []):
                code = p['code'].replace('sh', '').replace('sz', '')
                picks.append({
                    'code': code,
                    'name': p['name'],
                    'buy_price': p.get('price', 0),
                    'strategy': strategy,
                    'date': '2026-03-19'
                })
        
        if picks:
            historical_data['2026-03-19'] = pd.DataFrame(picks)
            print(f"[OK] 加载3月19日选股: {len(picks)} 只股票")
    
    # 加载3月20日选股
    mar20_file = 'reports/daily/report_2026-03-20.json'
    if os.path.exists(mar20_file):
        with open(mar20_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        picks = []
        for strategy in ['momentum', 'reversal']:
            for p in data.get('stock_picks', {}).get(strategy, []):
                code = p['code'].replace('sh', '').replace('sz', '')
                picks.append({
                    'code': code,
                    'name': p['name'],
                    'buy_price': p.get('price', 0),
                    'strategy': strategy,
                    'date': '2026-03-20'
                })
        
        if picks:
            historical_data['2026-03-20'] = pd.DataFrame(picks)
            print(f"[OK] 加载3月20日选股: {len(picks)} 只股票")
    
    # 加载今日（3月22日）数据
    today_file = 'data/daily/market_2026-03-22.csv'
    if os.path.exists(today_file):
        df = pd.read_csv(today_file)
        historical_data['2026-03-22'] = df
        print(f"[OK] 加载3月22日数据: {len(df)} 只股票")
    
    return historical_data


def calculate_returns(historical_data):
    """计算收益率"""
    results = []
    
    # 3月19日买入 -> 3月22日卖出
    if '2026-03-19' in historical_data and '2026-03-22' in historical_data:
        print("\n计算 3月19日 -> 3月22日 收益...")
        
        buy_df = historical_data['2026-03-19']
        sell_df = historical_data['2026-03-22']
        sell_prices = dict(zip(sell_df['code'].astype(str), sell_df['latest']))
        
        for _, row in buy_df.iterrows():
            code = str(row['code'])
            buy_price = row['buy_price']
            sell_price = sell_prices.get(code, 0)
            
            if buy_price > 0 and sell_price > 0:
                return_pct = (sell_price - buy_price) / buy_price * 100
                results.append({
                    'buy_date': '2026-03-19',
                    'sell_date': '2026-03-22',
                    'code': code,
                    'name': row['name'],
                    'strategy': row['strategy'],
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'days_held': 3  # 持有3天
                })
    
    # 3月20日买入 -> 3月22日卖出
    if '2026-03-20' in historical_data and '2026-03-22' in historical_data:
        print("计算 3月20日 -> 3月22日 收益...")
        
        buy_df = historical_data['2026-03-20']
        sell_df = historical_data['2026-03-22']
        sell_prices = dict(zip(sell_df['code'].astype(str), sell_df['latest']))
        
        for _, row in buy_df.iterrows():
            code = str(row['code'])
            buy_price = row['buy_price']
            sell_price = sell_prices.get(code, 0)
            
            if buy_price > 0 and sell_price > 0:
                return_pct = (sell_price - buy_price) / buy_price * 100
                results.append({
                    'buy_date': '2026-03-20',
                    'sell_date': '2026-03-22',
                    'code': code,
                    'name': row['name'],
                    'strategy': row['strategy'],
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'days_held': 2  # 持有2天
                })
    
    return pd.DataFrame(results)


def generate_report(df):
    """生成完整回测报告"""
    if df.empty:
        print("\n没有可计算的数据")
        return
    
    print("\n" + "=" * 80)
    print("3月历史回测报告 (基于已有数据)")
    print("=" * 80)
    
    # 总体统计
    total = len(df)
    avg_return = df['return_pct'].mean()
    win_rate = (df['return_pct'] > 0).mean() * 100
    
    print(f"\n【总体统计】")
    print(f"  总交易次数: {total}")
    print(f"  平均收益率: {avg_return:.2f}%")
    print(f"  胜率: {win_rate:.1f}%")
    print(f"  最大单笔盈利: {df['return_pct'].max():.2f}%")
    print(f"  最大单笔亏损: {df['return_pct'].min():.2f}%")
    
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
    print("=" * 80)
    
    for date in sorted(df['buy_date'].unique()):
        date_df = df[df['buy_date'] == date].sort_values('return_pct', ascending=False)
        sell_date = date_df['sell_date'].iloc[0]
        days_held = date_df['days_held'].iloc[0]
        
        print(f"\n【{date} 买入 -> {sell_date} 卖出 (持有{days_held}天)】")
        print(f"{'代码':<10} {'名称':<12} {'策略':<10} {'买入价':<10} {'卖出价':<10} {'收益率':<10}")
        print("-" * 80)
        
        for _, row in date_df.iterrows():
            print(f"{row['code']:<10} {row['name']:<12} {row['strategy']:<10} "
                  f"{row['buy_price']:<10.2f} {row['sell_price']:<10.2f} {row['return_pct']:>+8.2f}%")
        
        # 当日统计
        day_return = date_df['return_pct'].mean()
        day_win = (date_df['return_pct'] > 0).sum()
        day_total = len(date_df)
        print(f"\n  当日平均收益: {day_return:+.2f}% | 胜率: {day_win}/{day_total} ({day_win/day_total*100:.1f}%)")
        print()
    
    # 最佳/最差交易
    print("【最佳交易 TOP 5】")
    best = df.nlargest(5, 'return_pct')
    for _, row in best.iterrows():
        print(f"  {row['buy_date']} {row['code']} {row['name']}: {row['return_pct']:+.2f}%")
    
    print("\n【最差交易 BOTTOM 5】")
    worst = df.nsmallest(5, 'return_pct')
    for _, row in worst.iterrows():
        print(f"  {row['buy_date']} {row['code']} {row['name']}: {row['return_pct']:+.2f}%")
    
    # 保存结果
    os.makedirs('reports', exist_ok=True)
    output = f'reports/final_march_backtest_{datetime.now():%Y%m%d_%H%M%S}.csv'
    df.to_csv(output, index=False, encoding='utf-8-sig')
    print(f"\n[OK] 详细结果已保存: {output}")
    print("=" * 80)


def main():
    print("=" * 80)
    print("3月历史回测 - 基于保存的选股数据")
    print("=" * 80)
    print("\n说明：利用3月19日、20日的选股记录和今日（3月22日）价格计算收益\n")
    
    # 1. 加载历史数据
    historical_data = load_historical_picks()
    
    if len(historical_data) < 2:
        print("\n数据不足，无法进行回测")
        return
    
    # 2. 计算收益
    df = calculate_returns(historical_data)
    
    # 3. 生成报告
    generate_report(df)


if __name__ == "__main__":
    main()
