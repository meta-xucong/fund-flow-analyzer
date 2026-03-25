#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试当前可用数据源的完整性
"""
import os
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1'

import sys
sys.path.insert(0, '.')

import akshare as ak
import requests
import pandas as pd
from datetime import datetime

print("=" * 80)
print("测试当前可用数据源完整性")
print("=" * 80)
print()

results = {}

# 1. 测试股票列表
print("[1] 股票列表...")
try:
    stock_list = ak.stock_info_a_code_name()
    print(f"  [OK] 成功: 获取 {len(stock_list)} 只股票")
    results['stock_list'] = {'status': 'OK', 'count': len(stock_list)}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['stock_list'] = {'status': 'FAIL', 'error': str(e)}

# 2. 测试腾讯实时行情
print("\n[2] 腾讯实时行情...")
try:
    url = "http://qt.gtimg.cn/q=sh600519,sz000858"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    content = resp.text
    if 'v_sh600519' in content and '~' in content:
        parts = content.split('v_sh600519="')[1].split('"')[0].split('~') if 'v_sh600519="' in content else []
        print(f"  [OK] 成功: 获取实时数据")
        print(f"       数据字段数: {len(parts)}")
        if len(parts) > 40:
            print(f"       包含: 名称、价格、涨跌幅、成交量、成交额等")
            # 显示部分字段
            field_names = ['代码', '名称', '最新价', '昨收', '今开', '成交量(手)', '成交额(万)', '涨跌%']
            for i, name in enumerate(field_names[:8]):
                if i+1 < len(parts):
                    print(f"       [{i+1}] {name}: {parts[i+1]}")
        results['tencent_realtime'] = {'status': 'OK', 'fields': len(parts)}
    else:
        print(f"  [WARN] 数据异常")
        results['tencent_realtime'] = {'status': 'WARN'}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['tencent_realtime'] = {'status': 'FAIL', 'error': str(e)}

# 3. 测试腾讯历史数据
print("\n[3] 腾讯历史数据...")
try:
    hist = ak.stock_zh_a_hist_tx(symbol="sh600519")
    if hist is not None and len(hist) > 0:
        print(f"  [OK] 成功: 获取历史数据 {len(hist)} 条")
        print(f"       字段: {list(hist.columns)}")
        print(f"       最新日期: {hist['date'].max()}")
        results['tencent_history'] = {'status': 'OK', 'count': len(hist), 'fields': list(hist.columns)}
    else:
        print(f"  [WARN] 无数据")
        results['tencent_history'] = {'status': 'WARN'}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['tencent_history'] = {'status': 'FAIL', 'error': str(e)}

# 4. 测试板块数据
print("\n[4] 板块数据...")
try:
    sectors = ak.stock_board_industry_name_em()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个板块")
    print(f"       字段: {list(sectors.columns)}")
    results['sectors'] = {'status': 'OK', 'count': len(sectors), 'fields': list(sectors.columns)}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['sectors'] = {'status': 'FAIL', 'error': str(e)}

# 5. 测试板块成分股
print("\n[5] 板块成分股...")
try:
    # 尝试获取某个板块的成分股
    cons = ak.stock_board_industry_cons_em(symbol="光伏设备")
    print(f"  [OK] 成功: 获取板块成分股 {len(cons)} 只")
    print(f"       字段: {list(cons.columns)}")
    results['sector_cons'] = {'status': 'OK', 'count': len(cons), 'fields': list(cons.columns)}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['sector_cons'] = {'status': 'FAIL', 'error': str(e)}

# 6. 测试个股资金流入
print("\n[6] 个股资金流入...")
try:
    fund = ak.stock_individual_fund_flow(stock="600519", market="sh")
    print(f"  [OK] 成功: 获取资金数据 {len(fund)} 条")
    print(f"       字段: {list(fund.columns)}")
    results['fund_flow'] = {'status': 'OK', 'count': len(fund), 'fields': list(fund.columns)}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['fund_flow'] = {'status': 'FAIL', 'error': str(e)}

# 7. 测试市场情绪相关
print("\n[7] 市场涨跌统计...")
try:
    # 用实时行情数据计算市场情绪
    url = "http://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    if 'sh000001' in resp.text:
        print(f"  [OK] 成功: 可以获取指数数据用于情绪分析")
        results['market_index'] = {'status': 'OK'}
    else:
        print(f"  [WARN] 数据异常")
        results['market_index'] = {'status': 'WARN'}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['market_index'] = {'status': 'FAIL', 'error': str(e)}

# 8. 测试量比数据
print("\n[8] 量比数据...")
try:
    # 腾讯API字段50是量比
    url = "http://qt.gtimg.cn/q=sh600519"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    parts = resp.text.split('~')
    if len(parts) > 50:
        volume_ratio = parts[50] if len(parts) > 50 else 'N/A'
        print(f"  [OK] 成功: 腾讯API包含量比数据 (字段[50]: {volume_ratio})")
        results['volume_ratio'] = {'status': 'OK', 'value': volume_ratio}
    else:
        print(f"  [WARN] 字段不足，无法获取量比 (只有{len(parts)}个字段)")
        results['volume_ratio'] = {'status': 'WARN'}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['volume_ratio'] = {'status': 'FAIL', 'error': str(e)}

# 9. 测试大盘数据
print("\n[9] 大盘实时数据...")
try:
    # 尝试获取大盘数据
    url = "http://qt.gtimg.cn/q=sh000001"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    parts = resp.text.split('~')
    if len(parts) > 35:
        # 上证指数数据
        index_name = parts[1] if len(parts) > 1 else 'N/A'
        latest = parts[3] if len(parts) > 3 else 'N/A'
        change_pct = parts[5] if len(parts) > 5 else 'N/A'
        print(f"  [OK] 成功: {index_name} 最新:{latest} 涨跌:{change_pct}%")
        results['market_realtime'] = {'status': 'OK'}
    else:
        print(f"  [WARN] 数据字段不足")
        results['market_realtime'] = {'status': 'WARN'}
except Exception as e:
    print(f"  [FAIL] 失败: {e}")
    results['market_realtime'] = {'status': 'FAIL', 'error': str(e)}

# 汇总
print("\n" + "=" * 80)
print("数据源完整性评估")
print("=" * 80)

ok_count = sum(1 for v in results.values() if v['status'] == 'OK')
fail_count = sum(1 for v in results.values() if v['status'] == 'FAIL')
warn_count = sum(1 for v in results.values() if v['status'] == 'WARN')

print(f"\n测试结果: [OK] {ok_count}项可用 | [WARN] {warn_count}项警告 | [FAIL] {fail_count}项失败")
print()

# 评估是否能生成完整报告
print("[完整报告所需数据评估]")
print()

requirements = {
    '个股实时行情（价格、涨跌幅）': 'tencent_realtime' in results and results['tencent_realtime']['status'] == 'OK',
    '个股量比': 'volume_ratio' in results and results['volume_ratio']['status'] == 'OK',
    '个股成交额': 'tencent_realtime' in results and results['tencent_realtime']['status'] == 'OK',
    '板块数据': 'sectors' in results and results['sectors']['status'] == 'OK',
    '板块成分股': 'sector_cons' in results and results['sector_cons']['status'] == 'OK',
    '资金流入数据': 'fund_flow' in results and results['fund_flow']['status'] == 'OK',
    '市场情绪（指数）': 'market_realtime' in results and results['market_realtime']['status'] == 'OK',
}

missing = []
for item, available in requirements.items():
    status = "[OK]" if available else "[MISSING]"
    print(f"  {status} {item}")
    if not available:
        missing.append(item)

print()
if not missing:
    print("[PASS] 所有必需数据均可获取，可以生成完整报告！")
else:
    print(f"[WARNING] 缺失 {len(missing)} 项数据，完整报告将受限")
    print(f"          缺失: {', '.join(missing)}")

print("=" * 80)
