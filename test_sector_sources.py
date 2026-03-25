#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试各种板块数据源
"""
import os
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1,10.push2.eastmoney.com,push2.eastmoney.com'

import sys
sys.path.insert(0, '.')

import akshare as ak
import requests
import pandas as pd
from datetime import datetime

print("=" * 80)
print("测试各种板块数据源")
print("=" * 80)
print()

# 1. 测试同花顺板块
print("[1] 同花顺板块数据...")
try:
    sectors = ak.stock_board_concept_name_ths()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个概念板块")
    print(f"       字段: {list(sectors.columns)}")
    print(f"       示例: {sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 2. 测试新浪板块
print("\n[2] 新浪板块数据...")
try:
    url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  [OK] 成功: 新浪API可用")
    print(f"       返回: {resp.text[:100]}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 3. 测试腾讯板块
print("\n[3] 腾讯板块数据...")
try:
    # 腾讯行业板块
    url = "http://qt.gtimg.cn/q=hy33,hy34,hy35"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"  [OK] 成功: 腾讯板块API可用")
    print(f"       返回: {resp.text[:200]}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 4. 测试AKShare其他板块接口
print("\n[4] AKShare板块行业数据 (stock_sector_spot)...")
try:
    sectors = ak.stock_sector_spot()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个板块")
    print(f"       字段: {list(sectors.columns)}")
    print(f"       示例:\n{sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 5. 测试AKShare行业板块
print("\n[5] AKShare行业板块 (stock_board_industry_name_ths)...")
try:
    sectors = ak.stock_board_industry_name_ths()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个行业板块")
    print(f"       字段: {list(sectors.columns)}")
    print(f"       示例:\n{sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 6. 测试概念板块
print("\n[6] AKShare概念板块 (stock_board_concept_name_ths)...")
try:
    sectors = ak.stock_board_concept_name_ths()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个概念板块")
    print(f"       字段: {list(sectors.columns)}")
    if len(sectors) > 0:
        print(f"       前3个板块:\n{sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 7. 测试板块资金流向（东方财富 - 另一个接口）
print("\n[7] 板块资金流向 (stock_sector_fund_flow_rank)...")
try:
    # 使用rank接口
    flow = ak.stock_sector_fund_flow_rank(indicator="5日排行")
    print(f"  [OK] 成功: 获取板块资金流向")
    print(f"       字段: {list(flow.columns)}")
    print(f"       示例:\n{flow.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 8. 测试板块成分股（同花顺）
print("\n[8] 板块成分股 - 同花顺 (stock_board_concept_cons_ths)...")
try:
    # 先获取板块列表
    sectors = ak.stock_board_concept_name_ths()
    if len(sectors) > 0:
        first_sector = sectors.iloc[0]['概念名称']
        print(f"       尝试获取板块 [{first_sector}] 的成分股...")
        cons = ak.stock_board_concept_cons_ths(symbol=first_sector)
        print(f"  [OK] 成功: 获取板块成分股 {len(cons)} 只")
        print(f"       字段: {list(cons.columns)}")
        print(f"       示例:\n{cons.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 9. 测试申万行业板块
print("\n[9] 申万行业板块 (stock_sector_spot)...")
try:
    sectors = ak.stock_sector_spot()
    if sectors is not None and len(sectors) > 0:
        print(f"  [OK] 成功: 获取 {len(sectors)} 个板块")
        print(f"       板块示例: {sectors.iloc[0].to_dict()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 10. 尝试直接获取板块实时行情
print("\n[10] 板块实时行情 (腾讯API)...")
try:
    # 尝试获取板块指数
    url = "http://qt.gtimg.cn/q=sz399006,sz399001,sh000001"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    if resp.status_code == 200:
        print(f"  [OK] 成功: 指数数据可用")
        # 解析看看
        lines = resp.text.split(';')
        for line in lines[:3]:
            if '~' in line:
                parts = line.split('~')
                if len(parts) > 2:
                    print(f"       {parts[1]}: {parts[3]}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 11. 测试Sina板块行情
print("\n[11] Sina板块行情...")
try:
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodes"
    resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
    if resp.status_code == 200:
        print(f"  [OK] 成功: Sina板块节点可用")
        print(f"       返回长度: {len(resp.text)}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 12. 测试AKShare行业资金流向
print("\n[12] 行业资金流向 (stock_industry_fund)...")
try:
    fund = ak.stock_industry_fund()
    print(f"  [OK] 成功: 获取行业资金流向")
    print(f"       字段: {list(fund.columns)}")
    print(f"       示例:\n{fund.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 13. 测试板块涨跌排行
print("\n[13] 板块涨跌排行 (stock_board_industry_spot_em)...")
try:
    sectors = ak.stock_board_industry_spot_em()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个行业板块")
    print(f"       字段: {list(sectors.columns)}")
    print(f"       示例:\n{sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

# 14. 测试概念板块涨跌排行
print("\n[14] 概念板块涨跌排行 (stock_board_concept_spot_em)...")
try:
    sectors = ak.stock_board_concept_spot_em()
    print(f"  [OK] 成功: 获取 {len(sectors)} 个概念板块")
    print(f"       字段: {list(sectors.columns)}")
    print(f"       示例:\n{sectors.head(3).to_string()}")
except Exception as e:
    print(f"  [FAIL] 失败: {e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
