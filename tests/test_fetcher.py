# -*- coding: utf-8 -*-
"""
数据采集模块测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.fetcher import DataFetcher, retry_on_failure, DataFetchError


class TestRetryOnFailure(unittest.TestCase):
    """测试重试装饰器"""
    
    def test_success_on_first_attempt(self):
        """第一次尝试成功"""
        @retry_on_failure(max_retries=3, delay=0)
        def success_func():
            return "success"
        
        result = success_func()
        self.assertEqual(result, "success")
    
    def test_retry_on_failure(self):
        """失败后重试"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("暂时失败")
            return "success"
        
        result = fail_then_succeed()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)
    
    def test_retry_exhausted(self):
        """重试次数耗尽"""
        @retry_on_failure(max_retries=2, delay=0)
        def always_fail():
            raise Exception("总是失败")
        
        with self.assertRaises(Exception):
            always_fail()


class TestDataFetcher(unittest.TestCase):
    """测试数据采集器"""
    
    def setUp(self):
        """测试前置"""
        self.fetcher = DataFetcher()
    
    @patch('core.fetcher.ak')
    def test_fetch_market_spot_success(self, mock_ak):
        """测试获取市场数据成功"""
        # 模拟返回数据
        mock_data = pd.DataFrame({
            '代码': ['000001', '000002'],
            '名称': ['平安银行', '万科A'],
            '最新价': [10.5, 15.2],
            '涨跌幅': [2.5, -1.2],
            '成交量': [1000000, 2000000],
            '成交额': [10500000, 30400000],
            '量比': [1.5, 0.8],
        })
        mock_ak.stock_zh_a_spot_em.return_value = mock_data
        
        result = self.fetcher.fetch_market_spot()
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIn('code', result.columns)
        self.assertIn('name', result.columns)
        self.assertIn('change_pct', result.columns)
    
    @patch('core.fetcher.ak')
    def test_fetch_market_spot_empty(self, mock_ak):
        """测试获取市场数据为空"""
        mock_ak.stock_zh_a_spot_em.return_value = pd.DataFrame()
        
        result = self.fetcher.fetch_market_spot()
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)
    
    @patch('core.fetcher.ak')
    def test_fetch_sector_list(self, mock_ak):
        """测试获取板块列表"""
        mock_data = pd.DataFrame({
            '排名': [1, 2],
            '板块名称': ['AI算力', '机器人'],
            '板块代码': ['BK0428', 'BK0800'],
            '涨跌幅': [3.2, 2.8],
            '主力净流入': [500000000, 300000000],
        })
        mock_ak.stock_board_concept_name_em.return_value = mock_data
        
        result = self.fetcher.fetch_sector_list()
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertIn('sector_name', result.columns)
        self.assertIn('sector_code', result.columns)
    
    @patch('core.fetcher.ak')
    def test_fetch_northbound_flow(self, mock_ak):
        """测试获取北向资金"""
        mock_data = pd.DataFrame({
            '日期': ['2024-03-01', '2024-03-02'],
            '当日资金流入': [100000000, -50000000],
            '当日成交净买额': [120000000, -30000000],
        })
        mock_ak.stock_hsgt_hist_em.return_value = mock_data
        
        result = self.fetcher.fetch_northbound_flow(days=5)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)


class TestDataValidation(unittest.TestCase):
    """测试数据验证"""
    
    def test_column_mapping(self):
        """测试列名映射"""
        # 模拟原始数据
        raw_data = pd.DataFrame({
            '代码': ['000001'],
            '名称': ['测试'],
            '最新价': [10.0],
            '涨跌幅': [5.0],
        })
        
        # 验证映射后的列名
        column_mapping = {
            '代码': 'code',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'change_pct',
        }
        
        mapped_data = raw_data.rename(columns=column_mapping)
        
        self.assertIn('code', mapped_data.columns)
        self.assertIn('name', mapped_data.columns)
        self.assertEqual(mapped_data['code'].iloc[0], '000001')


if __name__ == '__main__':
    unittest.main()
