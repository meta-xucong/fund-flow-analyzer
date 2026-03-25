#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有模块是否能正常导入"""
    print("测试模块导入...")
    
    try:
        from backend.data_fetcher import DataFetcher
        print("[OK] data_fetcher 导入成功")
    except Exception as e:
        print(f"[FAIL] data_fetcher 导入失败: {e}")
        return False
    
    try:
        from backend.report_generator import ReportGenerator
        print("[OK] report_generator 导入成功")
    except Exception as e:
        print(f"[FAIL] report_generator 导入失败: {e}")
        return False
    
    try:
        from backend.backtest_engine import BacktestEngine
        print("[OK] backtest_engine 导入成功")
    except Exception as e:
        print(f"[FAIL] backtest_engine 导入失败: {e}")
        return False
    
    try:
        from database.db_manager import DatabaseManager
        print("[OK] db_manager 导入成功")
    except Exception as e:
        print(f"[FAIL] db_manager 导入失败: {e}")
        return False
    
    try:
        from scheduler.daily_scheduler import DailyScheduler
        print("[OK] daily_scheduler 导入成功")
    except Exception as e:
        print(f"[FAIL] daily_scheduler 导入失败: {e}")
        return False
    
    return True


def test_data_fetcher():
    """测试数据获取"""
    print("\n测试数据获取...")
    
    try:
        from backend.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        # 测试获取股票列表
        stocks = fetcher.get_stock_list()
        print(f"[OK] 获取股票列表成功: {len(stocks)} 只")
        
        # 测试获取板块数据
        sectors = fetcher.stock_sector_spot_fixed() if hasattr(fetcher, 'stock_sector_spot_fixed') else None
        if sectors is None:
            import akshare as ak
            sectors = ak.stock_sector_spot()
        
        if sectors is not None:
            print(f"✓ 获取板块数据成功: {len(sectors)} 个板块")
        
        return True
    except Exception as e:
        print(f"[FAIL] 数据获取测试失败: {e}")
        return False


def test_database():
    """测试数据库"""
    print("\n测试数据库...")
    
    try:
        from database.db_manager import DatabaseManager
        db = DatabaseManager(db_path='database/test.db')
        
        # 测试保存和读取
        test_data = {'test': 'data', 'number': 123}
        db.save_settings({'test_key': test_data})
        
        settings = db.get_settings()
        if 'test_key' in settings:
            print("[OK] 数据库读写成功")
        else:
            print("[FAIL] 数据库读写失败")
            return False
        
        # 清理测试数据库
        import os
        if os.path.exists('database/test.db'):
            os.remove('database/test.db')
        
        return True
    except Exception as e:
        print(f"[FAIL] 数据库测试失败: {e}")
        return False


def test_report_generator():
    """测试报告生成"""
    print("\n测试报告生成...")
    
    try:
        from backend.report_generator import ReportGenerator
        from backend.data_fetcher import DataFetcher
        
        generator = ReportGenerator()
        fetcher = DataFetcher()
        
        # 使用测试数据
        import pandas as pd
        import numpy as np
        
        # 创建模拟数据
        stocks_df = pd.DataFrame({
            'code': ['000001', '000002', '600000'],
            'name': ['平安银行', '万科A', '浦发银行'],
            'change_pct': [3.5, -4.2, 5.1],
            'volume_ratio': [2.5, 3.0, 1.8],
            'amount': [50000, 80000, 60000],
            'open': [10.0, 15.0, 8.0],
            'latest': [10.35, 14.37, 8.41],
            'pre_close': [10.0, 15.0, 8.0]
        })
        
        sentiment = {
            'score': 55.5,
            'status': '中性偏乐观',
            'up_count': 1500,
            'down_count': 800,
            'up_ratio': 0.65,
            'limit_up': 50,
            'limit_down': 5,
            'avg_change': 0.85
        }
        
        sectors_df = pd.DataFrame({
            '板块': ['电力', '银行', '科技'],
            '涨跌幅': [2.5, 1.8, -0.5]
        })
        
        data = {
            'stocks': stocks_df,
            'sectors': sectors_df,
            'sentiment': sentiment,
            'date': '2025-02-05'
        }
        
        report = generator.generate_report(data)
        
        if report and 'sentiment' in report:
            print("[OK] 报告生成成功")
            print(f"  - 动量选股: {len(report['momentum_picks'])} 只")
            print(f"  - 反转选股: {len(report['reversal_picks'])} 只")
            return True
        else:
            print("[FAIL] 报告生成失败")
            return False
            
    except Exception as e:
        print(f"[FAIL] 报告生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("盘前资金流向分析系统 - 测试套件")
    print("="*60)
    
    results = []
    
    # 测试导入
    results.append(("模块导入", test_imports()))
    
    # 测试数据获取
    results.append(("数据获取", test_data_fetcher()))
    
    # 测试数据库
    results.append(("数据库", test_database()))
    
    # 测试报告生成
    results.append(("报告生成", test_report_generator()))
    
    # 汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {status} - {name}")
    
    print("-"*60)
    print(f"总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！应用可以正常运行。")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 项测试失败，请检查错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
