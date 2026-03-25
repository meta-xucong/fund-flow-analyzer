#!/usr/bin/env python3
"""
最终测试 - 带代理绕过
"""
import os
os.environ['NO_PROXY'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'
os.environ['no_proxy'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("数据源可用性测试 - 带代理绕过")
print("=" * 60)

import akshare as ak
import warnings
warnings.filterwarnings('ignore')

tests = [
    ("stock_zh_a_spot (同花顺/新浪)", lambda: ak.stock_zh_a_spot()),
    ("stock_zh_a_spot_em (东财)", lambda: ak.stock_zh_a_spot_em()),
    ("stock_zh_a_hist_tx (腾讯历史)", lambda: ak.stock_zh_a_hist_tx(symbol='sz002730')),
]

results = []
for name, func in tests:
    try:
        result = func()
        count = len(result) if result is not None else 0
        status = "OK" if count > 0 else "Empty"
        results.append((name, status, count))
    except Exception as e:
        err = type(e).__name__
        results.append((name, err, 0))

print("\n测试结果:")
print("-" * 60)
for name, status, count in results:
    symbol = "[OK]" if status == "OK" else "[FAIL]"
    print(f"{symbol} {name:<35} {status:>15} ({count})")

print("\n" + "=" * 60)
print("总结:")
ok_count = sum(1 for _, s, _ in results if s == "OK")
print(f"  可用: {ok_count}/{len(results)}")
print("=" * 60)
