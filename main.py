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
    支持盘前数据截止时间控制 (默认9:25)
    """
    
    def __init__(self, run_mode: str = None, cutoff_minute: int = None):
        """
        初始化系统
        
        Args:
            run_mode: 运行模式 (live/backtest_25/backtest_30)
            cutoff_minute: 数据截止分钟数，None则根据模式自动选择
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("盘前资金流向分析系统初始化...")
        
        # 设置运行模式
        self.run_mode = run_mode or settings.RUN_MODE_LIVE
        
        # 根据模式确定数据截止时间
        if cutoff_minute is None:
            if self.run_mode == settings.RUN_MODE_BACKTEST_30:
                # 回测30分钟模式 - 使用完整数据(收盘价)
                self.cutoff_minute = 30
                self.use_open_price = False
            else:
                # 实时模式或回测25分钟模式 - 使用9:25数据
                self.cutoff_minute = settings.DATA_CUTOFF_MINUTE
                self.use_open_price = (self.run_mode == settings.RUN_MODE_BACKTEST_25)
        else:
            self.cutoff_minute = cutoff_minute
            self.use_open_price = False
        
        self.logger.info(f"运行模式: {self.run_mode}")
        self.logger.info(f"数据截止时间: 09:{self.cutoff_minute:02d}")
        if self.use_open_price:
            self.logger.info("回测模式: 使用开盘价模拟9:25数据")
        
        # 初始化各模块
        self.fetcher = DataFetcher(cutoff_minute=self.cutoff_minute)
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
            market_data = self.fetcher.fetch_market_spot(use_open_price=self.use_open_price)
            sector_list = self.fetcher.fetch_sector_list()
            northbound_data = self.fetcher.fetch_northbound_flow(days=5)
            
            if market_data is None or len(market_data) == 0:
                raise RuntimeError("获取市场数据失败")
            
            self.logger.info(f"[OK] 市场数据: {len(market_data)} 只股票")
            if sector_list is not None:
                self.logger.info(f"[OK] 板块数据: {len(sector_list)} 个板块")
            
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
                
                self.logger.info("[OK] 数据存储完成")
            
            # ========== 3. 市场分析 ==========
            self.logger.info("\n【3/5】市场分析...")
            
            # 情绪分析
            sentiment = self.analyzer.analyze_market_sentiment(market_data)
            self.logger.info(f"[OK] 市场情绪: {sentiment['sentiment']} (分数: {sentiment['score']:.1f})")
            
            # 板块分析
            if sector_list is not None and len(sector_list) > 0:
                sector_analysis = self.analyzer.analyze_sector_rotation(sector_list)
                self.logger.info(f"[OK] 热点板块: {sector_analysis.get('top_sector', '未知')}")
            else:
                self.logger.warning("[WARN] 板块数据为空，跳过板块分析")
                sector_analysis = {'top_sector': '未知', 'strong_sectors': [], 'focus_recommendation': '暂无'}
            
            # 量能分析
            volume_analysis = self.analyzer.analyze_volume(market_data)
            self.logger.info(f"[OK] 量能状态: {volume_analysis.get('volume_assessment', '未知')}")
            
            # ========== 4. 选股策略 ==========
            self.logger.info("\n【4/5】执行选股策略...")
            
            stock_picks = self.selector.execute_all(market_data, top_n=10)
            
            for strategy_name, picks in stock_picks.items():
                count = len(picks) if picks is not None else 0
                self.logger.info(f"[OK] {strategy_name}: 选出 {count} 只股票")
                
                # 保存选股结果
                if save_data and picks is not None and len(picks) > 0:
                    self.storage.save_stock_picks(picks, strategy_name, date)
            
            # ========== 5. 报告生成 ==========
            self.logger.info("\n【5/5】生成报告...")
            
            # 准备板块数据 (已计算强度)
            if sector_list is not None and len(sector_list) > 0:
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
            
            self.logger.info(f"[OK] 报告已保存:")
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
    
    def run_backtest(self, start_date: str, end_date: str, mode: str = None) -> dict:
        """
        执行回测
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            mode: 回测模式 (25/30)，默认使用当前系统设置
            
        Returns:
            回测结果
        """
        # 确定回测模式
        if mode == '30':
            backtest_mode = settings.RUN_MODE_BACKTEST_30
            self.logger.info(f"开始回测 [30分钟完整数据模式]: {start_date} 至 {end_date}")
        elif mode == '25':
            backtest_mode = settings.RUN_MODE_BACKTEST_25
            self.logger.info(f"开始回测 [25分钟实战模式]: {start_date} 至 {end_date}")
        else:
            backtest_mode = self.run_mode
            self.logger.info(f"开始回测 [{backtest_mode}模式]: {start_date} 至 {end_date}")
        
        # 临时切换模式用于回测
        original_mode = self.run_mode
        original_cutoff = self.cutoff_minute
        original_use_open = self.use_open_price
        
        if mode == '27':
            self.run_mode = settings.RUN_MODE_BACKTEST_25
            self.cutoff_minute = 27
            self.use_open_price = True
            self.fetcher.cutoff_minute = 27
        elif mode == '30':
            self.run_mode = settings.RUN_MODE_BACKTEST_30
            self.cutoff_minute = 30
            self.use_open_price = False
            self.fetcher.cutoff_minute = 30
        
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
        self.logger.info(f"数据截止时间: 09:{self.cutoff_minute:02d}")
        
        results = []
        for date in dates:
            result = self.run_daily_analysis(date, save_data=True)
            results.append(result)
        
        # 恢复原始模式
        self.run_mode = original_mode
        self.cutoff_minute = original_cutoff
        self.use_open_price = original_use_open
        self.fetcher.cutoff_minute = original_cutoff
        
        # 汇总回测结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        self.logger.info(f"\n回测完成 [{mode or 'current'}模式]: {success_count}/{len(dates)} 天成功")
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'mode': mode or 'current',
            'cutoff_minute': self.cutoff_minute,
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
        description='盘前资金流向分析系统 - 支持9:25数据截止时间',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 实时交易模式 (默认9:25拉取数据，留5分钟决策)
  python main.py
  
  # 回测模式 - 25分钟实战数据 (开盘价模拟9:25)
  python main.py --backtest 2024-01-01 2024-03-19 --mode 25
  
  # 回测模式 - 30分钟完整数据 (收盘价)
  python main.py --backtest 2024-01-01 2024-03-19 --mode 30
  
  # 其他操作
  python main.py --date 2024-03-19          # 指定日期分析
  python main.py --query 2024-03-19         # 查询历史报告
  python main.py --latest                   # 查看最新报告
  python main.py --cutoff 25                # 自定义截止时间(9:25)
        """
    )
    
    parser.add_argument('--date', type=str, help='分析日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--backtest', nargs=2, metavar=('START', 'END'), 
                       help='回测模式，指定开始和结束日期')
    parser.add_argument('--mode', type=str, choices=['live', '25', '30'],
                       help='运行模式: live=实时(9:25), 25=回测25分钟, 30=回测30分钟')
    parser.add_argument('--cutoff', type=int, default=None,
                       help='数据截止分钟数 (默认25，即9:25)')
    parser.add_argument('--query', type=str, help='查询历史报告日期 (YYYY-MM-DD)')
    parser.add_argument('--latest', action='store_true', help='查看最新报告')
    parser.add_argument('--no-save', action='store_true', help='不保存数据到数据库')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 确定运行模式
    run_mode = settings.RUN_MODE_LIVE  # 默认实时模式
    if args.mode == '27':
        run_mode = settings.RUN_MODE_BACKTEST_25
    elif args.mode == '30':
        run_mode = settings.RUN_MODE_BACKTEST_30
    elif args.mode == 'live':
        run_mode = settings.RUN_MODE_LIVE
    
    # 初始化系统
    system = FundFlowSystem(run_mode=run_mode, cutoff_minute=args.cutoff)
    
    # 执行命令
    if args.backtest:
        # 回测模式
        start_date, end_date = args.backtest
        # 根据--mode参数确定回测模式，默认25
        backtest_mode = args.mode if args.mode in ['25', '30'] else '25'
        result = system.run_backtest(start_date, end_date, mode=backtest_mode)
        print(f"\n回测结果 [{result['mode']}模式]: {result['success_days']}/{result['total_days']} 天成功")
        
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
            print("\n[OK] 分析执行成功!")
        else:
            print(f"\n[ERROR] 分析执行失败: {result.get('error', '未知错误')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
