# -*- coding: utf-8 -*-
"""
全局配置模块

包含系统配置、路径设置、算法参数等
"""
import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Settings:
    """系统配置类"""
    
    # 项目根目录
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    
    # 数据目录
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    DB_PATH: Path = DATA_DIR / "market_data.db"
    
    # 报告目录
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    DAILY_REPORTS_DIR: Path = REPORTS_DIR / "daily"
    ARCHIVE_DIR: Path = REPORTS_DIR / "archive"
    
    # 日志目录
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # AKShare配置
    AKSHARE_TIMEOUT: int = 60  # API调用超时时间(秒)
    MAX_RETRIES: int = 3  # 最大重试次数
    RETRY_DELAY: float = 1.0  # 重试间隔(秒)
    
    # 数据库配置
    DB_ECHO: bool = False  # 是否打印SQL语句
    
    # 报告生成时间 (每日) - 实时交易模式
    REPORT_HOUR: int = 9
    REPORT_MINUTE: int = 25  # 9:25拉取数据，集合竞价结束，留5分钟决策时间
    
    # 数据获取截止配置
    DATA_CUTOFF_MINUTE: int = 25  # 数据截止分钟数 (25 = 9:25，集合竞价结束)
    DECISION_BUFFER_MINUTES: int = 5  # 决策缓冲时间(分钟)
    
    # 运行模式
    RUN_MODE_LIVE: str = "live"       # 实时模式 - 固定25分钟
    RUN_MODE_BACKTEST_25: str = "backtest_25"  # 回测25分钟
    RUN_MODE_BACKTEST_30: str = "backtest_30"  # 回测30分钟(完整)
    
    # 板块强度计算权重 (总分100)
    SECTOR_WEIGHTS: Dict[str, float] = None
    
    # 选股策略参数
    MOMENTUM_MIN_CHANGE: float = 2.0   # 动量策略最小涨幅(%)
    MOMENTUM_MAX_CHANGE: float = 7.0   # 动量策略最大涨幅(%)
    MOMENTUM_MIN_VOLUME_RATIO: float = 1.5  # 最小量比
    MOMENTUM_MIN_AMOUNT: float = 3e8   # 最小成交额(元)
    
    REVERSAL_MIN_CHANGE: float = -7.0  # 反转策略最小跌幅(%)
    REVERSAL_MAX_CHANGE: float = -3.0  # 反转策略最大跌幅(%)
    REVERSAL_MIN_VOLUME_RATIO: float = 2.0  # 最小量比
    
    # 重点监控板块 (代码: 名称)
    FOCUS_SECTORS: Dict[str, str] = None
    
    # 可视化配色方案
    COLORS: Dict[str, str] = None
    
    # 图表尺寸
    FIGURE_SIZE: tuple = (12, 8)
    DPI: int = 100
    
    def __post_init__(self):
        """初始化后处理"""
        # 创建必要的目录
        for dir_path in [
            self.DATA_DIR, self.RAW_DATA_DIR, self.PROCESSED_DATA_DIR,
            self.REPORTS_DIR, self.DAILY_REPORTS_DIR, self.ARCHIVE_DIR,
            self.LOGS_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化权重配置
        if self.SECTOR_WEIGHTS is None:
            self.SECTOR_WEIGHTS = {
                'change_pct': 0.25,        # 涨跌幅
                'fund_flow_ratio': 0.25,   # 资金流入占比
                'contribution': 0.25,      # 板块贡献度
                'leader_performance': 0.25 # 龙头表现
            }
        
        # 初始化重点板块
        if self.FOCUS_SECTORS is None:
            self.FOCUS_SECTORS = {
                'BK0428': 'AI算力',
                'BK0800': '机器人',
                'BK0493': '新能源汽车',
                'BK0479': '芯片',
                'BK0484': '人工智能',
                'BK0731': '储能',
                'BK0919': 'ChatGPT',
                'BK1060': '低空经济',
            }
        
        # 初始化配色方案
        if self.COLORS is None:
            self.COLORS = {
                'up': '#E74C3C',           # 红色 - 上涨
                'down': '#27AE60',         # 绿色 - 下跌
                'neutral': '#95A5A6',      # 灰色 - 中性
                'highlight': '#F39C12',    # 橙色 - 重点
                'primary': '#3498DB',      # 蓝色 - 主色
                'background': '#FFFFFF',   # 白色背景
                'grid': '#ECF0F1',         # 网格线
            }


# 全局配置实例
settings = Settings()
