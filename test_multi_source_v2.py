#!/usr/bin/env python3
"""
测试多源获取器V2 - 验证轮询和故障转移
"""
import sys
sys.path.insert(0, '.')

from core.multi_source_fetcher import get_multi_source_fetcher
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=" * 60)
print("多源获取器V2测试")
print("=" * 60)

fetcher = get_multi_source_fetcher()

# 查看数据源状态
print("\n【数据源状态】")
stats = fetcher.get_source_stats()
print(stats.to_string(index=False))

# 测试获取数据
print("\n【测试数据获取】")
df = fetcher.fetch_market_spot(max_retries=2, retry_delay=1.0)

if df is not None and len(df) > 0:
    print(f"\n✓ 成功获取 {len(df)} 条数据")
    print(f"  数据源: {df.get('data_source', ['unknown']).iloc[0]}")
    print(f"  列数: {len(df.columns)}")
else:
    print("\n✗ 获取失败")

print("\n" + "=" * 60)
