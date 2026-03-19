# -*- coding: utf-8 -*-
"""
分析算法模块

提供市场分析和板块强度计算功能
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)


class SectorStrengthCalculator:
    """
    板块强度评分计算器
    
    基于多维度计算板块强度评分(总分100):
    - 涨跌幅: 25%
    - 资金流入占比: 25%
    - 板块贡献度: 25%
    - 龙头表现: 25%
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化计算器
        
        Args:
            weights: 评分权重字典，默认使用配置
        """
        self.weights = weights or settings.SECTOR_WEIGHTS
        self._validate_weights()
    
    def _validate_weights(self):
        """验证权重配置"""
        total = sum(self.weights.values())
        if not np.isclose(total, 1.0, atol=0.01):
            logger.warning(f"权重总和不为1.0: {total}，将自动归一化")
            # 归一化
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def calculate(self, sector_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算板块强度评分
        
        Args:
            sector_data: 板块原始数据DataFrame，需包含:
                - sector_code: 板块代码
                - sector_name: 板块名称
                - change_pct: 涨跌幅(%)
                - main_inflow: 主力净流入
                - main_inflow_ratio: 主力净流入占比
                - up_count: 上涨家数
                - down_count: 下跌家数
                - leader_change_pct: 龙头涨跌幅(%)
                
        Returns:
            包含strength_score的DataFrame
        """
        logger.info("开始计算板块强度评分...")
        
        df = sector_data.copy()
        
        # 确保必要的列存在
        required_cols = ['sector_code', 'sector_name']
        for col in required_cols:
            if col not in df.columns:
                raise AnalysisError(f"缺少必要列: {col}")
        
        # 计算各项分数 (0-100)
        
        # 1. 涨跌幅分数 (25%)
        if 'change_pct' in df.columns:
            df['change_pct_score'] = self._calc_change_score(df['change_pct'])
        else:
            df['change_pct_score'] = 50.0
        
        # 2. 资金流入占比分数 (25%)
        if 'main_inflow_ratio' in df.columns:
            df['fund_flow_score'] = self._calc_fund_flow_score(df['main_inflow_ratio'])
        elif 'main_inflow' in df.columns:
            # 如果没有占比，使用净流入标准化
            df['fund_flow_score'] = self._normalize_score(df['main_inflow']) * 100
        else:
            df['fund_flow_score'] = 50.0
        
        # 3. 板块贡献度分数 (25%) - 基于上涨家数占比
        if 'up_count' in df.columns and 'down_count' in df.columns:
            df['contribution_score'] = self._calc_contribution_score(
                df['up_count'], df['down_count']
            )
        else:
            df['contribution_score'] = 50.0
        
        # 4. 龙头表现分数 (25%)
        if 'leader_change_pct' in df.columns:
            df['leader_score'] = self._calc_change_score(df['leader_change_pct'])
        else:
            df['leader_score'] = 50.0
        
        # 计算总分
        df['strength_score'] = (
            df['change_pct_score'] * self.weights.get('change_pct', 0.25) +
            df['fund_flow_score'] * self.weights.get('fund_flow_ratio', 0.25) +
            df['contribution_score'] * self.weights.get('contribution', 0.25) +
            df['leader_score'] * self.weights.get('leader_performance', 0.25)
        )
        
        # 确保分数在0-100范围内
        df['strength_score'] = df['strength_score'].clip(0, 100)
        
        # 添加评级
        df['strength_rating'] = df['strength_score'].apply(self._get_rating)
        
        # 按分数排序
        df = df.sort_values('strength_score', ascending=False).reset_index(drop=True)
        
        logger.info(f"板块强度评分计算完成，共 {len(df)} 个板块")
        return df
    
    def _calc_change_score(self, change_pct: pd.Series) -> pd.Series:
        """
        计算涨跌幅分数
        
        评分规则:
        - >= 5%: 90-100分
        - 3-5%: 70-90分
        - 1-3%: 50-70分
        - 0-1%: 30-50分
        - < 0%: 0-30分
        """
        score = pd.Series(50.0, index=change_pct.index)
        
        score = np.where(
            change_pct >= 5, 95 - (change_pct - 5) * 2,
            np.where(
                change_pct >= 3, 90 - (5 - change_pct) * 10,
                np.where(
                    change_pct >= 1, 70 - (3 - change_pct) * 10,
                    np.where(
                        change_pct >= 0, 50 - (1 - change_pct) * 20,
                        30 + change_pct * 3
                    )
                )
            )
        )
        
        return pd.Series(score, index=change_pct.index).clip(0, 100)
    
    def _calc_fund_flow_score(self, fund_flow_ratio: pd.Series) -> pd.Series:
        """
        计算资金流入分数
        
        评分规则:
        - >= 5%: 90-100分
        - 2-5%: 70-90分
        - 0-2%: 50-70分
        - < 0%: 0-50分
        """
        score = pd.Series(50.0, index=fund_flow_ratio.index)
        
        score = np.where(
            fund_flow_ratio >= 5, 95 - (fund_flow_ratio - 5),
            np.where(
                fund_flow_ratio >= 2, 90 - (5 - fund_flow_ratio) * 6.67,
                np.where(
                    fund_flow_ratio >= 0, 70 - (2 - fund_flow_ratio) * 10,
                    50 + fund_flow_ratio * 10
                )
            )
        )
        
        return pd.Series(score, index=fund_flow_ratio.index).clip(0, 100)
    
    def _calc_contribution_score(self, up_count: pd.Series, 
                                  down_count: pd.Series) -> pd.Series:
        """
        计算板块贡献度分数
        
        基于上涨家数占比评分
        """
        total = up_count + down_count
        total = total.replace(0, 1)  # 避免除零
        
        up_ratio = up_count / total
        return (up_ratio * 100).clip(0, 100)
    
    def _normalize_score(self, values: pd.Series) -> pd.Series:
        """标准化分数到0-1范围"""
        min_val = values.min()
        max_val = values.max()
        
        if max_val == min_val:
            return pd.Series(0.5, index=values.index)
        
        return (values - min_val) / (max_val - min_val)
    
    def _get_rating(self, score: float) -> str:
        """根据分数获取评级"""
        if score >= 80:
            return "强势"
        elif score >= 60:
            return "偏强"
        elif score >= 40:
            return "中性"
        elif score >= 20:
            return "偏弱"
        else:
            return "弱势"
    
    def get_top_sectors(self, sector_data: pd.DataFrame, 
                        n: int = 10) -> pd.DataFrame:
        """
        获取排名靠前的板块
        
        Args:
            sector_data: 板块数据
            n: 返回数量
            
        Returns:
            前N名板块DataFrame
        """
        df = self.calculate(sector_data)
        return df.head(n)


class MarketAnalyzer:
    """
    市场分析器
    
    提供市场情绪分析、趋势判断等功能
    """
    
    def __init__(self):
        """初始化分析器"""
        self.sector_calculator = SectorStrengthCalculator()
    
    def analyze_market_sentiment(self, market_data: pd.DataFrame) -> Dict:
        """
        分析市场情绪
        
        Args:
            market_data: 市场概况DataFrame
            
        Returns:
            情绪分析结果字典
        """
        logger.info("开始分析市场情绪...")
        
        total = len(market_data)
        if total == 0:
            return {
                'sentiment': '未知',
                'score': 50.0,
                'description': '无数据'
            }
        
        # 计算基础指标
        up_count = len(market_data[market_data['change_pct'] > 0])
        down_count = len(market_data[market_data['change_pct'] < 0])
        flat_count = total - up_count - down_count
        
        up_ratio = up_count / total
        down_ratio = down_count / total
        
        # 涨跌停统计
        limit_up = len(market_data[market_data['change_pct'] >= 9.5])
        limit_down = len(market_data[market_data['change_pct'] <= -9.5])
        
        # 计算情绪分数 (0-100)
        sentiment_score = up_ratio * 100
        
        # 判断情绪等级
        if sentiment_score >= 70:
            sentiment = '乐观'
        elif sentiment_score >= 55:
            sentiment = '偏乐观'
        elif sentiment_score >= 45:
            sentiment = '中性'
        elif sentiment_score >= 30:
            sentiment = '偏悲观'
        else:
            sentiment = '悲观'
        
        # 计算平均涨跌幅
        avg_change = market_data['change_pct'].mean()
        
        # 计算成交额
        total_amount = market_data['amount'].sum() if 'amount' in market_data.columns else 0
        
        result = {
            'sentiment': sentiment,
            'score': round(sentiment_score, 2),
            'up_ratio': round(up_ratio * 100, 2),
            'down_ratio': round(down_ratio * 100, 2),
            'flat_ratio': round(flat_count / total * 100, 2),
            'limit_up_count': limit_up,
            'limit_down_count': limit_down,
            'avg_change_pct': round(avg_change, 2),
            'total_amount': float(total_amount),
            'description': self._generate_sentiment_description(
                sentiment, up_ratio, limit_up, limit_down
            )
        }
        
        logger.info(f"市场情绪分析完成: {sentiment} (分数: {sentiment_score:.1f})")
        return result
    
    def analyze_sector_rotation(self, sector_data: pd.DataFrame,
                                 prev_sector_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        分析板块轮动
        
        Args:
            sector_data: 当前板块数据
            prev_sector_data: 上一期板块数据，可选
            
        Returns:
            板块轮动分析结果
        """
        logger.info("开始分析板块轮动...")
        
        # 计算板块强度
        df = self.sector_calculator.calculate(sector_data)
        
        # 获取强势板块 (前10)
        strong_sectors = df.head(10)['sector_name'].tolist()
        
        # 获取弱势板块 (后10)
        weak_sectors = df.tail(10)['sector_name'].tolist()
        
        # 如果有历史数据，计算变化
        momentum_sectors = []
        if prev_sector_data is not None:
            prev_df = self.sector_calculator.calculate(prev_sector_data)
            
            # 合并比较
            merged = df[['sector_code', 'sector_name', 'strength_score']].merge(
                prev_df[['sector_code', 'strength_score']],
                on='sector_code',
                suffixes=('', '_prev'),
                how='left'
            )
            
            merged['score_change'] = merged['strength_score'] - merged['strength_score_prev'].fillna(0)
            
            # 获取动量板块 (分数上升最多的)
            momentum_sectors = merged.nlargest(5, 'score_change')['sector_name'].tolist()
        
        result = {
            'strong_sectors': strong_sectors,
            'weak_sectors': weak_sectors,
            'momentum_sectors': momentum_sectors,
            'top_sector': df.iloc[0]['sector_name'] if len(df) > 0 else None,
            'focus_recommendation': self._generate_focus_recommendation(df)
        }
        
        logger.info(f"板块轮动分析完成，强势板块: {strong_sectors[:3]}")
        return result
    
    def analyze_volume(self, market_data: pd.DataFrame,
                       history_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        分析量能情况
        
        Args:
            market_data: 当前市场数据
            history_data: 历史数据，用于对比
            
        Returns:
            量能分析结果
        """
        logger.info("开始分析量能...")
        
        total_amount = market_data['amount'].sum() if 'amount' in market_data.columns else 0
        
        # 计算放量个股比例
        high_volume = len(market_data[
            (market_data['volume_ratio'] > 2) if 'volume_ratio' in market_data.columns else []
        ])
        high_volume_ratio = high_volume / len(market_data) * 100 if len(market_data) > 0 else 0
        
        result = {
            'total_amount': float(total_amount),
            'total_amount_display': self._format_amount(total_amount),
            'high_volume_ratio': round(high_volume_ratio, 2),
            'volume_assessment': '放量' if high_volume_ratio > 20 else '正常' if high_volume_ratio > 10 else '缩量'
        }
        
        # 如果有历史数据，计算环比
        if history_data is not None and 'amount' in history_data.columns:
            prev_amount = history_data['amount'].sum()
            if prev_amount > 0:
                change_ratio = (total_amount - prev_amount) / prev_amount * 100
                result['amount_change_ratio'] = round(change_ratio, 2)
        
        return result
    
    def _generate_sentiment_description(self, sentiment: str, 
                                        up_ratio: float,
                                        limit_up: int,
                                        limit_down: int) -> str:
        """生成情绪描述"""
        parts = [f"市场情绪{sentiment}"]
        
        if up_ratio > 0.6:
            parts.append("上涨个股占比高")
        elif up_ratio < 0.4:
            parts.append("下跌个股居多")
        
        if limit_up > 30:
            parts.append(f"涨停家数较多({limit_up}家)")
        
        if limit_down > 10:
            parts.append(f"注意风险，跌停{limit_down}家")
        
        return "，".join(parts)
    
    def _generate_focus_recommendation(self, sector_df: pd.DataFrame) -> str:
        """生成关注建议"""
        if len(sector_df) == 0:
            return "暂无建议"
        
        top3 = sector_df.head(3)['sector_name'].tolist()
        return f"关注{', '.join(top3)}等板块机会"
    
    def _format_amount(self, amount: float) -> str:
        """格式化金额显示"""
        if amount >= 1e12:
            return f"{amount/1e12:.2f}万亿"
        elif amount >= 1e8:
            return f"{amount/1e8:.2f}亿"
        elif amount >= 1e4:
            return f"{amount/1e4:.2f}万"
        else:
            return f"{amount:.2f}"


class AnalysisError(Exception):
    """分析异常"""
    pass
