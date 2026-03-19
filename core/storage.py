# -*- coding: utf-8 -*-
"""
数据存储模块

提供SQLite数据库操作，支持数据存储和查询
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

from config.settings import settings

logger = logging.getLogger(__name__)


class DataStorage:
    """
    数据存储管理器
    
    封装SQLite数据库操作，提供数据持久化功能
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化存储管理器
        
        Args:
            db_path: 数据库文件路径，默认使用配置路径
        """
        self.db_path = db_path or settings.DB_PATH
        self.engine = None
        self._init_engine()
        self._init_tables()
    
    def _init_engine(self):
        """初始化数据库引擎"""
        try:
            connection_string = f"sqlite:///{self.db_path}"
            self.engine = create_engine(
                connection_string,
                echo=settings.DB_ECHO,
                pool_pre_ping=True,  # 连接健康检查
                pool_recycle=3600,   # 连接回收时间
            )
            logger.info(f"数据库引擎初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise StorageError(f"数据库引擎初始化失败: {e}")
    
    def _init_tables(self):
        """初始化数据表结构"""
        try:
            with self.engine.connect() as conn:
                # 市场概况表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS market_overview (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_stocks INTEGER,
                        up_count INTEGER,
                        down_count INTEGER,
                        limit_up_count INTEGER,
                        limit_down_count INTEGER,
                        total_amount REAL,
                        sentiment_score REAL,
                        northbound_net REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                """))
                
                # 板块数据表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS sector_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        sector_code VARCHAR(20) NOT NULL,
                        sector_name VARCHAR(50),
                        change_pct REAL,
                        amount REAL,
                        main_inflow REAL,
                        main_inflow_ratio REAL,
                        up_count INTEGER,
                        down_count INTEGER,
                        leader_stock VARCHAR(20),
                        leader_change_pct REAL,
                        strength_score REAL,
                        fetch_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date, sector_code)
                    )
                """))
                
                # 个股数据表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stock_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        code VARCHAR(20) NOT NULL,
                        name VARCHAR(50),
                        sector_codes TEXT,
                        latest_price REAL,
                        change_pct REAL,
                        change_amount REAL,
                        volume REAL,
                        amount REAL,
                        volume_ratio REAL,
                        turnover REAL,
                        amplitude REAL,
                        high REAL,
                        low REAL,
                        open_price REAL,
                        pre_close REAL,
                        pe_dynamic REAL,
                        pb REAL,
                        total_market_cap REAL,
                        float_market_cap REAL,
                        main_inflow_1d REAL,
                        main_inflow_5d REAL,
                        main_inflow_10d REAL,
                        fetch_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date, code)
                    )
                """))
                
                # 资金流向明细表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS fund_flow_detail (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        code VARCHAR(20) NOT NULL,
                        name VARCHAR(50),
                        main_inflow REAL,
                        main_inflow_ratio REAL,
                        super_large_inflow REAL,
                        large_inflow REAL,
                        medium_inflow REAL,
                        small_inflow REAL,
                        fetch_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date, code)
                    )
                """))
                
                # 选股结果表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stock_picks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        strategy VARCHAR(20) NOT NULL,
                        code VARCHAR(20) NOT NULL,
                        name VARCHAR(50),
                        score REAL,
                        rank INTEGER,
                        reason TEXT,
                        change_pct REAL,
                        volume_ratio REAL,
                        amount REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date, strategy, code)
                    )
                """))
                
                # 北向资金流向表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS northbound_flow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        daily_inflow REAL,
                        daily_balance REAL,
                        cumulative_inflow REAL,
                        net_buy REAL,
                        buy_amount REAL,
                        sell_amount REAL,
                        sh_daily_inflow REAL,
                        sh_cumulative REAL,
                        sz_daily_inflow REAL,
                        sz_cumulative REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                """))
                
                # 创建索引
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_sector_data_date 
                    ON sector_data(date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_stock_data_date 
                    ON stock_data(date)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_stock_picks_date 
                    ON stock_picks(date, strategy)
                """))
                
                conn.commit()
                logger.info("数据表初始化完成")
                
        except SQLAlchemyError as e:
            logger.error(f"初始化数据表失败: {e}")
            raise StorageError(f"初始化数据表失败: {e}")
    
    def save_market_overview(self, data: pd.DataFrame, date: Optional[str] = None) -> bool:
        """
        保存市场概况数据
        
        Args:
            data: 市场概况DataFrame
            date: 数据日期，默认今天
            
        Returns:
            是否保存成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 计算市场统计
            total_stocks = len(data)
            up_count = len(data[data['change_pct'] > 0])
            down_count = len(data[data['change_pct'] < 0])
            limit_up_count = len(data[data['change_pct'] >= 9.5])
            limit_down_count = len(data[data['change_pct'] <= -9.5])
            total_amount = data['amount'].sum() if 'amount' in data.columns else 0
            
            # 计算情绪分数 (0-100)
            if total_stocks > 0:
                sentiment_score = (up_count / total_stocks) * 100
            else:
                sentiment_score = 50.0
            
            # 保存到数据库
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT OR REPLACE INTO market_overview 
                    (date, total_stocks, up_count, down_count, 
                     limit_up_count, limit_down_count, total_amount, sentiment_score)
                    VALUES (:date, :total_stocks, :up_count, :down_count,
                            :limit_up_count, :limit_down_count, :total_amount, :sentiment_score)
                """), {
                    'date': date,
                    'total_stocks': total_stocks,
                    'up_count': up_count,
                    'down_count': down_count,
                    'limit_up_count': limit_up_count,
                    'limit_down_count': limit_down_count,
                    'total_amount': float(total_amount),
                    'sentiment_score': float(sentiment_score)
                })
                conn.commit()
            
            logger.info(f"市场概况数据已保存: {date}")
            return True
            
        except Exception as e:
            logger.error(f"保存市场概况数据失败: {e}")
            return False
    
    def save_sector_data(self, data: pd.DataFrame, date: Optional[str] = None) -> bool:
        """
        保存板块数据
        
        Args:
            data: 板块数据DataFrame
            date: 数据日期，默认今天
            
        Returns:
            是否保存成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 添加日期列
            data = data.copy()
            data['date'] = date
            
            # 选择需要的列
            columns = [
                'date', 'sector_code', 'sector_name', 'change_pct', 'amount',
                'main_inflow', 'main_inflow_ratio', 'up_count', 'down_count',
                'leader_stock', 'leader_change_pct', 'strength_score', 'fetch_time'
            ]
            
            # 只保留存在的列
            existing_columns = [c for c in columns if c in data.columns]
            df_to_save = data[existing_columns]
            
            # 保存到数据库
            df_to_save.to_sql(
                'sector_data',
                self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"板块数据已保存: {date}, 共 {len(df_to_save)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存板块数据失败: {e}")
            return False
    
    def save_stock_data(self, data: pd.DataFrame, date: Optional[str] = None) -> bool:
        """
        保存个股数据
        
        Args:
            data: 个股数据DataFrame
            date: 数据日期，默认今天
            
        Returns:
            是否保存成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 添加日期列
            data = data.copy()
            data['date'] = date
            
            # 列名映射
            column_mapping = {
                'open': 'open_price',
            }
            data = data.rename(columns=column_mapping)
            
            # 保存到数据库
            data.to_sql(
                'stock_data',
                self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"个股数据已保存: {date}, 共 {len(data)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存个股数据失败: {e}")
            return False
    
    def save_stock_picks(self, data: pd.DataFrame, strategy: str, 
                         date: Optional[str] = None) -> bool:
        """
        保存选股结果
        
        Args:
            data: 选股结果DataFrame
            strategy: 策略名称
            date: 数据日期，默认今天
            
        Returns:
            是否保存成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 添加元数据
            data = data.copy()
            data['date'] = date
            data['strategy'] = strategy
            data['rank'] = range(1, len(data) + 1)
            
            # 保存到数据库
            data.to_sql(
                'stock_picks',
                self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"选股结果已保存: {date} {strategy}, 共 {len(data)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存选股结果失败: {e}")
            return False
    
    def save_northbound_flow(self, data: pd.DataFrame) -> bool:
        """
        保存北向资金流向
        
        Args:
            data: 北向资金DataFrame
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到数据库
            data.to_sql(
                'northbound_flow',
                self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"北向资金流向已保存: 共 {len(data)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存北向资金流向失败: {e}")
            return False
    
    def query_market_overview(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        查询市场概况历史数据
        
        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            市场概况DataFrame
        """
        query = """
            SELECT * FROM market_overview 
            WHERE date BETWEEN :start_date AND :end_date
            ORDER BY date DESC
        """
        
        with self.engine.connect() as conn:
            result = pd.read_sql_query(
                text(query),
                conn,
                params={'start_date': start_date, 'end_date': end_date}
            )
        
        return result
    
    def query_sector_data(self, date: str, limit: int = 50) -> pd.DataFrame:
        """
        查询板块数据
        
        Args:
            date: 日期 YYYY-MM-DD
            limit: 返回数量限制
            
        Returns:
            板块数据DataFrame
        """
        query = """
            SELECT * FROM sector_data 
            WHERE date = :date
            ORDER BY strength_score DESC
            LIMIT :limit
        """
        
        with self.engine.connect() as conn:
            result = pd.read_sql_query(
                text(query),
                conn,
                params={'date': date, 'limit': limit}
            )
        
        return result
    
    def query_stock_picks(self, date: str, strategy: Optional[str] = None) -> pd.DataFrame:
        """
        查询选股结果
        
        Args:
            date: 日期 YYYY-MM-DD
            strategy: 策略名称，默认为None查询所有
            
        Returns:
            选股结果DataFrame
        """
        if strategy:
            query = """
                SELECT * FROM stock_picks 
                WHERE date = :date AND strategy = :strategy
                ORDER BY rank
            """
            params = {'date': date, 'strategy': strategy}
        else:
            query = """
                SELECT * FROM stock_picks 
                WHERE date = :date
                ORDER BY strategy, rank
            """
            params = {'date': date}
        
        with self.engine.connect() as conn:
            result = pd.read_sql_query(text(query), conn, params=params)
        
        return result
    
    def get_latest_date(self, table: str) -> Optional[str]:
        """
        获取某表最新数据日期
        
        Args:
            table: 表名
            
        Returns:
            最新日期字符串，无数据返回None
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT MAX(date) as latest_date FROM {table}")
                ).fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"获取最新日期失败: {e}")
            return None
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        执行自定义SQL查询
        
        Args:
            query: SQL语句
            params: 查询参数
            
        Returns:
            查询结果DataFrame
        """
        with self.engine.connect() as conn:
            result = pd.read_sql_query(text(query), conn, params=params or {})
        return result


class StorageError(Exception):
    """存储异常"""
    pass
