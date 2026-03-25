#!/usr/bin/env python3
"""
带代理例外启动脚本
自动设置NO_PROXY环境变量后运行数据获取
"""

import os
import sys

# 设置代理例外
os.environ['NO_PROXY'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'
os.environ['no_proxy'] = 'eastmoney.com,push2.eastmoney.com,push2his.eastmoney.com,10jqka.com.cn,localhost,127.0.0.1'

# 添加到系统路径
sys.path.insert(0, '.')

print("=" * 60)
print("盘前资金流向分析系统 - 代理绕过模式")
print("=" * 60)
print("已设置NO_PROXY例外:")
print("  - *.eastmoney.com")
print("  - *.10jqka.com.cn")
print("  - localhost, 127.0.0.1")
print("=" * 60)

# 测试数据获取
from core.fetcher import DataFetcher

fetcher = DataFetcher()
print("\n测试数据获取...")
df = fetcher.fetch_market_spot()

if df is not None and len(df) > 0:
    print(f"✓ 成功获取 {len(df)} 条数据")
    print(f"  数据源: {df.get('data_source', ['unknown'])[0] if 'data_source' in df.columns else 'unknown'}")
else:
    print("✗ 获取失败")
