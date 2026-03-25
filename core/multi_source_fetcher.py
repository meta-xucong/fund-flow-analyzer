"""
多数据源获取器 - 提供智能数据获取和故障转移

功能特性:
1. 多数据源自动切换 - 当主数据源失败时自动切换到备用源
2. 优先级队列 - 根据数据源性能和可靠性排序
3. 可靠性统计 - 追踪每个数据源的成功率和响应时间
4. 自适应回退 - 根据历史表现动态调整数据源优先级

更新: 2026-03-22 - 整合了修复后的数据源（腾讯、港股、新股等）
"""

import os
# 设置代理例外
os.environ['NO_PROXY'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'
os.environ['no_proxy'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'

import akshare as ak
import pandas as pd
import time
import logging
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """数据源配置"""
    name: str
    priority: int  # 数字越小优先级越高
    fetch_func: Callable[[], Optional[pd.DataFrame]]
    description: str
    enabled: bool = True
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[datetime] = None
    last_failure_reason: Optional[str] = None
    
    @property
    def total_calls(self) -> int:
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0  # 默认为100%，让新源有机会被使用
        return self.success_count / self.total_calls
    
    @property
    def reliability_score(self) -> float:
        """综合可靠性评分 (0-100)"""
        if not self.enabled:
            return 0.0
        
        # 基于成功率
        score = self.success_rate * 60
        
        # 基于调用次数（经验值）
        if self.total_calls > 10:
            score += 20
        elif self.total_calls > 0:
            score += 10
        
        # 基于响应时间
        if 0 < self.avg_response_time < 5:
            score += 20
        elif 0 < self.avg_response_time < 10:
            score += 10
        
        return score
    
    def record_success(self, response_time: float):
        self.success_count += 1
        # 更新平均响应时间
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * (self.success_count - 1) + response_time) / self.success_count
        self.last_used = datetime.now()
        self.last_failure_reason = None
    
    def record_failure(self, reason: str):
        self.failure_count += 1
        self.last_failure_reason = reason
        logger.warning(f"数据源 {self.name} 失败: {reason}")
    
    def __repr__(self):
        return (f"DataSource({self.name}, priority={self.priority}, "
                f"success_rate={self.success_rate:.1%}, enabled={self.enabled})")


class MultiSourceFetcher:
    """
    多数据源获取器
    
    智能管理多个数据源，自动进行故障转移和负载均衡
    """
    
    def __init__(self):
        self.data_sources: List[DataSource] = []
        self._init_sources()
    
    def _init_sources(self):
        """初始化数据源 - 按优先级排序"""
        
        # ===== 实时行情数据源 =====
        
        # Priority 1: 同花顺/新浪 (当前网络环境最稳定)
        self.data_sources.append(DataSource(
            name="tonghuashun_sina",
            priority=1,
            fetch_func=self._fetch_spot_tonghuashun_sina,
            description="同花顺/新浪实时行情 - 实时性较好，当前网络环境下最稳定"
        ))
        
        # Priority 2: 腾讯 (备用实时源)
        self.data_sources.append(DataSource(
            name="tencent_spot",
            priority=2,
            fetch_func=self._fetch_spot_tencent,
            description="腾讯实时行情 - 需处理特殊格式"
        ))
        
        # Priority 3: 东财 (网络不通，暂时禁用)
        self.data_sources.append(DataSource(
            name="eastmoney_spot",
            priority=3,
            fetch_func=self._fetch_spot_eastmoney,
            description="东方财富实时行情 - 数据最全但被代理屏蔽",
            enabled=False  # 网络不通，禁用
        ))
        
        # ===== 历史数据数据源 =====
        
        # Priority 4: 腾讯历史数据 (已修复)
        self.data_sources.append(DataSource(
            name="tencent_hist",
            priority=4,
            fetch_func=self._fetch_hist_tencent,
            description="腾讯历史数据 - 使用sz/sh前缀格式，可用于验证数据"
        ))
        
        # ===== 辅助数据源 =====
        
        # Priority 5: 新股数据
        self.data_sources.append(DataSource(
            name="new_stocks",
            priority=5,
            fetch_func=self._fetch_new_stocks,
            description="新股数据 - 补充新上市股票信息"
        ))
        
        # Priority 6: 港股数据 (用于交叉验证)
        self.data_sources.append(DataSource(
            name="hk_spot",
            priority=6,
            fetch_func=self._fetch_hk_spot,
            description="港股实时行情 - 可用于跨市场分析"
        ))
    
    # ============ 实时行情获取函数 ============
    
    def _fetch_spot_tonghuashun_sina(self) -> Optional[pd.DataFrame]:
        """新浪实时行情 - Priority 1 (使用自定义新浪获取器)"""
        try:
            # 使用新浪获取器（绕过AKShare问题）
            from core.sina_fetcher import SinaDataFetcher
            fetcher = SinaDataFetcher()
            df = fetcher.fetch_market_spot(500)  # 获取500只样本
            if df is not None and len(df) > 0:
                return df
            return None
        except Exception as e:
            logger.warning(f"新浪数据获取失败: {e}")
            return None
    
    def _fetch_spot_tencent(self) -> Optional[pd.DataFrame]:
        """腾讯实时行情 - Priority 2"""
        try:
            df = ak.stock_zh_a_spot_tx()
            if df is not None and len(df) > 0:
                df = self._standardize_spot_columns(df)
                return df
            return None
        except Exception as e:
            logger.warning(f"腾讯数据获取失败: {e}")
            return None
    
    def _fetch_spot_eastmoney(self) -> Optional[pd.DataFrame]:
        """东方财富实时行情 - Priority 3 (Disabled due to network)"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and len(df) > 0:
                df = self._standardize_spot_columns(df)
                return df
            return None
        except Exception as e:
            logger.warning(f"东财数据获取失败: {e}")
            return None
    
    # ============ 历史数据获取函数 ============
    
    def _fetch_hist_tencent(self) -> Optional[pd.DataFrame]:
        """
        腾讯历史数据 - Priority 4
        使用 sz002730 格式获取个股历史数据
        可用于验证和补充实时数据
        """
        try:
            # 获取单个股票历史数据作为测试
            # 实际使用时应该传入股票代码参数
            df = ak.stock_zh_a_hist_tx(symbol='sz002730')
            if df is not None and len(df) > 0:
                logger.info(f"腾讯历史数据: {len(df)} 条记录")
                return df
            return None
        except Exception as e:
            logger.warning(f"腾讯历史数据获取失败: {e}")
            return None
    
    def _fetch_new_stocks(self) -> Optional[pd.DataFrame]:
        """新股数据 - Priority 5"""
        try:
            df = ak.stock_zh_a_new()
            if df is not None and len(df) > 0:
                logger.info(f"新股数据: {len(df)} 只新股")
                return df
            return None
        except Exception as e:
            logger.warning(f"新股数据获取失败: {e}")
            return None
    
    def _fetch_hk_spot(self) -> Optional[pd.DataFrame]:
        """港股实时行情 - Priority 6"""
        try:
            df = ak.stock_hk_spot_em()
            if df is not None and len(df) > 0:
                logger.info(f"港股数据: {len(df)} 只股票")
                return df
            return None
        except Exception as e:
            logger.warning(f"港股数据获取失败: {e}")
            return None
    
    def _standardize_spot_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化实时行情列名"""
        # 列名映射
        column_map = {
            '代码': 'code',
            '名称': 'name',
            '最新价': 'latest',
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
            '市盈率-动态': 'pe',
            '市净率': 'pb',
            '总市值': 'total_market_cap',
            '流通市值': 'float_market_cap',
            '涨速': 'change_speed',
            '5分钟涨跌': 'change_5min',
            '60日涨跌幅': 'change_60d',
            '年初至今涨跌幅': 'change_ytd',
        }
        
        # 重命名列
        df = df.rename(columns=column_map)
        
        # 确保必要列存在
        required_columns = ['code', 'name', 'latest', 'change_pct']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"缺失必要列: {col}")
        
        return df
    
    def _standardize_data(self, df: pd.DataFrame, source_name: str) -> pd.DataFrame:
        """标准化数据格式，确保一致性"""
        # 添加数据源标记
        df['data_source'] = source_name
        df['fetch_time'] = datetime.now()
        
        # 数据类型转换
        numeric_columns = ['latest', 'change_pct', 'volume', 'amount', 'volume_ratio']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 过滤无效数据
        if 'latest' in df.columns:
            df = df[df['latest'] > 0]
        
        if 'change_pct' in df.columns:
            df = df[df['change_pct'].abs() < 50]  # 过滤异常涨跌幅
        
        return df
    
    def fetch_market_spot(self, max_retries: int = 3, retry_delay: float = 2.0) -> Optional[pd.DataFrame]:
        """
        获取A股实时行情数据，支持自动故障转移
        
        Args:
            max_retries: 每个数据源的最大重试次数
            retry_delay: 重试间隔（秒）
        
        Returns:
            标准化后的行情DataFrame，失败返回None
        """
        enabled_sources = [s for s in self.data_sources if s.enabled]
        
        if not enabled_sources:
            logger.error("没有可用的数据源")
            return None
        
        # 按优先级排序（优先级数字越小越靠前）
        sorted_sources = sorted(enabled_sources, key=lambda s: (s.priority, -s.reliability_score))
        
        logger.info(f"开始获取行情数据，可用源: {len(sorted_sources)}")
        
        for attempt in range(max_retries):
            logger.debug(f"第 {attempt + 1} 轮尝试")
            
            for source in sorted_sources:
                start_time = time.time()
                
                try:
                    logger.info(f"尝试数据源: {source.name} ({source.description})")
                    
                    df = source.fetch_func()
                    
                    if df is not None and len(df) > 0:
                        # 记录成功
                        response_time = time.time() - start_time
                        source.record_success(response_time)
                        
                        # 标准化数据
                        df = self._standardize_data(df, source.name)
                        
                        logger.info(f"✓ {source.name} 成功: {len(df)} 条记录，耗时 {response_time:.2f}s")
                        return df
                    else:
                        source.record_failure("返回空数据")
                        
                except Exception as e:
                    response_time = time.time() - start_time
                    source.record_failure(str(e))
                    logger.warning(f"✗ {source.name} 失败 ({response_time:.2f}s): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay}s 后重试...")
                time.sleep(retry_delay)
        
        logger.error("所有数据源均获取失败")
        return None
    
    def fetch_market_spot_with_fallback(self, primary_source: str = "tonghuashun_sina") -> Optional[pd.DataFrame]:
        """
        从指定主数据源获取，失败时自动切换到备用源
        
        Args:
            primary_source: 首选数据源名称
        
        Returns:
            行情DataFrame
        """
        source_map = {s.name: s for s in self.data_sources if s.enabled}
        
        if primary_source in source_map:
            # 尝试主数据源
            df = source_map[primary_source].fetch_func()
            if df is not None and len(df) > 0:
                return self._standardize_data(df, primary_source)
        
        # 主数据源失败，使用自动故障转移
        return self.fetch_market_spot()
    
    def get_source_stats(self) -> pd.DataFrame:
        """获取各数据源的统计信息"""
        stats = []
        for source in self.data_sources:
            stats.append({
                'name': source.name,
                'enabled': source.enabled,
                'priority': source.priority,
                'success_rate': f"{source.success_rate:.1%}",
                'total_calls': source.total_calls,
                'avg_response_time': f"{source.avg_response_time:.2f}s",
                'reliability_score': f"{source.reliability_score:.1f}",
                'last_failure': source.last_failure_reason[:50] if source.last_failure_reason else None
            })
        return pd.DataFrame(stats)
    
    def disable_source(self, source_name: str):
        """禁用指定数据源"""
        for source in self.data_sources:
            if source.name == source_name:
                source.enabled = False
                logger.info(f"已禁用数据源: {source_name}")
                return True
        return False
    
    def enable_source(self, source_name: str):
        """启用指定数据源"""
        for source in self.data_sources:
            if source.name == source_name:
                source.enabled = True
                logger.info(f"已启用数据源: {source_name}")
                return True
        return False


# 全局单例
_fetcher_instance: Optional[MultiSourceFetcher] = None


def get_multi_source_fetcher() -> MultiSourceFetcher:
    """获取多数据源获取器单例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = MultiSourceFetcher()
    return _fetcher_instance


def reset_fetcher():
    """重置获取器（用于测试）"""
    global _fetcher_instance
    _fetcher_instance = None


# ============ 便捷函数 ============

def fetch_spot_data(preferred_source: str = "tonghuashun_sina") -> Optional[pd.DataFrame]:
    """
    便捷函数：获取实时行情数据
    
    Args:
        preferred_source: 首选数据源
    
    Returns:
        行情DataFrame
    """
    fetcher = get_multi_source_fetcher()
    return fetcher.fetch_market_spot_with_fallback(preferred_source)


def get_data_source_stats() -> pd.DataFrame:
    """便捷函数：获取数据源统计"""
    fetcher = get_multi_source_fetcher()
    return fetcher.get_source_stats()


# ============ 测试代码 ============

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("多数据源获取器测试")
    print("=" * 60)
    
    fetcher = get_multi_source_fetcher()
    
    # 测试实时行情获取
    print("\n【测试1】实时行情获取")
    df = fetcher.fetch_market_spot(max_retries=2, retry_delay=1.0)
    if df is not None:
        print(f"✓ 成功获取 {len(df)} 条记录")
        print(f"  数据源: {df['data_source'].iloc[0] if 'data_source' in df.columns else 'unknown'}")
        print(f"  列名: {list(df.columns)}")
    else:
        print("✗ 获取失败")
    
    # 显示数据源统计
    print("\n【测试2】数据源统计")
    stats = fetcher.get_source_stats()
    print(stats.to_string(index=False))
