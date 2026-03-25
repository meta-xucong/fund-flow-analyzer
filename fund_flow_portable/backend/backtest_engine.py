#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎 - 基于真实历史数据
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

from backend.data_fetcher import DataFetcher
from backend.report_generator import ReportGenerator

class BacktestEngine:
    """回测引擎 - 使用真实历史数据计算收益"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.report_generator = ReportGenerator()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(base_dir, 'reports', 'backtest')
        os.makedirs(self.results_dir, exist_ok=True)
        self.current_status = {
            'is_running': False,
            'progress': 0,
            'current_step': '',
            'current_date': '',
            'message': ''
        }
    
    def get_status(self) -> Dict:
        """获取当前回测状态"""
        return self.current_status.copy()
    
    def update_status(self, progress: int = None, step: str = None, date: str = None, message: str = None):
        """更新回测状态"""
        if progress is not None:
            self.current_status['progress'] = progress
        if step is not None:
            self.current_status['current_step'] = step
        if date is not None:
            self.current_status['current_date'] = date
        if message is not None:
            self.current_status['message'] = message
    
    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日列表（简化版）"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        days = []
        current = start
        while current <= end:
            if current.weekday() < 5:  # 0-4 是周一到周五
                days.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return days
    
    def get_future_dates(self, date_str: str, days: int = 5) -> List[str]:
        """获取指定日期后的N个交易日"""
        date = datetime.strptime(date_str, '%Y-%m-%d')
        future_dates = []
        current = date + timedelta(days=1)
        
        while len(future_dates) < days:
            if current.weekday() < 5:
                future_dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return future_dates
    
    def fetch_stock_prices(self, code: str, dates: List[str]) -> Dict[str, float]:
        """
        获取股票在多个日期的收盘价
        
        Returns:
            {date: close_price}
        """
        prices = {}
        
        if not dates:
            return prices
        
        try:
            # 转换日期格式
            start_date = datetime.strptime(min(dates), '%Y-%m-%d')
            end_date = datetime.strptime(max(dates), '%Y-%m-%d')
            
            # 添加市场前缀
            symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
            
            # 使用AKShare获取历史数据
            import akshare as ak
            start = (start_date - pd.Timedelta(days=3)).strftime('%Y%m%d')
            end = (end_date + pd.Timedelta(days=1)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist_tx(symbol=symbol, start_date=start, end_date=end)
            
            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                for date_str in dates:
                    row = df[df['date'] == date_str]
                    if not row.empty:
                        prices[date_str] = float(row.iloc[0]['close'])
            
        except Exception as e:
            logger.error(f"获取 {code} 历史价格失败: {e}")
        
        return prices
    
    def run_backtest(self, start_date: str, end_date: str, 
                     progress_callback: Optional[Callable] = None) -> Dict:
        """
        运行回测 - 基于真实历史数据
        
        逻辑：
        1. 获取当天的选股结果（使用开盘价作为买入价）
        2. 获取接下来5个交易日的收盘价
        3. 计算每天的收益和累计收益
        """
        import time
        
        self.current_status['is_running'] = True
        self.update_status(progress=0, step='准备阶段', message='获取交易日列表...')
        
        trading_days = self.get_trading_days(start_date, end_date)
        
        if not trading_days:
            self.current_status['is_running'] = False
            return {'error': '没有可交易日'}
        
        results = {
            'start_date': start_date,
            'end_date': end_date,
            'trading_days': trading_days,
            'daily_reports': [],
            'trades': [],
            'summary': {}
        }
        
        total_days = len(trading_days)
        
        for idx, date_str in enumerate(trading_days):
            print(f"[{date_str}] 回测中... ({idx+1}/{total_days})")
            self.update_status(
                progress=int(idx / total_days * 100),
                step='获取当日数据',
                date=date_str,
                message=f'正在获取 {date_str} 的选股数据...'
            )
            
            # 1. 获取当天的市场数据
            try:
                data = self.data_fetcher.fetch_daily_data(
                    date_str, 
                    sample_size=100,
                    use_historical=True
                )
            except Exception as e:
                logger.error(f"[{date_str}] 数据获取异常: {e}")
                data = None
            
            if data is None or data.get('stocks') is None or (hasattr(data.get('stocks'), 'empty') and data['stocks'].empty):
                print(f"[{date_str}] 数据获取失败，跳过")
                continue
            
            print(f"[{date_str}] 获取到 {len(data['stocks'])} 只股票")
            
            # 2. 生成报告（选股）
            self.update_status(
                step='选股分析',
                date=date_str,
                message=f'正在分析 {date_str} 的选股...'
            )
            
            report = self.report_generator.generate_report(data)
            if report:
                momentum_count = len(report.get('momentum_picks', []))
                reversal_count = len(report.get('reversal_picks', []))
                print(f"[{date_str}] 动量: {momentum_count} 只, 反转: {reversal_count} 只")
                
                results['daily_reports'].append(report)
                
                # 3. 获取未来5天的价格并计算收益
                future_dates = self.get_future_dates(date_str, 5)
                
                self.update_status(
                    step='获取后续价格',
                    date=date_str,
                    message=f'正在获取后续 {len(future_dates)} 天的价格数据...'
                )
                
                # 处理每只推荐股
                all_picks = report.get('momentum_picks', []) + report.get('reversal_picks', [])
                
                for stock in all_picks:
                    trade = self._create_trade_with_history(stock, date_str, future_dates, report)
                    if trade:
                        results['trades'].append(trade)
            
            # 更新进度
            progress = int((idx + 1) / total_days * 100)
            self.update_status(progress=progress)
            if progress_callback:
                progress_callback(progress)
        
        self.update_status(step='汇总统计', message='正在计算回测统计结果...')
        
        # 计算汇总统计
        results['summary'] = self.calculate_summary(results['trades'])
        
        self.current_status['is_running'] = False
        self.update_status(
            progress=100, 
            step='完成', 
            message=f'回测完成！共生成 {len(results["trades"])} 笔交易'
        )
        
        return results
    
    def _create_trade_with_history(self, stock: Dict, buy_date: str, future_dates: List[str], report: Dict) -> Optional[Dict]:
        """
        创建交易记录 - 包含5天历史收益
        
        Args:
            stock: 股票信息
            buy_date: 买入日期
            future_dates: 未来5个交易日的日期列表
            report: 完整报告（用于判断策略类型）
        
        Returns:
            包含每日收益的交易记录
        """
        code = stock.get('code')
        name = stock.get('name')
        
        # 买入价格使用当天的开盘价
        buy_price = stock.get('open', 0)
        if buy_price <= 0:
            return None
        
        # 判断策略类型
        strategy = '动量' if stock in report.get('momentum_picks', []) else '反转'
        
        # 获取未来5天的收盘价
        future_prices = self.fetch_stock_prices(code, future_dates)
        
        if not future_prices:
            return None
        
        # 计算每日收益
        daily_returns = []
        cumulative_return = 0
        
        for i, future_date in enumerate(future_dates):
            if future_date in future_prices:
                sell_price = future_prices[future_date]
                daily_return = (sell_price - buy_price) / buy_price * 100
                cumulative_return = daily_return  # 累计收益就是到当天的收益
                
                daily_returns.append({
                    'day': int(i + 1),  # 确保是整数
                    'date': str(future_date),
                    'price': float(round(sell_price, 2)),
                    'daily_return': float(round(daily_return, 2)),
                    'cumulative_return': float(round(cumulative_return, 2))
                })
        
        if not daily_returns:
            return None
        
        # 最终收益是第5天的收益（或最后一天）
        final_return = daily_returns[-1]['cumulative_return'] if daily_returns else 0
        
        return {
            'code': code,
            'name': name,
            'strategy': strategy,
            'buy_date': buy_date,
            'buy_price': round(buy_price, 2),
            'daily_returns': daily_returns,
            'total_return': round(final_return, 2),
            'score': stock.get('score', 0),
            'reason': stock.get('reason', '')
        }
    
    def calculate_summary(self, trades: List[Dict]) -> Dict:
        """计算汇总统计"""
        if not trades:
            return {
                'total_trades': 0,
                'momentum': {'count': 0, 'avg_return': 0, 'win_rate': 0},
                'reversal': {'count': 0, 'avg_return': 0, 'win_rate': 0},
                'overall': {'avg_return': 0, 'win_rate': 0, 'max_return': 0, 'min_return': 0, 'median_return': 0}
            }
        
        momentum_trades = [t for t in trades if t['strategy'] == '动量']
        reversal_trades = [t for t in trades if t['strategy'] == '反转']
        
        def calc_stats(trade_list):
            if not trade_list:
                return {'count': 0, 'avg_return': 0, 'win_rate': 0}
            returns = [t['total_return'] for t in trade_list]
            return {
                'count': len(trade_list),
                'avg_return': round(sum(returns) / len(returns), 2),
                'win_rate': round(len([r for r in returns if r > 0]) / len(returns) * 100, 1)
            }
        
        momentum_stats = calc_stats(momentum_trades)
        reversal_stats = calc_stats(reversal_trades)
        
        all_returns = [t['total_return'] for t in trades]
        all_returns_sorted = sorted(all_returns)
        n = len(all_returns_sorted)
        
        return {
            'total_trades': len(trades),
            'momentum': momentum_stats,
            'reversal': reversal_stats,
            'overall': {
                'avg_return': round(sum(all_returns) / len(all_returns), 2),
                'win_rate': round(len([r for r in all_returns if r > 0]) / len(all_returns) * 100, 1),
                'max_return': round(max(all_returns), 2),
                'min_return': round(min(all_returns), 2),
                'median_return': round(all_returns_sorted[n // 2], 2) if n > 0 else 0
            }
        }
    
    def create_download_package(self, result: Dict, result_id: str = None) -> str:
        """创建下载压缩包"""
        if result_id is None:
            result_id = f"{result['start_date']}_{result['end_date']}"
        temp_dir = os.path.join(self.results_dir, f'temp_{result_id}')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # 1. 汇总报告
            summary_md = self._format_summary_markdown(result)
            with open(os.path.join(temp_dir, 'summary.md'), 'w', encoding='utf-8') as f:
                f.write(summary_md)
            
            # 2. 交易记录（包含每日收益）
            trades = result.get('trades', [])
            if trades:
                # 展开每日收益为CSV格式
                rows = []
                for trade in trades:
                    base = {
                        'code': trade['code'],
                        'name': trade['name'],
                        'strategy': trade['strategy'],
                        'buy_date': trade['buy_date'],
                        'buy_price': trade['buy_price'],
                        'total_return': trade['total_return']
                    }
                    # 添加每日收益
                    for dr in trade.get('daily_returns', []):
                        row = base.copy()
                        row['day'] = dr['day']
                        row['date'] = dr['date']
                        row['price'] = dr['price']
                        row['daily_return'] = dr['daily_return']
                        row['cumulative_return'] = dr['cumulative_return']
                        rows.append(row)
                
                trades_df = pd.DataFrame(rows)
                trades_df.to_csv(os.path.join(temp_dir, 'trades.csv'), 
                                index=False, encoding='utf-8-sig')
            
            # 3. 每日详细报告
            daily_reports_dir = os.path.join(temp_dir, 'daily_reports')
            os.makedirs(daily_reports_dir, exist_ok=True)
            
            for report in result.get('daily_reports', []):
                date_str = report.get('date', 'unknown')
                daily_md = self._format_daily_report(report)
                with open(os.path.join(daily_reports_dir, f'{date_str}.md'), 'w', encoding='utf-8') as f:
                    f.write(daily_md)
            
            # 4. 创建ZIP包
            import zipfile
            zip_path = os.path.join(self.results_dir, f'backtest_{result_id}.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return zip_path
            
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _format_daily_report(self, report: Dict) -> str:
        """格式化单日报告为Markdown"""
        lines = []
        date_str = report.get('date', 'unknown')
        
        lines.append(f"# {date_str} 盘前资金流向分析报告")
        lines.append("")
        
        # 市场情绪
        sentiment = report.get('sentiment', {})
        lines.append("## 市场情绪")
        lines.append(f"- 情绪状态: {sentiment.get('status', '未知')}")
        lines.append(f"- 情绪得分: {sentiment.get('score', 0)}")
        lines.append("")
        
        # 动量选股
        momentum = report.get('momentum_picks', [])
        lines.append(f"## 动量策略选股 ({len(momentum)}只)")
        if momentum:
            lines.append("")
            lines.append("| 代码 | 名称 | 买入价(开盘) | 得分 | 原因 |")
            lines.append("|------|------|-------------|------|------|")
            for stock in momentum:
                lines.append(f"| {stock.get('code', '')} | {stock.get('name', '')} | {stock.get('open', 0):.2f} | {stock.get('score', 0):.1f} | {stock.get('reason', '')} |")
        else:
            lines.append("无符合条件的股票")
        lines.append("")
        
        # 反转选股
        reversal = report.get('reversal_picks', [])
        lines.append(f"## 反转策略选股 ({len(reversal)}只)")
        if reversal:
            lines.append("")
            lines.append("| 代码 | 名称 | 买入价(开盘) | 得分 | 原因 |")
            lines.append("|------|------|-------------|------|------|")
            for stock in reversal:
                lines.append(f"| {stock.get('code', '')} | {stock.get('name', '')} | {stock.get('open', 0):.2f} | {stock.get('score', 0):.1f} | {stock.get('reason', '')} |")
        else:
            lines.append("无符合条件的股票")
        lines.append("")
        
        # 操作建议
        summary = report.get('summary', {})
        lines.append("## 操作建议")
        lines.append(f"- 建议仓位: {summary.get('position_suggestion', '未知')}")
        lines.append(f"- 风险等级: {summary.get('risk_level', '未知')}")
        lines.append(f"- 建议: {summary.get('advice', '无')}")
        watchlist = summary.get('watchlist', [])
        if watchlist:
            lines.append(f"- 观察名单: {', '.join(watchlist)}")
        
        return '\n'.join(lines)
    
    def _format_summary_markdown(self, result: Dict) -> str:
        """格式化汇总报告为Markdown"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"回测报告 {result['start_date']} 至 {result['end_date']}")
        lines.append("=" * 80)
        lines.append("")
        
        summary = result.get('summary', {})
        
        lines.append("【回测概况】")
        lines.append(f"  交易日数: {len(result.get('trading_days', []))} 天")
        lines.append(f"  总交易次数: {summary.get('total_trades', 0)} 笔")
        lines.append("")
        
        lines.append("【策略表现】")
        mom = summary.get('momentum', {})
        rev = summary.get('reversal', {})
        lines.append(f"  动量策略: {mom.get('count', 0)}笔, 平均收益{mom.get('avg_return', 0)}%, 胜率{mom.get('win_rate', 0)}%")
        lines.append(f"  反转策略: {rev.get('count', 0)}笔, 平均收益{rev.get('avg_return', 0)}%, 胜率{rev.get('win_rate', 0)}%")
        lines.append("")
        
        lines.append("【总体统计】")
        ov = summary.get('overall', {})
        lines.append(f"  平均收益率: {ov.get('avg_return', 0)}%")
        lines.append(f"  胜率: {ov.get('win_rate', 0)}%")
        lines.append(f"  最高收益: {ov.get('max_return', 0)}%")
        lines.append(f"  最低收益: {ov.get('min_return', 0)}%")
        lines.append("")
        
        # 添加TOP5收益股票
        trades = result.get('trades', [])
        if trades:
            lines.append("【收益TOP5】")
            sorted_trades = sorted(trades, key=lambda x: x['total_return'], reverse=True)[:5]
            for i, t in enumerate(sorted_trades, 1):
                lines.append(f"  {i}. {t['name']}({t['code']}): {t['total_return']:.2f}% ({t['strategy']})")
            lines.append("")
        
        return '\n'.join(lines)
