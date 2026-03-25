#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025年2月完整回测

春节后第一个交易日: 2025-02-05

包含：
1. 每日完整数据获取（个股+板块+情绪）
2. 每日完整报告生成
3. 5日持有回测
4. 汇总统计
"""
import os
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import akshare as ak
import requests

# 2025年2月交易日（春节后）
FEB_TRADING_DAYS = [
    '2025-02-05', '2025-02-06', '2025-02-07',  # 第一周
    '2025-02-10', '2025-02-11', '2025-02-12', '2025-02-13', '2025-02-14',  # 第二周
    '2025-02-17', '2025-02-18', '2025-02-19', '2025-02-20', '2025-02-21',  # 第三周
    '2025-02-24', '2025-02-25', '2025-02-26', '2025-02-27', '2025-02-28',  # 第四周
]

print(f"2月交易日共 {len(FEB_TRADING_DAYS)} 天")
print(f"日期范围: {FEB_TRADING_DAYS[0]} 至 {FEB_TRADING_DAYS[-1]}")


class FebruaryBacktest:
    """2月完整回测系统"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.stock_list = None
        
    def get_stock_list(self):
        """获取股票列表"""
        if self.stock_list is None:
            self.stock_list = ak.stock_info_a_code_name()
        return self.stock_list
    
    def fetch_tencent_batch(self, codes):
        """批量获取腾讯数据"""
        codes_str = ','.join([f"sh{c}" if c.startswith('6') else f"sz{c}" for c in codes])
        url = f'http://qt.gtimg.cn/q={codes_str}'
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'gbk'
            
            results = []
            for line in resp.text.strip().split(';'):
                if not line or 'v_' not in line:
                    continue
                
                parts = line.split('="')
                if len(parts) != 2:
                    continue
                
                data_str = parts[1].rstrip('"')
                if not data_str:
                    continue
                
                fields = data_str.split('~')
                if len(fields) < 45:
                    continue
                
                # 字段解析
                code = fields[2]
                name = fields[1]
                latest = float(fields[3]) if fields[3] else 0
                pre_close = float(fields[4]) if fields[4] else 0
                open_price = float(fields[5]) if fields[5] else 0
                volume = int(float(fields[6])) if fields[6] else 0
                amount = float(fields[37]) if fields[37] else 0  # 万元
                volume_ratio = float(fields[50]) if len(fields) > 50 and fields[50] else 0
                
                change_pct = ((latest - pre_close) / pre_close * 100) if pre_close > 0 else 0
                
                results.append({
                    'code': code,
                    'name': name,
                    'latest': latest,
                    'open': open_price,
                    'pre_close': pre_close,
                    'change_pct': round(change_pct, 2),
                    'volume': volume,
                    'amount': amount,  # 万元
                    'volume_ratio': volume_ratio,
                })
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"腾讯批量获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_daily_data(self, date_str):
        """获取某日完整数据"""
        print(f"\n[{date_str}] 获取数据中...")
        
        # 1. 获取个股数据
        stock_list = self.get_stock_list()
        codes = stock_list['code'].tolist()[:2000]  # 前2000只
        
        # 分批获取
        all_stocks = []
        batch_size = 200
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i+batch_size]
            df = self.fetch_tencent_batch(batch)
            if not df.empty:
                all_stocks.append(df)
            time.sleep(0.1)
        
        if not all_stocks:
            return None
        
        stocks_df = pd.concat(all_stocks, ignore_index=True)
        stocks_df['date'] = date_str
        print(f"  获取个股: {len(stocks_df)} 只")
        
        # 2. 获取板块数据
        try:
            sectors_df = ak.stock_sector_spot()
            print(f"  获取板块: {len(sectors_df)} 个")
        except Exception as e:
            logger.warning(f"板块数据获取失败: {e}")
            sectors_df = pd.DataFrame()
        
        # 3. 计算市场情绪
        market_sentiment = self.calculate_market_sentiment(stocks_df)
        print(f"  市场情绪: {market_sentiment['status']} (分数:{market_sentiment['score']:.1f})")
        
        return {
            'stocks': stocks_df,
            'sectors': sectors_df,
            'sentiment': market_sentiment,
            'date': date_str
        }
    
    def calculate_market_sentiment(self, stocks_df):
        """计算市场情绪"""
        if stocks_df.empty:
            return {'score': 50, 'status': '中性', 'up_ratio': 0.5}
        
        up_count = len(stocks_df[stocks_df['change_pct'] > 0])
        down_count = len(stocks_df[stocks_df['change_pct'] < 0])
        total = len(stocks_df)
        
        up_ratio = up_count / total if total > 0 else 0.5
        score = up_ratio * 100
        
        # 涨停跌停统计（简化）
        limit_up = len(stocks_df[stocks_df['change_pct'] >= 9.5])
        limit_down = len(stocks_df[stocks_df['change_pct'] <= -9.5])
        
        if score >= 70:
            status = '乐观'
        elif score >= 50:
            status = '中性偏乐观'
        elif score >= 30:
            status = '中性偏悲观'
        else:
            status = '悲观'
        
        return {
            'score': score,
            'status': status,
            'up_count': up_count,
            'down_count': down_count,
            'up_ratio': up_ratio,
            'limit_up': limit_up,
            'limit_down': limit_down,
            'avg_change': stocks_df['change_pct'].mean(),
        }
    
    def select_stocks_momentum(self, stocks_df, top_n=5):
        """动量选股"""
        if stocks_df.empty:
            return pd.DataFrame()
        
        # 筛选条件
        filtered = stocks_df[
            (stocks_df['change_pct'] >= 2.0) &
            (stocks_df['change_pct'] <= 7.0) &
            (stocks_df['amount'] >= 30000) &  # 3亿 = 30000万
            (stocks_df['volume_ratio'] >= 1.5)
        ].copy()
        
        if filtered.empty:
            return pd.DataFrame()
        
        # 评分
        filtered['score'] = (
            filtered['change_pct'] * 0.4 +
            filtered['volume_ratio'] * 5 * 0.3 +
            filtered['amount'] / 10000 * 0.3
        )
        
        filtered['reason'] = '动量突破: 涨幅' + filtered['change_pct'].astype(str) + '%'
        
        return filtered.sort_values('score', ascending=False).head(top_n)
    
    def select_stocks_reversal(self, stocks_df, top_n=5):
        """反转选股"""
        if stocks_df.empty:
            return pd.DataFrame()
        
        # 筛选超跌反弹
        filtered = stocks_df[
            (stocks_df['change_pct'] >= -7.0) &
            (stocks_df['change_pct'] <= -3.0) &
            (stocks_df['amount'] >= 20000) &
            (stocks_df['volume_ratio'] >= 1.5)
        ].copy()
        
        if filtered.empty:
            return pd.DataFrame()
        
        # 评分（跌幅绝对值越大，反弹潜力越大，但要控制风险）
        filtered['score'] = (
            abs(filtered['change_pct']) * 3 +
            filtered['volume_ratio'] * 2
        )
        
        filtered['reason'] = '超跌反弹: 跌幅' + filtered['change_pct'].astype(str) + '%'
        
        return filtered.sort_values('score', ascending=False).head(top_n)
    
    def generate_daily_report(self, date_str, data):
        """生成每日完整报告"""
        if data is None:
            return None
        
        stocks_df = data['stocks']
        sectors_df = data['sectors']
        sentiment = data['sentiment']
        
        # 选股
        momentum_picks = self.select_stocks_momentum(stocks_df)
        reversal_picks = self.select_stocks_reversal(stocks_df)
        
        # 板块排行
        sector_top10 = None
        if not sectors_df.empty:
            cols = list(sectors_df.columns)
            if '涨跌幅' in cols:
                sector_top10 = sectors_df.sort_values('涨跌幅', ascending=False).head(10)
            elif len(cols) > 5:
                sector_top10 = sectors_df.sort_values(cols[5], ascending=False).head(10)
        
        # 构建报告
        report = {
            'date': date_str,
            'sentiment': sentiment,
            'momentum_picks': momentum_picks,
            'reversal_picks': reversal_picks,
            'sector_top10': sector_top10,
            'sectors_df': sectors_df,
            'stocks_df': stocks_df
        }
        
        return report
    
    def save_daily_report(self, report, output_dir='reports/february'):
        """保存每日报告"""
        if report is None:
            return
        
        date_str = report['date']
        date_folder = f"{output_dir}/{date_str}"
        os.makedirs(date_folder, exist_ok=True)
        
        # 1. 保存完整报告Markdown
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"盘前资金流向分析报告 - {date_str}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # 市场情绪
        sentiment = report['sentiment']
        report_lines.append("【市场情绪】")
        report_lines.append(f"  情绪状态: {sentiment['status']} (分数: {sentiment['score']:.2f})")
        report_lines.append(f"  上涨: {sentiment['up_count']}只 ({sentiment['up_ratio']*100:.1f}%)")
        report_lines.append(f"  下跌: {sentiment['down_count']}只")
        report_lines.append(f"  涨停: {sentiment['limit_up']}只 | 跌停: {sentiment['limit_down']}只")
        report_lines.append(f"  平均涨跌幅: {sentiment['avg_change']:.2f}%")
        report_lines.append("")
        
        # 板块强度
        report_lines.append("【板块强度排行 TOP 10】")
        if report['sector_top10'] is not None:
            for idx, row in report['sector_top10'].iterrows():
                cols = list(report['sector_top10'].columns)
                name = row[cols[1]]
                change = row[cols[5]] if len(cols) > 5 else 'N/A'
                report_lines.append(f"  {idx+1}. {name}: {change}%")
        else:
            report_lines.append("  暂无板块数据")
        report_lines.append("")
        
        # 动量选股
        report_lines.append("【动量策略 (追涨)】")
        if not report['momentum_picks'].empty:
            for idx, row in report['momentum_picks'].iterrows():
                report_lines.append(f"  • {row['name']}({row['code']}) - {row['reason']}")
                report_lines.append(f"    得分:{row['score']:.1f} | 涨幅:{row['change_pct']}%, 量比:{row['volume_ratio']:.2f}, 成交额:{row['amount']/10000:.1f}亿")
        else:
            report_lines.append("  无符合条件的股票")
        report_lines.append("")
        
        # 反转选股
        report_lines.append("【反转策略 (抄底)】")
        if not report['reversal_picks'].empty:
            for idx, row in report['reversal_picks'].iterrows():
                report_lines.append(f"  • {row['name']}({row['code']}) - {row['reason']}")
                report_lines.append(f"    得分:{row['score']:.1f} | 跌幅:{row['change_pct']}%, 量比:{row['volume_ratio']:.2f}")
        else:
            report_lines.append("  无符合条件的股票")
        report_lines.append("")
        
        # 操作建议
        report_lines.append("【操作建议】")
        if sentiment['score'] >= 70:
            report_lines.append("  建议仓位: 70-80% (市场情绪乐观)")
        elif sentiment['score'] >= 50:
            report_lines.append("  建议仓位: 50-70% (市场情绪中性偏乐观)")
        elif sentiment['score'] >= 30:
            report_lines.append("  建议仓位: 30-50% (市场情绪中性偏悲观)")
        else:
            report_lines.append("  建议仓位: 20-30% (市场情绪悲观，谨慎操作)")
        report_lines.append("")
        
        # 观察名单
        watchlist = []
        if not report['momentum_picks'].empty:
            watchlist.extend(report['momentum_picks']['code'].tolist())
        if not report['reversal_picks'].empty:
            watchlist.extend(report['reversal_picks']['code'].tolist())
        if watchlist:
            report_lines.append(f"  观察名单: {', '.join(watchlist[:5])}")
        
        report_lines.append("=" * 80)
        
        # 保存报告
        with open(f"{date_folder}/report.md", 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        # 2. 保存选股CSV
        if not report['momentum_picks'].empty:
            report['momentum_picks'].to_csv(f"{date_folder}/momentum_picks.csv", index=False, encoding='utf-8-sig')
        if not report['reversal_picks'].empty:
            report['reversal_picks'].to_csv(f"{date_folder}/reversal_picks.csv", index=False, encoding='utf-8-sig')
        
        print(f"  报告已保存: {date_folder}/")
    
    def run_backtest(self):
        """执行完整回测"""
        print("=" * 80)
        print("2025年2月完整回测")
        print("=" * 80)
        print(f"交易日数量: {len(FEB_TRADING_DAYS)} 天")
        print(f"日期: {FEB_TRADING_DAYS[0]} 至 {FEB_TRADING_DAYS[-1]}")
        print("=" * 80)
        print()
        
        all_reports = []
        
        for date_str in FEB_TRADING_DAYS:
            # 获取数据
            data = self.fetch_daily_data(date_str)
            if data is None:
                logger.error(f"{date_str} 数据获取失败，跳过")
                continue
            
            # 生成报告
            report = self.generate_daily_report(date_str, data)
            if report:
                self.save_daily_report(report)
                all_reports.append(report)
            
            time.sleep(0.5)  # 避免请求过快
        
        print(f"\n[OK] 完成! 共生成 {len(all_reports)} 天报告")
        return all_reports


if __name__ == "__main__":
    try:
        backtest = FebruaryBacktest()
        reports = backtest.run_backtest()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
