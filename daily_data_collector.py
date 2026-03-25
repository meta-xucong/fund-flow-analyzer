#!/usr/bin/env python3
"""
每日数据收集器

从今天开始，每天收集收盘数据，用于未来回测
"""
import os
import sys
sys.path.insert(0, '.')

os.environ['NO_PROXY'] = 'sina.com.cn,gtimg.cn,localhost,127.0.0.1'

import pandas as pd
from datetime import datetime
from core.sina_fetcher import SinaDataFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_daily_data():
    """收集当日市场数据"""
    fetcher = SinaDataFetcher()
    
    today = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"收集 {today} 的市场数据...")
    
    # 获取500只股票样本
    df = fetcher.fetch_market_spot(500)
    
    if not df.empty:
        # 保存到CSV
        output_dir = 'data/daily'
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/market_{today}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"已保存: {filename} ({len(df)} 只股票)")
        
        # 同时更新数据库
        try:
            from core.storage import DataStorage
            storage = DataStorage()
            storage.save_market_data(df, today)
            logger.info(f"已更新数据库")
        except Exception as e:
            logger.warning(f"数据库更新失败: {e}")
        
        return True
    else:
        logger.error("数据获取失败")
        return False

if __name__ == "__main__":
    collect_daily_data()
