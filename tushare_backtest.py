#!/usr/bin/env python3
"""
使用Tushare获取历史数据进行回测

需要安装: pip install tushare
需要注册: https://tushare.pro/ 获取token
"""

# 示例代码（需要注册Tushare账号）
"""
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 设置token（需要注册获取）
ts.set_token('your_token_here')
pro = ts.pro_api()

# 获取3月份日线数据
df = pro.daily(trade_date='20250303')
print(f"2025-03-03 数据: {len(df)} 只股票")

# 批量获取数据
trade_dates = ['20250303', '20250304', '20250305', ...]
for date in trade_dates:
    df = pro.daily(trade_date=date)
    df.to_csv(f'data/daily/market_{date}.csv', index=False)
"""

print("Tushare Pro可以获取历史日线数据")
print("注册地址: https://tushare.pro/")
print("免费版有积分限制，需要积累积分才能获取更多数据")
