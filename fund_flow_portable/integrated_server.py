#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成服务器 - 同时提供前端和后端API
"""
import os
import sys
import signal
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import threading
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 设置环境变量
os.environ['NO_PROXY'] = 'qt.gtimg.cn,sina.com.cn,localhost,127.0.0.1'
os.environ['TQDM_DISABLE'] = '1'

from backend.data_fetcher import DataFetcher
from backend.report_generator import ReportGenerator
from backend.backtest_engine import BacktestEngine
from database.db_manager import DatabaseManager

# 前端目录
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

app = Flask(__name__)
CORS(app)

# 全局状态
app_status = {
    'daily_push_enabled': False,
    'last_push_time': None,
    'is_running_backtest': False,
    'backtest_progress': 0
}

# 初始化组件
data_fetcher = DataFetcher()
report_generator = ReportGenerator()
backtest_engine = BacktestEngine()
db_manager = DatabaseManager()

# 服务器运行标志
server_running = True

# ============ 前端路由 ============

@app.route('/')
def index():
    """提供前端主页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(FRONTEND_DIR, filename)

# ============ 辅助函数 ============

def is_market_open(date=None):
    """
    判断指定日期是否开市（简单规则：周一到周五开市，周末休市）
    注：未考虑法定节假日
    
    Returns:
        (bool, str) - (是否开市, 提示信息)
    """
    if date is None:
        date = datetime.now()
    
    weekday = date.weekday()  # 0=周一, 6=周日
    
    if weekday >= 5:  # 周六或周日
        days_until_monday = 7 - weekday
        next_open = date + timedelta(days=days_until_monday)
        return False, f"今日休市（周末），下次开市：{next_open.strftime('%Y-%m-%d')}（周一）"
    
    return True, "今日开市"

def fetch_today_data_with_retry(date_str, max_retries=3):
    """
    获取今日数据，带指数退避重试
    只获取指定日期数据，绝不回退到历史数据
    
    Args:
        date_str: 日期字符串 YYYY-MM-DD
        max_retries: 最大重试次数
        
    Returns:
        (data, error_msg) - 成功返回数据，失败返回错误信息
    """
    for attempt in range(max_retries + 1):
        try:
            print(f"[*] 第{attempt + 1}次尝试获取 {date_str} 数据...")
            
            # 只获取指定日期数据，force_current=True确保不回退
            data = data_fetcher.fetch_daily_data(
                date_str, 
                sample_size=2000, 
                use_historical=False,  # 不使用历史数据模式
                force_current=True     # 强制获取指定日期，不回退
            )
            
            # 检查数据是否有效（小心处理DataFrame）
            if data is not None:
                stocks = data.get('stocks')
                if stocks is not None:
                    # 检查stocks是否为空DataFrame或空列表
                    is_empty = False
                    if hasattr(stocks, 'empty'):  # DataFrame
                        is_empty = stocks.empty
                    elif hasattr(stocks, '__len__'):  # 列表或其他可迭代对象
                        is_empty = len(stocks) == 0
                    
                    if not is_empty:
                        print(f"[OK] 成功获取 {date_str} 数据")
                        return data, None
            
            if attempt < max_retries:
                # 指数退避：1秒, 2秒, 4秒
                delay = 2 ** attempt
                print(f"[!] 未获取到数据，{delay}秒后重试...")
                time.sleep(delay)
            else:
                return None, f"经过{max_retries + 1}次尝试，无法获取 {date_str} 数据"
                
        except Exception as e:
            print(f"[!] 获取数据异常: {e}")
            if attempt < max_retries:
                delay = 2 ** attempt
                print(f"[*] {delay}秒后重试...")
                time.sleep(delay)
            else:
                return None, f"获取数据失败: {str(e)}"
    
    return None, "未知错误"

# ============ API路由 ============

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    return jsonify({
        'success': True,
        'data': {
            'daily_push_enabled': app_status['daily_push_enabled'],
            'last_push_time': app_status['last_push_time'],
            'is_running_backtest': app_status['is_running_backtest'],
            'backtest_progress': app_status['backtest_progress'],
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/api/daily-report/today', methods=['GET'])
def get_today_report():
    """获取今日报告"""
    try:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        # 1. 判断今天是否开市
        is_open, msg = is_market_open(now)
        
        if not is_open:
            # 休市，返回提示
            return jsonify({
                'success': True,
                'data': {
                    'is_market_open': False,
                    'message': msg,
                    'date': date_str,
                    'sentiment': {'status': '休市', 'score': 0},
                    'sector_ranking': [],
                    'momentum_picks': [],
                    'reversal_picks': [],
                    'summary': {'position_suggestion': '休市', 'risk_level': '低', 'advice': msg},
                    'meta': {
                        'data_source': '-',
                        'fetch_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                        'data_date': date_str,
                        'data_period': '休市',
                        'data_description': msg,
                        'update_note': '股市休市期间无数据'
                    }
                }
            })
        
        # 2. 开市，必须获取今日数据（带指数退避重试）
        print(f"[*] 今日开市，获取 {date_str} 数据...")
        data, error_msg = fetch_today_data_with_retry(date_str, max_retries=3)
        
        if data is None:
            # 获取失败，返回错误
            return jsonify({
                'success': False,
                'message': f'今日开市但数据获取失败: {error_msg}',
                'error_type': 'DATA_FETCH_FAILED'
            })
        
        # 3. 生成报告
        report = report_generator.generate_report(data)
        
        # 4. 添加数据源和时间元数据
        report['meta'] = {
            'data_source': '腾讯财经 (stock_zh_a_hist_tx) + 申万行业',
            'fetch_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'data_date': date_str,
            'data_period': f'{date_str} 收盘数据',
            'data_description': f'基于 {date_str} 完整交易数据（09:30-15:00）计算',
            'update_note': f'最新可用数据日期: {date_str}'
        }
        
        return jsonify({'success': True, 'data': report})
        
    except Exception as e:
        print(f"[!] 获取今日报告失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': 'EXCEPTION'
        })

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """运行回测"""
    try:
        data = request.json
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '请提供开始和结束日期'})
        
        if app_status['is_running_backtest']:
            return jsonify({'success': False, 'message': '已有回测任务在运行'})
        
        def backtest_task():
            app_status['is_running_backtest'] = True
            app_status['backtest_progress'] = 0
            
            try:
                result = backtest_engine.run_backtest(
                    start_date, 
                    end_date,
                    progress_callback=lambda p: app_status.update({'backtest_progress': p})
                )
                db_manager.save_backtest_result({
                    'start_date': start_date,
                    'end_date': end_date,
                    'result': result,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                print(f"回测失败: {e}")
            finally:
                app_status['is_running_backtest'] = False
        
        thread = threading.Thread(target=backtest_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '回测任务已启动'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/backtest/progress', methods=['GET'])
def get_backtest_progress():
    """获取回测进度"""
    engine_status = backtest_engine.get_status()
    return jsonify({
        'success': True,
        'data': {
            'is_running': app_status['is_running_backtest'] or engine_status['is_running'],
            'progress': engine_status['progress'] if engine_status['is_running'] else app_status['backtest_progress'],
            'current_step': engine_status.get('current_step', ''),
            'current_date': engine_status.get('current_date', ''),
            'message': engine_status.get('message', '')
        }
    })

@app.route('/api/backtest/results', methods=['GET'])
def get_backtest_results():
    """获取回测结果列表"""
    try:
        results = db_manager.get_backtest_results()
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/backtest/result/<result_id>', methods=['GET'])
def get_single_backtest_result(result_id):
    """获取单个回测结果详情"""
    try:
        stored_result = db_manager.get_backtest_result(result_id)
        if not stored_result:
            return jsonify({'success': False, 'message': '结果不存在'}), 404
        
        if 'result' in stored_result and isinstance(stored_result['result'], dict):
            actual_result = stored_result['result']
            actual_result['start_date'] = stored_result.get('start_date', actual_result.get('start_date', result_id.split('_')[0]))
            actual_result['end_date'] = stored_result.get('end_date', actual_result.get('end_date', result_id.split('_')[1]))
            actual_result['created_at'] = stored_result.get('created_at')
        else:
            actual_result = stored_result
        
        return jsonify({'success': True, 'data': actual_result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/backtest/download/<result_id>', methods=['GET'])
def download_backtest(result_id):
    """下载回测结果"""
    try:
        stored_result = db_manager.get_backtest_result(result_id)
        if not stored_result:
            return jsonify({'success': False, 'message': '结果不存在'}), 404
        
        if 'result' in stored_result and isinstance(stored_result['result'], dict):
            actual_result = stored_result['result']
            actual_result['start_date'] = stored_result.get('start_date', result_id.split('_')[0])
            actual_result['end_date'] = stored_result.get('end_date', result_id.split('_')[1])
        else:
            actual_result = stored_result
        
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'backtest_results')
        os.makedirs(results_dir, exist_ok=True)
        
        engine = BacktestEngine()
        zip_path = engine.create_download_package(actual_result)
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"backtest_{actual_result['start_date']}_{actual_result['end_date']}.zip"
        )
    except Exception as e:
        import traceback
        print(f"Download error: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings/push', methods=['POST'])
def update_push_settings():
    """更新推送设置"""
    try:
        data = request.json
        app_status['daily_push_enabled'] = data.get('enabled', False)
        db_manager.save_settings({
            'daily_push_enabled': app_status['daily_push_enabled'],
            'push_channels': data.get('channels', {})
        })
        return jsonify({'success': True, 'message': '设置已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/settings/push', methods=['GET'])
def get_push_settings():
    """获取推送设置"""
    try:
        settings = db_manager.get_settings()
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """关闭服务器API端点"""
    global server_running
    server_running = False
    
    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
    
    shutdown_server()
    return jsonify({'success': True, 'message': 'Server shutting down...'})

def signal_handler(signum, frame):
    """信号处理器"""
    global server_running
    print(f'\n[*] 收到信号 {signum}，正在关闭服务器...')
    server_running = False
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("=" * 60)
    print("Fund Flow Analysis System - Integrated Server")
    print("=" * 60)
    print(f"\nFrontend directory: {FRONTEND_DIR}")
    print("\nStarting server...")
    print("URL: http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n[*] 服务器已停止")
    finally:
        print("[*] 清理完成")
