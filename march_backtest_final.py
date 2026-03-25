#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3月完整回测系统 - 最终版

任务：
1. 收集3月份所有可交易日数据
2. 每天9:30开盘前运行选股策略
3. 用次日数据计算实际收益率
4. 生成完整回测报告
"""
import os
import sys
sys.path.insert(0, '.')

os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,localhost,127.0.0.1'

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.sina_fetcher import SinaDataFetcher
from core.analyzer import MarketAnalyzer
from core.selector import MomentumStrategy, ReversalStrategy


class MarchBacktestSystem:
    """3月回测系统"""
    
    def __init__(self):
        self.fetcher = SinaDataFetcher()
        self.analyzer = MarketAnalyzer()
        self.momentum = MomentumStrategy()
        self.reversal = ReversalStrategy()
        
        # 3月份已知的可交易日（2025年3月）
        self.trading_days = [
            '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07',
            '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14',
            '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21',
        ]
    
    def collect_historical_data(self):
        """
        收集历史数据
        
        策略：
        1. 检查已有的JSON报告
        2. 提取其中的选股数据和价格信息
        3. 补充缺失的日期
        """
        historical_data = {}
        
        # 从JSON报告中提取历史数据
        json_files = glob.glob('reports/daily/report_*.json')
        for json_file in json_files:
            date_str = os.path.basename(json_file).replace('report_', '').replace('.json', '')
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取股票列表和价格
                stock_picks = data.get('stock_picks', {})
                
                # 构建当日数据DataFrame
                stocks = []
                for strategy in ['momentum', 'reversal']:
                    for pick in stock_picks.get(strategy, []):
                        code = pick.get('code', '').replace('sh', '').replace('sz', '')
                        stocks.append({
                            'code': code,
                            'name': pick.get('name', ''),
                            'latest': pick.get('price', pick.get('latest', 0)),
                            'change_pct': pick.get('change_pct', 0),
                            'strategy': strategy,
                            'date': date_str
                        })
                
                if stocks:
                    historical_data[date_str] = pd.DataFrame(stocks)
                    logger.info(f"从 {json_file} 加载了 {len(stocks)} 只股票")
            
            except Exception as e:
                logger.warning(f"读取 {json_file} 失败: {e}")
        
        return historical_data
    
    def collect_today_data(self):
        """收集今日数据"""
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"收集今日 ({today}) 数据...")
        
        # 获取500只股票样本
        df = self.fetcher.fetch_market_spot(500)
        
        if not df.empty:
            # 保存数据
            os.makedirs('data/daily', exist_ok=True)
            df.to_csv(f'data/daily/market_{today}.csv', index=False, encoding='utf-8-sig')
            
            # 运行选股策略
            picks = self.run_selection(df, today)
            
            return df, picks
        
        return None, None
    
    def run_selection(self, df, date_str):
        """运行选股策略"""
        logger.info(f"运行选股策略...")
        
        picks = {
            'date': date_str,
            'momentum': [],
            'reversal': []
        }
        
        # 动量策略
        mom_picks = self.momentum.select(df)
        if not mom_picks.empty:
            picks['momentum'] = mom_picks.head(10).to_dict('records')
        
        # 反转策略
        rev_picks = self.reversal.select(df)
        if not rev_picks.empty:
            picks['reversal'] = rev_picks.head(10).to_dict('records')
        
        logger.info(f"  动量: {len(picks['momentum'])} 只, 反转: {len(picks['reversal'])} 只")
        
        # 保存选股结果
        os.makedirs('reports/daily', exist_ok=True)
        with open(f'reports/daily/picks_{date_str}.json', 'w', encoding='utf-8') as f:
            json.dump(picks, f, ensure_ascii=False, indent=2)
        
        return picks
    
    def calculate_returns(self, historical_data):
        """
        计算收益率
        
        对于已有历史数据的日期，用次日数据计算收益
        """
        if len(historical_data) < 2:
            logger.warning("历史数据不足，无法计算收益率")
            return None
        
        results = []
        
        # 按日期排序
        dates = sorted(historical_data.keys())
        
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            current_df = historical_data[current_date]
            next_df = historical_data[next_date]
            
            # 构建次日价格字典
            next_prices = {}
            for _, row in next_df.iterrows():
                code = str(row['code'])
                next_prices[code] = row['latest']
            
            logger.info(f"\n计算 {current_date} -> {next_date} 的收益...")
            
            # 计算每只股票的收益
            for _, row in current_df.iterrows():
                code = str(row['code'])
                buy_price = row['latest']
                sell_price = next_prices.get(code, 0)
                
                if buy_price > 0 and sell_price > 0:
                    return_pct = (sell_price - buy_price) / buy_price * 100
                    
                    results.append({
                        'buy_date': current_date,
                        'sell_date': next_date,
                        'code': code,
                        'name': row.get('name', ''),
                        'strategy': row.get('strategy', 'unknown'),
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'return_pct': return_pct,
                    })
        
        return pd.DataFrame(results)
    
    def generate_report(self, returns_df):
        """生成回测报告"""
        if returns_df is None or returns_df.empty:
            print("\n没有回测结果")
            return
        
        print("\n" + "=" * 80)
        print("3月回测报告")
        print("=" * 80)
        
        # 总体统计
        total_trades = len(returns_df)
        avg_return = returns_df['return_pct'].mean()
        win_rate = (returns_df['return_pct'] > 0).mean() * 100
        median_return = returns_df['return_pct'].median()
        
        print(f"\n【总体统计】")
        print(f"  总交易次数: {total_trades}")
        print(f"  平均收益率: {avg_return:.2f}%")
        print(f"  中位数收益: {median_return:.2f}%")
        print(f"  胜率: {win_rate:.1f}%")
        print(f"  最大单笔收益: {returns_df['return_pct'].max():.2f}%")
        print(f"  最大单笔亏损: {returns_df['return_pct'].min():.2f}%")
        
        # 按策略统计
        print(f"\n【按策略统计】")
        for strategy in ['momentum', 'reversal']:
            strategy_df = returns_df[returns_df['strategy'] == strategy]
            if not strategy_df.empty:
                win_count = (strategy_df['return_pct'] > 0).sum()
                total_count = len(strategy_df)
                
                print(f"\n  {strategy.upper()}:")
                print(f"    交易次数: {total_count}")
                print(f"    盈利次数: {win_count}")
                print(f"    胜率: {win_count/total_count*100:.1f}%")
                print(f"    平均收益: {strategy_df['return_pct'].mean():.2f}%")
                print(f"    中位数收益: {strategy_df['return_pct'].median():.2f}%")
        
        # 按日期统计
        print(f"\n【按日期统计】")
        daily_stats = returns_df.groupby('buy_date').agg({
            'return_pct': ['count', 'mean', 'sum']
        }).round(2)
        print(daily_stats)
        
        # 最佳/最差交易
        print(f"\n【最佳交易 Top 5】")
        best = returns_df.nlargest(5, 'return_pct')
        for _, row in best.iterrows():
            print(f"  {row['buy_date']} {row['code']} {row['name']}: {row['return_pct']:+.2f}%")
        
        print(f"\n【最差交易 Bottom 5】")
        worst = returns_df.nsmallest(5, 'return_pct')
        for _, row in worst.iterrows():
            print(f"  {row['buy_date']} {row['code']} {row['name']}: {row['return_pct']:+.2f}%")
        
        # 保存结果
        os.makedirs('reports', exist_ok=True)
        output_file = f'reports/march_backtest_final_{datetime.now():%Y%m%d_%H%M%S}.csv'
        returns_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n详细结果已保存: {output_file}")
        
        print("\n" + "=" * 80)
    
    def run(self):
        """运行完整回测流程"""
        print("=" * 80)
        print("3月完整回测系统")
        print("=" * 80)
        
        # 1. 收集历史数据
        print("\n【阶段1】收集历史数据...")
        historical_data = self.collect_historical_data()
        
        # 2. 收集今日数据
        print("\n【阶段2】收集今日数据...")
        today_df, today_picks = self.collect_today_data()
        
        if today_df is not None:
            today_str = datetime.now().strftime('%Y-%m-%d')
            historical_data[today_str] = today_df
        
        logger.info(f"\n共收集 {len(historical_data)} 天的数据")
        
        # 3. 计算收益率
        print("\n【阶段3】计算收益率...")
        returns_df = self.calculate_returns(historical_data)
        
        # 4. 生成报告
        print("\n【阶段4】生成回测报告...")
        self.generate_report(returns_df)


if __name__ == "__main__":
    system = MarchBacktestSystem()
    system.run()
