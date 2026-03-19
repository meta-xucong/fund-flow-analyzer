# -*- coding: utf-8 -*-
"""
分析算法模块测试
"""
import unittest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analyzer import SectorStrengthCalculator, MarketAnalyzer, AnalysisError


class TestSectorStrengthCalculator(unittest.TestCase):
    """测试板块强度计算器"""
    
    def setUp(self):
        """测试前置"""
        self.calculator = SectorStrengthCalculator()
        
        # 构造测试数据
        self.sample_data = pd.DataFrame({
            'sector_code': ['BK001', 'BK002', 'BK003', 'BK004'],
            'sector_name': ['AI算力', '机器人', '新能源', '医药'],
            'change_pct': [5.2, 3.8, -1.5, 0.8],
            'main_inflow_ratio': [8.5, 4.2, -2.1, 1.5],
            'up_count': [45, 38, 15, 25],
            'down_count': [5, 12, 35, 20],
            'leader_change_pct': [7.2, 5.5, -3.2, 2.1],
        })
    
    def test_calculate_returns_dataframe(self):
        """测试返回值类型"""
        result = self.calculator.calculate(self.sample_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('strength_score', result.columns)
        self.assertIn('strength_rating', result.columns)
    
    def test_score_range(self):
        """测试分数范围"""
        result = self.calculator.calculate(self.sample_data)
        
        self.assertTrue((result['strength_score'] >= 0).all())
        self.assertTrue((result['strength_score'] <= 100).all())
    
    def test_score_ordering(self):
        """测试分数排序"""
        result = self.calculator.calculate(self.sample_data)
        
        # AI算力应该是第一名
        self.assertEqual(result.iloc[0]['sector_name'], 'AI算力')
        
        # 验证分数递减
        scores = result['strength_score'].values
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])
    
    def test_rating_classification(self):
        """测试评级分类"""
        result = self.calculator.calculate(self.sample_data)
        
        ratings = result['strength_rating'].unique()
        valid_ratings = ['强势', '偏强', '中性', '偏弱', '弱势']
        
        for rating in ratings:
            self.assertIn(rating, valid_ratings)
    
    def test_missing_columns(self):
        """测试缺少列的处理"""
        # 只提供部分列
        partial_data = pd.DataFrame({
            'sector_code': ['BK001'],
            'sector_name': ['测试'],
            'change_pct': [3.0],
        })
        
        result = self.calculator.calculate(partial_data)
        
        self.assertIn('strength_score', result.columns)
        self.assertEqual(len(result), 1)
    
    def test_get_top_sectors(self):
        """测试获取头部板块"""
        result = self.calculator.get_top_sectors(self.sample_data, n=2)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]['sector_name'], 'AI算力')


class TestMarketAnalyzer(unittest.TestCase):
    """测试市场分析器"""
    
    def setUp(self):
        """测试前置"""
        self.analyzer = MarketAnalyzer()
        
        # 构造测试市场数据
        np.random.seed(42)
        self.market_data = pd.DataFrame({
            'code': [f'{i:06d}' for i in range(100)],
            'name': [f'股票{i}' for i in range(100)],
            'change_pct': np.random.normal(0, 3, 100),
            'amount': np.random.uniform(1e7, 1e9, 100),
            'volume_ratio': np.random.uniform(0.5, 3, 100),
        })
    
    def test_analyze_market_sentiment(self):
        """测试情绪分析"""
        result = self.analyzer.analyze_market_sentiment(self.market_data)
        
        self.assertIn('sentiment', result)
        self.assertIn('score', result)
        self.assertIn('up_count', result)
        self.assertIn('down_count', result)
        
        self.assertIsInstance(result['score'], float)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)
    
    def test_analyze_market_sentiment_empty(self):
        """测试空数据情绪分析"""
        empty_data = pd.DataFrame()
        
        result = self.analyzer.analyze_market_sentiment(empty_data)
        
        self.assertEqual(result['sentiment'], '未知')
        self.assertEqual(result['score'], 50.0)
    
    def test_analyze_sector_rotation(self):
        """测试板块轮动分析"""
        sector_data = pd.DataFrame({
            'sector_code': ['BK001', 'BK002', 'BK003'],
            'sector_name': ['板块A', '板块B', '板块C'],
            'change_pct': [5.0, 3.0, -2.0],
            'main_inflow': [1e8, 5e7, -3e7],
            'up_count': [50, 40, 20],
            'down_count': [10, 20, 40],
        })
        
        result = self.analyzer.analyze_sector_rotation(sector_data)
        
        self.assertIn('strong_sectors', result)
        self.assertIn('weak_sectors', result)
        self.assertIn('top_sector', result)
        self.assertEqual(result['top_sector'], '板块A')
    
    def test_analyze_volume(self):
        """测试量能分析"""
        result = self.analyzer.analyze_volume(self.market_data)
        
        self.assertIn('total_amount', result)
        self.assertIn('high_volume_ratio', result)
        self.assertIn('volume_assessment', result)
        
        self.assertIsInstance(result['total_amount'], float)


class TestScoreCalculation(unittest.TestCase):
    """测试分数计算逻辑"""
    
    def setUp(self):
        self.calculator = SectorStrengthCalculator()
    
    def test_change_score_calculation(self):
        """测试涨跌幅分数计算"""
        # 涨5%应该得高分
        change_pct = pd.Series([5.0, 3.0, 1.0, 0.0, -2.0])
        scores = self.calculator._calc_change_score(change_pct)
        
        self.assertGreater(scores.iloc[0], scores.iloc[1])  # 5% > 3%
        self.assertGreater(scores.iloc[1], scores.iloc[2])  # 3% > 1%
        self.assertGreater(scores.iloc[2], scores.iloc[4])  # 1% > -2%
    
    def test_fund_flow_score_calculation(self):
        """测试资金分数计算"""
        fund_flow = pd.Series([5.0, 2.0, 0.0, -2.0])
        scores = self.calculator._calc_fund_flow_score(fund_flow)
        
        self.assertGreater(scores.iloc[0], scores.iloc[1])  # 5% > 2%
        self.assertGreater(scores.iloc[1], scores.iloc[3])  # 2% > -2%
    
    def test_contribution_score_calculation(self):
        """测试贡献度分数计算"""
        up_count = pd.Series([80, 50, 20, 0])
        down_count = pd.Series([20, 50, 80, 100])
        
        scores = self.calculator._calc_contribution_score(up_count, down_count)
        
        self.assertGreater(scores.iloc[0], scores.iloc[1])
        self.assertGreater(scores.iloc[1], scores.iloc[2])
        self.assertEqual(scores.iloc[3], 0)


if __name__ == '__main__':
    unittest.main()
