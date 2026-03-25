#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘前资金流向分析系统 - 后端主程序
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_file, send_from_directory
from datetime import datetime, timedelta
import threading
import json

from backend.data_fetcher import DataFetcher
from backend.report_generator import ReportGenerator
from backend.backtest_engine import BacktestEngine
from database.db_manager import DatabaseManager

app = Flask(__name__)

# 全局 CORS 处理
@app.after_request
def after_request(response):
    """添加 CORS 头到所有响应"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# 处理所有 OPTIONS 预检请求
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """处理 CORS 预检请求"""
    return jsonify({'status': 'ok'})

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


# 前端目录路径
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

@app.route('/')
def index():
    """提供前端主页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(FRONTEND_DIR, filename)


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
        
        # 获取数据
        data = data_fetcher.fetch_daily_data(date_str)
        if data is None:
            return jsonify({'success': False, 'message': '数据获取失败'})
        
        # 生成报告
        report = report_generator.generate_report(data)
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/daily-report/history/<date>', methods=['GET'])
def get_history_report(date):
    """获取历史报告"""
    try:
        report = db_manager.get_report(date)
        if report:
            return jsonify({'success': True, 'data': report})
        else:
            return jsonify({'success': False, 'message': '报告不存在'})
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
        
        # 检查是否正在运行
        if app_status['is_running_backtest']:
            return jsonify({'success': False, 'message': '已有回测任务在运行'})
        
        # 重置回测引擎状态
        backtest_engine.current_status = {
            'is_running': True,
            'progress': 0,
            'current_step': '准备中',
            'current_date': '',
            'message': '正在启动回测任务...'
        }
        
        # 在后台线程运行回测
        def backtest_task():
            app_status['is_running_backtest'] = True
            app_status['backtest_progress'] = 0
            
            try:
                result = backtest_engine.run_backtest(
                    start_date, 
                    end_date,
                    progress_callback=lambda p: app_status.update({'backtest_progress': p})
                )
                
                # 保存结果
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
    # 从回测引擎获取详细状态
    engine_status = backtest_engine.get_status()
    
    return jsonify({
        'success': True,
        'data': {
            'is_running': engine_status.get('is_running', False),
            'progress': engine_status.get('progress', 0),
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


@app.route('/api/backtest/delete/<result_id>', methods=['DELETE'])
def delete_backtest(result_id):
    """删除回测结果"""
    try:
        # 先获取记录信息以便删除文件
        stored_result = db_manager.get_backtest_result(result_id)
        
        if not stored_result:
            return jsonify({'success': False, 'message': '结果不存在'}), 404
        
        # 获取日期信息用于删除文件
        start_date = stored_result.get('start_date')
        end_date = stored_result.get('end_date')
        
        # 删除数据库记录
        deleted = db_manager.delete_backtest_result(result_id)
        
        if deleted:
            # 尝试删除对应的 zip 文件
            try:
                if start_date and end_date:
                    zip_filename = f"backtest_{start_date}_{end_date}.zip"
                    zip_path = os.path.join(backtest_engine.results_dir, zip_filename)
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
            except Exception as e:
                print(f"删除文件失败: {e}")
            
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
            
    except Exception as e:
        import traceback
        print(f"Delete error: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/backtest/download/<result_id>', methods=['GET'])
def download_backtest(result_id):
    """下载回测结果"""
    try:
        stored_result = db_manager.get_backtest_result(result_id)
        if not stored_result:
            return jsonify({'success': False, 'message': '结果不存在'}), 404
        
        # 处理包装结构，提取实际的回测数据
        if 'result' in stored_result and isinstance(stored_result['result'], dict):
            actual_result = stored_result['result']
            actual_result['start_date'] = stored_result.get('start_date', actual_result.get('start_date'))
            actual_result['end_date'] = stored_result.get('end_date', actual_result.get('end_date'))
        else:
            actual_result = stored_result
        
        # 确保有日期信息
        start_date = actual_result.get('start_date')
        end_date = actual_result.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'message': '回测结果缺少日期信息'}), 400
        
        # 检查文件是否已存在
        zip_filename = f"backtest_{start_date}_{end_date}.zip"
        zip_path = os.path.join(backtest_engine.results_dir, zip_filename)
        
        # 如果文件不存在，重新生成
        if not os.path.exists(zip_path):
            zip_path = backtest_engine.create_download_package(actual_result, result_id)
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
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
        
        # 保存到数据库
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


# 启动定时任务
from scheduler.daily_scheduler import start_scheduler

if __name__ == '__main__':
    # 初始化数据库
    db_manager.init_db()
    
    # 启动定时任务
    start_scheduler(app_status, data_fetcher, report_generator)
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=5000, debug=False)
