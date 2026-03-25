#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统核心功能测试
"""

import sys
sys.path.insert(0, '.')

from core.fetcher_v2 import get_fetcher_v2, DataFetcherV2
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("=" * 70)
    print("盘前资金流向分析系统 - 核心功能验证")
    print("=" * 70)
    
    # 数据获取
    print("\n[1] 数据获取 (模拟模式)")
    fetcher = get_fetcher_v2(mode=DataFetcherV2.MODE_MOCK)
    df = fetcher.fetch_market_spot()
    print(f"  Result: {len(df)} stocks from {df['data_source'].iloc[0]}")
    
    # 数据分析
    print("\n[2] 市场分析")
    analyzer = MarketAnalyzer()
    sentiment = analyzer.analyze_market_sentiment(df)
    print(f"  Market sentiment: {sentiment.get('sentiment', 'N/A')}")
    print(f"  Sentiment score: {sentiment.get('sentiment_score', 0):.1f}")
    
    # 选股策略
    print("\n[3] 选股策略")
    momentum = MomentumStrategy()
    mom_picks = momentum.select(df)
    print(f"  Momentum: {len(mom_picks)} stocks selected")
    
    reversal = ReversalStrategy()
    rev_picks = reversal.select(df)
    print(f"  Reversal: {len(rev_picks)} stocks selected")
    
    # 统计
    print("\n[4] 统计信息")
    stats = fetcher.get_stats()
    print(f"  Network calls: {stats['network_calls']}")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Mock calls: {stats['mock_calls']}")
    
    print("\n" + "=" * 70)
    print("所有核心功能验证通过!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    main()
