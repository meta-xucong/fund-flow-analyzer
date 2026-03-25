#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取3月份完整数据 - 所有可交易日

交易日：
3月3日-3月7日（5天）
3月10日-3月14日（5天）
3月17日-3月21日（5天）
共15个交易日

数据源：腾讯历史API（逐只获取）
"""
import os
os.environ['NO_PROXY'] = 'sina.com.cn,qt.gtimg.cn,gtimg.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

import pandas as pd
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.ultra_stable_fetcher import get_ultra_stable_fetcher


# 3月份所有可交易日
MARCH_TRADING_DAYS = [
    '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07',
    '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14',
    '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21',
]


def fetch_march_data():
    """
    获取3月份完整数据
    
    策略：
    1. 获取股票列表（前500只，加快速度）
    2. 对每只股票获取3月份历史
    3. 按日期整理保存
    """
    print("=" * 80)
    print("3月份完整数据获取")
    print("=" * 80)
    print(f"\n目标：获取 {len(MARCH_TRADING_DAYS)} 个交易日数据")
    print("交易日列表:")
    for i in range(0, len(MARCH_TRADING_DAYS), 5):
        print(f"  {', '.join(MARCH_TRADING_DAYS[i:i+5])}")
    
    fetcher = get_ultra_stable_fetcher()
    
    # 获取股票列表（取前500只热门股，加快速度）
    print("\n[1] 获取股票列表...")
    stock_list = fetcher.fetch_stock_list()
    
    # 取前500只（如果要全市场5491只，需要3-5小时）
    stock_sample = stock_list.head(500)
    print(f"  全市场: {len(stock_list)} 只")
    print(f"  本次获取: {len(stock_sample)} 只（前500只，加速处理）")
    
    # 按日期存储数据
    daily_data = {date: [] for date in MARCH_TRADING_DAYS}
    
    # 逐只获取历史数据
    print(f"\n[2] 逐只获取3月份历史数据...")
    print(f"  预计时间: {len(stock_sample) * 1.5:.0f} 秒 ({len(stock_sample) * 1.5 / 60:.1f} 分钟)")
    print("  开始获取...\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, row in stock_sample.iterrows():
        code = row['code']
        name = row['name']
        prefix = 'sh' if code.startswith('6') else 'sz'
        symbol = f'{prefix}{code}'
        
        try:
            # 获取该股票3月份历史
            hist = fetcher.fetch_tencent_hist(symbol)
            
            if hist is not None and len(hist) > 0:
                # 筛选3月份数据
                hist['date'] = hist['date'].astype(str)
                
                for date in MARCH_TRADING_DAYS:
                    day_data = hist[hist['date'] == date]
                    if len(day_data) > 0:
                        data = day_data.iloc[0].to_dict()
                        data['code'] = code
                        data['name'] = name
                        daily_data[date].append(data)
                
                success_count += 1
            else:
                fail_count += 1
            
            # 进度显示
            if (idx + 1) % 50 == 0:
                progress = (idx + 1) / len(stock_sample) * 100
                print(f"  进度: {idx + 1}/{len(stock_sample)} ({progress:.1f}%) "
                      f"成功:{success_count} 失败:{fail_count}")
            
            # 每10只暂停一下（限流）
            if idx % 10 == 0:
                time.sleep(0.3)
                
        except Exception as e:
            fail_count += 1
            logger.warning(f"获取 {code} 失败: {e}")
            continue
    
    print(f"\n  完成! 成功:{success_count} 失败:{fail_count}")
    
    # 保存每日数据
    print("\n[3] 保存每日数据...")
    import os
    os.makedirs('data/daily', exist_ok=True)
    
    total_stocks = 0
    for date in MARCH_TRADING_DAYS:
        if daily_data[date]:
            df = pd.DataFrame(daily_data[date])
            output_file = f'data/daily/market_{date}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"  {date}: {len(df)} 只股票 -> {output_file}")
            total_stocks += len(df)
    
    print(f"\n  总计: {total_stocks} 条记录")
    
    return daily_data


def verify_data():
    """验证已获取的数据"""
    import glob
    
    files = glob.glob('data/daily/market_2025-03-*.csv')
    files.sort()
    
    print("\n[数据验证]")
    print("-" * 80)
    
    total_files = 0
    total_records = 0
    
    for f in files:
        try:
            df = pd.read_csv(f)
            date = os.path.basename(f).replace('market_', '').replace('.csv', '')
            print(f"  {date}: {len(df):>4} 只股票")
            total_files += 1
            total_records += len(df)
        except:
            pass
    
    print("-" * 80)
    print(f"  文件数: {total_files}")
    print(f"  总记录: {total_records}")
    print("=" * 80)
    
    return total_files


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='获取3月份完整数据')
    parser.add_argument('--verify', action='store_true', help='只验证已有数据')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_data()
    else:
        # 获取数据
        data = fetch_march_data()
        
        # 验证
        print("\n")
        file_count = verify_data()
        
        if file_count >= len(MARCH_TRADING_DAYS):
            print("\n✓ 所有交易日数据已获取完成！")
        else:
            print(f"\n⚠ 只获取了 {file_count}/{len(MARCH_TRADING_DAYS)} 天数据")
            print("  可以重新运行继续获取")
