#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = 'database/fund_flow.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 每日报告表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                report_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 回测结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id TEXT UNIQUE NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 系统设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_report(self, report: Dict):
        """保存每日报告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        date = report['date']
        report_json = json.dumps(report, ensure_ascii=False)
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_reports (date, report_data)
            VALUES (?, ?)
        ''', (date, report_json))
        
        conn.commit()
        conn.close()
    
    def get_report(self, date: str) -> Optional[Dict]:
        """获取每日报告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT report_data FROM daily_reports WHERE date = ?', (date,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return json.loads(row['report_data'])
        return None
    
    def save_backtest_result(self, result: Dict):
        """保存回测结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result_id = f"{result['start_date']}_{result['end_date']}"
        result_json = json.dumps(result, ensure_ascii=False)
        
        cursor.execute('''
            INSERT OR REPLACE INTO backtest_results 
            (result_id, start_date, end_date, result_data)
            VALUES (?, ?, ?, ?)
        ''', (result_id, result['start_date'], result['end_date'], result_json))
        
        conn.commit()
        conn.close()
    
    def get_backtest_result(self, result_id: str) -> Optional[Dict]:
        """获取回测结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT result_data FROM backtest_results WHERE result_id = ?', (result_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return json.loads(row['result_data'])
        return None
    
    def get_backtest_results(self) -> List[Dict]:
        """获取所有回测结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT result_id, start_date, end_date, created_at 
            FROM backtest_results 
            ORDER BY created_at DESC
        ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['result_id'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return results
    
    def save_settings(self, settings: Dict):
        """保存设置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value in settings.items():
            value_json = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value_json))
        
        conn.commit()
        conn.close()
    
    def get_settings(self) -> Dict:
        """获取所有设置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM settings')
        
        settings = {}
        for row in cursor.fetchall():
            try:
                settings[row['key']] = json.loads(row['value'])
            except:
                settings[row['key']] = row['value']
        
        conn.close()
        return settings
    
    def delete_backtest_result(self, result_id: str) -> bool:
        """删除回测结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM backtest_results WHERE result_id = ?', (result_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except Exception as e:
            conn.close()
            print(f"删除回测结果失败: {e}")
            return False
