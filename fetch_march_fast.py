#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速获取3月份数据 - 多线程版本

由于单线程太慢，使用线程池加速
"""
import os
os.environ['NO_PROXY'] = 'sina.com.cn,qt.gtimg.cn,gtimg.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

import pandas as pd
from datetime import datetime
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import akshare as ak

# 3月份所有可交易日
MARCH_TRADING_DAYS = [
    '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07',
    '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14',
    '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21',
]

# 线程锁
print_lock = Lock()
data_lock = Lock()


def fetch_single_stock(args):
    """
    获取单只股票的3月份数据
    
    用于多线程执行
    """
    idx, code, name = args
    prefix = 'sh' if code.startswith('6') else 'sz'
    symbol = f'{prefix}{code}'
    
    try:
        # 直接调用AKShare，避免单例问题
        hist = ak.stock_zh_a_hist_tx(symbol=symbol)
        
        if hist is not None and len(hist) > 0:
            hist['date'] = hist['date'].astype(str)
            
            results = []
            for date in MARCH_TRADING_DAYS:
                day_data = hist[hist['date'] == date]
                if len(day_data) > 0:
                    data = day_data.iloc[0].to_dict()
                    data['code'] = code
                    data['name'] = name
                    data['date'] = date
                    results.append(data)
            
            with print_lock:
                if (idx + 1) % 10 == 0:
                    print(f"  进度: {idx + 1} 只股票处理完成")
            
            return results
        
    except Exception as e:
        with print_lock:
            if (idx + 1) % 20 == 0:
                pass  # 减少错误输出
    
    return []


def fetch_march_data_fast():
    """
    快速获取3月份数据 - 多线程版本
    """
    print("=" * 80)
    print("3月份完整数据获取 - 多线程加速版")
    print("=" * 80)
    print(f"\n目标：获取 {len(MARCH_TRADING_DAYS)} 个交易日数据")
    
    # 获取股票列表
    print("\n[1] 获取股票列表...")
    stock_list = ak.stock_info_a_code_name()
    stock_sample = stock_list.head(200)  # 取前200只，平衡速度和质量
    print(f"  本次获取: {len(stock_sample)} 只股票")
    
    # 准备参数
    stock_args = [(idx, row['code'], row['name']) 
                  for idx, row in stock_sample.iterrows()]
    
    # 多线程获取
    print(f"\n[2] 多线程获取历史数据 (8线程)...")
    print(f"  预计时间: 2-3分钟\n")
    
    all_results = []
    completed = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        # 提交所有任务
        future_to_stock = {
            executor.submit(fetch_single_stock, args): args 
            for args in stock_args
        }
        
        # 处理结果
        for future in as_completed(future_to_stock):
            try:
                result = future.result(timeout=10)
                if result:
                    all_results.extend(result)
                    completed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
    
    print(f"\n  完成! 成功:{completed} 失败:{failed}")
    print(f"  获取记录: {len(all_results)} 条")
    
    # 按日期整理
    print("\n[3] 整理数据...")
    daily_data = {date: [] for date in MARCH_TRADING_DAYS}
    
    for record in all_results:
        date = record['date']
        if date in daily_data:
            daily_data[date].append(record)
    
    # 保存数据
    print("\n[4] 保存数据...")
    os.makedirs('data/daily', exist_ok=True)
    
    for date in MARCH_TRADING_DAYS:
        if daily_data[date]:
            df = pd.DataFrame(daily_data[date])
            output_file = f'data/daily/market_{date}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"  {date}: {len(df)} 只股票")
    
    print("\n" + "=" * 80)
    print("数据获取完成！")
    print("=" * 80)
    
    return daily_data


if __name__ == "__main__":
    try:
        data = fetch_march_data_fast()
        
        # 验证
        import glob
        files = glob.glob('data/daily/market_2025-03-*.csv')
        print(f"\n[验证] 已获取 {len(files)}/{len(MARCH_TRADING_DAYS)} 天数据")
        
        if len(files) >= len(MARCH_TRADING_DAYS):
            print("\n✓ 所有交易日数据已获取！")
            print("\n现在可以运行回测:")
            print("  python march_backtest_complete.py")
        else:
            print(f"\n⚠ 获取了 {len(files)} 天数据，可以运行回测")
            
    except KeyboardInterrupt:
        print("\n\n用户中断，已保存部分数据")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
