#!/usr/bin/env python3
import sqlite3
import os

db_path = 'data/market_data.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    # 检查market_cache
    if any(t[0] == 'market_cache' for t in tables):
        cursor.execute('SELECT date FROM market_cache ORDER BY date DESC LIMIT 10')
        rows = cursor.fetchall()
        print('\nCached dates:')
        for row in rows:
            print(f'  {row[0]}')
    
    conn.close()
else:
    print('Database not found')
