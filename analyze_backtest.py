#!/usr/bin/env python3
"""Analyze backtest results"""
import json
import pandas as pd
from datetime import datetime

print("=" * 70)
print("3月回测结果分析")
print("=" * 70)

# 今日选股
with open('reports/daily/picks_2026-03-22.json', 'r', encoding='utf-8') as f:
    today = json.load(f)

print("\n[2026-03-22 选股]")
print(f"Momentum: {len(today['momentum'])} stocks")
for s in today['momentum'][:5]:
    print(f"  {s['code']} {s['name']}: {s.get('change_pct', 0):.2f}%")

print(f"\nReversal: {len(today['reversal'])} stocks")
for s in today['reversal'][:5]:
    print(f"  {s['code']} {s['name']}: {s.get('change_pct', 0):.2f}%")

# 3月19日选股
print("\n[2026-03-19 选股 - from report]")
with open('reports/daily/report_2026-03-19.json', 'r', encoding='utf-8') as f:
    mar19 = json.load(f)

print(f"Momentum: {len(mar19['stock_picks']['momentum'])} stocks")
for s in mar19['stock_picks']['momentum'][:5]:
    print(f"  {s['code']} {s['name']}: buy price {s.get('price', 'N/A')}")

print(f"\nReversal: {len(mar19['stock_picks']['reversal'])} stocks")
for s in mar19['stock_picks']['reversal'][:5]:
    print(f"  {s['code']} {s['name']}: buy price {s.get('price', 'N/A')}")

# 3月20日选股
print("\n[2026-03-20 选股 - from report]")
with open('reports/daily/report_2026-03-20.json', 'r', encoding='utf-8') as f:
    mar20 = json.load(f)

print(f"Momentum: {len(mar20['stock_picks']['momentum'])} stocks")
for s in mar20['stock_picks']['momentum'][:5]:
    print(f"  {s['code']} {s['name']}: {s.get('change_pct', 0):.2f}%")

print("\n" + "=" * 70)
