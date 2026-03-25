# -*- coding: utf-8 -*-
"""
验证3月19日选股在3月20日的收益表现
使用新浪实时数据API
"""
import os
import sys

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        del os.environ[k]

import requests
import pandas as pd

# 3月19日选股结果
momentum_picks = [
    ('sz301365', '矩阵股份'),
    ('sz301196', '唯科科技'),
    ('sz300720', '海川智能'),
    ('sz300308', '中际旭创'),
    ('sz002730', '电光科技'),
]

reversal_picks = [
    ('sz002809', '红墙股份'),
    ('sz300900', '广联航空'),
    ('sh600410', '华胜天成'),
    ('sz300606', '金太阳'),
    ('sh605286', '同力天启'),
]

# 3月19日的买入价格（根据报告中的开盘价）
buy_prices = {
    '301365': 28.08,   # 矩阵股份 涨幅7.0%
    '301196': 89.99,   # 唯科科技 涨幅6.8%
    '300720': 56.85,   # 海川智能 涨幅6.7%
    '300308': 170.00,  # 中际旭创 约6.4%
    '002730': 21.63,   # 电光科技 涨幅6.3%
    '002809': 12.15,   # 红墙股份 跌幅-7.0%
    '300900': 35.50,   # 广联航空 跌幅-6.9%
    '600410': 12.80,   # 华胜天成 跌幅-6.9%
    '300606': 18.50,   # 金太阳 跌幅-6.9%
    '605286': 22.30,   # 同力天启 跌幅-6.9%
}

headers = {'Referer': 'https://finance.sina.com.cn', 'User-Agent': 'Mozilla/5.0'}

print('=' * 80)
print('3月19日选股 3月20日收益验证')
print('买入: 3月19日 9:30开盘价 | 卖出: 3月20日 9:30开盘价')
print('=' * 80)

all_results = []

# 获取实时数据并计算收益
print('\n【正在获取3月20日开盘数据...】\n')

for strategy_name, picks in [('动量策略', momentum_picks), ('反转策略', reversal_picks)]:
    print(f'\n{strategy_name}:')
    print('-' * 80)
    
    for code, name in picks:
        try:
            url = f'https://hq.sinajs.cn/list={code}'
            r = requests.get(url, headers=headers, timeout=10)
            text = r.text
            
            # 解析新浪数据
            if '=' in text and '"' in text:
                data_part = text.split('="')[1].rstrip('";')
                fields = data_part.split(',')
                
                if len(fields) >= 10:
                    open_price = float(fields[1])      # 今日开盘
                    prev_close = float(fields[2])      # 昨日收盘(即3月19日收盘)
                    current = float(fields[3])         # 当前价
                    high = float(fields[4])            # 今日最高
                    
                    code_short = code[2:]
                    buy_price = buy_prices.get(code_short, prev_close)
                    
                    # 计算收益
                    overnight_return = (open_price - buy_price) / buy_price * 100
                    current_return = (current - buy_price) / buy_price * 100
                    max_possible = (high - buy_price) / buy_price * 100
                    
                    all_results.append({
                        'code': code_short,
                        'name': name,
                        'strategy': strategy_name,
                        'buy_price': buy_price,
                        'sell_price': open_price,
                        'current': current,
                        'overnight_return': overnight_return,
                        'current_return': current_return,
                    })
                    
                    signal = '[OK]' if overnight_return > 0 else '[FAIL]'
                    print(f'{signal} {code_short} {name}')
                    print(f'   买入: {buy_price:.2f} → 3/20开盘: {open_price:.2f} ({overnight_return:+.2f}%)')
                    print(f'   3/20当前: {current:.2f} (当前收益: {current_return:+.2f}%)')
                    print(f'   3/20最高: {high:.2f} (最高可获: {max_possible:+.2f}%)')
                    print()
        except Exception as e:
            print(f'{code}: 获取失败 - {str(e)[:50]}')

# 汇总统计
# 保存到CSV
df.to_csv('backtest_results_0319_0320.csv', index=False, encoding='utf-8-sig')
print('\n[SAVED] 数据已保存到 backtest_results_0319_0320.csv')

print('\n' + '=' * 80)
print('Summary Statistics')
print('=' * 80)

if all_results:
    df = pd.DataFrame(all_results)
    
    for strategy in ['动量策略', '反转策略']:
        strategy_df = df[df['strategy'] == strategy]
        if len(strategy_df) == 0:
            continue
        
        wins = (strategy_df['overnight_return'] > 0).sum()
        total = len(strategy_df)
        avg = strategy_df['overnight_return'].mean()
        best = strategy_df.loc[strategy_df['overnight_return'].idxmax()]
        worst = strategy_df.loc[strategy_df['overnight_return'].idxmin()]
        
        print(f'\n{strategy}:')
        print(f'  盈利: {wins}/{total} ({wins/total*100:.1f}%)')
        print(f'  平均隔夜收益: {avg:+.2f}%')
        print(f'  最佳: {best["name"]} ({best["overnight_return"]:+.2f}%)')
        print(f'  最差: {worst["name"]} ({worst["overnight_return"]:+.2f}%)')
    
    # 总体
    print('\n【总体表现】')
    wins = (df['overnight_return'] > 0).sum()
    total = len(df)
    avg = df['overnight_return'].mean()
    
    print(f'总交易次数: {total}')
    print(f'盈利次数: {wins} ({wins/total*100:.1f}%)')
    print(f'平均隔夜收益: {avg:+.2f}%')
    print(f'累计收益（等权）: {df["overnight_return"].sum():+.2f}%')

print('\n' + '=' * 80)
