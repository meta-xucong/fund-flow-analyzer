# -*- coding: utf-8 -*-
"""
盘前资金流向分析系统 - 主入口

每日自动执行数据采集、分析和报告生成
"""
import logging
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from core.fetcher import DataFetcher
from core.storage import DataStorage
from core.analyzer import MarketAnalyzer, SectorStrengthCalculator
from core.selector import StrategySelector
from core.report_generator import ReportGenerator


def setup_logging():
    """配置日志系统"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    # 文件处理器
    log_file = settings.LOGS_DIR / f"{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # 根日志配置
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        format=log_format
    )
    
    return logging.getLogger(__name__)


class FundFlowSystem:
    """
    盘前资金流向分析系统主类
    
    协调各模块完成每日分析任务
    """
    
    def __init__(self):
        """初始化系统"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("盘前资金流向分析系统初始化...")
        
        # 初始化各模块
        self.fetcher = DataFetcher()
        self.storage = DataStorage()
        self.analyzer = MarketAnalyzer()
        self.selector = StrategySelector()
        self.report_generator = ReportGenerator()
        self.sector_calculator = SectorStrengthCalculator()
        
        self.logger.info("系统初始化完成")
        self.logger.info("=" * 60)
    
    def run_daily_analysis(self, date: str = None, save_data: bool = True) -> dict:
        """
        执行每日分析
        
        Args:
            date: 分析日期 (YYYY-MM-DD)，默认今天
            save_data: 是否保存数据到数据库
            
        Returns:
            分析结果字典
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"开始执行每日分析: {date}")
        self.logger.info(f"{'='*60}\n")
        
        try:
            # ========== 1. 数据采集 ==========
            self.logger.info("【1/5】数据采集...")
            market_data = self.fetcher.fetch_market_spot()
            sector_list = self.fetcher.fetch_sector_list()
            northbound_data = self.fetcher.fetch_northbound_flow(days=5)
            
            if market_data is None or len(market_data) == 0:
                raise RuntimeError("获取市场数据失败")
            
            self.logger.info(f"✓ 市场数据: {len(market_data)} 只股票")
            if sector_list is not None:
                self.logger.info(f"✓ 板块数据: {len(sector_list)} 个板块")
            
            # ========== 2. 数据存储 ==========
            if save_data:
                self.logger.info("\n【2/5】数据存储...")
                
                # 保存市场概况
                self.storage.save_market_overview(market_data, date)
                
                # 保存个股数据
                self.storage.save_stock_data(market_data, date)
                
                # 保存板块数据 (先计算强度)
                if sector_list is not None and len(sector_list) > 0:
                    sector_with_score = self.sector_calculator.calculate(sector_list)
                    self.storage.save_sector_data(sector_with_score, date)
                
                # 保存北向资金
                if northbound_data is not None:
                    self.storage.save_northbound_flow(northbound_data)
                
                self.logger.info("✓ 数据存储完成")
            
            # ========== 3. 市场分析 ==========
            self.logger.info("\n【3/5】市场分析...")
            
            # 情绪分析
            sentiment = self.analyzer.analyze_market_sentiment(market_data)
            self.logger.info(f"✓ 市场情绪: {sentiment['sentiment']} (分数: {sentiment['score']:.1f})")
            
            # 板块分析
            sector_analysis = self.analyzer.analyze_sector_rotation(
                sector_list if sector_list is not None else pd.DataFrame()
            )
            self.logger.info(f"✓ 热点板块: {sector_analysis.get('top_sector', '未知')}")
            
            # 量能分析
            volume_analysis = self.analyzer.analyze_volume(market_data)
            self.logger.info(f"✓ 量能状态: {volume_analysis.get('volume_assessment', '未知')}")
            
            # ========== 4. 选股策略 ==========
            self.logger.info("\n【4/5】执行选股策略...")
            
            stock_picks = self.selector.execute_all(market_data, top_n=10)
            
            for strategy_name, picks in stock_picks.items():
                count = len(picks) if picks is not None else 0
                self.logger.info(f"✓ {strategy_name}: 选出 {count} 只股票")
                
                # 保存选股结果
                if save_data and picks is not None and len(picks) > 0:
                    self.storage.save_stock_picks(picks, strategy_name, date)
            
            # ========== 5. 报告生成 ==========
            self.logger.info("\n【5/5】生成报告...")
            
            # 准备板块数据 (已计算强度)
            if sector_list is not None:
                sector_data_scored = self.sector_calculator.calculate(sector_list)
            else:
                sector_data_scored = pd.DataFrame()
            
            # 生成完整报告
            report_data = self.report_generator.generate_full_report(
                market_data=market_data,
                sector_data=sector_data_scored,
                stock_picks=stock_picks,
                sentiment_analysis=sentiment,
                sector_analysis=sector_analysis,
                volume_analysis=volume_analysis,
                date=date
            )
            
            # 保存报告
            saved_files = self.report_generator.save_report(report_data, date)
            
            self.logger.info(f"✓ 报告已保存:")
            for file_type, file_path in saved_files.items():
                self.logger.info(f"  - {file_type}: {file_path}")
            
            # 输出文本报告摘要
            text_report = self.report_generator.generate_text_report(report_data)
            print("\n" + "="*80)
            print(text_report)
            print("="*80 + "\n")
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"每日分析完成: {date}")
            self.logger.info(f"{'='*60}\n")
            
            return {
                'status': 'success',
                'date': date,
                'sentiment': sentiment,
                'stock_picks': stock_picks,
                'saved_files': {k: str(v) for k, v in saved_files.items()},
                'report_data': report_data
            }
            
        except Exception as e:
            self.logger.error(f"分析执行失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'date': date,
                'error': str(e)
            }
    
    def run_backtest(self, start_date: str, end_date: str) -> dict:
        """
        执行回测
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            回测结果
        """
        self.logger.info(f"开始回测: {start_date} 至 {end_date}")
        
        # 生成日期列表
        dates = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            # 跳过周末
            if current.weekday() < 5:  # 0-4 是周一到周五
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        self.logger.info(f"回测日期: {len(dates)} 个交易日")
        
        results = []
        for date in dates:
            result = self.run_daily_analysis(date, save_data=True)
            results.append(result)
        
        # 汇总回测结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        self.logger.info(f"\n回测完成: {success_count}/{len(dates)} 天成功")
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': len(dates),
            'success_days': success_count,
            'results': results
        }
    
    def query_historical_report(self, date: str) -> dict:
        """
        查询历史报告
        
        Args:
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            历史报告数据
        """
        self.logger.info(f"查询历史报告: {date}")
        
        # 从数据库查询
        market_overview = self.storage.query_market_overview(date, date)
        sector_data = self.storage.query_sector_data(date)
        stock_picks = self.storage.query_stock_picks(date)
        
        return {
            'date': date,
            'market_overview': market_overview.to_dict('records') if len(market_overview) > 0 else [],
            'sector_data': sector_data.to_dict('records') if len(sector_data) > 0 else [],
            'stock_picks': stock_picks.to_dict('records') if len(stock_picks) > 0 else []
        }
    
    def get_latest_report(self) -> dict:
        """获取最新报告"""
        latest_date = self.storage.get_latest_date('market_overview')
        if latest_date:
            return self.query_historical_report(latest_date)
        return {'error': '无历史数据'}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='盘前资金流向分析系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 执行今日分析
  python main.py --date 2024-03-19  # 执行指定日期分析
  python main.py --backtest 2024-01-01 2024-03-19  # 回测
  python main.py --query 2024-03-19 # 查询历史报告
        """
    )
    
    parser.add_argument('--date', type=str, help='分析日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--backtest', nargs=2, metavar=('START', 'END'), 
                       help='回测模式，指定开始和结束日期')
    parser.add_argument('--query', type=str, help='查询历史报告日期 (YYYY-MM-DD)')
    parser.add_argument('--latest', action='store_true', help='查看最新报告')
    parser.add_argument('--no-save', action='store_true', help='不保存数据到数据库')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 初始化系统
    system = FundFlowSystem()
    
    # 执行命令
    if args.backtest:
        # 回测模式
        start_date, end_date = args.backtest
        result = system.run_backtest(start_date, end_date)
        print(f"\n回测结果: {result['success_days']}/{result['total_days']} 天成功")
        
    elif args.query:
        # 查询模式
        result = system.query_historical_report(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        
    elif args.latest:
        # 查看最新
        result = system.get_latest_report()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        
    else:
        # 日常分析模式
        result = system.run_daily_analysis(
            date=args.date,
            save_data=not args.no_save
        )
        
        if result['status'] == 'success':
            print("\n✓ 分析执行成功!")
        else:
            print(f"\n✗ 分析执行失败: {result.get('error', '未知错误')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
