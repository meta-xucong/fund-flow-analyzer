# -*- coding: utf-8 -*-
"""
过去3天回测分析报告 - 使用更健壮的请求方式
"""
import os
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

import requests
import pandas as pd
import time

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://quote.eastmoney.com/'
}

session = requests.Session()
session.headers.update(headers)

def get_stock_hist(code, start_date, end_date):
    """获取股票历史数据"""
    # 确定市场前缀
    prefix = '1' if code.startswith('6') else '0'
    
    url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'secid': f'{prefix}.{code}',
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101',  # 日K
        'fqt': '0',
        'beg': start_date,
        'end': end_date,
        '_': str(int(time.time() * 1000))
    }
    
    try:
        r = session.get(url, params=params, timeout=15)
        data = r.json()
        
        if 'data' not in data or 'klines' not in data['data']:
            return None
        
        lines = data['data']['klines']
        records = []
        for line in lines:
            parts = line.split(',')
            records.append({
                'date': parts[0],
                'open': float(parts[1]),
                'close': float(parts[2]),
                'high': float(parts[3]),
                'low': float(parts[4]),
                'volume': float(parts[5]),
                'amount': float(parts[6]),
                'amplitude': float(parts[7]),
                'change_pct': float(parts[8]),
                'change': float(parts[9]),
                'turnover': float(parts[10]) if parts[10] else 0
            })
        
        return pd.DataFrame(records)
    except Exception as e:
        print(f"获取{code}失败: {e}")
        return None

# 选股列表
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

print("=" * 80)
print("过去3天(2026-03-17至2026-03-19)回测分析报告")
print("=" * 80)

results = []

# 分析动量选股
print("\n【动量策略回测】")
print("-" * 80)

for code, name in momentum_picks.items():
    print(f"\n{name}({code}):")
    df = get_stock_hist(code, '20260317', '20260319')
    
    if df is None or len(df) == 0:
        print("  无法获取数据")
        continue
    
    for _, row in df.iterrows():
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        day_return = (close_price - open_price) / open_price * 100
        max_return = (high_price - open_price) / open_price * 100
        
        results.append({
            'code': code,
            'name': name,
            'date': row['date'],
            'strategy': 'momentum',
            'open': open_price,
            'close': close_price,
            'high': high_price,
            'day_return': day_return,
            'max_return': max_return,
            'change_pct': row['change_pct']
        })
        
        signal = "✓" if day_return > 0 else "✗"
        print(f"  {signal} {row['date']}: 开盘{open_price:.2f}→收盘{close_price:.2f} "
              f"收益{day_return:+.2f}% (最高{max_return:+.2f}%)")
    
    time.sleep(0.5)  # 避免请求过快

# 分析反转选股
print("\n【反转策略回测】")
print("-" * 80)

for code, name in reversal_picks.items():
    print(f"\n{name}({code}):")
    df = get_stock_hist(code, '20260317', '20260319')
    
    if df is None or len(df) == 0:
        print("  无法获取数据")
        continue
    
    for _, row in df.iterrows():
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        day_return = (close_price - open_price) / open_price * 100
        max_return = (high_price - open_price) / open_price * 100
        
        results.append({
            'code': code,
            'name': name,
            'date': row['date'],
            'strategy': 'reversal',
            'open': open_price,
            'close': close_price,
            'high': high_price,
            'day_return': day_return,
            'max_return': max_return,
            'change_pct': row['change_pct']
        })
        
        signal = "✓" if day_return > 0 else "✗"
        print(f"  {signal} {row['date']}: 开盘{open_price:.2f}→收盘{close_price:.2f} "
              f"收益{day_return:+.2f}% (最高{max_return:+.2f}%)")
    
    time.sleep(0.5)

# 汇总统计
print("\n" + "=" * 80)
print("汇总统计")
print("=" * 80)

if results:
    df_results = pd.DataFrame(results)
    
    # 按策略统计
    for strategy_name, strategy_code in [('动量策略', 'momentum'), ('反转策略', 'reversal')]:
        strategy_df = df_results[df_results['strategy'] == strategy_code]
        if len(strategy_df) == 0:
            continue
        
        win_count = (strategy_df['day_return'] > 0).sum()
        total = len(strategy_df)
        win_rate = win_count / total * 100
        avg_return = strategy_df['day_return'].mean()
        
        print(f"\n{strategy_name}:")
        print(f"  总次数: {total}")
        print(f"  胜率: {win_count}/{total} ({win_rate:.1f}%)")
        print(f"  平均收益: {avg_return:+.2f}%")
        print(f"  最大单日收益: {strategy_df['day_return'].max():+.2f}%")
        print(f"  最大单日亏损: {strategy_df['day_return'].min():+.2f}%")
        print(f"  平均盘中最高: {strategy_df['max_return'].mean():+.2f}%")
    
    # 总体统计
    print("\n总体表现:")
    win_count = (df_results['day_return'] > 0).sum()
    total = len(df_results)
    win_rate = win_count / total * 100
    avg_return = df_results['day_return'].mean()
    
    print(f"  总交易次数: {total}")
    print(f"  总胜率: {win_count}/{total} ({win_rate:.1f}%)")
    print(f"  总平均收益: {avg_return:+.2f}%")
    
    # 最佳/最差
    best = df_results.loc[df_results['day_return'].idxmax()]
    worst = df_results.loc[df_results['day_return'].idxmin()]
    
    print(f"\n最佳表现: {best['name']} {best['date']} {best['day_return']:+.2f}%")
    print(f"最差表现: {worst['name']} {worst['date']} {worst['day_return']:+.2f}%")

print("\n" + "=" * 80)
