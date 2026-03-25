#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import os
from datetime import datetime


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.output_dir = 'reports/daily'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, data: Dict) -> Dict:
        """
        生成完整报告
        
        Returns:
            Dict包含报告的所有数据
        """
        if data is None:
            return None
        
        stocks_df = data['stocks']
        sectors_df = data['sectors']
        sentiment = data['sentiment']
        date_str = data['date']
        
        # 选股
        momentum_picks = self.select_stocks_momentum(stocks_df)
        reversal_picks = self.select_stocks_reversal(stocks_df)
        
        # 板块排行
        sector_ranking = self.get_sector_ranking(sectors_df)
        
        # 构建报告
        report = {
            'date': date_str,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sentiment': sentiment,
            'sector_ranking': sector_ranking,
            'momentum_picks': momentum_picks.to_dict('records') if not momentum_picks.empty else [],
            'reversal_picks': reversal_picks.to_dict('records') if not reversal_picks.empty else [],
            'summary': self.generate_summary(sentiment, momentum_picks, reversal_picks)
        }
        
        # 保存报告
        self.save_report(report, date_str)
        
        return report
    
    def select_stocks_momentum(self, stocks_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """动量选股"""
        if stocks_df.empty:
            return pd.DataFrame()
        
        filtered = stocks_df[
            (stocks_df['change_pct'] >= 2.0) &
            (stocks_df['change_pct'] <= 7.0) &
            (stocks_df['amount'] >= 30000) &
            (stocks_df['volume_ratio'] >= 1.5)
        ].copy()
        
        if filtered.empty:
            return pd.DataFrame()
        
        filtered['score'] = (
            filtered['change_pct'] * 0.4 +
            filtered['volume_ratio'] * 2 * 0.3 +
            filtered['amount'] / 10000 * 0.3
        )
        
        filtered['reason'] = '动量突破: 涨幅' + filtered['change_pct'].astype(str) + '%'
        
        return filtered.sort_values('score', ascending=False).head(top_n)
    
    def select_stocks_reversal(self, stocks_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """反转选股 - 放宽条件"""
        if stocks_df.empty:
            return pd.DataFrame()
        
        # 选择下跌但基本面尚可的股票
        filtered = stocks_df[
            (stocks_df['change_pct'] >= -5.0) &
            (stocks_df['change_pct'] <= -1.0) &
            (stocks_df['amount'] >= 10000) &
            (stocks_df['volume_ratio'] >= 1.0)
        ].copy()
        
        if filtered.empty:
            return pd.DataFrame()
        
        # 综合评分：跌幅适中 + 量比活跃
        filtered['score'] = (
            abs(filtered['change_pct']) * 5 +
            filtered['volume_ratio'] * 2 +
            filtered['amount'] / 10000 * 0.5
        )
        
        filtered['reason'] = '超跌反弹: 跌幅' + filtered['change_pct'].astype(str) + '%'
        
        return filtered.sort_values('score', ascending=False).head(top_n)
    
    def get_sector_ranking(self, sectors_df: pd.DataFrame, top_n: int = 10) -> List[Dict]:
        """获取板块排行"""
        if sectors_df.empty:
            return []
        
        cols = list(sectors_df.columns)
        
        # 找到涨跌幅列
        change_col = None
        for col in cols:
            if '涨跌' in str(col):
                change_col = col
                break
        
        if change_col is None and len(cols) > 5:
            change_col = cols[5]
        
        if change_col:
            df_sorted = sectors_df.sort_values(change_col, ascending=False).head(top_n)
        else:
            df_sorted = sectors_df.head(top_n)
        
        result = []
        for idx, row in df_sorted.iterrows():
            result.append({
                'rank': len(result) + 1,
                'name': row[cols[1]] if len(cols) > 1 else 'Unknown',
                'change_pct': round(row[change_col], 2) if change_col else 0,
                'amount': row[cols[7]] if len(cols) > 7 else 0
            })
        
        return result
    
    def generate_summary(self, sentiment: Dict, momentum_picks: pd.DataFrame, 
                        reversal_picks: pd.DataFrame) -> Dict:
        """生成操作建议"""
        score = sentiment['score']
        
        if score >= 70:
            position = '70-80%'
            advice = '市场情绪乐观，积极布局'
        elif score >= 50:
            position = '50-70%'
            advice = '市场情绪中性偏乐观，适度参与'
        elif score >= 30:
            position = '30-50%'
            advice = '市场情绪中性偏悲观，控制仓位'
        else:
            position = '20-30%'
            advice = '市场情绪悲观，谨慎操作'
        
        watchlist = []
        if not momentum_picks.empty:
            watchlist.extend(momentum_picks['code'].tolist()[:3])
        if not reversal_picks.empty:
            watchlist.extend(reversal_picks['code'].tolist()[:2])
        
        return {
            'position_suggestion': position,
            'advice': advice,
            'watchlist': watchlist,
            'risk_level': '低' if score > 40 and score < 70 else '中'
        }
    
    def save_report(self, report: Dict, date_str: str):
        """保存报告到文件"""
        date_folder = os.path.join(self.output_dir, date_str)
        os.makedirs(date_folder, exist_ok=True)
        
        # 保存JSON格式
        import json
        json_path = os.path.join(date_folder, 'report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown格式
        md_path = os.path.join(date_folder, 'report.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._format_markdown(report))
    
    def _format_markdown(self, report: Dict) -> str:
        """格式化为Markdown"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"盘前资金流向分析报告 - {report['date']}")
        lines.append("=" * 80)
        lines.append("")
        
        # 市场情绪
        sentiment = report['sentiment']
        lines.append("【市场情绪】")
        lines.append(f"  情绪状态: {sentiment['status']} (分数: {sentiment['score']:.2f})")
        lines.append(f"  上涨: {sentiment['up_count']}只 ({sentiment['up_ratio']*100:.1f}%)")
        lines.append(f"  下跌: {sentiment['down_count']}只")
        lines.append(f"  涨停: {sentiment['limit_up']}只 | 跌停: {sentiment['limit_down']}只")
        lines.append(f"  平均涨跌幅: {sentiment['avg_change']:.2f}%")
        lines.append("")
        
        # 板块排行
        lines.append("【板块强度排行 TOP 10】")
        for sector in report['sector_ranking'][:10]:
            lines.append(f"  {sector['rank']}. {sector['name']}: {sector['change_pct']}%")
        lines.append("")
        
        # 动量选股
        lines.append("【动量策略 (追涨)】")
        for stock in report['momentum_picks']:
            lines.append(f"  • {stock['name']}({stock['code']}) - {stock['reason']}")
            lines.append(f"    得分:{stock['score']:.1f} | 涨幅:{stock['change_pct']}%, 量比:{stock['volume_ratio']:.2f}")
        lines.append("")
        
        # 反转选股
        lines.append("【反转策略 (抄底)】")
        for stock in report['reversal_picks']:
            lines.append(f"  • {stock['name']}({stock['code']}) - {stock['reason']}")
            lines.append(f"    得分:{stock['score']:.1f} | 跌幅:{stock['change_pct']}%")
        lines.append("")
        
        # 操作建议
        summary = report['summary']
        lines.append("【操作建议】")
        lines.append(f"  建议仓位: {summary['position_suggestion']}")
        lines.append(f"  风险等级: {summary['risk_level']}")
        lines.append(f"  建议: {summary['advice']}")
        if summary['watchlist']:
            lines.append(f"  观察名单: {', '.join(summary['watchlist'])}")
        
        lines.append("=" * 80)
        
        return '\n'.join(lines)
