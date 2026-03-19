# -*- coding: utf-8 -*-
"""
数据采集模块

使用AKShare获取A股市场数据
API文档: https://www.akshare.xyz/
"""
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, List, Dict, Callable

import akshare as ak
import pandas as pd
from config.settings import settings

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = None, delay: float = None):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数，默认使用配置
        delay: 重试间隔(秒)，默认使用配置
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRIES
    if delay is None:
        delay = settings.RETRY_DELAY
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} 第{attempt + 1}/{max_retries}次尝试失败: {e}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # 指数退避
            
            logger.error(f"{func.__name__} 所有重试均失败")
            raise last_exception
        return wrapper
    return decorator


class DataFetcher:
    """
    数据采集器
    
    封装AKShare API调用，提供统一的数据获取接口
    """
    
    def __init__(self):
        """初始化采集器"""
        self.akshare_version = ak.__version__
        logger.info(f"DataFetcher初始化完成，AKShare版本: {self.akshare_version}")
    
    @retry_on_failure()
    def fetch_market_spot(self) -> Optional[pd.DataFrame]:
        """
        获取A股实时行情数据
        
        API: ak.stock_zh_a_spot() (同花顺) / ak.stock_zh_a_spot_em() (东方财富)
        AKShare版本: 1.11.0+
        更新频率: 实时
        
        Returns:
            DataFrame包含所有A股实时行情，列包括:
            - code: 股票代码
            - name: 股票名称
            - latest_price: 最新价
            - change_pct: 涨跌幅(%)
            - volume: 成交量
            - amount: 成交额
            - volume_ratio: 量比
            
        Raises:
            DataFetchError: 数据获取失败
        """
        logger.info("开始获取A股实时行情...")
        
        # 首先尝试同花顺数据源 (限制较少)
        df = None
        try:
            logger.info("尝试同花顺数据源...")
            df = ak.stock_zh_a_spot()
            logger.info("[OK] 同花顺数据源成功")
        except Exception as e:
            logger.warning(f"同花顺数据源失败: {e}，尝试东方财富...")
            try:
                df = ak.stock_zh_a_spot_em()
                logger.info("[OK] 东方财富数据源成功")
            except Exception as e2:
                logger.error(f"所有数据源失败: {e2}")
                raise DataFetchError(f"获取行情数据失败: {e2}")
        
        # 列名标准化 (转换为snake_case) - 适用于所有数据源
        if df is not None:
            column_mapping = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'latest_price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '量比': 'volume_ratio',
                '换手率': 'turnover',
                '市盈率-动态': 'pe_dynamic',
                '市净率': 'pb',
                '总市值': 'total_market_cap',
                '流通市值': 'float_market_cap',
                '涨速': 'speed',
                '5分钟涨跌': 'change_5min',
                '60日涨跌幅': 'change_60d',
                '年初至今涨跌幅': 'change_ytd',
            }
            
            # 重命名存在的列
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            
            # 添加元数据
            df['fetch_time'] = datetime.now()
            df['data_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # 数据类型转换
            numeric_columns = [
                'latest_price', 'change_pct', 'change_amount', 'volume', 'amount',
                'amplitude', 'high', 'low', 'open', 'pre_close', 'volume_ratio',
                'turnover', 'pe_dynamic', 'pb', 'total_market_cap', 'float_market_cap'
            ]
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 过滤ST股票和退市股票
            if 'name' in df.columns:
                df = df[~df['name'].str.contains('ST|退', na=False)]
            
            logger.info(f"[OK] 成功获取 {len(df)} 只股票行情数据")
            return df
        else:
            raise DataFetchError("获取行情数据失败: 数据为空")
    
    @retry_on_failure()
    def fetch_sector_list(self) -> Optional[pd.DataFrame]:
        """
        获取板块列表
        
        API: ak.stock_board_concept_name_em() (东方财富) 
              备用: 同花顺数据
        
        Returns:
            DataFrame包含板块信息
        """
        logger.info("开始获取板块列表...")
        
        # 尝试东方财富数据源
        try:
            df = ak.stock_board_concept_name_em()
            
            column_mapping = {
                '排名': 'rank',
                '板块名称': 'sector_name',
                '板块代码': 'sector_code',
                '最新价': 'latest_price',
                '涨跌额': 'change_amount',
                '涨跌幅': 'change_pct',
                '总市值': 'total_market_cap',
                '换手率': 'turnover',
                '上涨家数': 'up_count',
                '下跌家数': 'down_count',
                '领涨股票': 'leader_stock',
                '领涨股票-涨跌幅': 'leader_change_pct',
            }
            
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            df['fetch_time'] = datetime.now()
            
            logger.info(f"成功获取 {len(df)} 个板块数据")
            return df
            
        except Exception as e:
            logger.warning(f"东财板块列表失败: {e}")
            logger.warning("使用备用空数据继续...")
            # 返回空数据让程序继续
            return pd.DataFrame()
    
    @retry_on_failure()
    def fetch_sector_flow(self, sector_code: str) -> Optional[pd.DataFrame]:
        """
        获取板块资金流向
        
        API: ak.stock_sector_fund_flow_rank()
        
        Args:
            sector_code: 板块代码
            
        Returns:
            DataFrame包含资金流向数据
        """
        logger.info(f"开始获取板块 {sector_code} 资金流向...")
        
        try:
            df = ak.stock_sector_fund_flow_rank()
            
            column_mapping = {
                '序号': 'rank',
                '板块': 'sector_name',
                '板块代码': 'sector_code',
                '最新价': 'latest_price',
                '涨跌额': 'change_amount',
                '涨跌幅': 'change_pct',
                '主力净流入': 'main_inflow',
                '主力净流入占比': 'main_inflow_ratio',
                '超大单净流入': 'super_large_inflow',
                '超大单净流入占比': 'super_large_inflow_ratio',
                '大单净流入': 'large_inflow',
                '大单净流入占比': 'large_inflow_ratio',
                '中单净流入': 'medium_inflow',
                '中单净流入占比': 'medium_inflow_ratio',
                '小单净流入': 'small_inflow',
                '小单净流入占比': 'small_inflow_ratio',
            }
            
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            df['fetch_time'] = datetime.now()
            
            # 筛选指定板块
            if sector_code:
                df = df[df['sector_code'] == sector_code]
            
            logger.info(f"成功获取板块资金流向数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            raise DataFetchError(f"获取板块资金流向失败: {e}")
    
    @retry_on_failure()
    def fetch_stock_fund_flow(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取个股资金流向
        
        API: ak.stock_individual_fund_flow()
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame包含个股资金流向历史
        """
        logger.info(f"开始获取股票 {stock_code} 资金流向...")
        
        try:
            # 注意: AKShare接口可能需要市场前缀
            if not stock_code.startswith(('0', '3', '6', '8', '4')):
                raise ValueError(f"无效的股票代码: {stock_code}")
            
            df = ak.stock_individual_fund_flow(
                stock=stock_code,
                market="sh" if stock_code.startswith('6') else "sz"
            )
            
            column_mapping = {
                '日期': 'date',
                '主力净流入': 'main_inflow',
                '小单净流入': 'small_inflow',
                '中单净流入': 'medium_inflow',
                '大单净流入': 'large_inflow',
                '超大单净流入': 'super_large_inflow',
                '主力净流入占比': 'main_inflow_ratio',
                '小单净流入占比': 'small_inflow_ratio',
                '中单净流入占比': 'medium_inflow_ratio',
                '大单净流入占比': 'large_inflow_ratio',
                '超大单净流入占比': 'super_large_inflow_ratio',
                '收盘价': 'close',
                '涨跌幅': 'change_pct',
            }
            
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            df['code'] = stock_code
            df['fetch_time'] = datetime.now()
            
            logger.info(f"成功获取股票 {stock_code} 资金流向: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取股票资金流向失败: {e}")
            raise DataFetchError(f"获取股票资金流向失败: {e}")
    
    @retry_on_failure()
    def fetch_northbound_flow(self, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取北向资金流向
        
        API: ak.stock_hsgt_hist_em()
        
        Args:
            days: 获取天数
            
        Returns:
            DataFrame包含北向资金流向历史
        """
        logger.info(f"开始获取北向资金流向 (最近{days}天)...")
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 尝试不同版本的参数名
            try:
                df = ak.stock_hsgt_hist_em(
                    symbol="北向资金",
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )
            except TypeError:
                # AKShare 1.18+ 参数名变更
                df = ak.stock_hsgt_hist_em(
                    symbol="北向资金",
                    period="daily"
                )
            
            column_mapping = {
                '日期': 'date',
                '当日资金流入': 'daily_inflow',
                '当日余额': 'daily_balance',
                '历史资金累计流入': 'cumulative_inflow',
                '当日成交净买额': 'net_buy',
                '买入成交额': 'buy_amount',
                '卖出成交额': 'sell_amount',
                '沪股通当日资金流入': 'sh_daily_inflow',
                '沪股通当日余额': 'sh_daily_balance',
                '沪股通历史资金累计流入': 'sh_cumulative',
                '深股通当日资金流入': 'sz_daily_inflow',
                '深股通当日余额': 'sz_daily_balance',
                '深股通历史资金累计流入': 'sz_cumulative',
            }
            
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            df['fetch_time'] = datetime.now()
            
            logger.info(f"成功获取北向资金流向: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.warning(f"获取北向资金流向失败: {e}")
            logger.warning("使用空数据继续...")
            return pd.DataFrame()
    
    def fetch_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        批量获取所有所需数据
        
        Returns:
            Dict包含所有数据
        """
        logger.info("开始批量获取所有数据...")
        
        result = {
            'market_spot': None,
            'sector_list': None,
            'northbound_flow': None,
        }
        
        # 获取市场概况
        result['market_spot'] = self.fetch_market_spot()
        
        # 获取板块列表
        result['sector_list'] = self.fetch_sector_list()
        
        # 获取北向资金流向
        result['northbound_flow'] = self.fetch_northbound_flow(days=5)
        
        logger.info("批量数据获取完成")
        return result


class DataFetchError(Exception):
    """数据获取异常"""
    pass
