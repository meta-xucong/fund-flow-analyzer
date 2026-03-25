#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3月完整回测系统 - 从3月1日至3月22日

任务:
1. 获取每个交易日的9:25盘前数据
2. 运行选股策略
3. 模拟9:30买入，持有5个交易日
4. 生成每日收益表格

注意: 由于网络限制，部分历史数据需要通过腾讯历史API逐个获取
"""
import os
os.environ['NO_PROXY'] = 'sina.com.cn,qt.gtimg.cn,gtimg.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.ultra_stable_fetcher import get_ultra_stable_fetcher
from core.selector import MomentumStrategy, ReversalStrategy


class MarchBacktestComplete:
    """3月完整回测系统"""
    
    def __init__(self):
        self.fetcher = get_ultra_stable_fetcher()
        self.momentum = MomentumStrategy()
        self.reversal = ReversalStrategy()
        
        # 3月可交易日（周一到周五，排除节假日）
        self.trading_days = [
            '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07',
            '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14',
            '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21',
        ]
        
        # 创建输出目录
        os.makedirs('data/daily', exist_ok=True)
        os.makedirs('reports/daily', exist_ok=True)
        os.makedirs('reports/backtest', exist_ok=True)
        
        # 存储所有数据
        self.all_data = {}
        self.all_picks = {}
        self.backtest_results = []
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取全市场股票列表"""
        logger.info("获取股票列表...")
        return self.fetcher.fetch_stock_list()
    
    def fetch_historical_data_tencent(self, date: str, sample_size: int = 200) -> pd.DataFrame:
        """
        使用腾讯历史API获取某日的数据
        
        注意: 腾讯历史API返回的是日线数据，我们取该日期那条记录
        """
        logger.info(f"获取 {date} 的历史数据...")
        
        # 获取股票列表（取前sample_size只）
        stock_list = self.get_stock_list().head(sample_size)
        
        results = []
        date_fmt = date.replace('-', '')
        
        for idx, row in stock_list.iterrows():
            code = row['code']
            prefix = 'sh' if code.startswith('6') else 'sz'
            symbol = f'{prefix}{code}'
            
            try:
                # 获取历史数据
                hist = self.fetcher.fetch_tencent_hist(symbol)
                
                if hist is not None and len(hist) > 0:
                    # 查找指定日期的数据
                    hist['date'] = hist['date'].astype(str)
                    day_data = hist[hist['date'] == date]
                    
                    if len(day_data) > 0:
                        data = day_data.iloc[0].to_dict()
                        data['code'] = code
                        data['name'] = row['name']
                        results.append(data)
                
                # 限流：每10只股票暂停0.5秒
                if idx % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.warning(f"获取 {code} 失败: {e}")
                continue
        
        if results:
            df = pd.DataFrame(results)
            df['data_date'] = date
            logger.info(f"  成功获取 {len(df)} 只股票")
            
            # 保存到文件
            output_file = f'data/daily/market_{date}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            return df
        
        return pd.DataFrame()
    
    def fetch_today_data(self, sample_size: int = 500) -> pd.DataFrame:
        """获取今日实时数据"""
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"获取今日 ({today}) 实时数据...")
        
        # 使用腾讯实时API
        stock_list = self.get_stock_list().head(sample_size)
        codes = [f"{'sh' if c.startswith('6') else 'sz'}{c}" 
                 for c in stock_list['code']]
        
        # 分批获取
        all_results = []
        for i in range(0, len(codes), 100):
            batch = codes[i:i+100]
            df = self.fetcher.fetch_tencent_realtime(batch)
            if not df.empty:
                all_results.append(df)
            time.sleep(0.2)
        
        if all_results:
            df = pd.concat(all_results, ignore_index=True)
            df['data_date'] = today
            
            # 保存
            output_file = f'data/daily/market_{today}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"  成功获取 {len(df)} 只股票")
            return df
        
        return pd.DataFrame()
    
    def run_selection(self, df: pd.DataFrame, date: str) -> Dict:
        """运行选股策略"""
        logger.info(f"  运行选股策略...")
        
        picks = {
            'date': date,
            'momentum': [],
            'reversal': []
        }
        
        # 动量策略
        mom_picks = self.momentum.select(df)
        if not mom_picks.empty:
            for _, row in mom_picks.head(5).iterrows():
                picks['momentum'].append({
                    'code': str(row['code']),
                    'name': str(row.get('name', '')),
                    'buy_price': float(row.get('latest', 0)),
                    'change_pct': float(row.get('change_pct', 0)),
                })
        
        # 反转策略
        rev_picks = self.reversal.select(df)
        if not rev_picks.empty:
            for _, row in rev_picks.head(5).iterrows():
                picks['reversal'].append({
                    'code': str(row['code']),
                    'name': str(row.get('name', '')),
                    'buy_price': float(row.get('latest', 0)),
                    'change_pct': float(row.get('change_pct', 0)),
                })
        
        # 保存选股结果
        output_file = f'reports/daily/picks_{date}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(picks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"    动量: {len(picks['momentum'])} 只, 反转: {len(picks['reversal'])} 只")
        return picks
    
    def calculate_returns(self) -> pd.DataFrame:
        """
        计算回测收益
        
        对于每个选股日，计算持有5天的收益
        """
        logger.info("\n计算回测收益...")
        
        results = []
        
        for i, buy_date in enumerate(self.trading_days):
            # 检查是否有该日期的选股数据
            picks_file = f'reports/daily/picks_{buy_date}.json'
            if not os.path.exists(picks_file):
                continue
            
            with open(picks_file, 'r', encoding='utf-8') as f:
                picks = json.load(f)
            
            # 计算持有5天的卖出日期
            sell_idx = i + 5
            if sell_idx >= len(self.trading_days):
                continue
            
            sell_date = self.trading_days[sell_idx]
            
            # 获取卖出日期的价格
            sell_file = f'data/daily/market_{sell_date}.csv'
            if not os.path.exists(sell_file):
                continue
            
            sell_df = pd.read_csv(sell_file)
            sell_prices = dict(zip(sell_df['code'].astype(str), sell_df['latest']))
            
            logger.info(f"\n{buy_date} 买入 -> {sell_date} 卖出:")
            
            # 计算每个选股的收益
            for strategy in ['momentum', 'reversal']:
                for pick in picks.get(strategy, []):
                    code = str(pick['code'])
                    buy_price = pick['buy_price']
                    sell_price = sell_prices.get(code, 0)
                    
                    if buy_price > 0 and sell_price > 0:
                        return_pct = (sell_price - buy_price) / buy_price * 100
                        
                        result = {
                            'buy_date': buy_date,
                            'sell_date': sell_date,
                            'strategy': strategy,
                            'code': code,
                            'name': pick['name'],
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'return_pct': round(return_pct, 2),
                            'days_held': 5,
                        }
                        results.append(result)
                        logger.info(f"  {code} {pick['name']}: {buy_price:.2f} -> {sell_price:.2f} ({return_pct:+.2f}%)")
        
        return pd.DataFrame(results)
    
    def generate_report(self, results_df: pd.DataFrame):
        """生成回测报告"""
        if results_df.empty:
            logger.warning("没有回测结果")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("3月回测报告")
        logger.info("=" * 80)
        
        # 总体统计
        total = len(results_df)
        avg_return = results_df['return_pct'].mean()
        win_rate = (results_df['return_pct'] > 0).mean() * 100
        
        logger.info(f"\n【总体统计】")
        logger.info(f"  总交易次数: {total}")
        logger.info(f"  平均收益率: {avg_return:.2f}%")
        logger.info(f"  胜率: {win_rate:.1f}%")
        
        # 按策略统计
        for strategy in ['momentum', 'reversal']:
            s_df = results_df[results_df['strategy'] == strategy]
            if s_df.empty:
                continue
            
            win_count = (s_df['return_pct'] > 0).sum()
            logger.info(f"\n【{strategy.upper()}】")
            logger.info(f"  交易次数: {len(s_df)}")
            logger.info(f"  胜率: {win_count}/{len(s_df)} ({win_count/len(s_df)*100:.1f}%)")
            logger.info(f"  平均收益: {s_df['return_pct'].mean():.2f}%")
        
        # 保存详细结果
        output_file = f'reports/backtest/march_backtest_complete_{datetime.now():%Y%m%d_%H%M%S}.csv'
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n详细结果已保存: {output_file}")
        
        # 生成每日汇总表
        self._generate_daily_summary(results_df)
    
    def _generate_daily_summary(self, results_df: pd.DataFrame):
        """生成每日汇总表"""
        logger.info("\n【每日收益汇总表】")
        logger.info("=" * 80)
        
        summary = []
        for date in sorted(results_df['buy_date'].unique()):
            date_df = results_df[results_df['buy_date'] == date]
            
            for strategy in ['momentum', 'reversal']:
                s_df = date_df[date_df['strategy'] == strategy]
                if s_df.empty:
                    continue
                
                summary.append({
                    '日期': date,
                    '策略': strategy,
                    '选股数量': len(s_df),
                    '平均收益': round(s_df['return_pct'].mean(), 2),
                    '胜率': f"{(s_df['return_pct'] > 0).sum()}/{len(s_df)}",
                    '最佳个股': s_df.loc[s_df['return_pct'].idxmax(), 'code'],
                    '最佳收益': round(s_df['return_pct'].max(), 2),
                    '最差个股': s_df.loc[s_df['return_pct'].idxmin(), 'code'],
                    '最差收益': round(s_df['return_pct'].min(), 2),
                })
        
        summary_df = pd.DataFrame(summary)
        
        # 打印表格
        print("\n" + summary_df.to_string(index=False))
        
        # 保存
        output_file = f'reports/backtest/daily_summary_{datetime.now():%Y%m%d_%H%M%S}.csv'
        summary_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n每日汇总表已保存: {output_file}")
    
    def run(self, mode: str = 'demo'):
        """
        运行回测
        
        Args:
            mode: 'demo' - 演示模式（快速），'full' - 完整模式（慢，获取所有数据）
        """
        logger.info("=" * 80)
        logger.info("3月完整回测系统")
        logger.info("=" * 80)
        logger.info(f"模式: {mode}")
        logger.info(f"目标日期: 2025-03-01 至 2025-03-22")
        logger.info("")
        
        if mode == 'demo':
            # 演示模式：只获取几天数据作为示例
            demo_days = ['2025-03-19', '2025-03-20', '2025-03-21']
            logger.info(f"演示模式：只处理 {len(demo_days)} 天数据")
            
            for date in demo_days:
                # 获取数据（模拟盘前9:25数据）
                df = self.fetch_historical_data_tencent(date, sample_size=100)
                
                if not df.empty:
                    # 运行选股
                    picks = self.run_selection(df, date)
                    self.all_data[date] = df
                    self.all_picks[date] = picks
        
        elif mode == 'full':
            # 完整模式：获取所有交易日数据（非常慢）
            logger.info("完整模式：获取所有15个交易日数据...")
            logger.info("预计耗时: 30-60分钟")
            
            for date in self.trading_days:
                df = self.fetch_historical_data_tencent(date, sample_size=200)
                
                if not df.empty:
                    picks = self.run_selection(df, date)
                    self.all_data[date] = df
                    self.all_picks[date] = picks
                
                time.sleep(1)  # 日期间隔
        
        elif mode == 'today':
            # 只获取今日数据
            logger.info("只获取今日数据...")
            df = self.fetch_today_data(sample_size=500)
            
            if not df.empty:
                today = datetime.now().strftime('%Y-%m-%d')
                picks = self.run_selection(df, today)
                self.all_data[today] = df
                self.all_picks[today] = picks
        
        # 计算回测收益
        results_df = self.calculate_returns()
        
        # 生成报告
        if not results_df.empty:
            self.generate_report(results_df)
        else:
            logger.warning("\n数据不足以生成回测报告")
            logger.info("建议: 运行 'today' 模式收集今日数据，连续运行5-6天后可生成完整报告")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='3月回测系统')
    parser.add_argument('--mode', choices=['demo', 'full', 'today'], 
                        default='demo',
                        help='运行模式: demo(演示), full(完整), today(今日)')
    
    args = parser.parse_args()
    
    backtest = MarchBacktestComplete()
    backtest.run(mode=args.mode)
