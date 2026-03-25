# -*- coding: utf-8 -*-
"""
回测数据收集脚本

请在网络环境良好的机器上运行此脚本，收集过去3天的数据进行回测分析。

使用方法:
    python collect_backtest_data.py
    
输出:
    backtest_data_YYYYMMDD.csv - 包含所有选股的历史数据
"""
import os
import sys

# 清除代理设置 - 必须在最前面
os.environ['NO_PROXY'] = '*'
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if k in os.environ:
        del os.environ[k]

# 重新加载 akshare 模块（如果需要）
if 'akshare' in sys.modules:
    del sys.modules['akshare']

import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import time

# 选股列表 (基于3月20日报告)
STOCK_LIST = {
    # 动量策略
    '002730': {'name': '电光科技', 'strategy': 'momentum'},
    '300565': {'name': '科信技术', 'strategy': 'momentum'},
    '002756': {'name': '永兴材料', 'strategy': 'momentum'},
    '002487': {'name': '大金重工', 'strategy': 'momentum'},
    '000973': {'name': '佛塑科技', 'strategy': 'momentum'},
    # 反转策略
    '002208': {'name': '合肥城建', 'strategy': 'reversal'},
    '600589': {'name': '大位科技', 'strategy': 'reversal'},
    '600610': {'name': '中毅达', 'strategy': 'reversal'},
    '300961': {'name': '深水海纳', 'strategy': 'reversal'},
    '300201': {'name': '海伦哲', 'strategy': 'reversal'},
}

# 回测日期
DATES = ['20260317', '20260318', '20260319']

def get_stock_hist(code, start_date, end_date):
    """获取股票历史数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date
        )
        return df
    except Exception as e:
        print(f"  获取{code}失败: {e}")
        return None

def main():
    print("=" * 80)
    print("回测数据收集")
    print("=" * 80)
    print(f"\nStock count: {len(STOCK_LIST)}")
    print(f"Dates: {DATES}")
    print()
    
    all_data = []
    
    for code, info in STOCK_LIST.items():
        name = info['name']
        strategy = info['strategy']
        
        print(f"Fetching {name}({code}) [{strategy}]...")
        
        for date_str in DATES:
            df = get_stock_hist(code, date_str, date_str)
            
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                
                # 计算收益指标
                open_price = row['开盘']
                close_price = row['收盘']
                high_price = row['最高']
                low_price = row['最低']
                
                day_return = (close_price - open_price) / open_price * 100
                max_return = (high_price - open_price) / open_price * 100
                min_return = (low_price - open_price) / open_price * 100
                
                all_data.append({
                    'code': code,
                    'name': name,
                    'strategy': strategy,
                    'date': row['日期'],
                    'open': open_price,
                    'close': close_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'change_pct': row['涨跌幅'],
                    'day_return': day_return,
                    'max_return': max_return,
                    'min_return': min_return,
                })
                
                print(f"  {row['日期']}: 开盘{open_price:.2f} 收盘{close_price:.2f} 收益{day_return:+.2f}%")
            else:
                print(f"  {date_str}: 无数据")
            
            time.sleep(0.3)  # 避免请求过快
        
        print()
    
    # 保存数据
    if all_data:
        df = pd.DataFrame(all_data)
        output_file = f"backtest_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ 数据已保存: {output_file}")
        print(f"  共 {len(df)} 条记录")
        
        # 显示汇总统计
        print("\n" + "=" * 80)
        print("汇总统计")
        print("=" * 80)
        
        for strategy in ['momentum', 'reversal']:
            strategy_df = df[df['strategy'] == strategy]
            if len(strategy_df) == 0:
                continue
            
            win_count = (strategy_df['day_return'] > 0).sum()
            total = len(strategy_df)
            win_rate = win_count / total * 100
            avg_return = strategy_df['day_return'].mean()
            
            strategy_name = "动量策略" if strategy == 'momentum' else "反转策略"
            print(f"\n{strategy_name}:")
            print(f"  总次数: {total}")
            print(f"  胜率: {win_count}/{total} ({win_rate:.1f}%)")
            print(f"  平均收益: {avg_return:+.2f}%")
            print(f"  最大盈利: {strategy_df['day_return'].max():+.2f}%")
            print(f"  最大亏损: {strategy_df['day_return'].min():+.2f}%")
        
        # 总体统计
        print("\n总体:")
        win_count = (df['day_return'] > 0).sum()
        total = len(df)
        win_rate = win_count / total * 100
        avg_return = df['day_return'].mean()
        print(f"  总次数: {total}")
        print(f"  胜率: {win_count}/{total} ({win_rate:.1f}%)")
        print(f"  平均收益: {avg_return:+.2f}%")
        
        # 最佳/最差
        best = df.loc[df['day_return'].idxmax()]
        worst = df.loc[df['day_return'].idxmin()]
        print(f"\n最佳: {best['name']} {best['date']} {best['day_return']:+.2f}%")
        print(f"最差: {worst['name']} {worst['date']} {worst['day_return']:+.2f}%")
    else:
        print("[ERROR] No data collected")

if __name__ == '__main__':
    main()
