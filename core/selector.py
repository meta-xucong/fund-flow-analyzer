# -*- coding: utf-8 -*-
"""
选股策略模块

提供多种选股策略实现
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)


class StockSelectionStrategy(ABC):
    """
    选股策略抽象基类
    
    所有具体策略必须继承此类并实现select方法
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass
    
    @abstractmethod
    def select(self, market_data: pd.DataFrame, 
               top_n: int = 10) -> pd.DataFrame:
        """
        执行选股
        
        Args:
            market_data: 全市场数据DataFrame
            top_n: 返回股票数量
            
        Returns:
            精选股票DataFrame，必须包含:
            - code: 股票代码
            - name: 股票名称
            - score: 评分
            - reason: 选股理由
        """
        pass
    
    def validate_data(self, market_data: pd.DataFrame) -> bool:
        """
        验证输入数据
        
        Args:
            market_data: 市场数据
            
        Returns:
            数据是否有效
        """
        if market_data is None or len(market_data) == 0:
            logger.warning("输入数据为空")
            return False
        
        required_cols = ['code', 'name']
        for col in required_cols:
            if col not in market_data.columns:
                logger.warning(f"缺少必要列: {col}")
                return False
        
        return True
    
    def _format_reason(self, **kwargs) -> str:
        """格式化选股理由"""
        parts = []
        for key, value in kwargs.items():
            if isinstance(value, float):
                parts.append(f"{key}:{value:.2f}")
            else:
                parts.append(f"{key}:{value}")
        return ", ".join(parts)


class MomentumStrategy(StockSelectionStrategy):
    """
    动量策略 - 追涨型
    
    选股条件:
    - 涨幅 2% ~ 7% (避免涨停无法买入)
    - 量比 > 150% (放量)
    - 成交额 > 3亿 (流动性充足)
    - 1日主力资金净流入 > 0
    
    适用场景: 市场强势，热点明确时
    """
    
    name = "momentum"
    description = "动量突破策略，追涨强势股"
    
    # 选股参数
    MIN_CHANGE_PCT = settings.MOMENTUM_MIN_CHANGE  # 最小涨幅
    MAX_CHANGE_PCT = settings.MOMENTUM_MAX_CHANGE  # 最大涨幅
    MIN_VOLUME_RATIO = settings.MOMENTUM_MIN_VOLUME_RATIO  # 最小量比
    MIN_AMOUNT = settings.MOMENTUM_MIN_AMOUNT  # 最小成交额
    
    def select(self, market_data: pd.DataFrame, 
               top_n: int = 10) -> pd.DataFrame:
        """
        执行动量选股
        
        Args:
            market_data: 全市场数据
            top_n: 返回数量
            
        Returns:
            动量选股结果
        """
        logger.info(f"开始执行动量选股 (参数: 涨幅{self.MIN_CHANGE_PCT}%~{self.MAX_CHANGE_PCT}%)...")
        
        if not self.validate_data(market_data):
            return pd.DataFrame()
        
        # 过滤条件
        df = market_data.copy()
        
        # 基本条件过滤
        mask = (
            (df['change_pct'] >= self.MIN_CHANGE_PCT) &
            (df['change_pct'] <= self.MAX_CHANGE_PCT)
        )
        
        # 量比条件 (如果有)
        if 'volume_ratio' in df.columns:
            mask &= (df['volume_ratio'] >= self.MIN_VOLUME_RATIO)
        
        # 成交额条件 (如果有)
        if 'amount' in df.columns:
            mask &= (df['amount'] >= self.MIN_AMOUNT)
        
        # 资金流入条件 (如果有)
        if 'main_inflow_1d' in df.columns:
            mask &= (df['main_inflow_1d'] > 0)
        
        filtered = df[mask].copy()
        
        if len(filtered) == 0:
            logger.warning("动量策略: 没有符合条件的股票")
            return pd.DataFrame()
        
        logger.info(f"动量策略过滤后剩余 {len(filtered)} 只股票")
        
        # 计算得分
        # Score = 涨幅*0.4 + (量比-1)*10*0.2 + 资金流入得分*0.4
        
        # 涨幅得分 (已满足基本条件，直接按比例)
        filtered['change_score'] = filtered['change_pct'] / self.MAX_CHANGE_PCT * 100
        
        # 量比得分
        if 'volume_ratio' in filtered.columns:
            filtered['volume_score'] = (filtered['volume_ratio'] - 1) * 20
            filtered['volume_score'] = filtered['volume_score'].clip(0, 100)
        else:
            filtered['volume_score'] = 50
        
        # 资金得分
        if 'main_inflow_1d' in filtered.columns:
            # 标准化到0-100
            max_inflow = filtered['main_inflow_1d'].max()
            if max_inflow > 0:
                filtered['fund_score'] = filtered['main_inflow_1d'] / max_inflow * 100
            else:
                filtered['fund_score'] = 50
        else:
            filtered['fund_score'] = 50
        
        # 综合得分
        filtered['score'] = (
            filtered['change_score'] * 0.4 +
            filtered['volume_score'] * 0.2 +
            filtered['fund_score'] * 0.4
        )
        
        # 生成理由
        filtered['reason'] = filtered.apply(
            lambda row: self._format_reason(
                涨幅=f"{row['change_pct']:.1f}%",
                量比=row.get('volume_ratio', 'N/A'),
                成交额=f"{row.get('amount', 0)/1e8:.1f}亿"
            ),
            axis=1
        )
        
        # 排序并选择top_n
        result = filtered.nlargest(top_n, 'score')[['code', 'name', 'score', 'reason', 'change_pct']]
        
        logger.info(f"动量选股完成，选出 {len(result)} 只股票")
        return result


class ReversalStrategy(StockSelectionStrategy):
    """
    反转策略 - 抄底型
    
    选股条件:
    - 跌幅 -7% ~ -3% (避免跌停)
    - 量比 > 2 (放量下跌，可能有承接)
    - 5日主力资金净流入 > 0 (中线资金看好)
    - 成交额 > 2亿
    
    适用场景: 市场调整，寻找反弹机会
    """
    
    name = "reversal"
    description = "反转抄底策略，低吸反弹股"
    
    # 选股参数
    MIN_CHANGE_PCT = settings.REVERSAL_MIN_CHANGE  # 最小跌幅
    MAX_CHANGE_PCT = settings.REVERSAL_MAX_CHANGE  # 最大跌幅
    MIN_VOLUME_RATIO = settings.REVERSAL_MIN_VOLUME_RATIO  # 最小量比
    MIN_AMOUNT = 2e8  # 最小成交额
    
    def select(self, market_data: pd.DataFrame, 
               top_n: int = 10) -> pd.DataFrame:
        """
        执行反转选股
        
        Args:
            market_data: 全市场数据
            top_n: 返回数量
            
        Returns:
            反转选股结果
        """
        logger.info(f"开始执行反转选股 (参数: 跌幅{self.MIN_CHANGE_PCT}%~{self.MAX_CHANGE_PCT}%)...")
        
        if not self.validate_data(market_data):
            return pd.DataFrame()
        
        df = market_data.copy()
        
        # 基本条件过滤
        mask = (
            (df['change_pct'] >= self.MIN_CHANGE_PCT) &
            (df['change_pct'] <= self.MAX_CHANGE_PCT)
        )
        
        # 量比条件
        if 'volume_ratio' in df.columns:
            mask &= (df['volume_ratio'] >= self.MIN_VOLUME_RATIO)
        
        # 成交额条件
        if 'amount' in df.columns:
            mask &= (df['amount'] >= self.MIN_AMOUNT)
        
        # 5日资金条件 (优先选择)
        if 'main_inflow_5d' in df.columns:
            # 不要求必须满足，但会加分
            has_5d_inflow = df['main_inflow_5d'] > 0
        else:
            has_5d_inflow = pd.Series(False, index=df.index)
        
        filtered = df[mask].copy()
        
        if len(filtered) == 0:
            logger.warning("反转策略: 没有符合条件的股票")
            return pd.DataFrame()
        
        logger.info(f"反转策略过滤后剩余 {len(filtered)} 只股票")
        
        # 计算得分
        # Score = |跌幅|*0.3 + 5日资金得分*0.5 + 量比得分*0.2
        
        # 跌幅得分 (跌幅越大得分越高，但有上限)
        filtered['drop_score'] = filtered['change_pct'].abs() / 7 * 100
        filtered['drop_score'] = filtered['drop_score'].clip(0, 100)
        
        # 量比得分
        if 'volume_ratio' in filtered.columns:
            filtered['volume_score'] = (filtered['volume_ratio'] - 1) * 20
            filtered['volume_score'] = filtered['volume_score'].clip(0, 100)
        else:
            filtered['volume_score'] = 50
        
        # 5日资金得分 (非常重要)
        if 'main_inflow_5d' in filtered.columns:
            max_5d = filtered['main_inflow_5d'].max()
            if max_5d > 0:
                filtered['fund_5d_score'] = filtered['main_inflow_5d'] / max_5d * 100
            else:
                filtered['fund_5d_score'] = 0
        else:
            filtered['fund_5d_score'] = 30  # 默认中等分数
        
        #  bonus: 5日资金为正的额外加分
        if 'main_inflow_5d' in filtered.columns:
            filtered['bonus'] = np.where(
                filtered['main_inflow_5d'] > 0, 20, 0
            )
        else:
            filtered['bonus'] = 0
        
        # 综合得分
        filtered['score'] = (
            filtered['drop_score'] * 0.3 +
            filtered['volume_score'] * 0.2 +
            filtered['fund_5d_score'] * 0.5 +
            filtered['bonus']
        )
        
        # 生成理由
        filtered['reason'] = filtered.apply(
            lambda row: self._format_reason(
                跌幅=f"{row['change_pct']:.1f}%",
                量比=row.get('volume_ratio', 'N/A'),
                资金5日=f"{row.get('main_inflow_5d', 0)/1e8:.1f}亿" if 'main_inflow_5d' in row else 'N/A'
            ),
            axis=1
        )
        
        result = filtered.nlargest(top_n, 'score')[['code', 'name', 'score', 'reason', 'change_pct']]
        
        logger.info(f"反转选股完成，选出 {len(result)} 只股票")
        return result


class FundFlowStrategy(StockSelectionStrategy):
    """
    资金流向策略 - 中线布局型
    
    选股条件:
    - 5日主力资金净流入为正
    - 近5日平均涨幅 > 1% (有上升趋势)
    - 当日涨幅 < 7% (避免追高)
    - 成交额 > 5亿 (主力资金关注)
    
    适用场景: 中线布局，跟踪主力资金
    """
    
    name = "fund_flow"
    description = "资金流向策略，跟踪主力布局"
    
    # 选股参数
    MIN_5D_CHANGE = 1.0  # 5日最小平均涨幅
    MAX_TODAY_CHANGE = 7.0  # 当日最大涨幅
    MIN_AMOUNT = 5e8  # 最小成交额
    
    def select(self, market_data: pd.DataFrame, 
               top_n: int = 10) -> pd.DataFrame:
        """
        执行资金流向选股
        
        Args:
            market_data: 全市场数据
            top_n: 返回数量
            
        Returns:
            资金流向选股结果
        """
        logger.info("开始执行资金流向选股...")
        
        if not self.validate_data(market_data):
            return pd.DataFrame()
        
        df = market_data.copy()
        
        # 基本条件
        mask = pd.Series(True, index=df.index)
        
        # 5日资金条件 (必须有)
        if 'main_inflow_5d' in df.columns:
            mask &= (df['main_inflow_5d'] > 0)
        else:
            logger.warning("缺少5日资金数据，跳过资金流向策略")
            return pd.DataFrame()
        
        # 当日涨幅限制
        if 'change_pct' in df.columns:
            mask &= (df['change_pct'] < self.MAX_TODAY_CHANGE)
        
        # 成交额条件
        if 'amount' in df.columns:
            mask &= (df['amount'] >= self.MIN_AMOUNT)
        
        # 5日涨幅条件 (如果有)
        if 'change_5d' in df.columns:
            mask &= (df['change_5d'] / 5 >= self.MIN_5D_CHANGE)
        
        filtered = df[mask].copy()
        
        if len(filtered) == 0:
            logger.warning("资金流向策略: 没有符合条件的股票")
            return pd.DataFrame()
        
        logger.info(f"资金流向策略过滤后剩余 {len(filtered)} 只股票")
        
        # 计算得分
        # Score = 5日资金得分*0.6 + 1日资金得分*0.3 + (5-当日涨幅)*0.1
        
        # 5日资金得分
        max_5d = filtered['main_inflow_5d'].max()
        if max_5d > 0:
            filtered['fund_5d_score'] = filtered['main_inflow_5d'] / max_5d * 100
        else:
            filtered['fund_5d_score'] = 0
        
        # 1日资金得分
        if 'main_inflow_1d' in filtered.columns:
            max_1d = filtered['main_inflow_1d'].max()
            if max_1d > 0:
                filtered['fund_1d_score'] = filtered['main_inflow_1d'] / max_1d * 100
            else:
                filtered['fund_1d_score'] = 0
        else:
            filtered['fund_1d_score'] = 50
        
        # 当日涨幅得分 (涨幅适中最好，2-5%)
        if 'change_pct' in filtered.columns:
            # 最优区间2-5%，超出减分
            filtered['change_score'] = 100 - abs(filtered['change_pct'] - 3.5) * 10
            filtered['change_score'] = filtered['change_score'].clip(0, 100)
        else:
            filtered['change_score'] = 50
        
        # 综合得分
        filtered['score'] = (
            filtered['fund_5d_score'] * 0.6 +
            filtered['fund_1d_score'] * 0.3 +
            filtered['change_score'] * 0.1
        )
        
        # 生成理由
        filtered['reason'] = filtered.apply(
            lambda row: self._format_reason(
                资金5日=f"{row['main_inflow_5d']/1e8:.1f}亿",
                资金1日=f"{row.get('main_inflow_1d', 0)/1e8:.1f}亿" if 'main_inflow_1d' in row else 'N/A',
                涨幅=f"{row.get('change_pct', 0):.1f}%"
            ),
            axis=1
        )
        
        result = filtered.nlargest(top_n, 'score')[['code', 'name', 'score', 'reason', 'change_pct']]
        
        logger.info(f"资金流向选股完成，选出 {len(result)} 只股票")
        return result


class StrategySelector:
    """
    策略选择器
    
    管理所有选股策略，提供统一的策略执行接口
    """
    
    def __init__(self):
        """初始化策略选择器"""
        self.strategies: Dict[str, StockSelectionStrategy] = {
            'momentum': MomentumStrategy(),
            'reversal': ReversalStrategy(),
            'fund_flow': FundFlowStrategy(),
        }
        logger.info(f"策略选择器初始化完成，已加载 {len(self.strategies)} 个策略")
    
    def execute_strategy(self, strategy_name: str, 
                         market_data: pd.DataFrame,
                         top_n: int = 10) -> pd.DataFrame:
        """
        执行指定策略
        
        Args:
            strategy_name: 策略名称
            market_data: 市场数据
            top_n: 返回数量
            
        Returns:
            选股结果DataFrame
        """
        if strategy_name not in self.strategies:
            logger.error(f"未知策略: {strategy_name}")
            return pd.DataFrame()
        
        strategy = self.strategies[strategy_name]
        logger.info(f"执行策略: {strategy.name} - {strategy.description}")
        
        return strategy.select(market_data, top_n)
    
    def execute_all(self, market_data: pd.DataFrame,
                    top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """
        执行所有策略
        
        Args:
            market_data: 市场数据
            top_n: 每个策略返回数量
            
        Returns:
            Dict[str, DataFrame] 各策略选股结果
        """
        results = {}
        
        for name, strategy in self.strategies.items():
            try:
                result = strategy.select(market_data, top_n)
                results[name] = result
            except Exception as e:
                logger.error(f"策略 {name} 执行失败: {e}")
                results[name] = pd.DataFrame()
        
        return results
    
    def get_strategy_list(self) -> List[Dict]:
        """
        获取策略列表
        
        Returns:
            策略信息列表
        """
        return [
            {
                'name': s.name,
                'description': s.description
            }
            for s in self.strategies.values()
        ]


class SelectionError(Exception):
    """选股异常"""
    pass
