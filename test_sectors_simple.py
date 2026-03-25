#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn'

import akshare as ak
import pandas as pd

print("=" * 80)
print("Testing Available Sector Data Sources")
print("=" * 80)
print()

# 1. Test stock_sector_spot
print("[1] Testing stock_sector_spot (SWS Industry)...")
try:
    df = ak.stock_sector_spot()
    print(f"    SUCCESS: Got {len(df)} sectors")
    cols = list(df.columns)
    print(f"    Columns: {cols}")
    print()
    print("    First sector data:")
    first = df.iloc[0]
    for col in cols[:8]:
        print(f"      {col}: {first[col]}")
    print()
    
    # Check if we have change data
    if len(cols) > 4:
        print(f"    Change column ({cols[4]}) sample values:")
        print(f"      {df[cols[4]].head(5).tolist()}")
    
    result1 = "OK"
except Exception as e:
    print(f"    FAIL: {e}")
    result1 = "FAIL"

print()

# 2. Test THS concept sectors
print("[2] Testing THS Concept Sectors...")
try:
    df = ak.stock_board_concept_name_ths()
    print(f"    SUCCESS: Got {len(df)} concept sectors")
    print(f"    Columns: {list(df.columns)}")
    print(f"    First 10 sectors: {df['name'].head(10).tolist()}")
    result2 = "OK"
except Exception as e:
    print(f"    FAIL: {e}")
    result2 = "FAIL"

print()

# 3. Test THS industry sectors  
print("[3] Testing THS Industry Sectors...")
try:
    df = ak.stock_board_industry_name_ths()
    print(f"    SUCCESS: Got {len(df)} industry sectors")
    print(f"    First 10 sectors: {df['name'].head(10).tolist()}")
    result3 = "OK"
except Exception as e:
    print(f"    FAIL: {e}")
    result3 = "FAIL"

print()

# 4. Test sector constituents
print("[4] Testing THS Sector Constituents...")
try:
    # Get concept list first
    concepts = ak.stock_board_concept_name_ths()
    if len(concepts) > 0:
        test_sector = concepts.iloc[0]['name']
        print(f"    Testing with sector: {test_sector}")
        cons = ak.stock_board_concept_cons_ths(symbol=test_sector)
        print(f"    SUCCESS: Got {len(cons)} stocks")
        print(f"    Columns: {list(cons.columns)}")
        print(f"    First 3 stocks: {cons.head(3).to_dict('records')}")
        result4 = "OK"
    else:
        print("    No concepts found")
        result4 = "FAIL"
except Exception as e:
    print(f"    FAIL: {e}")
    result4 = "FAIL"

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  stock_sector_spot:        {result1}")
print(f"  THS Concept Sectors:      {result2}")
print(f"  THS Industry Sectors:     {result3}")
print(f"  THS Sector Constituents:  {result4}")
print()

if result1 == "OK" or result2 == "OK":
    print("  [PASS] At least one sector data source is available!")
    print("         Can generate reports with sector analysis.")
else:
    print("  [WARNING] No sector data source available.")
