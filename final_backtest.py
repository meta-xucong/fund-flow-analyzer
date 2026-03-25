#!/usr/bin/env python3
"""
3月回测 - 使用新浪/腾讯数据源（绕过东财）
"""
import os
# 必须在导入任何网络库之前设置
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
for key in list(os.environ.keys()):
    if 'proxy' in key.lower() and key not in ['NO_PROXY', 'no_proxy']:
        os.environ[key] = ''

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.sina_fetcher import SinaDataFetcher
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy


class FinalBacktest:
    """使用新浪数据源进行回测"""
    
    def __init__(self):
        self.fetcher = SinaDataFetcher()
        self.momentum = MomentumStrategy()
        self.reversal = ReversalStrategy()
        
    def collect_multi_day_data(self, days=5):
        """
        收集多天的数据
        
        策略: 每天运行一次脚本，保存数据，累积几天后进行分析
        """
        all_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            logger.info(f"收集 {date} 数据...")
            df = self.fetcher.fetch_market_spot(500)
            
            if not df.empty:
                df['date'] = date
                all_data.append(df)
                
                # 保存每日数据
                output_dir = 'data/daily'
                os.makedirs(output_dir, exist_ok=True)
                df.to_csv(f'{output_dir}/market_{date}.csv', index=False, encoding='utf-8-sig')
                logger.info(f"  已保存 {len(df)} 只股票")
            
            if i < days - 1:
                import time
                time.sleep(1)
        
        return all_data
    
    def analyze_past_performance(self):
        """分析过去保存的数据"""
        import glob
        
        files = glob.glob('data/daily/market_*.csv')
        if len(files) < 2:
            logger.warning("数据不足，需要至少2天的数据")
            return None
        
        files.sort()
        
        results = []
        
        for i in range(len(files) - 1):
            current_file = files[i]
            next_file = files[i + 1]
            
            # 提取日期
            current_date = os.path.basename(current_file).replace('market_', '').replace('.csv', '')
            next_date = os.path.basename(next_file).replace('market_', '').replace('.csv', '')
            
            logger.info(f"\n分析 {current_date} -> {next_date}")
            
            # 读取数据
            current_df = pd.read_csv(current_file)
            next_df = pd.read_csv(next_file)
            
            if current_df.empty or next_df.empty:
                continue
            
            # 次日价格字典
            next_prices = dict(zip(next_df['code'].astype(str), next_df['latest']))
            
            # 运行选股策略
            for strategy_name, strategy in [('momentum', self.momentum), ('reversal', self.reversal)]:
                picks = strategy.select(current_df)
                
                if picks.empty:
                    continue
                
                current_prices = dict(zip(current_df['code'].astype(str), current_df['latest']))
                
                for _, row in picks.iterrows():
                    code = str(row['code'])
                    buy_price = current_prices.get(code, 0)
                    sell_price = next_prices.get(code, 0)
                    
                    if buy_price > 0 and sell_price > 0:
                        return_pct = (sell_price - buy_price) / buy_price * 100
                        
                        results.append({
                            'buy_date': current_date,
                            'sell_date': next_date,
                            'strategy': strategy_name,
                            'code': code,
                            'name': row.get('name', ''),
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'return_pct': return_pct,
                        })
        
        return pd.DataFrame(results)
    
    def generate_report(self, df):
        """生成回测报告"""
        if df is None or df.empty:
            print("没有回测结果")
            return
        
        print("\n" + "=" * 70)
        print("回测结果汇总")
        print("=" * 70)
        
        # 总体统计
        total = len(df)
        avg_return = df['return_pct'].mean()
        win_rate = (df['return_pct'] > 0).mean() * 100
        
        print(f"\n总体统计:")
        print(f"  总交易次数: {total}")
        print(f"  平均收益率: {avg_return:.2f}%")
        print(f"  胜率: {win_rate:.1f}%")
        print(f"  最大收益: {df['return_pct'].max():.2f}%")
        print(f"  最大亏损: {df['return_pct'].min():.2f}%")
        
        # 按策略
        print(f"\n按策略统计:")
        for strategy in ['momentum', 'reversal']:
            s_df = df[df['strategy'] == strategy]
            if not s_df.empty:
                print(f"\n  {strategy}:")
                print(f"    交易次数: {len(s_df)}")
                print(f"    平均收益: {s_df['return_pct'].mean():.2f}%")
                print(f"    胜率: {(s_df['return_pct'] > 0).mean() * 100:.1f}%")
        
        # 保存
        os.makedirs('reports', exist_ok=True)
        output = f'reports/backtest_{datetime.now():%Y%m%d_%H%M%S}.csv'
        df.to_csv(output, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存: {output}")


def main():
    print("=" * 70)
    print("3月回测系统 - 新浪/腾讯数据源")
    print("=" * 70)
    
    backtest = FinalBacktest()
    
    # 模式1: 收集今天数据
    print("\n【模式1】收集今日数据...")
    backtest.collect_multi_day_data(days=1)
    
    # 模式2: 分析已有数据
    print("\n【模式2】分析已有数据...")
    results = backtest.analyze_past_performance()
    
    if results is not None and not results.empty:
        backtest.generate_report(results)
    else:
        print("\n提示: 需要至少2天的历史数据才能进行回测")
        print("      请每天运行此脚本收集数据，累积几天后自动分析")


if __name__ == "__main__":
    main()
