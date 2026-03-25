#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
"""
import os
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1'
os.environ['TQDM_DISABLE'] = '1'  # 禁用 tqdm 进度条

import requests
import pandas as pd
import akshare as ak
from typing import Optional, List, Dict
from datetime import datetime
import time
import logging
import concurrent.futures
from functools import wraps
import signal
import warnings

# 忽略一些警告
warnings.filterwarnings('ignore')

# 超时装饰器（使用signal，更可靠）
def timeout(seconds):
    """超时装饰器，用于限制函数执行时间"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Windows 不支持 signal.SIGALRM，使用 ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Function {func.__name__} timed out after {seconds} seconds")
                    return None
                except Exception as e:
                    logger.debug(f"Function {func.__name__} error: {e}")
                    return None
        return wrapper
    return decorator

# 指数退避重试装饰器
def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=30.0, exceptions=(Exception,)):
    """
    指数退避重试装饰器
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        exceptions: 需要捕获的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.debug(f"{func.__name__} 最终失败（{max_retries}次重试后）: {e}")
                        raise
                    
                    # 计算指数退避延迟
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.debug(f"{func.__name__} 第{attempt+1}次尝试失败，{delay:.1f}秒后重试: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.stock_list_cache = None
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        if self.stock_list_cache is None:
            self.stock_list_cache = ak.stock_info_a_code_name()
        return self.stock_list_cache
    
    def fetch_tencent_batch(self, codes: List[str]) -> pd.DataFrame:
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
                
                try:
                    results.append({
                        'code': fields[2],
                        'name': fields[1],
                        'latest': float(fields[3]) if fields[3] else 0,
                        'open': float(fields[5]) if fields[5] else 0,
                        'pre_close': float(fields[4]) if fields[4] else 0,
                        'change_pct': float(fields[5]) if fields[5] else 0,
                        'volume': int(float(fields[6])) if fields[6] else 0,
                        'amount': float(fields[37]) if fields[37] else 0,
                        'volume_ratio': float(fields[50]) if len(fields) > 50 and fields[50] else 0,
                    })
                except:
                    continue
            
            df = pd.DataFrame(results)
            if not df.empty and 'latest' in df.columns and 'pre_close' in df.columns:
                df['change_pct'] = ((df['latest'] - df['pre_close']) / df['pre_close'] * 100).round(2)
            
            return df
            
        except Exception as e:
            logger.error(f"腾讯批量获取失败: {e}")
            return pd.DataFrame()
    
    def _fetch_single_stock_hist(self, code: str, date_str: str, stock_list: pd.DataFrame) -> Optional[Dict]:
        """
        获取单只股票历史数据（使用腾讯接口 stock_zh_a_hist_tx）
        
        接口说明:
        - 使用 ak.stock_zh_a_hist_tx() 获取腾讯历史数据
        - 返回字段: date, open, close, high, low, amount(手)
        - 需要在NO_PROXY中排除腾讯域名
        
        Args:
            code: 6位股票代码
            date_str: 日期字符串 YYYY-MM-DD
            stock_list: 股票列表DataFrame
            
        Returns:
            股票数据字典或None
        """
        max_retries = 2
        base_delay = 0.3
        
        for attempt in range(max_retries + 1):
            try:
                # 转换日期格式
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # 添加市场前缀
                symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
                
                # 获取目标日期前后几天的数据，确保包含目标日期
                start = (target_date - pd.Timedelta(days=3)).strftime('%Y%m%d')
                end = (target_date + pd.Timedelta(days=1)).strftime('%Y%m%d')
                
                # 使用线程池设置超时
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        ak.stock_zh_a_hist_tx,
                        symbol=symbol,
                        start_date=start,
                        end_date=end
                    )
                    try:
                        df = future.result(timeout=10)  # 10秒超时
                    except concurrent.futures.TimeoutError:
                        if attempt < max_retries:
                            delay = min(base_delay * (2 ** attempt), 3.0)
                            logger.debug(f"  {code} timeout, retry in {delay:.1f}s ({attempt+1}/{max_retries})")
                            time.sleep(delay)
                            continue
                        logger.debug(f"  {code} timeout after 10s, giving up")
                        return None
                
                if df is not None and not df.empty:
                    # 查找目标日期
                    df['date'] = pd.to_datetime(df['date'])
                    target_row = df[df['date'].dt.strftime('%Y-%m-%d') == date_str]
                    
                    if target_row.empty:
                        return None
                    
                    row = target_row.iloc[0]
                    close_price = float(row['close'])
                    open_price = float(row['open'])
                    high_price = float(row['high'])
                    low_price = float(row['low'])
                    volume = int(row['amount'])  # 单位：手
                    
                    # 计算涨跌幅（需要前一天收盘价）
                    prev_close = open_price  # 默认用开盘价
                    change_pct = 0.0
                    try:
                        target_idx = df[df['date'].dt.strftime('%Y-%m-%d') == date_str].index[0]
                        if target_idx > 0:
                            prev_close = float(df.iloc[target_idx - 1]['close'])
                            change_pct = ((close_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    except:
                        pass
                    
                    # 估算成交额
                    avg_price = (high_price + low_price) / 2
                    amount = volume * avg_price * 100  # 元
                    
                    # 伪量比：根据涨跌幅估算活跃度
                    volume_ratio = max(1.0, abs(change_pct) * 0.5 + 0.5)
                    
                    # 获取股票名称
                    name = code
                    code_matches = stock_list[stock_list['code'] == code]
                    if len(code_matches) > 0:
                        name = code_matches['name'].values[0]
                    
                    return {
                        'code': code,
                        'name': name,
                        'latest': close_price,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'pre_close': prev_close,
                        'change_pct': round(change_pct, 2),
                        'volume': volume,
                        'amount': amount / 10000,  # 转换为万元
                        'volume_ratio': volume_ratio,
                    }
                return None
                
            except Exception as e:
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), 3.0)
                    logger.debug(f"  {code} error: {e}, retry in {delay:.1f}s ({attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    logger.debug(f"  {code} fetch failed after {max_retries} retries: {e}")
        return None
    
    # 保留旧方法名以兼容
    _fetch_single_stock = _fetch_single_stock_hist

    def fetch_historical_data(self, date_str: str, sample_size: int = 200, status_callback=None) -> Optional[pd.DataFrame]:
        """
        使用akshare获取历史数据（带超时、指数退避和失败保护）
        
        优化点：
        1. 使用线程池并发获取（控制并发数）
        2. 单只股票有重试机制和超时保护
        3. 总体时间限制
        4. 失败率监控，失败率过高时提前退出
        
        Args:
            date_str: 日期字符串 YYYY-MM-DD
            sample_size: 采样股票数量
            status_callback: 状态回调函数
        
        Returns:
            DataFrame包含股票数据
        """
        logger.info(f"[{date_str}] fetching historical data with backoff protection...")
        
        try:
            stock_list = self.get_stock_list()
            codes = stock_list['code'].tolist()[:sample_size]
            
            results = []
            total = len(codes)
            failed_count = 0
            start_time = time.time()
            max_total_time = 60  # 总时间限制60秒（单日期）
            max_fail_rate = 0.5  # 最大失败率50%，超过则提前退出
            
            # 使用线程池并发获取，但控制并发数（AKShare接口不宜过高并发）
            # 回测时使用低并发以避免超时
            max_workers = min(2, (sample_size // 50) + 1)  # 保守设置，确保稳定性
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_code = {
                    executor.submit(self._fetch_single_stock_hist, code, date_str, stock_list): code
                    for code in codes
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_code):
                    completed += 1
                    code = future_to_code[future]
                    
                    # 检查总体时间
                    elapsed = time.time() - start_time
                    if elapsed > max_total_time:
                        logger.warning(f"[{date_str}] total time exceeded {max_total_time}s, cancelling remaining")
                        # 取消剩余任务
                        for f in future_to_code:
                            if not f.done():
                                f.cancel()
                        break
                    
                    # 检查失败率
                    if completed > 20:
                        fail_rate = failed_count / completed
                        if fail_rate > max_fail_rate:
                            logger.warning(f"[{date_str}] fail rate {fail_rate:.1%} too high, stopping")
                            # 取消剩余任务
                            for f in future_to_code:
                                if not f.done():
                                    f.cancel()
                            break
                    
                    try:
                        stock_data = future.result()
                        if stock_data:
                            results.append(stock_data)
                        else:
                            failed_count += 1
                    except Exception as e:
                        failed_count += 1
                        logger.debug(f"  {code} exception: {e}")
                    
                    # 每10只更新一次状态
                    if status_callback and completed % 10 == 0:
                        progress = int(completed / total * 100)
                        fail_rate = failed_count / completed if completed > 0 else 0
                        status_callback(
                            f'正在获取 {date_str} ({completed}/{total}, 成功{len(results)}, 失败率{fail_rate:.0%})',
                            progress
                        )
            
            elapsed = time.time() - start_time
            final_msg = f'已完成 {date_str}，共 {len(results)} 只股票，耗时{elapsed:.1f}s'
            if status_callback:
                status_callback(final_msg, 100)
            logger.info(f"[{date_str}] {final_msg}")
            
            if not results:
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            df['date'] = date_str
            return df
            
        except Exception as e:
            logger.error(f"[{date_str}] historical data fetch failed: {e}")
            return pd.DataFrame()
    
    def fetch_daily_data(self, date_str: str, sample_size: int = 2000, use_historical: bool = False, status_callback=None) -> Optional[Dict]:
        """
        获取某日完整数据
        
        Args:
            date_str: 日期字符串 YYYY-MM-DD
            sample_size: 采样股票数量
            use_historical: 是否强制使用历史数据（用于回测）
            status_callback: 状态回调函数
        
        Returns:
            Dict包含stocks, sectors, sentiment
        """
        logger.info(f"[{date_str}] fetching data... (use_historical={use_historical})")
        
        # 如果强制使用历史数据，直接调用历史数据接口
        if use_historical:
            logger.info(f"  using historical data (forced)")
            stocks_df = self.fetch_historical_data(date_str, sample_size=min(sample_size, 300), status_callback=status_callback)
            if stocks_df.empty:
                logger.error(f"  historical data fetch failed for {date_str}")
                return None
            
            # 获取板块数据
            sectors_df = pd.DataFrame()
            try:
                sectors_df = ak.stock_sector_spot()
                logger.info(f"  sectors: {len(sectors_df)}")
            except Exception as e:
                logger.warning(f"板块数据获取失败: {e}")
                sectors_df = pd.DataFrame()
            
            # 计算市场情绪
            sentiment = self.calculate_market_sentiment(stocks_df)
            logger.info(f"  sentiment: {sentiment['status']} score:{sentiment['score']:.1f}")
            
            return {
                'stocks': stocks_df,
                'sectors': sectors_df,
                'sentiment': sentiment,
                'date': date_str
            }
        
        try:
            # 1. 获取个股数据（优先使用实时接口）
            stock_list = self.get_stock_list()
            codes = stock_list['code'].tolist()[:sample_size]
            
            all_stocks = []
            batch_size = 200
            for i in range(0, len(codes), batch_size):
                batch = codes[i:i+batch_size]
                df = self.fetch_tencent_batch(batch)
                if not df.empty:
                    all_stocks.append(df)
                time.sleep(0.05)
            
            stocks_df = pd.DataFrame()
            if all_stocks:
                stocks_df = pd.concat(all_stocks, ignore_index=True)
                stocks_df['date'] = date_str
                logger.info(f"  stocks (realtime): {len(stocks_df)}")
                
                # 检查数据质量：如果平均成交量为0，说明是休市日，使用历史数据
                avg_volume = stocks_df['volume'].mean() if not stocks_df.empty else 0
                if avg_volume == 0:
                    logger.warning(f"  realtime data shows market closed, trying historical data...")
                    hist_df = self.fetch_historical_data(date_str, sample_size=200)
                    if not hist_df.empty:
                        stocks_df = hist_df
                        logger.info(f"  using historical data: {len(stocks_df)} stocks")
            else:
                # 实时接口失败，尝试历史数据
                logger.warning(f"  realtime fetch failed, trying historical data...")
                stocks_df = self.fetch_historical_data(date_str, sample_size=200)
            
            if stocks_df.empty:
                logger.error(f"  no data available for {date_str}")
                return None
            
            # 2. 获取板块数据
            sectors_df = pd.DataFrame()
            try:
                sectors_df = ak.stock_sector_spot()
                logger.info(f"  sectors: {len(sectors_df)}")
            except Exception as e:
                logger.warning(f"板块数据获取失败: {e}")
                sectors_df = pd.DataFrame()
            
            # 3. 计算市场情绪
            sentiment = self.calculate_market_sentiment(stocks_df)
            logger.info(f"  sentiment: {sentiment['status']} score:{sentiment['score']:.1f}")
            
            return {
                'stocks': stocks_df,
                'sectors': sectors_df,
                'sentiment': sentiment,
                'date': date_str
            }
            
        except Exception as e:
            logger.error(f"[{date_str}] data fetch failed: {e}")
            return None
    
    def calculate_market_sentiment(self, stocks_df: pd.DataFrame) -> Dict:
        """计算市场情绪"""
        if stocks_df.empty:
            return {'score': 50, 'status': '中性', 'up_ratio': 0.5}
        
        up_count = len(stocks_df[stocks_df['change_pct'] > 0])
        down_count = len(stocks_df[stocks_df['change_pct'] < 0])
        total = len(stocks_df)
        
        up_ratio = up_count / total if total > 0 else 0.5
        score = up_ratio * 100
        
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
            'score': round(score, 2),
            'status': status,
            'up_count': up_count,
            'down_count': down_count,
            'up_ratio': round(up_ratio, 4),
            'limit_up': limit_up,
            'limit_down': limit_down,
            'avg_change': round(stocks_df['change_pct'].mean(), 2)
        }
