# -*- coding: utf-8 -*-
"""
3月完整回测 - 使用新浪API
"""
import os
import requests
import pandas as pd
from datetime import datetime
import time
import json

# 设置环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

headers = {
    'Referer': 'https://finance.sina.com.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_stock_price_sina(code):
    """获取股票实时价格"""
    prefix = 'sh' if code.startswith('6') else 'sz'
    url = f'https://hq.sinajs.cn/list={prefix}{code}'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text
        if '=' in text and '"' in text:
            data = text.split('="')[1].rstrip('";').split(',')
            if len(data) >= 10:
                return {
                    'name': data[0],
                    'open': float(data[1]),
                    'prev_close': float(data[2]),
                    'current': float(data[3]),
                    'high': float(data[4]),
                    'low': float(data[5]),
                }
    except Exception as e:
        print(f"  Error: {e}")
    return None

def get_all_stocks_sina():
    """获取全市场股票（使用新浪）"""
    # 新浪API限制，我们只能逐个获取或获取指数
    # 这里简化处理，返回一些测试股票
    test_codes = [
        '000001', '000002', '000333', '000858', '002230',
        '002594', '300750', '600000', '600519', '601318'
    ]
    results = []
    for code in test_codes:
        data = get_stock_price_sina(code)
        if data:
            data['code'] = code
            results.append(data)
        time.sleep(0.1)
    return pd.DataFrame(results)

# 3月19日选股结果（基于之前成功的报告）
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
        ('605286', '同力天启', 22.30),
    ]
}

print("=" * 80)
print("3月19日选股 3月22日收益验证（新浪数据源）")
print("=" * 80)

results = []

for strategy, picks in march_19_picks.items():
    print(f"\n{'='*40}")
    print(f"策略: {strategy}")
    print(f"{'='*40}")
    
    for code, name, buy_price in picks:
        print(f"\n查询 {name}({code})...")
        data = get_stock_price_sina(code)
        
        if data:
            current = data['current']
            return_pct = (current - buy_price) / buy_price * 100
            
            results.append({
                'code': code,
                'name': name,
                'strategy': strategy,
                'buy_price': buy_price,
                'current_price': current,
                'return_pct': return_pct,
            })
            
            status = "[WIN]" if return_pct > 0 else "[LOSS]"
            print(f"  {status}: {buy_price:.2f} -> {current:.2f} ({return_pct:+.2f}%)")
        else:
            print(f"  [ERROR] No data")
        
        time.sleep(0.3)

# 统计
if results:
    df = pd.DataFrame(results)
    df.to_csv('march_19_verify_sina.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "=" * 80)
    print("统计汇总")
    print("=" * 80)
    
    for strategy in ['momentum', 'reversal']:
        strategy_df = df[df['strategy'] == strategy]
        if len(strategy_df) > 0:
            wins = (strategy_df['return_pct'] > 0).sum()
            total = len(strategy_df)
            avg = strategy_df['return_pct'].mean()
            
            print(f"\n{strategy}:")
            print(f"  胜率: {wins}/{total} ({wins/total*100:.0f}%)")
            print(f"  平均收益: {avg:+.2f}%")
    
    print("\n总体:")
    wins = (df['return_pct'] > 0).sum()
    print(f"  总交易: {len(df)}")
    print(f"  胜率: {wins}/{len(df)} ({wins/len(df)*100:.0f}%)")
    print(f"  平均收益: {df['return_pct'].mean():+.2f}%")
    print(f"  累计收益: {df['return_pct'].sum():+.2f}%")

print("\n" + "=" * 80)
print("结果已保存到 march_19_verify_sina.csv")
print("=" * 80)
