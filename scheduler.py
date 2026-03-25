# -*- coding: utf-8 -*-
"""
定时任务调度模块

每日9:25自动执行盘前分析，留5分钟决策时间
"""
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from main import FundFlowSystem, setup_logging

logger = logging.getLogger(__name__)


class DailyScheduler:
    """
    每日定时任务调度器
    
    支持两种模式:
    1. 实时模式: 每日9:25自动执行，留5分钟决策时间
    2. 立即执行: 立即运行一次分析
    """
    
    def __init__(self):
        """初始化调度器"""
        self.logger = logging.getLogger(__name__)
        self.system = None
        
    def wait_until_925(self):
        """
        等待直到9:25
        
        如果当前时间已经超过9:25，则等到明天的9:25
        """
        now = datetime.now()
        target = now.replace(hour=9, minute=25, second=0, microsecond=0)
        
        if now >= target:
            # 今天已经过了9:25，等到明天
            target = target + timedelta(days=1)
            self.logger.info(f"今日已过9:25，等待到明天9:25执行")
        
        wait_seconds = (target - now).total_seconds()
        wait_minutes = wait_seconds / 60
        
        self.logger.info(f"等待 {wait_minutes:.1f} 分钟直到 {target.strftime('%Y-%m-%d %H:%M')}")
        
        # 每小时输出一次等待日志
        while wait_seconds > 3600:
            time.sleep(3600)
            wait_seconds -= 3600
            self.logger.info(f"还需等待 {wait_seconds/60:.1f} 分钟...")
        
        # 最后等待剩余时间
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        self.logger.info("到达9:25，开始执行分析")
    
    def run_once(self):
        """
        立即执行一次分析
        
        用于手动触发或测试
        """
        self.logger.info("=" * 60)
        self.logger.info("立即执行盘前分析 (模拟9:25模式)")
        self.logger.info("=" * 60)
        
        # 使用实时模式(9:25数据)
        self.system = FundFlowSystem(run_mode=settings.RUN_MODE_LIVE)
        
        result = self.system.run_daily_analysis(save_data=True)
        
        if result['status'] == 'success':
            self.logger.info("✓ 分析执行成功!")
            # 输出关键结论
            sentiment = result.get('sentiment', {})
            self.logger.info(f"  市场情绪: {sentiment.get('sentiment', '未知')} "
                           f"(分数: {sentiment.get('score', 0):.1f})")
            
            stock_picks = result.get('stock_picks', {})
            for strategy, picks in stock_picks.items():
                if picks is not None and len(picks) > 0:
                    self.logger.info(f"  {strategy}: 选出 {len(picks)} 只股票")
        else:
            self.logger.error(f"✗ 分析执行失败: {result.get('error', '未知错误')}")
        
        return result
    
    def run_daily(self):
        """
        每日定时执行
        
        每个交易日9:25自动执行分析
        """
        self.logger.info("=" * 60)
        self.logger.info("启动每日定时任务调度器")
        self.logger.info(f"数据截止时间: 9:{settings.DATA_CUTOFF_MINUTE:02d}")
        self.logger.info(f"决策缓冲时间: {settings.DECISION_BUFFER_MINUTES}分钟")
        self.logger.info("=" * 60)
        
        while True:
            try:
                # 等待到9:25
                self.wait_until_925()
                
                # 检查是否是交易日（简单检查：周一到周五）
                now = datetime.now()
                if now.weekday() >= 5:  # 周六=5, 周日=6
                    self.logger.info("周末休市，跳过执行")
                    # 等待到下周一
                    continue
                
                self.logger.info("开始执行盘前分析...")
                
                # 初始化系统
                self.system = FundFlowSystem(run_mode=settings.RUN_MODE_LIVE)
                
                # 执行分析
                result = self.system.run_daily_analysis(save_data=True)
                
                if result['status'] == 'success':
                    self.logger.info("✓ 分析执行成功!")
                    self.logger.info(f"报告已保存，请在9:30开盘前完成决策")
                else:
                    self.logger.error(f"✗ 分析执行失败: {result.get('error', '未知错误')}")
                
                self.logger.info("-" * 60)
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，退出调度器")
                break
            except Exception as e:
                self.logger.error(f"执行异常: {e}", exc_info=True)
                # 等待5分钟后重试
                self.logger.info("5分钟后重试...")
                time.sleep(300)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='盘前资金流向分析系统 - 定时任务调度器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scheduler.py           # 启动每日9:25定时任务
  python scheduler.py --now     # 立即执行一次
  python scheduler.py --backtest 2024-01-01 2024-03-19 --mode 25
        """
    )
    
    parser.add_argument('--now', action='store_true', 
                       help='立即执行一次分析')
    parser.add_argument('--backtest', nargs=2, metavar=('START', 'END'),
                       help='回测模式，指定开始和结束日期')
    parser.add_argument('--mode', type=str, choices=['25', '30'], default='25',
                       help='回测模式: 25=25分钟实战, 30=30分钟完整')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    scheduler = DailyScheduler()
    
    if args.backtest:
        # 回测模式
        start_date, end_date = args.backtest
        from main import FundFlowSystem
        
        system = FundFlowSystem(run_mode=settings.RUN_MODE_BACKTEST_25 if args.mode == '25' else settings.RUN_MODE_BACKTEST_30)
        result = system.run_backtest(start_date, end_date, mode=args.mode)
        print(f"\n回测结果 [{result['mode']}模式]: {result['success_days']}/{result['total_days']} 天成功")
        
    elif args.now:
        # 立即执行
        scheduler.run_once()
    else:
        # 启动定时任务
        scheduler.run_daily()


if __name__ == '__main__':
    main()
