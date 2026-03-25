#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
"""
import schedule
import time
import threading
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyScheduler:
    """每日定时任务调度器"""
    
    def __init__(self, app_status, data_fetcher, report_generator, db_manager):
        self.app_status = app_status
        self.data_fetcher = data_fetcher
        self.report_generator = report_generator
        self.db_manager = db_manager
        self.running = False
        self.thread = None
    
    def job_daily_push(self):
        """每日推送任务"""
        try:
            logger.info("执行每日推送任务...")
            
            # 检查是否启用
            if not self.app_status.get('daily_push_enabled', False):
                logger.info("每日推送未启用，跳过")
                return
            
            # 获取今日日期
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # 获取数据
            data = self.data_fetcher.fetch_daily_data(date_str)
            if data is None:
                logger.error("数据获取失败")
                return
            
            # 生成报告
            report = self.report_generator.generate_report(data)
            
            # 保存到数据库
            self.db_manager.save_report(report)
            
            # 更新状态
            self.app_status['last_push_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"每日推送完成: {date_str}")
            
            # TODO: 发送到推送渠道（邮件/Telegram等）
            self.send_push_notification(report)
            
        except Exception as e:
            logger.error(f"每日推送任务失败: {e}")
    
    def send_push_notification(self, report: dict):
        """发送推送通知"""
        # 这里可以实现邮件、Telegram等推送
        # 暂时只记录日志
        logger.info("推送通知已发送")
    
    def run_scheduler(self):
        """运行调度器"""
        logger.info("定时任务调度器已启动")
        
        # 设置定时任务：每天9:25执行
        schedule.every().day.at("09:25").do(self.job_daily_push)
        
        while self.running:
            schedule.run_pending()
            time.sleep(30)  # 每30秒检查一次
    
    def start(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        logger.info("调度器线程已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("调度器已停止")


def start_scheduler(app_status, data_fetcher, report_generator, db_manager=None):
    """启动调度器的便捷函数"""
    from database.db_manager import DatabaseManager
    
    if db_manager is None:
        db_manager = DatabaseManager()
    
    scheduler = DailyScheduler(app_status, data_fetcher, report_generator, db_manager)
    scheduler.start()
    
    return scheduler


# 用于测试
if __name__ == '__main__':
    # 测试代码
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from backend.data_fetcher import DataFetcher
    from backend.report_generator import ReportGenerator
    from database.db_manager import DatabaseManager
    
    app_status = {'daily_push_enabled': True}
    data_fetcher = DataFetcher()
    report_generator = ReportGenerator()
    db_manager = DatabaseManager()
    
    scheduler = DailyScheduler(app_status, data_fetcher, report_generator, db_manager)
    
    # 立即执行一次测试
    scheduler.job_daily_push()
