# -*- coding: utf-8 -*-
"""
终极稳定版数据获取器 - 带严格限流和指数退避

参考AKShare官方实现和社区经验:
- 东财API: ~5次/秒 (最严格)
- 新浪API: ~10-20次/秒
- 腾讯API: 相对宽松
- 建议安全间隔: 0.2-0.5秒/请求

特性:
1. 令牌桶限流 (Token Bucket Rate Limiter)
2. 指数退避 + 随机抖动
3. 自适应延迟调整
4. 熔断机制 (Circuit Breaker)
5. 连接池管理
"""

import os
os.environ['NO_PROXY'] = 'sina.com.cn,qt.gtimg.cn,gtimg.cn,eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com'

import time
import random
import logging
import requests
import pandas as pd
from typing import Optional, Callable, Any, Dict, Tuple
from datetime import datetime, timedelta
from functools import wraps
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    令牌桶限流器
    
    控制请求速率，避免触发反爬机制
    """
    
    def __init__(self, rate: float = 2.0, burst: int = 5):
        """
        初始化限流器
        
        Args:
            rate: 每秒允许的请求数 (默认2次/秒 = 0.5秒间隔)
            burst: 突发请求容量 (默认5个)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = False
    
    def acquire(self, blocking: bool = True) -> bool:
        """
        获取一个令牌
        
        Args:
            blocking: 是否阻塞等待
        
        Returns:
            是否成功获取令牌
        """
        while True:
            now = time.time()
            elapsed = now - self.last_update
            
            # 添加新令牌
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            if not blocking:
                return False
            
            # 等待令牌可用
            sleep_time = (1 - self.tokens) / self.rate
            time.sleep(sleep_time)


class CircuitBreaker:
    """
    熔断器
    
    连续失败时自动开启熔断，防止雪崩效应
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 连续失败次数阈值
            recovery_timeout: 熔断后恢复等待时间(秒)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行被保护的函数
        """
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                logger.info("熔断器进入半开状态，尝试恢复")
            else:
                raise Exception(f"熔断器开启中，请{self.recovery_timeout}秒后重试")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """成功回调"""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            logger.info("熔断器关闭，服务恢复正常")
        self.failure_count = 0
    
    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"熔断器开启! 连续失败{self.failure_count}次")


def exponential_backoff_retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    指数退避重试装饰器
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟(秒)
        max_delay: 最大延迟(秒)
        exponential_base: 指数基数
        jitter: 是否添加随机抖动
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # 计算指数退避延迟
                        delay = base_delay * (exponential_base ** attempt)
                        delay = min(delay, max_delay)
                        
                        # 添加随机抖动 (0-20%)
                        if jitter:
                            delay *= (1 + random.uniform(0, 0.2))
                        
                        logger.warning(
                            f"{func.__name__} 第{attempt + 1}次失败: {e}, "
                            f"{delay:.2f}秒后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数，放弃")
            
            raise last_exception
        
        return wrapper
    return decorator


class UltraStableFetcher:
    """
    终极稳定版数据获取器
    
    集成限流、熔断、指数退避等机制
    """
    
    def __init__(self):
        # 针对不同数据源设置不同的限流策略
        self.rate_limiters = {
            'tencent': TokenBucketRateLimiter(rate=3.0, burst=5),    # 腾讯: 3次/秒
            'sina': TokenBucketRateLimiter(rate=2.0, burst=3),       # 新浪: 2次/秒 (更严格)
            'eastmoney': TokenBucketRateLimiter(rate=1.0, burst=2),  # 东财: 1次/秒 (最严格)
        }
        
        # 熔断器
        self.circuit_breakers = {
            'tencent': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
            'sina': CircuitBreaker(failure_threshold=3, recovery_timeout=30),
            'eastmoney': CircuitBreaker(failure_threshold=3, recovery_timeout=120),
        }
        
        # Session配置
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_delay': 0.0,
        }
    
    def _make_request(
        self,
        url: str,
        params: Dict = None,
        headers: Dict = None,
        source: str = 'sina',
        timeout: int = 15
    ) -> requests.Response:
        """
        发送HTTP请求，带限流和熔断
        """
        # 获取对应数据源的限流器和熔断器
        rate_limiter = self.rate_limiters.get(source, self.rate_limiters['sina'])
        circuit_breaker = self.circuit_breakers.get(source, self.circuit_breakers['sina'])
        
        # 限流
        rate_limiter.acquire()
        
        # 熔断保护下的请求
        def do_request():
            self.stats['total_requests'] += 1
            start_time = time.time()
            
            try:
                resp = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
                resp.raise_for_status()
                
                self.stats['successful_requests'] += 1
                elapsed = time.time() - start_time
                self.stats['total_delay'] += elapsed
                
                return resp
                
            except Exception as e:
                self.stats['failed_requests'] += 1
                raise e
        
        return circuit_breaker.call(do_request)
    
    @exponential_backoff_retry(max_retries=5, base_delay=1.0, max_delay=30.0)
    def fetch_tencent_realtime(self, codes: list) -> pd.DataFrame:
        """
        获取腾讯实时行情 (带指数退避)
        """
        if not codes:
            return pd.DataFrame()
        
        codes_str = ','.join(codes)
        url = f'http://qt.gtimg.cn/q={codes_str}'
        
        resp = self._make_request(
            url,
            source='tencent',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        resp.encoding = 'gbk'
        
        # 解析数据
        results = []
        for line in resp.text.strip().split(';'):
            line = line.strip()
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
            
            results.append({
                'code': fields[2],
                'name': fields[1],
                'latest': float(fields[3]) if fields[3] else 0,
                'pre_close': float(fields[4]) if fields[4] else 0,
                'open': float(fields[5]) if fields[5] else 0,
                'high': float(fields[33]) if fields[33] else 0,
                'low': float(fields[34]) if fields[34] else 0,
                'volume': int(float(fields[6])) if fields[6] else 0,
                'amount': float(fields[37]) * 10000 if fields[37] else 0,
                'volume_ratio': float(fields[38]) if fields[38] else 0,
                'pe': float(fields[39]) if fields[39] else 0,
                'pb': float(fields[46]) if fields[46] else 0,
                'change_pct': float(fields[32]) if len(fields) > 32 and fields[32] else 0,
            })
        
        df = pd.DataFrame(results)
        if not df.empty and 'change_pct' not in df.columns:
            df['change_pct'] = ((df['latest'] - df['pre_close']) / df['pre_close'] * 100).round(2)
        
        return df
    
    @exponential_backoff_retry(max_retries=5, base_delay=1.0, max_delay=30.0)
    def fetch_sina_realtime(self, codes: list) -> pd.DataFrame:
        """
        获取新浪实时行情 (带指数退避)
        """
        if not codes:
            return pd.DataFrame()
        
        codes_str = ','.join(codes)
        url = f'https://hq.sinajs.cn/list={codes_str}'
        
        resp = self._make_request(
            url,
            source='sina',
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://finance.sina.com.cn',
            }
        )
        
        resp.encoding = 'gb2312'
        
        # 解析数据
        results = []
        for line in resp.text.strip().split(';'):
            line = line.strip()
            if not line or 'var hq_str_' not in line:
                continue
            
            parts = line.split('="')
            if len(parts) != 2:
                continue
            
            code_key = parts[0].replace('var hq_str_', '')
            data_str = parts[1].rstrip('"')
            
            if not data_str:
                continue
            
            fields = data_str.split(',')
            if len(fields) < 33:
                continue
            
            results.append({
                'code': code_key[2:],
                'name': fields[0],
                'open': float(fields[1]) if fields[1] else 0,
                'pre_close': float(fields[2]) if fields[2] else 0,
                'latest': float(fields[3]) if fields[3] else 0,
                'high': float(fields[4]) if fields[4] else 0,
                'low': float(fields[5]) if fields[5] else 0,
                'volume': int(float(fields[8])) if fields[8] else 0,
                'amount': float(fields[9]) if fields[9] else 0,
                'date': fields[30],
                'time': fields[31],
            })
        
        df = pd.DataFrame(results)
        if not df.empty:
            df['change_pct'] = ((df['latest'] - df['pre_close']) / df['pre_close'] * 100).round(2)
        
        return df
    
    def fetch_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表 (带重试)
        """
        import akshare as ak
        
        @exponential_backoff_retry(max_retries=3, base_delay=2.0)
        def _fetch():
            return ak.stock_info_a_code_name()
        
        return _fetch()
    
    def fetch_tencent_hist(self, symbol: str) -> pd.DataFrame:
        """
        获取腾讯历史数据 (带指数退避)
        
        Args:
            symbol: 股票代码，如 'sz000001', 'sh600000'
        
        Returns:
            DataFrame with historical data
        """
        import akshare as ak
        
        @exponential_backoff_retry(max_retries=5, base_delay=1.0, max_delay=30.0)
        def _fetch():
            return ak.stock_zh_a_hist_tx(symbol=symbol)
        
        try:
            return _fetch()
        except Exception as e:
            logger.warning(f"获取 {symbol} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total_requests']
        success = self.stats['successful_requests']
        failed = self.stats['failed_requests']
        
        avg_delay = self.stats['total_delay'] / total if total > 0 else 0
        
        return {
            'total_requests': total,
            'successful_requests': success,
            'failed_requests': failed,
            'success_rate': f"{success/total*100:.1f}%" if total > 0 else "N/A",
            'average_delay': f"{avg_delay:.3f}s",
        }


# 全局单例
_fetcher_instance = None


def get_ultra_stable_fetcher() -> UltraStableFetcher:
    """获取终极稳定版获取器单例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = UltraStableFetcher()
    return _fetcher_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("终极稳定版数据获取器测试")
    print("=" * 70)
    
    fetcher = get_ultra_stable_fetcher()
    
    # 测试获取股票列表
    print("\n[测试1] 获取股票列表...")
    stock_list = fetcher.fetch_stock_list()
    print(f"  成功: {len(stock_list)} 只股票")
    
    # 测试获取实时行情
    print("\n[测试2] 获取腾讯实时行情 (50只)...")
    sample_codes = [f"{'sh' if c.startswith('6') else 'sz'}{c}" 
                    for c in stock_list['code'].head(50)]
    df = fetcher.fetch_tencent_realtime(sample_codes)
    print(f"  成功: {len(df)} 只股票")
    if not df.empty:
        print(f"  示例: {df.iloc[0]['code']} {df.iloc[0]['name']} @ {df.iloc[0]['latest']}")
    
    # 打印统计
    print("\n[统计信息]")
    stats = fetcher.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
