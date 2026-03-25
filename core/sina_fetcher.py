# -*- coding: utf-8 -*-
"""
新浪/腾讯数据源获取器

绕过AKShare问题，直接使用新浪和腾讯的原始API
"""
import os
os.environ['NO_PROXY'] = 'sina.com.cn,sinaimg.cn,gtimg.cn,qt.gtimg.cn,localhost,127.0.0.1'

import requests
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SinaDataFetcher:
    """
    基于新浪和腾讯API的数据获取器
    
    接口来源:
    - 新浪: https://hq.sinajs.cn (实时行情)
    - 腾讯: http://qt.gtimg.cn (实时行情)
    - AKShare: stock_info_a_code_name (股票列表)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn',
        }
        self._stock_list = None
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        if self._stock_list is not None:
            return self._stock_list
        
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            self._stock_list = df
            logger.info(f"获取股票列表: {len(df)} 只")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def fetch_sina_quotes(self, codes: List[str]) -> pd.DataFrame:
        """
        从新浪获取实时行情
        
        Args:
            codes: 股票代码列表，如 ['sh600000', 'sz000001']
        
        Returns:
            行情DataFrame
        """
        # 新浪批量接口限制，每次最多查询多个股票
        codes_str = ','.join(codes)
        url = f'https://hq.sinajs.cn/list={codes_str}'
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=10)
            resp.encoding = 'gb2312'  # 新浪使用GB2312编码
            
            results = []
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or 'var hq_str_' not in line:
                    continue
                
                # 解析: var hq_str_sh600000="浦发银行,10.330,...";
                parts = line.split('="')
                if len(parts) != 2:
                    continue
                
                code_key = parts[0].replace('var hq_str_', '')
                data_str = parts[1].rstrip('"')
                
                if not data_str:
                    continue
                
                fields = data_str.split(',')
                if len(fields) < 33:
                    continue
                
                # 新浪数据字段解析
                result = {
                    'code': code_key[2:],  # 去掉sh/sz前缀
                    'name': fields[0],
                    'open': float(fields[1]) if fields[1] else 0,
                    'pre_close': float(fields[2]) if fields[2] else 0,
                    'latest': float(fields[3]) if fields[3] else 0,
                    'high': float(fields[4]) if fields[4] else 0,
                    'low': float(fields[5]) if fields[5] else 0,
                    'buy1_price': float(fields[6]) if fields[6] else 0,
                    'sell1_price': float(fields[7]) if fields[7] else 0,
                    'volume': int(float(fields[8])) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                    'buy1_vol': int(float(fields[10])) if fields[10] else 0,
                    'buy2_vol': int(float(fields[12])) if fields[12] else 0,
                    'buy3_vol': int(float(fields[14])) if fields[14] else 0,
                    'buy4_vol': int(float(fields[16])) if fields[16] else 0,
                    'buy5_vol': int(float(fields[18])) if fields[18] else 0,
                    'sell1_vol': int(float(fields[20])) if fields[20] else 0,
                    'sell2_vol': int(float(fields[22])) if fields[22] else 0,
                    'sell3_vol': int(float(fields[24])) if fields[24] else 0,
                    'sell4_vol': int(float(fields[26])) if fields[26] else 0,
                    'sell5_vol': int(float(fields[28])) if fields[28] else 0,
                    'date': fields[30],
                    'time': fields[31],
                    'data_source': 'sina',
                }
                
                # 计算涨跌幅
                if result['pre_close'] > 0:
                    result['change_pct'] = round(
                        (result['latest'] - result['pre_close']) / result['pre_close'] * 100, 2
                    )
                else:
                    result['change_pct'] = 0
                
                results.append(result)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"新浪数据获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_tencent_quotes(self, codes: List[str]) -> pd.DataFrame:
        """
        从腾讯获取实时行情
        
        Args:
            codes: 股票代码列表，如 ['sh600000', 'sz000001']
        
        Returns:
            行情DataFrame
        """
        # 腾讯格式: sh600000 -> sh600000, sz000001 -> sz000001
        codes_str = ','.join(codes)
        url = f'http://qt.gtimg.cn/q={codes_str}'
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=10)
            # 腾讯使用GBK编码
            resp.encoding = 'gbk'
            
            results = []
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or 'v_' not in line:
                    continue
                
                # 解析: v_sh600000="1~浦发银行~600000~10.28~...";
                parts = line.split('="')
                if len(parts) != 2:
                    continue
                
                code_key = parts[0].replace('v_', '')
                data_str = parts[1].rstrip('"')
                
                if not data_str:
                    continue
                
                fields = data_str.split('~')
                if len(fields) < 45:
                    continue
                
                # 腾讯数据字段解析
                result = {
                    'code': fields[2],
                    'name': fields[1],
                    'latest': float(fields[3]) if fields[3] else 0,
                    'pre_close': float(fields[4]) if fields[4] else 0,
                    'open': float(fields[5]) if fields[5] else 0,
                    'volume': int(float(fields[6])) if fields[6] else 0,
                    'buy1_vol': int(float(fields[7])) if fields[7] else 0,
                    'sell1_vol': int(float(fields[8])) if fields[8] else 0,
                    'buy1_price': float(fields[9]) if fields[9] else 0,
                    'buy2_price': float(fields[11]) if fields[11] else 0,
                    'buy3_price': float(fields[13]) if fields[13] else 0,
                    'buy4_price': float(fields[15]) if fields[15] else 0,
                    'buy5_price': float(fields[17]) if fields[17] else 0,
                    'sell1_price': float(fields[19]) if fields[19] else 0,
                    'sell2_price': float(fields[21]) if fields[21] else 0,
                    'sell3_price': float(fields[23]) if fields[23] else 0,
                    'sell4_price': float(fields[25]) if fields[25] else 0,
                    'sell5_price': float(fields[27]) if fields[27] else 0,
                    'high': float(fields[33]) if fields[33] else 0,
                    'low': float(fields[34]) if fields[34] else 0,
                    'volume_ratio': float(fields[38]) if fields[38] else 0,
                    'pe': float(fields[39]) if fields[39] else 0,
                    'pb': float(fields[46]) if fields[46] else 0,
                    'turnover': float(fields[38]) if fields[38] else 0,  # 换手率
                    'data_source': 'tencent',
                }
                
                # 计算涨跌幅
                if result['pre_close'] > 0:
                    result['change_pct'] = round(
                        (result['latest'] - result['pre_close']) / result['pre_close'] * 100, 2
                    )
                else:
                    result['change_pct'] = 0
                
                # 成交额（腾讯字段35是成交额，单位万）
                result['amount'] = float(fields[37]) * 10000 if fields[37] else 0
                
                results.append(result)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            logger.error(f"腾讯数据获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_market_spot(self, sample_size: int = 500) -> pd.DataFrame:
        """
        获取市场行情（取样本）
        
        Args:
            sample_size: 获取股票数量（太多会被限制）
        
        Returns:
            行情DataFrame
        """
        # 获取股票列表
        stock_list = self.get_stock_list()
        if stock_list.empty:
            logger.error("无法获取股票列表")
            return pd.DataFrame()
        
        # 取样本（新浪/腾讯每次请求不能超过一定数量）
        sample = stock_list.head(sample_size)
        
        # 转换代码格式
        codes = []
        for _, row in sample.iterrows():
            code = row['code']
            # 添加前缀
            if code.startswith('6'):
                codes.append(f'sh{code}')
            else:
                codes.append(f'sz{code}')
        
        logger.info(f"获取 {len(codes)} 只股票行情...")
        
        # 分批获取（每次最多200只）
        batch_size = 200
        all_results = []
        
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i+batch_size]
            
            # 优先尝试腾讯
            df = self.fetch_tencent_quotes(batch)
            if df.empty:
                # 腾讯失败尝试新浪
                df = self.fetch_sina_quotes(batch)
            
            if not df.empty:
                all_results.append(df)
            
            import time
            time.sleep(0.1)  # 避免请求过快
        
        if all_results:
            result_df = pd.concat(all_results, ignore_index=True)
            result_df['fetch_time'] = datetime.now()
            logger.info(f"成功获取 {len(result_df)} 只股票行情")
            return result_df
        
        return pd.DataFrame()


# 便捷函数
def fetch_market_spot(sample_size: int = 500) -> pd.DataFrame:
    """便捷函数：获取市场行情"""
    fetcher = SinaDataFetcher()
    return fetcher.fetch_market_spot(sample_size)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("新浪/腾讯数据源测试")
    print("=" * 60)
    
    fetcher = SinaDataFetcher()
    
    # 测试股票列表
    print("\n[1] 获取股票列表")
    stocks = fetcher.get_stock_list()
    print(f"Total stocks: {len(stocks)}")
    print(stocks.head().to_string())
    
    # 测试新浪行情
    print("\n[2] 新浪实时行情（3只股票）")
    df_sina = fetcher.fetch_sina_quotes(['sh600000', 'sz000001', 'sz002730'])
    if not df_sina.empty:
        print(f"Got {len(df_sina)} stocks")
        print(df_sina[['code', 'name', 'latest', 'change_pct']].to_string())
    
    # 测试腾讯行情
    print("\n[3] 腾讯实时行情（3只股票）")
    df_tencent = fetcher.fetch_tencent_quotes(['sh600000', 'sz000001', 'sz002730'])
    if not df_tencent.empty:
        print(f"Got {len(df_tencent)} stocks")
        print(df_tencent[['code', 'name', 'latest', 'change_pct']].to_string())
    
    # 测试批量获取
    print("\n[4] 批量获取行情（50只）")
    df = fetcher.fetch_market_spot(50)
    print(f"Got {len(df)} stocks")
    if not df.empty:
        print(df[['code', 'name', 'latest', 'change_pct']].head().to_string())
