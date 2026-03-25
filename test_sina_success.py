#!/usr/bin/env python3
"""
新浪/腾讯数据源测试 - 最终验证
"""
import sys
sys.path.insert(0, '.')

from core.sina_fetcher import SinaDataFetcher
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("=" * 70)
    print("盘前资金流向分析系统 - 新浪/腾讯数据源验证")
    print("=" * 70)
    
    fetcher = SinaDataFetcher()
    
    # 1. 获取数据
    print("\n[1] 获取市场数据 (200只股票样本)")
    df = fetcher.fetch_market_spot(200)
    print(f"  Result: {len(df)} stocks from {df['data_source'].iloc[0] if not df.empty else 'N/A'}")
    
    if df.empty:
        print("  FAIL: No data retrieved")
        return
    
    # 2. 市场分析
    print("\n[2] 市场分析")
    analyzer = MarketAnalyzer()
    sentiment = analyzer.analyze_market_sentiment(df)
    print(f"  Sentiment: {sentiment.get('sentiment', 'N/A')}")
    print(f"  Score: {sentiment.get('sentiment_score', 0):.1f}")
    print(f"  Up: {sentiment.get('up_count', 0)}, Down: {sentiment.get('down_count', 0)}")
    
    # 3. 选股
    print("\n[3] 选股策略")
    momentum = MomentumStrategy()
    mom_picks = momentum.select(df)
    print(f"  Momentum: {len(mom_picks)} stocks")
    
    reversal = ReversalStrategy()
    rev_picks = reversal.select(df)
    print(f"  Reversal: {len(rev_picks)} stocks")
    
    # 4. 显示样本
    print("\n[4] 动量选股结果")
    if not mom_picks.empty:
        cols = [c for c in ['code', 'name', 'latest', 'change_pct', 'volume_ratio'] if c in mom_picks.columns]
        print(mom_picks[cols].head().to_string(index=False))
    
    print("\n" + "=" * 70)
    print("新浪/腾讯数据源验证成功！")
    print("=" * 70)

if __name__ == "__main__":
    main()
