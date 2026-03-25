#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare历史数据获取模块（基于官方推荐接口）

使用AKShare官方推荐的 stock_zh_a_hist 接口获取历史数据
文档: https://akshare.akfamily.xyz/data/stock/stock.html
"""
import os
import sys
import time
import logging
from typing import Optional, List, Dict, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import akshare as ak

logger = logging.getLogger(__name__)


class HistoricalDataFetcher:
    """
    历史数据获取器（基于AKShare官方推荐接口）
    
    使用 stock_zh_a_hist 接口，优势：
    1. 数据质量高
    2. 访问无限制
    3. 支持任意历史日期
    4. 返回字段完整（含换手率、量比等）
    """
    
    def __init__(self):
        self.stock_list_cache = None
        self._cache = {}  # 简单缓存
        
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        if self.stock_list_cache is None:
            self.stock_list_cache = ak.stock_info_a_code_name()
        return self.stock_list_cache
    
    def fetch_single_stock_hist(self, 
                                code: str, 
                                date_str: str,
                                name: str = "") -> Optional[Dict]:
        """
        获取单只股票的历史数据（使用官方推荐接口 stock_zh_a_hist）
        
        Args:
            code: 股票代码（如 '000001'）
            date_str: 日期（格式 '2025-03-05'）
            name: 股票名称
            
        Returns:
            包含股票数据的字典，或None（如果获取失败）
        """
        try:
            # 转换日期格式 2025-03-05 -> 20250305
            date_fmt = date_str.replace('-', '')
            
            # 使用AKShare官方推荐接口 stock_zh_a_hist
            # 文档: https://akshare.akfamily.xyz/data/stock/stock.html
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=date_fmt,
                end_date=date_fmt,
                adjust=""  # 不复权
            )
            
            if df is None or df.empty:
                return None
            
            row = df.iloc[0]
            
            # 字段映射（AKShare返回的字段）
            return {
                'code': code,
                'name': name or code,
                'date': date_str,
                'open': float(row['开盘']),
                'close': float(row['收盘']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'volume': int(row['成交量']),  # 手
                'amount': float(row['成交额']) / 10000,  # 转换为万元
                'change_pct': float(row['涨跌幅']),  # %
                'change_amt': float(row['涨跌额']),
                'turnover': float(row['换手率']),  # %
                'amplitude': float(row['振幅']),  # %
                # 计算伪量比（历史数据没有量比，用换手率估算）
                # 换手率 > 2% 认为是活跃，对应量比 > 1.5
                'volume_ratio': max(1.0, float(row['换手率']) / 2),
            }
            
        except Exception as e:
            logger.debug(f"{code} fetch failed: {e}")
            return None
    
    def fetch_daily_data(self, 
                         date_str: str, 
                         sample_size: int = 200,
                         max_workers: int = 10,
                         status_callback: Optional[Callable] = None) -> Optional[pd.DataFrame]:
        """
        获取某日全部股票的历史数据
        
        Args:
            date_str: 日期（格式 '2025-03-05'）
            sample_size: 采样股票数量
            max_workers: 并发线程数
            status_callback: 进度回调函数
            
        Returns:
            DataFrame包含当日所有股票数据
        """
        logger.info(f"[{date_str}] Fetching historical data using stock_zh_a_hist...")
        
        try:
            stock_list = self.get_stock_list()
            codes = stock_list['code'].tolist()[:sample_size]
            names = dict(zip(stock_list['code'], stock_list['name']))
            
            results = []
            total = len(codes)
            completed = 0
            
            # 使用线程池并发获取（但控制并发数，避免被封）
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_code = {
                    executor.submit(self.fetch_single_stock_hist, code, date_str, names.get(code, "")): code 
                    for code in codes
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_code):
                    completed += 1
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    # 更新进度
                    if status_callback and completed % 10 == 0:
                        progress = int(completed / total * 100)
                        status_callback(f'已获取 {completed}/{total} 只股票，成功 {len(results)} 只', progress)
                    
                    # 小延迟避免请求过快
                    time.sleep(0.05)
            
            if not results:
                logger.warning(f"[{date_str}] No data fetched")
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            logger.info(f"[{date_str}] Successfully fetched {len(df)} stocks")
            return df
            
        except Exception as e:
            logger.error(f"[{date_str}] Failed to fetch daily data: {e}")
            return pd.DataFrame()
    
    def fetch_multi_days(self,
                         start_date: str,
                         end_date: str,
                         sample_size: int = 200) -> Dict[str, pd.DataFrame]:
        """
        获取多日历史数据
        
        Args:
            start_date: 开始日期 '2025-03-05'
            end_date: 结束日期 '2025-03-15'
            sample_size: 每日采样股票数
            
        Returns:
            字典 {date: DataFrame}
        """
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        results = {}
        current = start
        
        while current <= end:
            if current.weekday() < 5:  # 只取交易日
                date_str = current.strftime('%Y-%m-%d')
                df = self.fetch_daily_data(date_str, sample_size)
                if not df.empty:
                    results[date_str] = df
            current += timedelta(days=1)
        
        return results


# 兼容性函数（保持与原接口一致）
def fetch_historical_data(date_str: str, 
                          sample_size: int = 200,
                          status_callback: Optional[Callable] = None) -> Optional[pd.DataFrame]:
    """
    兼容性函数，保持与原data_fetcher接口一致
    """
    fetcher = HistoricalDataFetcher()
    return fetcher.fetch_daily_data(date_str, sample_size, status_callback=status_callback)


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    fetcher = HistoricalDataFetcher()
    
    print("=== 测试单股获取 ===")
    result = fetcher.fetch_single_stock_hist("000001", "2025-03-05")
    if result:
        print(f"成功获取: {result}")
    else:
        print("获取失败")
    
    print("\n=== 测试批量获取 ===")
    df = fetcher.fetch_daily_data("2025-03-05", sample_size=10)
    if not df.empty:
        print(f"成功获取 {len(df)} 只股票")
        print(df.head())
    else:
        print("获取失败")
