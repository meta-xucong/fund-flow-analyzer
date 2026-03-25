"""
自适应数据获取器 - 在当前网络环境下智能选择可用数据源

当前环境限制:
- 同花顺/新浪实时接口: 返回HTML错误（可能是API变更）
- 东财实时接口: 被代理屏蔽
- 腾讯历史接口: 可用但速度慢
- 日线数据接口: 可用

策略:
1. 优先使用日线数据获取全市场数据（盘前可用前一日数据）
2. 使用历史数据接口作为补充
3. 提供模拟数据功能用于测试
"""

import akshare as ak
import pandas as pd
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AdaptiveDataFetcher:
    """
    自适应数据获取器
    
    根据当前网络环境选择最佳数据源
    """
    
    def __init__(self):
        self.last_success_source = None
        self.cache = {}  # 简单缓存
    
    def fetch_market_data(self, date: Optional[str] = None, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        获取市场数据
        
        优先顺序:
        1. 日线数据 (stock_zh_a_daily) - 最稳定
        2. 新股数据 + 历史数据组合
        3. 缓存数据（如果启用）
        
        Args:
            date: 指定日期，默认为昨天
            use_cache: 是否使用缓存
        
        Returns:
            行情DataFrame
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        # 检查缓存
        cache_key = f"market_{date}"
        if use_cache and cache_key in self.cache:
            logger.info(f"使用缓存数据: {date}")
            return self.cache[cache_key].copy()
        
        # 尝试获取日线数据（分批获取避免超时）
        df = self._fetch_daily_data_sample()
        if df is not None and len(df) > 0:
            self.last_success_source = "daily_sample"
            if use_cache:
                self.cache[cache_key] = df.copy()
            return df
        
        # 尝试获取新股数据作为补充
        df = self._fetch_new_stocks()
        if df is not None and len(df) > 0:
            self.last_success_source = "new_stocks"
            if use_cache:
                self.cache[cache_key] = df.copy()
            return df
        
        logger.error("所有数据源均不可用")
        return None
    
    def _fetch_daily_data_sample(self, max_stocks: int = 100) -> Optional[pd.DataFrame]:
        """
        获取日线数据样本
        
        获取部分活跃股票的日线数据作为市场参考
        """
        try:
            # 获取股票列表
            stock_list = ak.stock_zh_a_spot_em()
            if stock_list is None or len(stock_list) == 0:
                return None
            
            # 按成交额排序，取前N只
            stock_list = stock_list.sort_values('成交额', ascending=False).head(max_stocks)
            
            results = []
            for _, row in stock_list.head(50).iterrows():  # 限制数量避免超时
                try:
                    code = row['代码']
                    # 获取日线数据
                    hist = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                             start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                                             end_date=datetime.now().strftime('%Y%m%d'),
                                             adjust="qfq")
                    if hist is not None and len(hist) > 0:
                        latest = hist.iloc[-1].copy()
                        latest['code'] = code
                        latest['name'] = row['名称']
                        results.append(latest)
                except Exception as e:
                    continue
            
            if results:
                df = pd.DataFrame(results)
                df['data_source'] = 'daily_sample'
                df['fetch_time'] = datetime.now()
                logger.info(f"日线样本数据: {len(df)} 只股票")
                return df
            
            return None
            
        except Exception as e:
            logger.warning(f"日线数据样本获取失败: {e}")
            return None
    
    def _fetch_new_stocks(self) -> Optional[pd.DataFrame]:
        """获取新股数据"""
        try:
            df = ak.stock_zh_a_new()
            if df is not None and len(df) > 0:
                df = df.rename(columns={
                    '代码': 'code',
                    '名称': 'name',
                    '最新价': 'latest',
                    '涨跌幅': 'change_pct',
                })
                df['data_source'] = 'new_stocks'
                df['fetch_time'] = datetime.now()
                logger.info(f"新股数据: {len(df)} 只")
                return df
            return None
        except Exception as e:
            logger.warning(f"新股数据获取失败: {e}")
            return None
    
    def fetch_single_stock_hist(self, code: str, days: int = 5) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据
        
        Args:
            code: 股票代码
            days: 获取天数
        
        Returns:
            历史数据DataFrame
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 30)  # 多取一些确保有足够交易日
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )
            
            if df is not None and len(df) > 0:
                df['code'] = code
                df['data_source'] = 'hist'
                df['fetch_time'] = datetime.now()
                return df.tail(days)  # 返回最近N天
            
            return None
            
        except Exception as e:
            logger.warning(f"股票 {code} 历史数据获取失败: {e}")
            return None
    
    def generate_mock_data(self, n_stocks: int = 500) -> pd.DataFrame:
        """
        生成模拟数据用于测试
        
        Args:
            n_stocks: 生成股票数量
        
        Returns:
            模拟行情DataFrame
        """
        import numpy as np
        
        np.random.seed(42)  # 可重复
        
        codes = [f"{np.random.randint(300000, 301000):06d}" for _ in range(n_stocks)]
        names = [f"股票{i}" for i in range(n_stocks)]
        
        base_prices = np.random.uniform(5, 100, n_stocks)
        change_pcts = np.random.normal(0, 2, n_stocks)  # 正态分布，均值0，标准差2%
        
        df = pd.DataFrame({
            'code': codes,
            'name': names,
            'pre_close': base_prices,
            'change_pct': change_pcts,
            'latest': base_prices * (1 + change_pcts / 100),
            'volume': np.random.randint(100000, 10000000, n_stocks),
            'amount': np.random.uniform(1e7, 1e9, n_stocks),
            'data_source': 'mock',
            'fetch_time': datetime.now()
        })
        
        logger.info(f"生成模拟数据: {len(df)} 只股票")
        return df


# 全局单例
_fetcher_instance: Optional[AdaptiveDataFetcher] = None


def get_adaptive_fetcher() -> AdaptiveDataFetcher:
    """获取自适应获取器单例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = AdaptiveDataFetcher()
    return _fetcher_instance


# 便捷函数
def fetch_market_data(date: Optional[str] = None, use_mock: bool = False) -> Optional[pd.DataFrame]:
    """
    便捷函数：获取市场数据
    
    Args:
        date: 指定日期
        use_mock: 失败时是否使用模拟数据
    
    Returns:
        行情DataFrame
    """
    fetcher = get_adaptive_fetcher()
    df = fetcher.fetch_market_data(date)
    
    if df is None and use_mock:
        logger.warning("使用模拟数据")
        df = fetcher.generate_mock_data()
    
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("自适应数据获取器测试")
    print("=" * 60)
    
    fetcher = get_adaptive_fetcher()
    
    # 测试数据获取
    print("\n[测试1] 获取市场数据")
    df = fetcher.fetch_market_data()
    if df is not None:
        print(f"OK: {len(df)} 条记录")
        print(f"   数据源: {df['data_source'].iloc[0]}")
    else:
        print("FAIL: 获取失败")
    
    # 测试单只股票历史
    print("\n[测试2] 获取单只股票历史")
    hist = fetcher.fetch_single_stock_hist('000001', days=5)
    if hist is not None:
        print(f"OK: {len(hist)} 条记录")
        print(hist[['日期', '收盘', '涨跌幅']].to_string(index=False))
    else:
        print("FAIL: 获取失败")
    
    # 测试模拟数据
    print("\n[测试3] 生成模拟数据")
    mock = fetcher.generate_mock_data(10)
    print(f"OK: {len(mock)} 只股票")
    print(mock[['code', 'name', 'latest', 'change_pct']].head().to_string(index=False))
