# -*- coding: utf-8 -*-
"""
分析原理解释模块

将算法逻辑转化为可读的分析说明
无需AI，纯代码逻辑生成解释文本
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AnalysisExplainer:
    """
    分析解释器
    
    将量化分析结果转化为人类可读的解释文本
    """
    
    def __init__(self):
        """初始化解释器"""
        self.explanations = []
    
    def explain_market_sentiment(self, sentiment: Dict) -> str:
        """
        解释市场情绪结论
        
        Args:
            sentiment: 情绪分析结果
            
        Returns:
            解释文本
        """
        score = sentiment.get('score', 50)
        up_ratio = sentiment.get('up_ratio', 50)
        limit_up = sentiment.get('limit_up_count', 0)
        limit_down = sentiment.get('limit_down_count', 0)
        avg_change = sentiment.get('avg_change_pct', 0)
        
        parts = []
        
        # 基于分数的判断
        if score >= 70:
            parts.append(f"市场情绪乐观（分数{score:.1f}分），上涨个股占比{up_ratio:.1f}%")
            if limit_up > 30:
                parts.append(f"，涨停家数达{limit_up}家，显示资金活跃")
        elif score >= 50:
            parts.append(f"市场情绪中性偏乐观（分数{score:.1f}分）")
            if up_ratio > 55:
                parts.append(f"，虽然涨跌比{up_ratio:.1f}%:{100-up_ratio:.1f}%偏向多方，但力度有限")
        elif score >= 30:
            parts.append(f"市场情绪偏弱（分数{score:.1f}分）")
            if limit_down > 10:
                parts.append(f"，跌停{limit_down}家显示抛压较重")
        else:
            parts.append(f"市场情绪悲观（分数{score:.1f}分）")
            parts.append(f"，上涨个股仅{up_ratio:.1f}%，平均涨跌幅{avg_change:.2f}%显示普遍下跌")
            if limit_down > 20:
                parts.append(f"，跌停家数{limit_down}家显示恐慌情绪")
        
        return "".join(parts)
    
    def explain_volume_analysis(self, volume: Dict) -> str:
        """
        解释量能分析结论
        
        Args:
            volume: 量能分析结果
            
        Returns:
            解释文本
        """
        assessment = volume.get('volume_assessment', '正常')
        high_volume_ratio = volume.get('high_volume_ratio', 0)
        total_amount = volume.get('total_amount', 0)
        
        parts = []
        
        # 格式化成交额
        if total_amount >= 1e12:
            amount_str = f"{total_amount/1e12:.2f}万亿"
        elif total_amount >= 1e8:
            amount_str = f"{total_amount/1e8:.2f}亿"
        else:
            amount_str = f"{total_amount/1e4:.2f}万"
        
        if assessment == '放量':
            parts.append(f"量能充沛，总成交{amount_str}，放量个股占比{high_volume_ratio:.1f}%")
            if high_volume_ratio > 30:
                parts.append("，显示资金积极入场，交投活跃")
            else:
                parts.append("，部分板块有资金关注")
        elif assessment == '缩量':
            parts.append(f"量能萎缩，总成交{amount_str}，观望情绪浓厚")
            parts.append("，建议等待放量信号")
        else:
            parts.append(f"量能正常，总成交{amount_str}，市场处于平衡状态")
        
        return "".join(parts)
    
    def explain_sector_strength(self, sector_data: pd.DataFrame, top_n: int = 3) -> str:
        """
        解释板块强度结论
        
        Args:
            sector_data: 板块数据（已计算强度）
            top_n: 解释前N个板块
            
        Returns:
            解释文本
        """
        if sector_data is None or len(sector_data) == 0:
            return "暂无板块数据"
        
        parts = []
        
        # 解释TOP板块
        for i, row in sector_data.head(top_n).iterrows():
            name = row.get('sector_name', '未知')
            score = row.get('strength_score', 0)
            change = row.get('change_pct', 0)
            fund = row.get('main_inflow', 0)
            rating = row.get('strength_rating', '')
            
            part = f"【{name}】强度{score:.1f}分（{rating}）"
            
            # 分析强势原因
            reasons = []
            if change >= 3:
                reasons.append(f"涨幅{change:.1f}%表现亮眼")
            elif change >= 1:
                reasons.append(f"上涨{change:.1f}%稳健")
            
            if fund > 0:
                fund_yi = fund / 1e8
                if fund_yi > 10:
                    reasons.append(f"主力资金大幅流入{fund_yi:.1f}亿")
                elif fund_yi > 1:
                    reasons.append(f"资金净流入{fund_yi:.1f}亿")
            
            if reasons:
                part += "，" + "，".join(reasons)
            
            parts.append(part)
        
        return "\n".join(parts)
    
    def explain_stock_pick(self, strategy_name: str, stock: pd.Series) -> str:
        """
        解释选股理由
        
        Args:
            strategy_name: 策略名称
            stock: 股票数据
            
        Returns:
            解释文本
        """
        name = stock.get('name', '')
        code = stock.get('code', '')
        score = stock.get('score', 0)
        
        if strategy_name == 'momentum':
            change = stock.get('change_pct', 0)
            volume_ratio = stock.get('volume_ratio', 0)
            amount = stock.get('amount', 0)
            
            parts = [f"{name}({code})动量强劲："]
            parts.append(f"涨幅{change:.1f}%处于2-7%最佳追涨区间")
            
            if volume_ratio > 1.5:
                parts.append(f"，量比{volume_ratio:.1f}倍显示放量突破")
            
            if amount > 3e8:
                parts.append(f"，成交额{amount/1e8:.1f}亿流动性充足")
            
            parts.append(f"，综合得分{score:.1f}分")
            
            return "".join(parts)
            
        elif strategy_name == 'reversal':
            change = stock.get('change_pct', 0)
            fund_5d = stock.get('main_inflow_5d', 0)
            
            parts = [f"{name}({code})超跌反弹："]
            parts.append(f"跌幅{change:.1f}%处于-7%至-3%反弹区间")
            
            if fund_5d > 0:
                parts.append(f"，5日资金净流入显示中线资金看好")
            
            parts.append(f"，综合得分{score:.1f}分，适合低吸")
            
            return "".join(parts)
            
        elif strategy_name == 'fund_flow':
            fund_5d = stock.get('main_inflow_5d', 0)
            change = stock.get('change_pct', 0)
            
            parts = [f"{name}({code})资金布局："]
            if fund_5d > 0:
                parts.append(f"5日主力净流入{fund_5d/1e8:.1f}亿")
            
            if change < 7:
                parts.append(f"，当前涨幅{change:.1f}%未过热，有介入空间")
            
            parts.append(f"，综合得分{score:.1f}分，适合中线持有")
            
            return "".join(parts)
        
        return f"{name}({code})综合得分{score:.1f}分"
    
    def explain_risk_assessment(self, sentiment: Dict, sector_analysis: Dict) -> str:
        """
        解释风险评估结论
        
        Args:
            sentiment: 情绪分析
            sector_analysis: 板块分析
            
        Returns:
            解释文本
        """
        score = sentiment.get('score', 50)
        limit_up = sentiment.get('limit_up_count', 0)
        limit_down = sentiment.get('limit_down_count', 0)
        
        parts = []
        
        if score > 75:
            parts.append("市场过热风险：")
            parts.append(f"情绪分数{score:.1f}分接近高位，上涨个股占比过高")
            if limit_up > 50:
                parts.append(f"，涨停{limit_up}家显示炒作过热")
            parts.append("，建议降低仓位防范回调")
            
        elif score < 30:
            parts.append("市场恐慌风险：")
            parts.append(f"情绪分数{score:.1f}分处于低位")
            if limit_down > 10:
                parts.append(f"，跌停{limit_down}家显示恐慌情绪")
            parts.append("，建议观望或轻仓试错")
            
        else:
            parts.append("风险适中：")
            parts.append(f"情绪分数{score:.1f}分处于合理区间")
            if limit_up > limit_down * 3:
                parts.append("，涨停家数远超跌停，赚钱效应较好")
            parts.append("，可按策略正常操作")
        
        # 板块风险
        strong_sectors = sector_analysis.get('strong_sectors', [])
        if len(strong_sectors) > 0:
            parts.append(f"\n热点板块风险：关注{strong_sectors[0]}等板块的持续性")
        
        return "".join(parts)
    
    def generate_full_explanation(self, 
                                   sentiment: Dict,
                                   volume: Dict,
                                   sector_data: pd.DataFrame,
                                   stock_picks: Dict[str, pd.DataFrame],
                                   sector_analysis: Dict) -> Dict[str, str]:
        """
        生成完整解释
        
        Returns:
            各部分的解释字典
        """
        explanations = {
            'market_sentiment': self.explain_market_sentiment(sentiment),
            'volume_analysis': self.explain_volume_analysis(volume),
            'sector_strength': self.explain_sector_strength(sector_data),
            'risk_assessment': self.explain_risk_assessment(sentiment, sector_analysis),
            'stock_picks': {}
        }
        
        # 解释选股
        for strategy, picks in stock_picks.items():
            if picks is not None and len(picks) > 0:
                strategy_explanations = []
                for _, stock in picks.head(3).iterrows():
                    strategy_explanations.append(
                        self.explain_stock_pick(strategy, stock)
                    )
                explanations['stock_picks'][strategy] = strategy_explanations
        
        return explanations


class PrincipleLibrary:
    """
    原理知识库
    
    存储各分析模块的原理说明
    """
    
    PRINCIPLES = {
        'market_sentiment': """
【市场情绪分析原理】
1. 情绪分数计算公式：上涨个股占比 × 100
   - 70分以上：乐观，上涨个股超过70%
   - 50-70分：中性偏乐观
   - 30-50分：中性偏悲观
   - 30分以下：悲观，下跌个股超过70%

2. 辅助判断指标：
   - 涨停家数 > 50：过热信号
   - 跌停家数 > 10：风险信号
   - 平均涨跌幅：反映整体涨跌幅度
""",
        'sector_strength': """
【板块强度评分原理】
采用四维度加权评分（总分100分）：

1. 涨跌幅评分（25%权重）
   - ≥5%：90-100分（强势）
   - 3-5%：70-90分（偏强）
   - 1-3%：50-70分（中性）
   - 0-1%：30-50分（偏弱）
   - <0%：0-30分（弱势）

2. 资金流入评分（25%权重）
   - 主力净流入占比越高得分越高
   - 负流入直接降低评分

3. 板块贡献度（25%权重）
   - 上涨家数占比 × 100
   - 反映板块内个股普涨程度

4. 龙头表现（25%权重）
   - 龙头股涨幅按涨跌幅规则评分
   - 龙头强势带动板块情绪

评级标准：
- 80分以上：强势板块
- 60-80分：偏强板块
- 40-60分：中性板块
- 40分以下：弱势板块
""",
        'momentum_strategy': """
【动量策略（追涨）原理】

选股逻辑：
1. 涨幅筛选：2% ≤ 涨幅 ≤ 7%
   - 低于2%：动力不足
   - 高于7%：接近涨停，风险增大

2. 量比筛选：量比 > 1.5
   - 量比大于1表示放量
   - 量比越大资金关注度越高

3. 成交额筛选：成交额 > 3亿
   - 确保流动性充足
   - 避免小盘股操纵

4. 资金筛选：主力净流入 > 0
   - 确保有资金推动

评分公式：
得分 = 涨幅得分×0.4 + 量比得分×0.2 + 资金得分×0.4

适用场景：市场强势，热点明确时追涨强势股
""",
        'reversal_strategy': """
【反转策略（抄底）原理】

选股逻辑：
1. 跌幅筛选：-7% ≤ 跌幅 ≤ -3%
   - 跌幅过深（>-7%）：可能有利空
   - 跌幅过浅（<-3%）：反弹空间有限

2. 量比筛选：量比 > 2
   - 放量下跌说明有承接盘
   - 可能是洗盘或恐慌盘涌出

3. 资金筛选：5日主力净流入 > 0
   - 中线资金看好
   - 短期调整是介入机会

评分公式：
得分 = |跌幅|×0.3 + 5日资金得分×0.5 + 量比得分×0.2

适用场景：市场调整，寻找反弹机会时低吸
""",
        'fund_flow_strategy': """
【资金流向策略（中线）原理】

选股逻辑：
1. 5日资金筛选：5日主力净流入 > 0
   - 资金持续流入
   - 主力在悄悄建仓

2. 当日涨幅限制：当日涨幅 < 7%
   - 避免追高
   - 寻找仍在低位布局的标的

3. 成交额筛选：成交额 > 5亿
   - 主力资金能进得去
   - 也出得来的标的

评分公式：
得分 = 5日资金得分×0.6 + 1日资金得分×0.3 + 涨幅适中得分×0.1

适用场景：中线布局，跟踪主力资金动向
""",
        'risk_assessment': """
【风险评估原理】

风险等级判断：
1. 高风险
   - 情绪分数 > 80分：市场过热
   - 情绪分数 < 30分：市场恐慌
   - 涨停 > 50家或跌停 > 20家：极端行情

2. 中等风险
   - 情绪分数 65-80分或30-40分
   - 市场处于情绪转折期

3. 低风险
   - 情绪分数 40-65分
   - 涨跌停家数正常
   - 市场处于平衡状态

仓位建议：
- 高风险：降低仓位至30-50%
- 中等风险：控制仓位50-70%
- 低风险：正常仓位70-80%
"""
    }
    
    @classmethod
    def get_principle(cls, name: str) -> str:
        """获取原理说明"""
        return cls.PRINCIPLES.get(name, "暂无原理说明")
    
    @classmethod
    def get_all_principles(cls) -> Dict[str, str]:
        """获取所有原理说明"""
        return cls.PRINCIPLES.copy()


# 便捷函数
def explain_analysis(sentiment: Dict, volume: Dict, 
                     sector_data: pd.DataFrame,
                     stock_picks: Dict[str, pd.DataFrame],
                     sector_analysis: Dict) -> Dict[str, str]:
    """
    快速生成分析解释的便捷函数
    """
    explainer = AnalysisExplainer()
    return explainer.generate_full_explanation(
        sentiment, volume, sector_data, stock_picks, sector_analysis
    )
