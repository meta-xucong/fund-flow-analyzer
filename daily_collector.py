#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日数据收集器

每天9:25运行，收集市场数据并运行选股策略
第二天计算收益
"""
import os
import sys
sys.path.insert(0, '.')

# 设置代理绕过
os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,localhost,127.0.0.1'

import pandas as pd
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.sina_fetcher import SinaDataFetcher
from core.selector import MomentumStrategy, ReversalStrategy


def collect_daily_data():
    """
    收集每日9:25数据
    
    流程：
    1. 获取全市场股票列表
    2. 获取实时行情（500只样本）
    3. 运行选股策略
    4. 保存数据和选股结果
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 70)
    print(f"每日数据收集 - {today} 09:25")
    print("=" * 70)
    
    fetcher = SinaDataFetcher()
    
    # 1. 获取市场数据
    logger.info("获取市场数据...")
    df = fetcher.fetch_market_spot(500)
    
    if df.empty:
        logger.error("数据获取失败")
        return False
    
    logger.info(f"获取 {len(df)} 只股票数据")
    
    # 2. 保存原始数据
    os.makedirs('data/daily', exist_ok=True)
    data_file = f'data/daily/market_{today}.csv'
    df.to_csv(data_file, index=False, encoding='utf-8-sig')
    logger.info(f"数据已保存: {data_file}")
    
    # 3. 运行选股策略
    logger.info("运行选股策略...")
    momentum = MomentumStrategy()
    reversal = ReversalStrategy()
    
    mom_picks = momentum.select(df)
    rev_picks = reversal.select(df)
    
    # 4. 保存选股结果
    picks = {
        'date': today,
        'time': '09:25',
        'momentum': [],
        'reversal': []
    }
    
    if not mom_picks.empty:
        # 保存前10只
        for _, row in mom_picks.head(10).iterrows():
            picks['momentum'].append({
                'code': str(row['code']),
                'name': str(row.get('name', '')),
                'price': float(row.get('latest', 0)),
                'change_pct': float(row.get('change_pct', 0)),
                'volume_ratio': float(row.get('volume_ratio', 0)) if 'volume_ratio' in row else None,
            })
    
    if not rev_picks.empty:
        for _, row in rev_picks.head(10).iterrows():
            picks['reversal'].append({
                'code': str(row['code']),
                'name': str(row.get('name', '')),
                'price': float(row.get('latest', 0)),
                'change_pct': float(row.get('change_pct', 0)),
            })
    
    os.makedirs('reports/daily', exist_ok=True)
    picks_file = f'reports/daily/picks_{today}.json'
    with open(picks_file, 'w', encoding='utf-8') as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"选股结果已保存: {picks_file}")
    
    # 5. 打印今日选股
    print("\n【今日选股 - 9:25】")
    print(f"\n动量策略 ({len(picks['momentum'])} 只):")
    for s in picks['momentum'][:5]:
        print(f"  {s['code']} {s['name']}: {s['price']:.2f} ({s['change_pct']:+.2f}%)")
    
    print(f"\n反转策略 ({len(picks['reversal'])} 只):")
    for s in picks['reversal'][:5]:
        print(f"  {s['code']} {s['name']}: {s['price']:.2f} ({s['change_pct']:+.2f}%)")
    
    print("\n" + "=" * 70)
    print(f"数据收集完成！请明天9:25再次运行，计算今日选股收益。")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    collect_daily_data()
