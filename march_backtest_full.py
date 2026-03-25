# -*- coding: utf-8 -*-
"""
2026年3月完整回测
使用25分钟模式（9:25开盘价买入），验证次日及后续收益
"""
import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from calendar import monthrange

# 保持Clash代理，但设置NO_PROXY
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

# 添加项目路径
sys.path.insert(0, '.')

from main import FundFlowSystem
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

headers = {
    'Referer': 'https://finance.sina.com.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def is_trading_day(date):
    """判断是否为交易日（简单判断：周一到周五）"""
    return date.weekday() < 5

def get_trading_dates(year, month):
    """获取指定月份的所有交易日"""
    _, last_day = monthrange(year, month)
    dates = []
    for day in range(1, last_day + 1):
        date = datetime(year, month, day)
        if is_trading_day(date):
            dates.append(date.strftime('%Y-%m-%d'))
    return dates

def fetch_with_retry(func, max_retries=5, delay=3):
    """带重试的数据获取"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise

def get_stock_price_sina(code, max_retries=5):
    """获取股票实时价格（新浪API）"""
    prefix = 'sh' if code.startswith('6') else 'sz'
    url = f'https://hq.sinajs.cn/list={prefix}{code}'
    
    def fetch():
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text
        if '=' in text and '"' in text:
            data_part = text.split('="')[1].rstrip('";')
            fields = data_part.split(',')
            if len(fields) >= 10:
                return {
                    'name': fields[0],
                    'open': float(fields[1]),
                    'prev_close': float(fields[2]),
                    'current': float(fields[3]),
                    'high': float(fields[4]),
                    'low': float(fields[5]),
                }
        return None
    
    try:
        return fetch_with_retry(fetch, max_retries)
    except Exception as e:
        logger.error(f"Failed to fetch {code}: {e}")
        return None

def run_backtest_for_date(date_str, max_retries=3):
    """
    对指定日期运行25分钟模式回测
    返回选股结果
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Running backtest for {date_str}")
    logger.info(f"{'='*60}")
    
    for attempt in range(max_retries):
        try:
            # 初始化系统（25分钟模式）
            system = FundFlowSystem(run_mode='backtest_25')
            result = system.run_daily_analysis(date_str, save_data=False)
            
            if result['status'] == 'success':
                picks = result.get('stock_picks', {})
                logger.info(f"Success! momentum: {len(picks.get('momentum', []))}, reversal: {len(picks.get('reversal', []))}")
                return result
            else:
                logger.error(f"Analysis failed: {result.get('error', 'unknown')}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in 10 seconds...")
                time.sleep(10)
    
    return None

def verify_returns(picks_data, check_date, days_after=1):
    """
    验证选股在N天后的收益
    picks_data: {date: {strategy: [stocks]}}
    check_date: 验证日期
    days_after: 买入后几天
    """
    results = []
    
    for buy_date, strategies in picks_data.items():
        for strategy, stocks in strategies.items():
            for stock in stocks:
                code = stock.get('code', '')
                name = stock.get('name', '')
                buy_price = stock.get('buy_price', stock.get('open', 0))
                
                # 获取验证日期的价格
                data = get_stock_price_sina(code)
                if data and buy_price > 0:
                    current_price = data['current']
                    return_pct = (current_price - buy_price) / buy_price * 100
                    
                    results.append({
                        'buy_date': buy_date,
                        'check_date': check_date,
                        'strategy': strategy,
                        'code': code,
                        'name': name,
                        'buy_price': buy_price,
                        'current_price': current_price,
                        'return_pct': return_pct,
                        'days_after': days_after,
                    })
                    
    return results

def save_intermediate(data, filename):
    """保存中间结果"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved intermediate data to {filename}")

def main():
    """主函数"""
    logger.info("="*80)
    logger.info("Starting March 2026 Full Backtest")
    logger.info("="*80)
    
    # 获取3月所有交易日
    trading_dates = get_trading_dates(2026, 3)
    logger.info(f"Trading dates in March 2026: {len(trading_dates)} days")
    logger.info(f"Dates: {trading_dates}")
    
    # 存储所有回测结果
    all_results = {}
    failed_dates = []
    
    # 阶段1: 运行每一天的回测
    logger.info("\n" + "="*80)
    logger.info("PHASE 1: Running daily backtests")
    logger.info("="*80)
    
    for date_str in trading_dates:
        result = run_backtest_for_date(date_str)
        
        if result and result['status'] == 'success':
            picks = result.get('stock_picks', {})
            all_results[date_str] = {
                'momentum': picks.get('momentum', []),
                'reversal': picks.get('reversal', []),
                'sentiment': result.get('sentiment', {}),
            }
            # 保存中间结果
            save_intermediate(all_results, 'backtest_intermediate.json')
        else:
            failed_dates.append(date_str)
            logger.error(f"Failed to process {date_str}")
        
        # 短暂休息，避免请求过快
        time.sleep(2)
    
    logger.info(f"\nPhase 1 complete. Success: {len(all_results)}, Failed: {len(failed_dates)}")
    
    # 阶段2: 获取收益验证（当前价格）
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: Verifying returns with current prices")
    logger.info("="*80)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    verification_results = []
    
    for date_str, data in all_results.items():
        logger.info(f"Verifying returns for {date_str} picks...")
        
        # 计算买入后到今天的收益
        buy_date = datetime.strptime(date_str, '%Y-%m-%d')
        days_diff = (datetime.now() - buy_date).days
        
        for strategy in ['momentum', 'reversal']:
            for stock in data.get(strategy, []):
                code = stock.get('code', '')
                name = stock.get('name', '')
                
                # 从报告中获取开盘价（买入价）
                buy_price = stock.get('open', 0)
                
                # 获取当前价格
                price_data = get_stock_price_sina(code)
                if price_data and buy_price > 0:
                    current_price = price_data['current']
                    return_pct = (current_price - buy_price) / buy_price * 100
                    
                    verification_results.append({
                        'buy_date': date_str,
                        'verify_date': current_date,
                        'strategy': strategy,
                        'code': code,
                        'name': name,
                        'buy_price': buy_price,
                        'current_price': current_price,
                        'return_pct': return_pct,
                        'holding_days': days_diff,
                    })
        
        time.sleep(1)  # 避免请求过快
    
    # 阶段3: 生成报告
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: Generating report")
    logger.info("="*80)
    
    if verification_results:
        df = pd.DataFrame(verification_results)
        
        # 保存详细结果
        df.to_csv('march_backtest_full_results.csv', index=False, encoding='utf-8-sig')
        logger.info(f"Saved detailed results to march_backtest_full_results.csv")
        
        # 生成汇总统计
        summary = {
            'total_trades': len(df),
            'total_profit': (df['return_pct'] > 0).sum(),
            'total_loss': (df['return_pct'] <= 0).sum(),
            'win_rate': (df['return_pct'] > 0).mean() * 100,
            'avg_return': df['return_pct'].mean(),
            'max_return': df['return_pct'].max(),
            'min_return': df['return_pct'].min(),
            'total_pnl': df['return_pct'].sum(),
        }
        
        # 按策略统计
        for strategy in ['momentum', 'reversal']:
            strategy_df = df[df['strategy'] == strategy]
            if len(strategy_df) > 0:
                summary[f'{strategy}_trades'] = len(strategy_df)
                summary[f'{strategy}_win_rate'] = (strategy_df['return_pct'] > 0).mean() * 100
                summary[f'{strategy}_avg_return'] = strategy_df['return_pct'].mean()
                summary[f'{strategy}_total_pnl'] = strategy_df['return_pct'].sum()
        
        # 保存汇总
        with open('march_backtest_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 打印报告
        logger.info("\n" + "="*80)
        logger.info("BACKTEST REPORT - MARCH 2026")
        logger.info("="*80)
        logger.info(f"Total trading days analyzed: {len(all_results)}")
        logger.info(f"Total stock picks: {summary['total_trades']}")
        logger.info(f"Win rate: {summary['win_rate']:.1f}% ({summary['total_profit']}/{summary['total_trades']})")
        logger.info(f"Average return: {summary['avg_return']:+.2f}%")
        logger.info(f"Total P&L (equal weight): {summary['total_pnl']:+.2f}%")
        logger.info(f"Max single return: {summary['max_return']:+.2f}%")
        logger.info(f"Min single return: {summary['min_return']:+.2f}%")
        
        logger.info("\nBy Strategy:")
        for strategy in ['momentum', 'reversal']:
            key = f'{strategy}_trades'
            if key in summary:
                logger.info(f"  {strategy.upper()}:")
                logger.info(f"    Trades: {summary[key]}")
                logger.info(f"    Win rate: {summary[f'{strategy}_win_rate']:.1f}%")
                logger.info(f"    Avg return: {summary[f'{strategy}_avg_return']:+.2f}%")
                logger.info(f"    Total P&L: {summary[f'{strategy}_total_pnl']:+.2f}%")
    
    logger.info("\n" + "="*80)
    logger.info("BACKTEST COMPLETE")
    logger.info("="*80)
    logger.info(f"Results saved to:")
    logger.info(f"  - march_backtest_full_results.csv")
    logger.info(f"  - march_backtest_summary.json")
    logger.info(f"  - backtest_intermediate.json")

if __name__ == '__main__':
    main()
