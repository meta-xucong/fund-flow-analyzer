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
from datetime import datetime
import threading

# 导入后端模块
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

# ============ 前端路由 ============

@app.route('/')
def index():
    """提供前端主页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(FRONTEND_DIR, filename)

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
        date_str = datetime.now().strftime('%Y-%m-%d')
        data = data_fetcher.fetch_daily_data(date_str)
        if data is None:
            return jsonify({'success': False, 'message': '数据获取失败'})
        
        report = report_generator.generate_report(data)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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
        thread.start()
        
        return jsonify({'success': True, 'message': '回测任务已启动'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/backtest/progress', methods=['GET'])
def get_backtest_progress():
    """获取回测进度"""
    # 获取引擎的详细状态
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
        
        # 处理包装结构，提取实际的回测数据
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
        
        # 处理包装结构：数据库中存储的是 {start_date, end_date, result: {...}, created_at}
        # 需要提取 result 字段作为实际回测数据
        if 'result' in stored_result and isinstance(stored_result['result'], dict):
            actual_result = stored_result['result']
            # 确保有完整的元数据
            actual_result['start_date'] = stored_result.get('start_date', result_id.split('_')[0])
            actual_result['end_date'] = stored_result.get('end_date', result_id.split('_')[1])
        else:
            actual_result = stored_result
        
        # 确保结果目录存在
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'backtest_results')
        os.makedirs(results_dir, exist_ok=True)
        
        # 生成压缩包
        from backend.backtest_engine import BacktestEngine
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

def shutdown_server():
    """优雅关闭服务器"""
    print("\n[*] 正在关闭服务器...")
    
    # 关闭Flask的请求上下文
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    
    print("[*] 服务器已关闭")

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """API端点：关闭服务器"""
    shutdown_server()
    return jsonify({'success': True, 'message': 'Server shutting down...'})

# 全局标志用于控制服务器运行
server_running = True

def signal_handler(sig, frame):
    """信号处理器"""
    global server_running
    print('\n[*] 收到关闭信号，正在优雅关闭...')
    server_running = False
    # 给服务器一点时间处理剩余请求
    time.sleep(0.5)
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
        # 使用 threaded=True 但设置更合理的参数
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            threaded=True,
            use_reloader=False  # 禁用重载器，避免双进程
        )
    except KeyboardInterrupt:
        print("\n[*] 服务器已停止")
    finally:
        print("[*] 清理完成")
