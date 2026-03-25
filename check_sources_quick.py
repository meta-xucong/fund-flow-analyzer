#!/usr/bin/env python3
"""快速检查可用数据源 - 当前网络环境"""

import akshare as ak
import warnings
warnings.filterwarnings('ignore')

def quick_test(name, func, timeout=10):
    """快速测试单个API"""
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def handler(signum, frame):
        raise TimeoutError()
    
    # Windows may not support signal.SIGALRM
    try:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout)
    except:
        pass
    
    try:
        result = func()
        if result is not None and len(result) > 0:
            return True, len(result), "OK"
        return False, 0, "Empty"
    except TimeoutError:
        return False, 0, "Timeout"
    except Exception as e:
        err_str = str(e)[:30]
        if "proxy" in str(e).lower() or "ProxyError" in str(e):
            return False, 0, "ProxyBlocked"
        elif "json" in str(e).lower() or "decode" in str(e).lower():
            return False, 0, "JSONError"
        elif "stock" in str(e).lower() and "exist" in str(e).lower():
            return False, 0, "StockNotExist"
        return False, 0, f"Error:{type(e).__name__[:15]}"

print("=" * 70)
print("Data Source Availability Check - Current Network")
print("=" * 70)
print("Time: 2026-03-22")
print("Proxy: Clash 127.0.0.1:7890")
print("-" * 70)

# 测试列表
sources = [
    ("stock_zh_a_spot (同花顺/新浪实时)", lambda: ak.stock_zh_a_spot()),
    ("stock_zh_a_spot_em (东财实时)", lambda: ak.stock_zh_a_spot_em()),
    ("stock_zh_a_hist (东财历史)", lambda: ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20250320', end_date='20250321')),
    ("stock_zh_a_hist_tx (腾讯历史)", lambda: ak.stock_zh_a_hist_tx(symbol='sz002730')),
    ("stock_zh_a_new (新股)", lambda: ak.stock_zh_a_new()),
    ("stock_hk_spot_em (港股)", lambda: ak.stock_hk_spot_em().head(100)),
    ("stock_zh_a_daily (新浪日线)", lambda: ak.stock_zh_a_daily(symbol='sh600000', start_date='20250320', end_date='20250321')),
]

results = []
for name, func in sources:
    ok, count, status = quick_test(name, func)
    results.append((name, ok, count, status))
    symbol = "[OK]" if ok else "[FAIL]"
    print(f"{symbol} {name:<40} {status}")

print("-" * 70)
print("Summary:")
available = [r for r in results if r[1]]
print(f"  Available: {len(available)}/{len(results)}")
for name, _, count, status in available:
    print(f"    - {name} ({count} records)")
