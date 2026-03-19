# -*- coding: utf-8 -*-
"""
报告生成模块

提供报告生成、可视化和导出功能
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams

from config.settings import settings

logger = logging.getLogger(__name__)

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False


class ReportGenerator:
    """
    报告生成器
    
    生成文本报告、JSON报告和可视化图表
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录，默认使用配置
        """
        self.output_dir = output_dir or settings.DAILY_REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.colors = settings.COLORS
        self.fig_size = settings.FIGURE_SIZE
        self.dpi = settings.DPI
        
        logger.info(f"报告生成器初始化完成，输出目录: {self.output_dir}")
    
    def generate_full_report(self,
                            market_data: pd.DataFrame,
                            sector_data: pd.DataFrame,
                            stock_picks: Dict[str, pd.DataFrame],
                            sentiment_analysis: Dict,
                            sector_analysis: Dict,
                            volume_analysis: Dict,
                            date: Optional[str] = None) -> Dict[str, Any]:
        """
        生成完整报告
        
        Args:
            market_data: 市场数据
            sector_data: 板块数据
            stock_picks: 选股结果字典
            sentiment_analysis: 情绪分析结果
            sector_analysis: 板块分析结果
            volume_analysis: 量能分析结果
            date: 报告日期，默认今天
            
        Returns:
            完整报告字典
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始生成完整报告: {date}")
        
        report = {
            'meta': {
                'report_id': f"RPT{date.replace('-', '')}090000",
                'date': date,
                'data_source': 'AKShare',
                'version': '1.0',
                'generated_at': datetime.now().isoformat()
            },
            'summary': {
                'market_sentiment': sentiment_analysis.get('sentiment', '未知'),
                'sentiment_score': sentiment_analysis.get('score', 50.0),
                'top_sector': sector_analysis.get('top_sector', '未知'),
                'focus_action': sector_analysis.get('focus_recommendation', '观望'),
                'risk_level': self._assess_risk_level(sentiment_analysis)
            },
            'market_overview': {
                'total_stocks': sentiment_analysis.get('total_stocks', 0),
                'up_count': int(sentiment_analysis.get('up_count', 0)),
                'down_count': int(sentiment_analysis.get('down_count', 0)),
                'limit_up_count': sentiment_analysis.get('limit_up_count', 0),
                'limit_down_count': sentiment_analysis.get('limit_down_count', 0),
                'total_amount': sentiment_analysis.get('total_amount', 0),
                'total_amount_display': self._format_amount(
                    sentiment_analysis.get('total_amount', 0)
                ),
                'avg_change_pct': sentiment_analysis.get('avg_change_pct', 0),
                'up_ratio': sentiment_analysis.get('up_ratio', 0),
            },
            'volume_analysis': volume_analysis,
            'sector_ranking': self._format_sector_ranking(sector_data),
            'stock_picks': self._format_stock_picks(stock_picks),
            'risk_assessment': self._generate_risk_assessment(
                sentiment_analysis, sector_analysis
            ),
            'action_plan': self._generate_action_plan(
                sector_analysis, stock_picks
            )
        }
        
        logger.info(f"完整报告生成完成")
        return report
    
    def generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成文本格式报告
        
        Args:
            report_data: 报告数据字典
            
        Returns:
            文本格式报告
        """
        meta = report_data['meta']
        summary = report_data['summary']
        market = report_data['market_overview']
        volume = report_data.get('volume_analysis', {})
        sectors = report_data.get('sector_ranking', [])
        picks = report_data.get('stock_picks', {})
        risk = report_data.get('risk_assessment', {})
        action = report_data.get('action_plan', {})
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"  盘前资金流向分析报告  {meta['date']}")
        lines.append("=" * 80)
        lines.append("")
        
        # 市场情绪
        lines.append("【市场情绪】")
        lines.append(f"  情绪状态: {summary['market_sentiment']} (分数: {summary['sentiment_score']})")
        lines.append(f"  上涨: {market['up_count']}只 ({market['up_ratio']:.1f}%) | "
                    f"下跌: {market['down_count']}只 | "
                    f"涨停: {market['limit_up_count']}只 | 跌停: {market['limit_down_count']}只")
        lines.append(f"  总成交额: {market['total_amount_display']} | 平均涨跌幅: {market['avg_change_pct']:.2f}%")
        if volume:
            lines.append(f"  量能状态: {volume.get('volume_assessment', '未知')} | "
                        f"放量个股占比: {volume.get('high_volume_ratio', 0):.1f}%")
        lines.append("")
        
        # 板块排行
        lines.append("【板块强度排行 TOP 10】")
        for i, sector in enumerate(sectors[:10], 1):
            emoji = "🔥" if i <= 3 else "📈" if sector.get('change_pct', 0) > 0 else "📉"
            lines.append(f"  {i:2d}. {emoji} {sector['sector_name']:<12} "
                        f"涨跌幅:{sector.get('change_pct', 0):>+6.2f}%  "
                        f"强度分:{sector.get('strength_score', 0):>5.1f}  "
                        f"评级:{sector.get('strength_rating', '未知')}")
        lines.append("")
        
        # 选股结果
        for strategy_name, stocks in picks.items():
            if not stocks:
                continue
            
            strategy_names = {
                'momentum': '动量策略 (追涨)',
                'reversal': '反转策略 (抄底)',
                'fund_flow': '资金流向策略 (中线)'
            }
            lines.append(f"【{strategy_names.get(strategy_name, strategy_name)}】")
            for stock in stocks[:5]:  # 只显示前5
                lines.append(f"  📌 {stock['code']} {stock['name']:<8} "
                            f"得分:{stock['score']:.1f} | {stock['reason']}")
            lines.append("")
        
        # 风险评估
        lines.append("【风险评估】")
        lines.append(f"  风险等级: {risk.get('market_risk', '未知')}")
        for suggestion in risk.get('suggestions', []):
            lines.append(f"  ⚠️  {suggestion}")
        lines.append("")
        
        # 操作建议
        lines.append("【操作建议】")
        lines.append(f"  建议仓位: {action.get('position_suggestion', '50%')}")
        lines.append(f"  关注板块: {summary['focus_action']}")
        if action.get('watchlist'):
            lines.append(f"  观察名单: {', '.join(action['watchlist'][:5])}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"报告生成时间: {meta['generated_at']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """
        生成JSON格式报告
        
        Args:
            report_data: 报告数据字典
            
        Returns:
            JSON格式字符串
        """
        return json.dumps(report_data, ensure_ascii=False, indent=2, default=str)
    
    def save_report(self, report_data: Dict[str, Any], 
                    date: Optional[str] = None) -> Dict[str, Path]:
        """
        保存报告到文件
        
        Args:
            report_data: 报告数据
            date: 日期，默认今天
            
        Returns:
            保存的文件路径字典
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        file_prefix = f"report_{date}"
        saved_files = {}
        
        try:
            # 保存文本报告
            text_report = self.generate_text_report(report_data)
            text_path = self.output_dir / f"{file_prefix}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_report)
            saved_files['text'] = text_path
            logger.info(f"文本报告已保存: {text_path}")
            
            # 保存JSON报告
            json_report = self.generate_json_report(report_data)
            json_path = self.output_dir / f"{file_prefix}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_report)
            saved_files['json'] = json_path
            logger.info(f"JSON报告已保存: {json_path}")
            
            # 生成并保存图表
            chart_path = self.generate_charts(report_data, date)
            if chart_path:
                saved_files['chart'] = chart_path
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
        
        return saved_files
    
    def generate_charts(self, report_data: Dict[str, Any],
                        date: Optional[str] = None) -> Optional[Path]:
        """
        生成可视化图表
        
        Args:
            report_data: 报告数据
            date: 日期
            
        Returns:
            图表文件路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            fig = plt.figure(figsize=(16, 12), dpi=self.dpi)
            fig.suptitle(f'盘前资金流向分析报告 - {date}', fontsize=16, fontweight='bold')
            
            # 1. 市场涨跌分布
            ax1 = plt.subplot(2, 3, 1)
            self._plot_market_distribution(ax1, report_data['market_overview'])
            
            # 2. 板块强度排行
            ax2 = plt.subplot(2, 3, 2)
            self._plot_sector_ranking(ax2, report_data.get('sector_ranking', []))
            
            # 3. 情绪分数仪表盘
            ax3 = plt.subplot(2, 3, 3)
            self._plot_sentiment_gauge(ax3, report_data['summary'])
            
            # 4. 选股策略对比
            ax4 = plt.subplot(2, 3, 4)
            self._plot_strategy_comparison(ax4, report_data.get('stock_picks', {}))
            
            # 5. 量能分析
            ax5 = plt.subplot(2, 3, 5)
            self._plot_volume_analysis(ax5, report_data.get('volume_analysis', {}))
            
            # 6. 风险评估
            ax6 = plt.subplot(2, 3, 6)
            self._plot_risk_assessment(ax6, report_data.get('risk_assessment', {}))
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            # 保存图表
            chart_path = self.output_dir / f"report_{date}.png"
            plt.savefig(chart_path, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"图表已保存: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            return None
    
    def _plot_market_distribution(self, ax, market_data: Dict):
        """绘制市场涨跌分布"""
        up = market_data.get('up_count', 0)
        down = market_data.get('down_count', 0)
        total = market_data.get('total_stocks', up + down)
        flat = total - up - down
        
        labels = ['上涨', '下跌', '平盘']
        sizes = [up, down, flat]
        colors = [self.colors['up'], self.colors['down'], self.colors['neutral']]
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 10})
        ax.set_title('市场涨跌分布', fontsize=12, fontweight='bold')
    
    def _plot_sector_ranking(self, ax, sectors: List[Dict]):
        """绘制板块强度排行"""
        if not sectors:
            ax.text(0.5, 0.5, '无数据', ha='center', va='center')
            return
        
        top10 = sectors[:10]
        names = [s['sector_name'][:6] for s in top10]  # 截短名称
        scores = [s.get('strength_score', 0) for s in top10]
        changes = [s.get('change_pct', 0) for s in top10]
        
        colors = [self.colors['up'] if c > 0 else self.colors['down'] for c in changes]
        
        bars = ax.barh(range(len(names)), scores, color=colors, alpha=0.7)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel('强度分数', fontsize=10)
        ax.set_title('板块强度 TOP 10', fontsize=12, fontweight='bold')
        ax.set_xlim(0, 100)
        
        # 添加数值标签
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(score + 1, bar.get_y() + bar.get_height()/2,
                   f'{score:.1f}', va='center', fontsize=8)
    
    def _plot_sentiment_gauge(self, ax, summary: Dict):
        """绘制情绪分数仪表盘"""
        score = summary.get('sentiment_score', 50)
        sentiment = summary.get('market_sentiment', '未知')
        
        # 绘制半圆仪表盘
        theta = np.linspace(0, np.pi, 100)
        r = 1.0
        
        # 背景弧
        ax.fill_between(np.cos(theta), np.sin(theta), 0, alpha=0.1, color='gray')
        
        # 分数弧
        score_theta = theta[int(score)] if int(score) < len(theta) else theta[-1]
        score_arc = theta[:int(score) + 1] if int(score) < len(theta) else theta
        
        if len(score_arc) > 1:
            color = self._get_sentiment_color(score)
            ax.fill_between(np.cos(score_arc), np.sin(score_arc), 0, alpha=0.6, color=color)
        
        # 指针
        needle_angle = np.pi * (1 - score / 100)
        ax.arrow(0, 0, 0.8 * np.cos(needle_angle), 0.8 * np.sin(needle_angle),
                head_width=0.05, head_length=0.05, fc='black', ec='black')
        
        # 文字
        ax.text(0, -0.3, f'{score:.1f}', ha='center', va='center', 
               fontsize=24, fontweight='bold')
        ax.text(0, -0.6, sentiment, ha='center', va='center', fontsize=14)
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.8, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('市场情绪', fontsize=12, fontweight='bold')
    
    def _plot_strategy_comparison(self, ax, picks: Dict[str, List]):
        """绘制选股策略对比"""
        strategy_names = {
            'momentum': '动量',
            'reversal': '反转',
            'fund_flow': '资金流'
        }
        
        counts = []
        labels = []
        for key, name in strategy_names.items():
            if key in picks:
                counts.append(len(picks[key]))
                labels.append(name)
        
        if not counts:
            ax.text(0.5, 0.5, '无选股结果', ha='center', va='center')
            return
        
        colors = [self.colors['primary'], self.colors['highlight'], self.colors['neutral']]
        bars = ax.bar(labels, counts, color=colors[:len(labels)], alpha=0.7)
        ax.set_ylabel('选股数量', fontsize=10)
        ax.set_title('选股策略结果', fontsize=12, fontweight='bold')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    def _plot_volume_analysis(self, ax, volume: Dict):
        """绘制量能分析"""
        if not volume:
            ax.text(0.5, 0.5, '无数据', ha='center', va='center')
            return
        
        assessment = volume.get('volume_assessment', '未知')
        high_ratio = volume.get('high_volume_ratio', 0)
        
        # 简化的量能指示器
        categories = ['缩量', '正常', '放量']
        values = [30, 40, 30]  # 基础分布
        
        if assessment == '放量':
            highlight = 2
        elif assessment == '缩量':
            highlight = 0
        else:
            highlight = 1
        
        colors = ['lightgray'] * 3
        colors[highlight] = self.colors['highlight']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_ylabel('占比(%)', fontsize=10)
        ax.set_title(f'量能状态: {assessment}', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 100)
        
        # 添加放量比例标注
        ax.text(1, 80, f'放量个股\n{high_ratio:.1f}%', 
               ha='center', va='center', fontsize=11,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_risk_assessment(self, ax, risk: Dict):
        """绘制风险评估"""
        risk_level = risk.get('market_risk', '未知')
        suggestions = risk.get('suggestions', [])
        
        risk_colors = {
            '低': 'green',
            '中': 'orange',
            '高': 'red'
        }
        
        ax.text(0.5, 0.8, '风险等级', ha='center', va='center', 
               fontsize=14, transform=ax.transAxes)
        ax.text(0.5, 0.6, risk_level, ha='center', va='center',
               fontsize=28, fontweight='bold', color=risk_colors.get(risk_level, 'gray'),
               transform=ax.transAxes)
        
        # 建议列表
        y_pos = 0.4
        for suggestion in suggestions[:3]:
            ax.text(0.1, y_pos, f'• {suggestion}', ha='left', va='center',
                   fontsize=10, transform=ax.transAxes)
            y_pos -= 0.12
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('风险评估', fontsize=12, fontweight='bold')
    
    def _format_sector_ranking(self, sector_data: pd.DataFrame) -> List[Dict]:
        """格式化板块排名数据"""
        if sector_data is None or len(sector_data) == 0:
            return []
        
        columns = ['sector_code', 'sector_name', 'change_pct', 
                  'main_inflow', 'strength_score', 'strength_rating']
        
        result = []
        for _, row in sector_data.iterrows():
            item = {}
            for col in columns:
                if col in row:
                    item[col] = row[col]
            result.append(item)
        
        return result
    
    def _format_stock_picks(self, picks: Dict[str, pd.DataFrame]) -> Dict[str, List]:
        """格式化选股结果"""
        result = {}
        for strategy, df in picks.items():
            if df is None or len(df) == 0:
                result[strategy] = []
            else:
                result[strategy] = df.to_dict('records')
        return result
    
    def _assess_risk_level(self, sentiment: Dict) -> str:
        """评估风险等级"""
        score = sentiment.get('score', 50)
        limit_up = sentiment.get('limit_up_count', 0)
        limit_down = sentiment.get('limit_down_count', 0)
        
        if score > 80 and limit_up > 50:
            return '高'  # 过热
        elif score < 30 or limit_down > 20:
            return '高'  # 恐慌
        elif score > 65 or score < 35:
            return '中'
        else:
            return '低'
    
    def _generate_risk_assessment(self, sentiment: Dict, 
                                   sector_analysis: Dict) -> Dict:
        """生成风险评估"""
        score = sentiment.get('score', 50)
        suggestions = []
        
        if score > 75:
            suggestions.append("市场过热，注意高位回调风险")
            suggestions.append("建议降低仓位至50%以下")
        elif score < 30:
            suggestions.append("市场情绪低迷，谨慎操作")
            suggestions.append("建议观望或轻仓试错")
        else:
            suggestions.append("市场情绪正常，可按策略操作")
        
        if sector_analysis.get('momentum_sectors'):
            suggestions.append("关注动量板块的持续性")
        
        return {
            'market_risk': self._assess_risk_level(sentiment),
            'sector_risk': sector_analysis.get('top_sector', '未知'),
            'suggestions': suggestions
        }
    
    def _generate_action_plan(self, sector_analysis: Dict,
                              stock_picks: Dict[str, pd.DataFrame]) -> Dict:
        """生成行动计划"""
        watchlist = []
        
        # 收集观察股票
        for strategy, picks in stock_picks.items():
            if picks is not None and len(picks) > 0:
                watchlist.extend(picks['code'].tolist()[:3])
        
        # 去重
        watchlist = list(dict.fromkeys(watchlist))[:10]
        
        return {
            'watchlist': watchlist,
            'position_suggestion': '50%',
            'key_events': ['关注北向资金流向', '关注领涨板块持续性']
        }
    
    def _format_amount(self, amount: float) -> str:
        """格式化金额"""
        if amount >= 1e12:
            return f"{amount/1e12:.2f}万亿"
        elif amount >= 1e8:
            return f"{amount/1e8:.2f}亿"
        elif amount >= 1e4:
            return f"{amount/1e4:.2f}万"
        else:
            return f"{amount:.2f}"
    
    def _get_sentiment_color(self, score: float) -> str:
        """根据情绪分数获取颜色"""
        if score >= 70:
            return self.colors['up']
        elif score >= 40:
            return self.colors['highlight']
        else:
            return self.colors['down']


class ReportError(Exception):
    """报告生成异常"""
    pass
