# -*- coding: utf-8 -*-
"""
选股策略模块测试
"""
import unittest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.selector import (
    MomentumStrategy, ReversalStrategy, FundFlowStrategy,
    StrategySelector, StockSelectionStrategy
)


class TestMomentumStrategy(unittest.TestCase):
    """测试动量策略"""
    
    def setUp(self):
        """测试前置"""
        self.strategy = MomentumStrategy()
        
        # 构造测试数据
        self.market_data = pd.DataFrame({
            'code': ['000001', '000002', '000003', '000004', '000005'],
            'name': ['股票A', '股票B', '股票C', '股票D', '股票E'],
            'change_pct': [5.2, 3.8, 6.5, 1.5, 8.0],  # 1.5%和8%不满足条件
            'volume_ratio': [2.0, 1.8, 1.2, 2.5, 1.6],
            'amount': [5e8, 3e8, 2e8, 4e8, 1e8],
            'main_inflow_1d': [1e7, 5e6, -2e6, 8e6, 3e6],
        })
    
    def test_strategy_name(self):
        """测试策略名称"""
        self.assertEqual(self.strategy.name, 'momentum')
        self.assertIn('动量', self.strategy.description)
    
    def test_select_returns_dataframe(self):
        """测试返回DataFrame"""
        result = self.strategy.select(self.market_data, top_n=3)
        
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_select_filters_by_change_pct(self):
        """测试按涨幅过滤"""
        result = self.strategy.select(self.market_data, top_n=10)
        
        # 8%涨幅应该被过滤(超过MAX_CHANGE_PCT=7)
        codes = result['code'].tolist() if len(result) > 0 else []
        self.assertNotIn('000005', codes)
        
        # 1.5%涨幅应该被过滤(低于MIN_CHANGE_PCT=2)
        self.assertNotIn('000004', codes)
    
    def test_select_limits_results(self):
        """测试限制返回数量"""
        result = self.strategy.select(self.market_data, top_n=2)
        
        self.assertLessEqual(len(result), 2)
    
    def test_select_returns_required_columns(self):
        """测试返回必需列"""
        result = self.strategy.select(self.market_data, top_n=3)
        
        if len(result) > 0:
            self.assertIn('code', result.columns)
            self.assertIn('name', result.columns)
            self.assertIn('score', result.columns)
            self.assertIn('reason', result.columns)
    
    def test_empty_data(self):
        """测试空数据"""
        empty_data = pd.DataFrame()
        result = self.strategy.select(empty_data)
        
        self.assertEqual(len(result), 0)


class TestReversalStrategy(unittest.TestCase):
    """测试反转策略"""
    
    def setUp(self):
        """测试前置"""
        self.strategy = ReversalStrategy()
        
        self.market_data = pd.DataFrame({
            'code': ['000001', '000002', '000003', '000004', '000005'],
            'name': ['股票A', '股票B', '股票C', '股票D', '股票E'],
            'change_pct': [-5.2, -3.8, -6.5, -1.5, -9.0],  # -1.5%和-9%不满足条件
            'volume_ratio': [2.5, 2.2, 1.8, 3.0, 2.0],
            'amount': [5e8, 3e8, 2e8, 4e8, 1e8],
            'main_inflow_5d': [1e8, 5e7, -2e7, 8e7, 3e7],
        })
    
    def test_strategy_name(self):
        """测试策略名称"""
        self.assertEqual(self.strategy.name, 'reversal')
        self.assertIn('反转', self.strategy.description)
    
    def test_select_filters_by_change_pct(self):
        """测试按跌幅过滤"""
        result = self.strategy.select(self.market_data, top_n=10)
        
        codes = result['code'].tolist() if len(result) > 0 else []
        
        # -9%应该被过滤(超过MIN_CHANGE_PCT=-7)
        self.assertNotIn('000005', codes)
        
        # -1.5%应该被过滤(超过MAX_CHANGE_PCT=-3)
        self.assertNotIn('000004', codes)


class TestFundFlowStrategy(unittest.TestCase):
    """测试资金流向策略"""
    
    def setUp(self):
        """测试前置"""
        self.strategy = FundFlowStrategy()
        
        self.market_data = pd.DataFrame({
            'code': ['000001', '000002', '000003', '000004', '000005'],
            'name': ['股票A', '股票B', '股票C', '股票D', '股票E'],
            'change_pct': [3.0, 5.5, 8.5, 2.5, 4.0],  # 8.5%超过限制
            'amount': [8e8, 6e8, 5e8, 7e8, 4e8],  # 4e8小于MIN_AMOUNT
            'main_inflow_1d': [1e7, 5e6, 8e6, 3e6, 2e6],
            'main_inflow_5d': [5e7, 3e7, -1e7, 4e7, 2e7],  # -1e7不满足
        })
    
    def test_strategy_name(self):
        """测试策略名称"""
        self.assertEqual(self.strategy.name, 'fund_flow')
        self.assertIn('资金', self.strategy.description)
    
    def test_select_requires_5d_inflow(self):
        """测试需要5日资金为正"""
        result = self.strategy.select(self.market_data, top_n=10)
        
        codes = result['code'].tolist() if len(result) > 0 else []
        
        # 5日资金为负应该被过滤
        self.assertNotIn('000003', codes)
    
    def test_select_limits_today_change(self):
        """测试限制当日涨幅"""
        result = self.strategy.select(self.market_data, top_n=10)
        
        codes = result['code'].tolist() if len(result) > 0 else []
        
        # 8.5%涨幅应该被过滤
        self.assertNotIn('000003', codes)
    
    def test_select_requires_min_amount(self):
        """测试最小成交额限制"""
        result = self.strategy.select(self.market_data, top_n=10)
        
        codes = result['code'].tolist() if len(result) > 0 else []
        
        # 4e8小于最小成交额
        self.assertNotIn('000005', codes)


class TestStrategySelector(unittest.TestCase):
    """测试策略选择器"""
    
    def setUp(self):
        """测试前置"""
        self.selector = StrategySelector()
        
        self.market_data = pd.DataFrame({
            'code': ['000001', '000002', '000003', '000004', '000005'],
            'name': ['股票A', '股票B', '股票C', '股票D', '股票E'],
            'change_pct': [5.2, -4.5, 3.8, -2.5, 4.5],
            'volume_ratio': [2.0, 2.5, 1.8, 2.2, 1.5],
            'amount': [5e8, 4e8, 6e8, 3e8, 5e8],
            'main_inflow_1d': [1e7, -5e6, 8e6, 3e6, 2e6],
            'main_inflow_5d': [5e7, 3e7, 6e7, 4e7, 2e7],
        })
    
    def test_get_strategy_list(self):
        """测试获取策略列表"""
        strategies = self.selector.get_strategy_list()
        
        self.assertIsInstance(strategies, list)
        self.assertEqual(len(strategies), 3)
        
        names = [s['name'] for s in strategies]
        self.assertIn('momentum', names)
        self.assertIn('reversal', names)
        self.assertIn('fund_flow', names)
    
    def test_execute_strategy(self):
        """测试执行单个策略"""
        result = self.selector.execute_strategy('momentum', self.market_data, top_n=3)
        
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_execute_all(self):
        """测试执行所有策略"""
        results = self.selector.execute_all(self.market_data, top_n=3)
        
        self.assertIsInstance(results, dict)
        self.assertIn('momentum', results)
        self.assertIn('reversal', results)
        self.assertIn('fund_flow', results)
    
    def test_execute_unknown_strategy(self):
        """测试执行未知策略"""
        result = self.selector.execute_strategy('unknown', self.market_data)
        
        self.assertEqual(len(result), 0)


class TestDataValidation(unittest.TestCase):
    """测试数据验证"""
    
    def setUp(self):
        self.strategy = MomentumStrategy()
    
    def test_validate_data_empty(self):
        """测试空数据验证"""
        result = self.strategy.validate_data(pd.DataFrame())
        self.assertFalse(result)
    
    def test_validate_data_missing_columns(self):
        """测试缺少列"""
        data = pd.DataFrame({'unknown_col': [1, 2, 3]})
        result = self.strategy.validate_data(data)
        self.assertFalse(result)
    
    def test_validate_data_valid(self):
        """测试有效数据"""
        data = pd.DataFrame({
            'code': ['000001'],
            'name': ['测试'],
        })
        result = self.strategy.validate_data(data)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
