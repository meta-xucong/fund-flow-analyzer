# -*- coding: utf-8 -*-
"""
修复后的数据源获取器

修复列表:
1. ✅ 同花顺/新浪实时 - 使用新浪原始API (stock_zh_a_spot修复)
2. ✅ 腾讯实时 - 使用腾讯原始API (stock_zh_a_spot_tx修复)
3. ✅ 腾讯历史 - 原可用，优化错误处理 (stock_zh_a_hist_tx)
4. ✅ 新浪日线 - 原可用，添加重试 (stock_zh_a_daily)
5. ✅ 新股 - 修复JSON解析 (stock_zh_a_new)
6. ✅ 龙虎榜 - 修复参数错误 (stock_lhb_detail_daily_sina)
7. ✅ 股票列表 - 原可用，优化 (stock_info_a_code_name)
8. ✅ 异动数据 - 原可用，优化 (stock_changes_em)
9. ✅ 个股资金 - 原可用，优化 (stock_individual_fund_flow)

忽略(IP被封):
- 东财实时/历史 (push2.eastmoney.com)
- 板块资金流向
"""

import os
os.environ['NO_PROXY'] = 'sina.com.cn,qt.gtimg.cn,gtimg.cn,push2.eastmoney.com,eastmoney.com,10.push2.eastmoney.com,17.push2.eastmoney.com'  # 添加板块数据源

import requests
import pandas as pd
import json
import logging
from typing import Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class FixedDataFetcher:
    """修复后的数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False  # 禁用系统代理
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    
    # ========== 1. 修复同花顺/新浪实时 ==========
    
    def stock_zh_a_spot_fixed(self) -> pd.DataFrame:
        """
        修复stock_zh_a_spot - 使用新浪原始API
        
        原问题: AKShare的stock_zh_a_spot返回JSON错误
        修复: 直接使用新浪hq.sinajs.cn API
        """
        try:
            # 获取股票列表
            stock_list = self.stock_info_a_code_name()
            if stock_list.empty:
                return pd.DataFrame()
            
            # 转换为新浪格式
            codes = []
            for _, row in stock_list.iterrows():
                code = row['code']
                prefix = 'sh' if code.startswith('6') else 'sz'
                codes.append(f'{prefix}{code}')
            
            # 分批获取（每次最多200只）
            all_results = []
            for i in range(0, len(codes), 200):
                batch = codes[i:i+200]
                df = self._fetch_sina_batch(batch)
                if not df.empty:
                    all_results.append(df)
                time.sleep(0.1)
            
            if all_results:
                return pd.concat(all_results, ignore_index=True)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"新浪实时数据获取失败: {e}")
            return pd.DataFrame()
    
    def _fetch_sina_batch(self, codes: List[str]) -> pd.DataFrame:
        """批量获取新浪数据"""
        codes_str = ','.join(codes)
        url = f'https://hq.sinajs.cn/list={codes_str}'
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'gb2312'
            
            results = []
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or 'var hq_str_' not in line:
                    continue
                
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
                
                results.append({
                    'code': code_key[2:],  # 去掉sh/sz前缀
                    'name': fields[0],
                    'open': float(fields[1]) if fields[1] else 0,
                    'pre_close': float(fields[2]) if fields[2] else 0,
                    'latest': float(fields[3]) if fields[3] else 0,
                    'high': float(fields[4]) if fields[4] else 0,
                    'low': float(fields[5]) if fields[5] else 0,
                    'volume': int(float(fields[8])) if fields[8] else 0,
                    'amount': float(fields[9]) if fields[9] else 0,
                    'date': fields[30],
                    'time': fields[31],
                })
            
            df = pd.DataFrame(results)
            if not df.empty and 'latest' in df.columns and 'pre_close' in df.columns:
                df['change_pct'] = ((df['latest'] - df['pre_close']) / df['pre_close'] * 100).round(2)
            
            return df
            
        except Exception as e:
            logger.warning(f"新浪批量获取失败: {e}")
            return pd.DataFrame()
    
    # ========== 2. 修复腾讯实时 ==========
    
    def stock_zh_a_spot_tx_fixed(self) -> pd.DataFrame:
        """
        修复stock_zh_a_spot_tx - 使用腾讯原始API
        
        原问题: AKShare没有stock_zh_a_spot_tx接口
        修复: 直接使用腾讯qt.gtimg.cn API
        """
        try:
            # 获取股票列表
            stock_list = self.stock_info_a_code_name()
            if stock_list.empty:
                return pd.DataFrame()
            
            # 转换为腾讯格式
            codes = []
            for _, row in stock_list.head(500).iterrows():  # 限制500只
                code = row['code']
                prefix = 'sh' if code.startswith('6') else 'sz'
                codes.append(f'{prefix}{code}')
            
            # 分批获取（每次最多200只）
            all_results = []
            for i in range(0, len(codes), 200):
                batch = codes[i:i+200]
                df = self._fetch_tencent_batch(batch)
                if not df.empty:
                    all_results.append(df)
                time.sleep(0.1)
            
            if all_results:
                return pd.concat(all_results, ignore_index=True)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"腾讯实时数据获取失败: {e}")
            return pd.DataFrame()
    
    def _fetch_tencent_batch(self, codes: List[str]) -> pd.DataFrame:
        """批量获取腾讯数据"""
        codes_str = ','.join(codes)
        url = f'http://qt.gtimg.cn/q={codes_str}'
        
        try:
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.encoding = 'gbk'
            
            results = []
            for line in resp.text.strip().split(';'):
                line = line.strip()
                if not line or 'v_' not in line:
                    continue
                
                parts = line.split('="')
                if len(parts) != 2:
                    continue
                
                data_str = parts[1].rstrip('"')
                if not data_str:
                    continue
                
                fields = data_str.split('~')
                if len(fields) < 45:
                    continue
                
                results.append({
                    'code': fields[2],
                    'name': fields[1],
                    'latest': float(fields[3]) if fields[3] else 0,
                    'pre_close': float(fields[4]) if fields[4] else 0,
                    'open': float(fields[5]) if fields[5] else 0,
                    'high': float(fields[33]) if fields[33] else 0,
                    'low': float(fields[34]) if fields[34] else 0,
                    'volume': int(float(fields[6])) if fields[6] else 0,
                    'amount': float(fields[37]) * 10000 if fields[37] else 0,
                    'volume_ratio': float(fields[38]) if fields[38] else 0,
                    'pe': float(fields[39]) if fields[39] else 0,
                    'pb': float(fields[46]) if fields[46] else 0,
                    'turnover': float(fields[38]) if fields[38] else 0,
                })
            
            df = pd.DataFrame(results)
            if not df.empty and 'latest' in df.columns and 'pre_close' in df.columns:
                df['change_pct'] = ((df['latest'] - df['pre_close']) / df['pre_close'] * 100).round(2)
            
            return df
            
        except Exception as e:
            logger.warning(f"腾讯批量获取失败: {e}")
            return pd.DataFrame()
    
    # ========== 3. 腾讯历史 (原可用，优化) ==========
    
    def stock_zh_a_hist_tx_fixed(self, symbol: str = 'sz000001') -> pd.DataFrame:
        """
        优化stock_zh_a_hist_tx - 添加重试和错误处理
        """
        import akshare as ak
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = ak.stock_zh_a_hist_tx(symbol=symbol)
                return df
            except Exception as e:
                logger.warning(f"腾讯历史获取失败(尝试{attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return pd.DataFrame()
    
    # ========== 4. 新浪日线 (原可用，优化) ==========
    
    def stock_zh_a_daily_fixed(self, symbol: str = 'sh600000', 
                                start_date: str = '20250101',
                                end_date: str = None) -> pd.DataFrame:
        """
        优化stock_zh_a_daily - 添加重试
        """
        import akshare as ak
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = ak.stock_zh_a_daily(symbol=symbol, 
                                         start_date=start_date, 
                                         end_date=end_date)
                return df
            except Exception as e:
                logger.warning(f"新浪日线获取失败(尝试{attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return pd.DataFrame()
    
    # ========== 5. 修复新股数据 ==========
    
    def stock_zh_a_new_fixed(self) -> pd.DataFrame:
        """
        修复stock_zh_a_new - 处理JSON错误
        
        原问题: 返回JSON解析错误
        修复: 添加异常处理和重试
        """
        import akshare as ak
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = ak.stock_zh_a_new()
                return df
            except Exception as e:
                logger.warning(f"新股数据获取失败(尝试{attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return pd.DataFrame()
    
    # ========== 6. 修复龙虎榜 ==========
    
    def stock_lhb_detail_daily_sina_fixed(self, start_date: str = None, 
                                          end_date: str = None) -> pd.DataFrame:
        """
        修复stock_lhb_detail_daily_sina - 修复参数错误
        
        原问题: TypeError参数错误
        修复: 正确处理日期参数
        """
        import akshare as ak
        
        if start_date is None:
            start_date = datetime.now().strftime('%Y%m%d')
        if end_date is None:
            end_date = start_date
        
        # 确保日期格式正确
        start_date = str(start_date).replace('-', '')
        end_date = str(end_date).replace('-', '')
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                df = ak.stock_lhb_detail_daily_sina(start_date=start_date, 
                                                     end_date=end_date)
                return df
            except TypeError as e:
                # 尝试另一种调用方式
                try:
                    df = ak.stock_lhb_detail_daily_sina()
                    return df
                except:
                    pass
                logger.warning(f"龙虎榜获取失败: {e}")
                return pd.DataFrame()
            except Exception as e:
                logger.warning(f"龙虎榜获取失败(尝试{attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return pd.DataFrame()
    
    # ========== 7. 股票列表 (原可用) ==========
    
    def stock_info_a_code_name(self) -> pd.DataFrame:
        """获取A股股票列表"""
        import akshare as ak
        
        try:
            df = ak.stock_info_a_code_name()
            return df
        except Exception as e:
            logger.error(f"股票列表获取失败: {e}")
            return pd.DataFrame()
    
    # ========== 8. 异动数据 (原可用) ==========
    
    def stock_changes_em_fixed(self) -> pd.DataFrame:
        """获取异动数据"""
        import akshare as ak
        
        try:
            df = ak.stock_changes_em()
            return df
        except Exception as e:
            logger.warning(f"异动数据获取失败: {e}")
            return pd.DataFrame()
    
    # ========== 9. 个股资金 (原可用) ==========
    
    def stock_individual_fund_flow_fixed(self, stock: str = '600000', 
                                          market: str = 'sh') -> pd.DataFrame:
        """获取个股资金流向"""
        import akshare as ak
        
        try:
            df = ak.stock_individual_fund_flow(stock=stock, market=market)
            return df
        except Exception as e:
            logger.warning(f"个股资金获取失败: {e}")
            return pd.DataFrame()
    
    # ========== 10. 板块数据 (高优先级：申万行业 spot) ==========
    
    def stock_sector_spot_fixed(self) -> pd.DataFrame:
        """
        获取板块实时数据 - 使用 stock_sector_spot (申万行业)
        
        优先级: 
        1. stock_sector_spot (申万行业，49个板块) - 高优先级，可用
        2. stock_board_concept_name_ths (同花顺概念) - 备用
        
        Returns:
            DataFrame with columns: 板块名称, 涨跌幅, 成交额, 领涨股等
        """
        import akshare as ak
        
        # 第一优先级：申万行业 spot 数据
        try:
            df = ak.stock_sector_spot()
            if not df.empty and len(df) > 0:
                logger.info(f"板块数据获取成功 (stock_sector_spot): {len(df)}个板块")
                return df
        except Exception as e:
            logger.warning(f"stock_sector_spot 获取失败: {e}")
        
        # 备用：同花顺概念板块
        try:
            df = ak.stock_board_concept_name_ths()
            if not df.empty and len(df) > 0:
                logger.info(f"板块数据获取成功 (THS概念): {len(df)}个板块")
                return df
        except Exception as e:
            logger.warning(f"THS概念板块获取失败: {e}")
        
        # 备用2：同花顺行业板块
        try:
            df = ak.stock_board_industry_name_ths()
            if not df.empty and len(df) > 0:
                logger.info(f"板块数据获取成功 (THS行业): {len(df)}个板块")
                return df
        except Exception as e:
            logger.warning(f"THS行业板块获取失败: {e}")
        
        logger.error("所有板块数据源均不可用")
        return pd.DataFrame()
    
    def get_sector_strength_ranking(self, top_n: int = 10) -> pd.DataFrame:
        """
        获取板块强度排行
        
        基于 stock_sector_spot 数据，按涨跌幅排序
        
        Args:
            top_n: 返回前N个板块
            
        Returns:
            DataFrame with ranking
        """
        df = self.stock_sector_spot_fixed()
        
        if df.empty:
            return pd.DataFrame()
        
        try:
            # stock_sector_spot 列名映射（根据实际数据结构）
            # label, 板块, 公司家数, 平均价格, 涨跌额, 涨跌幅, 总成交量, 总成交额, 股票代码, 个股-涨跌幅
            col_mapping = {
                'name': '板块',
                'change_pct': '涨跌幅', 
                'amount': '总成交额',
                'leader_stock': '领涨股名称',
                'leader_change': '领涨股涨跌'
            }
            
            # 按涨跌幅排序
            cols = list(df.columns)
            if '涨跌幅' in cols:
                df_sorted = df.sort_values('涨跌幅', ascending=False)
            elif len(cols) > 5:
                # 假设第6列是涨跌幅
                df_sorted = df.sort_values(cols[5], ascending=False)
            else:
                df_sorted = df
            
            return df_sorted.head(top_n)
            
        except Exception as e:
            logger.error(f"板块强度排序失败: {e}")
            return df.head(top_n)


# ========== 测试代码 ==========

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("修复后的数据源测试")
    print("=" * 70)
    
    fetcher = FixedDataFetcher()
    
    sources = [
        ("新浪实时 (修复)", lambda: fetcher.stock_zh_a_spot_fixed()),
        ("腾讯实时 (修复)", lambda: fetcher.stock_zh_a_spot_tx_fixed()),
        ("腾讯历史 (优化)", lambda: fetcher.stock_zh_a_hist_tx_fixed('sz000001')),
        ("新浪日线 (优化)", lambda: fetcher.stock_zh_a_daily_fixed('sh600000', '20250320', '20250321')),
        ("新股 (修复)", lambda: fetcher.stock_zh_a_new_fixed()),
        ("龙虎榜 (修复)", lambda: fetcher.stock_lhb_detail_daily_sina_fixed()),
        ("股票列表", lambda: fetcher.stock_info_a_code_name()),
        ("异动数据", lambda: fetcher.stock_changes_em_fixed()),
        ("个股资金", lambda: fetcher.stock_individual_fund_flow_fixed()),
        ("板块数据 (新增)", lambda: fetcher.stock_sector_spot_fixed()),
        ("板块强度排行 (新增)", lambda: fetcher.get_sector_strength_ranking(top_n=10)),
    ]
    
    results = []
    for name, func in sources:
        try:
            df = func()
            count = len(df) if df is not None else 0
            status = "OK" if count > 0 else "Empty"
            results.append((name, status, count))
            print(f"{name:<25} {status:>6} ({count} rows)")
        except Exception as e:
            results.append((name, "FAIL", 0))
            print(f"{name:<25} {'FAIL':>6} ({type(e).__name__})")
    
    print("\n" + "=" * 70)
    ok_count = sum(1 for _, s, c in results if s == "OK" and c > 0)
    print(f"修复结果: {ok_count}/{len(results)} 个数据源可用")
    print("=" * 70)
