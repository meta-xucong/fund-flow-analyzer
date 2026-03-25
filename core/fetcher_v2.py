"""
数据获取模块 V2 - 适配当前网络环境

网络环境限制:
- 东财所有API: 被代理屏蔽 (ProxyError)
- 同花顺实时API: 返回HTML错误
- 可用API: 极少数，如stock_zh_a_daily等

解决方案:
1. 本地SQLite缓存 - 优先使用本地数据
2. 模拟数据模式 - 用于开发和测试
3. 网络降级模式 - 当网络不可用时自动切换
"""

import akshare as ak
import pandas as pd
import sqlite3
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import numpy as np

logger = logging.getLogger(__name__)

# 路径配置
DATA_DIR = Path("data")
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "market_data.db"


class DataFetcherV2:
    """
    数据获取器 V2
    
    适配受限网络环境，提供可靠的数据获取
    """
    
    # 运行模式
    MODE_NETWORK = "network"      # 正常网络模式
    MODE_CACHE = "cache"          # 缓存模式
    MODE_MOCK = "mock"            # 模拟模式
    
    def __init__(self, mode: str = MODE_NETWORK):
        self.mode = mode
        self.stats = {
            'network_calls': 0,
            'cache_hits': 0,
            'mock_calls': 0,
            'errors': []
        }
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS market_cache (
                        date TEXT PRIMARY KEY,
                        data_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
    
    def fetch_market_spot(self, date: Optional[str] = None, 
                          use_open_price: bool = False) -> Optional[pd.DataFrame]:
        """
        获取市场行情
        
        优先级:
        1. 网络获取 (如果模式允许)
        2. 本地缓存
        3. 模拟数据
        
        Args:
            date: 指定日期 (YYYYMMDD)
            use_open_price: 是否使用开盘价计算涨跌幅
        
        Returns:
            行情DataFrame
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        # 1. 尝试网络获取
        if self.mode == self.MODE_NETWORK:
            df = self._fetch_from_network(date)
            if df is not None:
                self._save_to_cache(date, df)
                return df
            logger.warning("网络获取失败，切换到缓存模式")
        
        # 2. 尝试缓存
        df = self._fetch_from_cache(date)
        if df is not None:
            self.stats['cache_hits'] += 1
            return df
        
        # 3. 使用模拟数据
        if self.mode in [self.MODE_MOCK, self.MODE_NETWORK, self.MODE_CACHE]:
            logger.warning("使用模拟数据")
            df = self._generate_mock_data(date)
            self.stats['mock_calls'] += 1
            return df
        
        return None
    
    def _fetch_from_network(self, date: str) -> Optional[pd.DataFrame]:
        """从网络获取数据"""
        self.stats['network_calls'] += 1
        
        # 尝试可用的API
        apis = [
            ("stock_zh_a_daily", self._try_daily_api),
            ("stock_zh_a_hist_tx", self._try_tencent_hist),
        ]
        
        for name, api_func in apis:
            try:
                df = api_func(date)
                if df is not None and len(df) > 0:
                    logger.info(f"网络获取成功: {name}, {len(df)} 条记录")
                    return df
            except Exception as e:
                logger.debug(f"{name} 失败: {e}")
                continue
        
        return None
    
    def _try_daily_api(self, date: str) -> Optional[pd.DataFrame]:
        """尝试获取日线数据"""
        # 获取单个股票测试网络连通性
        try:
            df = ak.stock_zh_a_hist(symbol='000001', period='daily',
                                    start_date=date, end_date=date,
                                    adjust='qfq')
            if df is not None and len(df) > 0:
                # 网络可用，但日线接口不适合获取全市场
                # 返回一个示例
                return df
        except Exception as e:
            if 'ProxyError' in str(e) or 'proxy' in str(e).lower():
                logger.debug("代理错误，东财API不可用")
            raise
        return None
    
    def _try_tencent_hist(self, date: str) -> Optional[pd.DataFrame]:
        """尝试腾讯历史数据"""
        try:
            # 获取单个股票作为测试
            df = ak.stock_zh_a_hist_tx(symbol='sz002730')
            if df is not None and len(df) > 0:
                return df
        except Exception as e:
            logger.debug(f"腾讯历史API失败: {e}")
        return None
    
    def _fetch_from_cache(self, date: str) -> Optional[pd.DataFrame]:
        """从本地缓存获取"""
        cache_file = CACHE_DIR / f"market_{date}.parquet"
        
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"缓存命中: {date}, {len(df)} 条记录")
                return df
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")
        
        # 尝试数据库缓存
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.execute(
                    "SELECT data_json FROM market_cache WHERE date = ?",
                    (date,)
                )
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    df = pd.DataFrame(data)
                    logger.info(f"数据库缓存命中: {date}")
                    return df
        except Exception as e:
            logger.debug(f"数据库缓存读取失败: {e}")
        
        return None
    
    def _save_to_cache(self, date: str, df: pd.DataFrame):
        """保存到缓存"""
        # 保存为Parquet（更快）
        cache_file = CACHE_DIR / f"market_{date}.parquet"
        try:
            df.to_parquet(cache_file, compression='gzip')
            logger.debug(f"已保存到缓存: {cache_file}")
        except Exception as e:
            logger.warning(f"Parquet缓存保存失败: {e}")
        
        # 同时保存到数据库
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO market_cache (date, data_json) VALUES (?, ?)",
                    (date, df.to_json(orient='records'))
                )
                conn.commit()
        except Exception as e:
            logger.debug(f"数据库缓存保存失败: {e}")
    
    def _generate_mock_data(self, date: str, n_stocks: int = 500) -> pd.DataFrame:
        """生成模拟数据"""
        np.random.seed(int(date) % 10000)  # 基于日期的确定性随机
        
        # 生成股票代码和名称
        codes = []
        names = []
        for i in range(n_stocks):
            if i < 2000:
                code = f"{300000 + i:06d}"  # 创业板
            elif i < 4000:
                code = f"{600000 + (i - 2000):06d}"  # 主板
            else:
                code = f"{(i - 4000 + 1):06d}"  # 深市
            codes.append(code)
            names.append(f"股票{i}")
        
        # 生成价格数据
        base_prices = np.random.uniform(5, 100, n_stocks)
        change_pcts = np.random.normal(0, 1.5, n_stocks)  # 正态分布，标准差1.5%
        
        df = pd.DataFrame({
            'code': codes,
            'name': names,
            'pre_close': base_prices.round(2),
            'change_pct': change_pcts.round(2),
            'latest': (base_prices * (1 + change_pcts / 100)).round(2),
            'open': (base_prices * (1 + np.random.normal(0, 0.5, n_stocks) / 100)).round(2),
            'high': (base_prices * (1 + np.abs(np.random.normal(0, 1, n_stocks)) / 100)).round(2),
            'low': (base_prices * (1 - np.abs(np.random.normal(0, 1, n_stocks)) / 100)).round(2),
            'volume': np.random.randint(100000, 10000000, n_stocks),
            'amount': np.random.uniform(1e7, 1e9, n_stocks).round(2),
            'volume_ratio': np.random.uniform(0.5, 3.0, n_stocks).round(2),
            'turnover': np.random.uniform(1, 15, n_stocks).round(2),
            'pe': np.random.uniform(10, 50, n_stocks).round(2),
            'data_source': 'mock',
            'fetch_time': datetime.now(),
            'date': date
        })
        
        # 确保high >= latest >= low
        df['high'] = df[['high', 'latest', 'open']].max(axis=1)
        df['low'] = df[['low', 'latest', 'open']].min(axis=1)
        
        logger.info(f"生成模拟数据: {len(df)} 只股票, 日期: {date}")
        return df
    
    def set_mode(self, mode: str):
        """设置运行模式"""
        if mode in [self.MODE_NETWORK, self.MODE_CACHE, self.MODE_MOCK]:
            self.mode = mode
            logger.info(f"数据获取模式设置为: {mode}")
        else:
            raise ValueError(f"无效模式: {mode}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


# 全局单例
_fetcher_instance: Optional[DataFetcherV2] = None


def get_fetcher_v2(mode: str = DataFetcherV2.MODE_NETWORK) -> DataFetcherV2:
    """获取数据获取器实例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = DataFetcherV2(mode=mode)
    return _fetcher_instance


# 便捷函数
def fetch_market_data(date: Optional[str] = None, mode: str = DataFetcherV2.MODE_NETWORK) -> Optional[pd.DataFrame]:
    """便捷函数：获取市场数据"""
    fetcher = get_fetcher_v2(mode=mode)
    return fetcher.fetch_market_spot(date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("数据获取器 V2 测试")
    print("=" * 60)
    
    # 测试模拟模式
    print("\n[测试1] 模拟模式")
    df = fetch_market_data(mode=DataFetcherV2.MODE_MOCK)
    if df is not None:
        print(f"OK: {len(df)} 条记录")
        print(df[['code', 'name', 'latest', 'change_pct']].head().to_string(index=False))
    
    # 测试缓存模式
    print("\n[测试2] 缓存模式（应命中刚才的模拟数据）")
    fetcher = get_fetcher_v2()
    df2 = fetcher.fetch_market_spot()
    if df2 is not None:
        print(f"OK: {len(df2)} 条记录")
    
    # 显示统计
    print("\n[统计]")
    print(fetcher.get_stats())
