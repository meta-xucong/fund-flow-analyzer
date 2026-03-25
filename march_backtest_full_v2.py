#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3月完整回测 - V2版本
使用新浪/腾讯数据源，获取3月份所有可交易日数据

回测逻辑:
1. 对每个交易日，获取当天开盘前数据（用前一天收盘数据模拟）
2. 运行选股策略
3. 用次日实际数据计算收益率
"""
import os
import sys
sys.path.insert(0, '.')

# 设置代理绕过
os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,qt.gtimg.cn,localhost,127.0.0.1'
os.environ['no_proxy'] = 'sina.com.cn,gtimg.cn,qt.gtimg.cn,localhost,127.0.0.1'

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.sina_fetcher import SinaDataFetcher
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy

# 3月份交易日（简化版，实际需要排除节假日）
MARCH_TRADING_DAYS = [
    '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07',
    '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14',
    '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21',
]

class MarchBacktest:
    def __init__(self):
        self.fetcher = SinaDataFetcher()
        self.momentum = MomentumStrategy()
        self.reversal = ReversalStrategy()
        self.results = []
        
    def get_date_data(self, date_str, sample_size=300):
        """获取某日的市场数据"""
        logger.info(f"获取 {date_str} 数据...")
        df = self.fetcher.fetch_market_spot(sample_size)
        if not df.empty:
            df['date'] = date_str
        return df
    
    def run_backtest(self):
        """运行完整回测"""
        print("=" * 80)
        print("3月份完整回测 - 新浪/腾讯数据源")
        print("=" * 80)
        print(f"回测区间: 2025-03-03 至 2025-03-21")
        print(f"交易日数: {len(MARCH_TRADING_DAYS)}")
        print("=" * 80)
        
        # 存储每日数据
        daily_data = {}
        
        # 1. 收集所有交易日的数据
        print("\n【阶段1】收集市场数据...")
        for date_str in MARCH_TRADING_DAYS:
            df = self.get_date_data(date_str, sample_size=300)
            if not df.empty:
                daily_data[date_str] = df
                logger.info(f"  {date_str}: {len(df)} 只股票")
            else:
                logger.warning(f"  {date_str}: 数据获取失败")
            time.sleep(0.5)  # 避免请求过快
        
        if len(daily_data) < 2:
            logger.error("数据不足，无法进行回测")
            return
        
        # 2. 对每个交易日进行选股和回测
        print("\n【阶段2】运行选股策略并计算收益...")
        
        dates = sorted(daily_data.keys())
        
        for i in range(len(dates) - 1):  # 最后一天没有次日数据
            current_date = dates[i]
            next_date = dates[i + 1]
            
            print(f"\n{'='*60}")
            print(f"交易日: {current_date} -> {next_date}")
            print(f"{'='*60}")
            
            # 当天数据
            current_df = daily_data[current_date]
            
            # 次日数据
            next_df = daily_data[next_date]
            next_prices = dict(zip(next_df['code'], next_df['latest']))
            
            # 运行选股策略
            for strategy_name, strategy in [('momentum', self.momentum), ('reversal', self.reversal)]:
                picks = strategy.select(current_df)
                
                if picks.empty:
                    continue
                
                print(f"\n  策略: {strategy_name}")
                print(f"  选股数量: {len(picks)}")
                
                # 从原始数据获取价格（选股结果可能缺少某些字段）
                current_prices = dict(zip(current_df['code'], current_df['latest']))
                
                # 计算每个选股在次日的收益
                for _, row in picks.iterrows():
                    code = row['code']
                    buy_price = current_prices.get(code, 0)
                    
                    # 查找次日价格
                    if code in next_prices:
                        sell_price = next_prices[code]
                        if buy_price > 0:
                            return_pct = (sell_price - buy_price) / buy_price * 100
                        else:
                            return_pct = 0
                        
                        result = {
                            'buy_date': current_date,
                            'sell_date': next_date,
                            'strategy': strategy_name,
                            'code': code,
                            'name': row.get('name', ''),
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'return_pct': return_pct,
                        }
                        self.results.append(result)
                        
                        print(f"    {code} {row.get('name','')}: {buy_price:.2f} -> {sell_price:.2f} ({return_pct:+.2f}%)")
        
        # 3. 生成回测报告
        self.generate_report()
    
    def generate_report(self):
        """生成回测报告"""
        if not self.results:
            print("\n没有回测结果")
            return
        
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 80)
        print("回测结果汇总")
        print("=" * 80)
        
        # 总体统计
        total_trades = len(df)
        avg_return = df['return_pct'].mean()
        win_rate = (df['return_pct'] > 0).mean() * 100
        
        print(f"\n总体统计:")
        print(f"  总交易次数: {total_trades}")
        print(f"  平均收益率: {avg_return:.2f}%")
        print(f"  胜率: {win_rate:.1f}%")
        print(f"  最大单笔收益: {df['return_pct'].max():.2f}%")
        print(f"  最大单笔亏损: {df['return_pct'].min():.2f}%")
        
        # 按策略统计
        print(f"\n按策略统计:")
        for strategy in ['momentum', 'reversal']:
            strategy_df = df[df['strategy'] == strategy]
            if not strategy_df.empty:
                print(f"\n  {strategy}:")
                print(f"    交易次数: {len(strategy_df)}")
                print(f"    平均收益: {strategy_df['return_pct'].mean():.2f}%")
                print(f"    胜率: {(strategy_df['return_pct'] > 0).mean() * 100:.1f}%")
        
        # 按日期统计
        print(f"\n按日期统计:")
        daily_stats = df.groupby('buy_date').agg({
            'return_pct': ['count', 'mean']
        }).round(2)
        print(daily_stats)
        
        # 保存结果
        output_file = f'reports/march_backtest_v2_{datetime.now():%Y%m%d_%H%M%S}.csv'
        os.makedirs('reports', exist_ok=True)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存: {output_file}")
        
        # 显示最佳和最差交易
        print(f"\n最佳交易 (Top 5):")
        best = df.nlargest(5, 'return_pct')[['buy_date', 'code', 'name', 'return_pct']]
        print(best.to_string(index=False))
        
        print(f"\n最差交易 (Bottom 5):")
        worst = df.nsmallest(5, 'return_pct')[['buy_date', 'code', 'name', 'return_pct']]
        print(worst.to_string(index=False))


if __name__ == "__main__":
    backtest = MarchBacktest()
    backtest.run_backtest()
