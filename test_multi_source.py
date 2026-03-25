#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源获取器测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.multi_source_fetcher import get_multi_source_fetcher
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("多数据源获取器测试")
    print("=" * 60)
    
    fetcher = get_multi_source_fetcher()
    
    # 测试实时行情获取
    print("\n[测试1] 实时行情获取")
    df = fetcher.fetch_market_spot(max_retries=2, retry_delay=1.0)
    if df is not None:
        print(f"OK: 成功获取 {len(df)} 条记录")
        if 'data_source' in df.columns:
            print(f"   数据源: {df['data_source'].iloc[0]}")
        print(f"   列数: {len(df.columns)}")
        print(f"   列名: {list(df.columns)[:8]}...")  # 显示前8个列名
    else:
        print("FAIL: 获取失败")
    
    # 显示数据源统计
    print("\n[测试2] 数据源统计")
    stats = fetcher.get_source_stats()
    print(stats.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
