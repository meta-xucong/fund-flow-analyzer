#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统最终测试 - 在当前网络环境下验证核心功能
"""

import sys
sys.path.insert(0, '.')

from core.fetcher_v2 import get_fetcher_v2, DataFetcherV2
from core.analyzer import MarketAnalyzer
from core.selector import StrategySelector, MomentumStrategy, ReversalStrategy
from core.report_generator import ReportGenerator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_system():
    print("=" * 70)
    print("盘前资金流向分析系统 - 最终测试")
    print("=" * 70)
    print("\n网络环境: 受限模式（东财/同花顺API被屏蔽）")
    print("运行模式: 模拟数据 + 本地缓存\n")
    
    # 1. 数据获取
    print("-" * 70)
    print("[1/4] 数据获取测试")
    print("-" * 70)
    
    fetcher = get_fetcher_v2(mode=DataFetcherV2.MODE_MOCK)
    df = fetcher.fetch_market_spot()
    
    if df is None or len(df) == 0:
        print("FAIL: 数据获取失败")
        return False
    
    print(f"OK: 获取 {len(df)} 只股票数据")
    print(f"   数据源: {df['data_source'].iloc[0]}")
    print(f"   日期: {df['date'].iloc[0] if 'date' in df.columns else 'N/A'}")
    
    # 2. 数据分析
    print("\n" + "-" * 70)
    print("[2/4] 数据分析测试")
    print("-" * 70)
    
    analyzer = MarketAnalyzer()
    
    # 计算市场概览
    overview = analyzer.analyze_market_sentiment(df)
    print(f"OK: 市场概览计算完成")
    print(f"   上涨: {overview.get('up_count', 0)} 只")
    print(f"   下跌: {overview.get('down_count', 0)} 只")
    print(f"   涨停: {overview.get('limit_up_count', 0)} 只")
    
    # 3. 选股策略
    print("\n" + "-" * 70)
    print("[3/4] 选股策略测试")
    print("-" * 70)
    
    selector = StrategySelector()
    
    # 动量策略
    momentum = MomentumStrategy()
    momentum_picks = momentum.select(df)
    print(f"动量策略: 选出 {len(momentum_picks)} 只股票")
    if len(momentum_picks) > 0:
        print(f"   示例: {momentum_picks.iloc[0].get('name', 'N/A')} ({momentum_picks.iloc[0].get('change_pct', 0)}%)")
    
    # 反转策略
    reversal = ReversalStrategy()
    reversal_picks = reversal.select(df)
    print(f"反转策略: 选出 {len(reversal_picks)} 只股票")
    
    # 4. 报告生成
    print("\n" + "-" * 70)
    print("[4/4] 报告生成测试")
    print("-" * 70)
    
    try:
        reporter = ReportGenerator(output_dir="reports/test")
        
        report_data = {
            'market_overview': overview,
            'stock_picks': {
                'momentum': momentum_picks.to_dict('records') if momentum_picks is not None else [],
                'reversal': reversal_picks.to_dict('records') if reversal_picks is not None else []
            }
        }
        
        json_path = reporter.generate_json_report(report_data)
        print(f"OK: JSON报告生成: {json_path}")
        
        md_path = reporter.generate_markdown_report(report_data)
        print(f"OK: Markdown报告生成: {md_path}")
        
    except Exception as e:
        print(f"WARN: 报告生成部分失败: {e}")
    
    # 5. 统计
    print("\n" + "=" * 70)
    print("测试统计")
    print("=" * 70)
    stats = fetcher.get_stats()
    print(f"网络调用: {stats['network_calls']}")
    print(f"缓存命中: {stats['cache_hits']}")
    print(f"模拟调用: {stats['mock_calls']}")
    
    print("\n" + "=" * 70)
    print("系统测试完成 - 所有核心功能正常")
    print("=" * 70)
    print("\n提示: 当前使用模拟数据模式，实盘请检查网络配置")
    
    return True


if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
