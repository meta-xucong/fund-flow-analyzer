/**
 * 盘前资金流向分析系统 - 前端应用
 */

// API基础URL - 自动检测
// 如果前端和后端在同一服务器，使用相对路径
// 如果分开部署，使用完整URL
const API_BASE = window.location.port === '5000' 
    ? '/api'  // 通过Flask访问时
    : 'http://127.0.0.1:5000/api';  // 开发时分开访问

class FundFlowApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.backtestInterval = null;
        this.currentBacktestId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.startClock();
        this.loadStatus();
        this.loadBacktestHistory();
        this.setDefaultBacktestDates();
    }

    // 设置默认回测日期为最近5天
    setDefaultBacktestDates() {
        const today = new Date();
        
        // 计算最近5天的日期范围
        const endDate = new Date(today);
        endDate.setDate(today.getDate() - 1); // 昨天（最近一个完整交易日）
        
        const startDate = new Date(endDate);
        startDate.setDate(endDate.getDate() - 4); // 往前推4天，共5天
        
        // 格式化为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        const startInput = document.getElementById('backtest-start');
        const endInput = document.getElementById('backtest-end');
        
        if (startInput) startInput.value = formatDate(startDate);
        if (endInput) endInput.value = formatDate(endDate);
    }

    // 绑定事件
    bindEvents() {
        // 导航切换
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.navigateTo(section);
            });
        });
    }

    // 导航到指定页面
    navigateTo(section) {
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.section === section) {
                item.classList.add('active');
            }
        });

        // 切换页面
        document.querySelectorAll('.section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        // 更新页面标题
        const titles = {
            'dashboard': '仪表盘',
            'daily': '今日报告',
            'backtest': '历史回测',
            'settings': '设置'
        };
        document.querySelector('.page-title').textContent = titles[section];

        this.currentSection = section;

        // 页面特定初始化
        if (section === 'daily') {
            this.loadTodayReport();
        }
    }

    // 时钟
    startClock() {
        const updateTime = () => {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('zh-CN');
        };
        updateTime();
        setInterval(updateTime, 1000);
    }

    // 加载系统状态
    async loadStatus() {
        try {
            console.log('Loading status from:', `${API_BASE}/status`);
            const response = await fetch(`${API_BASE}/status`, {
                method: 'GET',
                mode: 'cors',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Status loaded:', data);

            if (data.success) {
                const status = data.data;
                
                // 更新推送状态
                document.getElementById('push-status').textContent = 
                    status.daily_push_enabled ? '已启用' : '已禁用';
                
                // 更新上次推送时间
                document.getElementById('last-push').textContent = 
                    status.last_push_time || '--';
                
                // 更新回测状态
                document.getElementById('backtest-status').textContent = 
                    status.is_running_backtest ? '运行中' : '空闲';
                
                // 更新设置开关
                document.getElementById('push-enabled').checked = 
                    status.daily_push_enabled;
                
                // 更新服务器状态为在线
                document.getElementById('server-status').innerHTML = `
                    <span class="status-dot online"></span>
                    <span class="status-text">服务在线</span>
                `;
            }
        } catch (error) {
            console.error('加载状态失败:', error);
            document.getElementById('server-status').innerHTML = `
                <span class="status-dot offline"></span>
                <span class="status-text">服务离线 (${error.message})</span>
            `;
            
            // 显示错误提示
            this.showError('无法连接到后端服务，请确保: 1. 后端服务已启动 (python run.py) 2. 端口5000未被占用');
        }
    }
    
    // 显示错误信息
    showError(message) {
        console.error(message);
        // 可以在界面上添加一个错误提示区域
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 59, 48, 0.9);
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
            font-size: 14px;
            backdrop-filter: blur(10px);
        `;
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // 加载今日报告
    async loadTodayReport() {
        const container = document.getElementById('daily-report-content');
        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>正在连接服务...</p>
            </div>
        `;

        try {
            console.log('Loading today report from:', `${API_BASE}/daily-report/today`);
            const response = await fetch(`${API_BASE}/daily-report/today`, {
                method: 'GET',
                mode: 'cors',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Report data:', data);

            if (data.success) {
                this.renderDailyReport(data.data);
                this.updateLatestPreview(data.data);
            } else {
                container.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-icon">⚠️</span>
                        <p>${data.message || '获取报告失败'}</p>
                        <button class="glass-button small" onclick="app.loadTodayReport()">重试</button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载报告失败:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">❌</span>
                    <p>连接失败: ${error.message}</p>
                    <p style="font-size: 12px; color: #86868b; margin-top: 8px;">
                        请确保后端服务已启动: python run.py
                    </p>
                    <button class="glass-button small" onclick="app.loadTodayReport()" style="margin-top: 16px;">
                        重试
                    </button>
                </div>
            `;
        }
    }

    // 渲染每日报告
    renderDailyReport(report) {
        const container = document.getElementById('daily-report-content');
        
        const sentiment = report.sentiment;
        const sectors = report.sector_ranking || [];
        const momentum = report.momentum_picks || [];
        const reversal = report.reversal_picks || [];
        const summary = report.summary;

        let html = `
            <div class="report-content">
                <!-- 市场情绪 -->
                <div class="glass-card report-section">
                    <h4>市场情绪</h4>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">情绪状态</span>
                            <span class="status-value">${sentiment.status}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">情绪分数</span>
                            <span class="status-value">${sentiment.score.toFixed(1)}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">上涨/下跌</span>
                            <span class="status-value">${sentiment.up_count}/${sentiment.down_count}</span>
                        </div>
                    </div>
                </div>

                <!-- 板块排行 -->
                <div class="glass-card report-section">
                    <h4>板块强度 TOP 10</h4>
                    <div class="stock-list">
                        ${sectors.slice(0, 10).map(s => `
                            <div class="stock-item">
                                <div class="stock-info">
                                    <span class="stock-name">${s.rank}. ${s.name}</span>
                                </div>
                                <span class="stock-score" style="color: ${s.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                    ${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- 动量选股 -->
                <div class="glass-card report-section">
                    <h4>动量策略 (追涨)</h4>
                    <div class="stock-list">
                        ${momentum.length > 0 ? momentum.map(s => `
                            <div class="stock-item">
                                <div class="stock-info">
                                    <span class="stock-name">${s.name}</span>
                                    <span class="stock-code">${s.code}</span>
                                    <span class="stock-reason">${s.reason}</span>
                                </div>
                                <span class="stock-score">${s.score.toFixed(1)}分</span>
                            </div>
                        `).join('') : '<p style="color: var(--text-tertiary)">无符合条件的股票</p>'}
                    </div>
                </div>

                <!-- 反转选股 -->
                <div class="glass-card report-section">
                    <h4>反转策略 (抄底)</h4>
                    <div class="stock-list">
                        ${reversal.length > 0 ? reversal.map(s => `
                            <div class="stock-item reversal">
                                <div class="stock-info">
                                    <span class="stock-name">${s.name}</span>
                                    <span class="stock-code">${s.code}</span>
                                    <span class="stock-reason">${s.reason}</span>
                                </div>
                                <span class="stock-score">${s.score.toFixed(1)}分</span>
                            </div>
                        `).join('') : '<p style="color: var(--text-tertiary)">无符合条件的股票</p>'}
                    </div>
                </div>

                <!-- 操作建议 -->
                <div class="glass-card report-section">
                    <h4>操作建议</h4>
                    <p><strong>建议仓位:</strong> ${summary.position_suggestion}</p>
                    <p><strong>风险等级:</strong> ${summary.risk_level}</p>
                    <p><strong>建议:</strong> ${summary.advice}</p>
                    ${summary.watchlist.length > 0 ? `
                        <p><strong>观察名单:</strong> ${summary.watchlist.join(', ')}</p>
                    ` : ''}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    // 更新仪表盘最新报告预览
    updateLatestPreview(report) {
        const preview = document.getElementById('latest-report-preview');
        const dateEl = document.getElementById('latest-report-date');
        
        dateEl.textContent = report.date;
        
        const momentum = report.momentum_picks || [];
        const reversal = report.reversal_picks || [];
        
        preview.innerHTML = `
            <div class="stock-list">
                ${momentum.slice(0, 3).map(s => `
                    <div class="stock-item">
                        <div class="stock-info">
                            <span class="stock-name">${s.name}</span>
                            <span class="stock-code">${s.code}</span>
                        </div>
                        <span class="stock-score">+${s.change_pct}%</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // 运行回测
    async runBacktest() {
        const startDate = document.getElementById('backtest-start').value;
        const endDate = document.getElementById('backtest-end').value;
        
        if (!startDate || !endDate) {
            alert('请选择开始和结束日期');
            return;
        }

        if (startDate > endDate) {
            alert('开始日期不能晚于结束日期');
            return;
        }

        // 显示进度条和状态区域
        document.getElementById('backtest-progress').style.display = 'flex';
        document.getElementById('backtest-detail-status').style.display = 'block';
        document.getElementById('run-backtest-btn').disabled = true;
        document.getElementById('run-backtest-btn').innerHTML = `
            <span class="btn-icon">⏳</span>
            <span class="btn-text">启动中...</span>
        `;
        
        // 初始化状态显示
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-text').textContent = '0%';
        document.getElementById('status-step').textContent = '准备中';
        document.getElementById('status-date').textContent = '';
        document.getElementById('status-message').innerHTML = '<span class="spinner"></span>正在启动回测任务...';

        try {
            console.log('Starting backtest:', startDate, 'to', endDate);
            const response = await fetch(`${API_BASE}/backtest/run`, {
                method: 'POST',
                mode: 'cors',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Backtest response:', data);

            if (data.success) {
                document.getElementById('run-backtest-btn').innerHTML = `
                    <span class="btn-icon">⏳</span>
                    <span class="btn-text">运行中...</span>
                `;
                // 显示进度条和状态区域
                document.getElementById('backtest-progress').style.display = 'block';
                document.getElementById('backtest-detail-status').style.display = 'block';
                this.startProgressPolling();
            } else {
                alert(data.message || '启动回测失败');
                this.resetBacktestUI();
            }
        } catch (error) {
            console.error('启动回测失败:', error);
            alert('连接失败: ' + error.message + '\n请确保后端服务已启动');
            this.resetBacktestUI();
        }
    }

    // 轮询回测进度
    startProgressPolling() {
        // 显示状态区域
        document.getElementById('backtest-detail-status').style.display = 'block';
        
        let failCount = 0;
        const maxFails = 10; // 允许最多10次连续失败
        let lastProgress = -1;
        let stallCount = 0;
        
        this.backtestInterval = setInterval(async () => {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 8000); // 8秒超时
                
                const response = await fetch(`${API_BASE}/backtest/progress`, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    failCount++;
                    console.warn(`进度请求失败 (${failCount}/${maxFails}): ${response.status}`);
                    return; // 继续轮询
                }
                
                const data = await response.json();
                failCount = 0; // 成功时重置失败计数

                if (data.success) {
                    const progress = data.data.progress;
                    const step = data.data.current_step || '';
                    const date = data.data.current_date || '';
                    const message = data.data.message || '';
                    const isRunning = data.data.is_running;
                    
                    // 检测进度是否卡住
                    if (progress === lastProgress) {
                        stallCount++;
                    } else {
                        stallCount = 0;
                        lastProgress = progress;
                    }
                    
                    // 更新进度条和状态
                    document.getElementById('progress-fill').style.width = `${progress}%`;
                    document.getElementById('progress-text').textContent = `${progress}%`;
                    
                    if (step) {
                        const stepEl = document.getElementById('status-step');
                        stepEl.textContent = step;
                        stepEl.className = 'status-value status-step-badge ' + this.getStepClass(step);
                    }
                    if (date) {
                        document.getElementById('status-date').textContent = date;
                    }
                    if (message) {
                        document.getElementById('status-message').innerHTML = 
                            `<span class="spinner"></span>${message}`;
                    }

                    // 完成判断
                    if (!isRunning && progress >= 100) {
                        clearInterval(this.backtestInterval);
                        document.getElementById('backtest-detail-status').style.display = 'none';
                        this.onBacktestComplete();
                    }
                    
                    // 如果卡住太久（15次轮询约30秒无变化），提示用户
                    if (stallCount > 20) {
                        document.getElementById('status-message').innerHTML = 
                            `<span style="color:orange">处理中，请稍候...</span>`;
                    }
                }
            } catch (error) {
                failCount++;
                console.warn(`网络请求失败 (${failCount}/${maxFails}):`, error.message);
                
                // 只有连续失败多次后才提示
                if (failCount >= maxFails) {
                    console.error('网络连接不稳定');
                    clearInterval(this.backtestInterval);
                    this.resetBacktestUI();
                    document.getElementById('status-message').innerHTML = 
                        `<span style="color:red">网络不稳定，请刷新页面查看最新结果</span>`;
                }
            }
        }, 2000); // 2秒轮询一次
    }
    
    // 获取步骤样式类
    getStepClass(step) {
        const stepMap = {
            '数据获取': 'data-fetch',
            '生成报告': 'report',
            '模拟交易': 'trade',
            '汇总统计': 'summary'
        };
        return stepMap[step] || '';
    }

    // 回测完成
    async onBacktestComplete() {
        this.resetBacktestUI();
        
        // 加载最新结果并展示
        await this.loadLatestBacktestResult();
        
        // 加载历史记录
        await this.loadBacktestHistory();
        
        // 显示结果区域
        document.getElementById('backtest-results').style.display = 'block';
        
        this.showSuccess('回测完成！');
    }
    
    // 加载最新回测结果
    async loadLatestBacktestResult() {
        try {
            const response = await fetch(`${API_BASE}/backtest/results`);
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                // 获取最新的结果
                const latest = data.data[0];
                this.currentBacktestId = latest.id;
                const resultResponse = await fetch(`${API_BASE}/backtest/result/${latest.id}`);
                const resultData = await resultResponse.json();
                
                if (resultData.success) {
                    this.renderBacktestResult(resultData.data);
                }
            }
        } catch (error) {
            console.error('加载回测结果失败:', error);
        }
    }
    
    // 渲染回测结果
    renderBacktestResult(result) {
        const container = document.getElementById('results-content');
        const summary = result.summary || {};
        const trades = result.trades || [];
        
        // 总体统计
        const overall = summary.overall || {};
        const momentum = summary.momentum || {};
        const reversal = summary.reversal || {};
        
        let html = `
            <div class="backtest-summary">
                <h4>回测概况</h4>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-label">回测期间</span>
                        <span class="summary-value">${result.start_date} 至 ${result.end_date}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">总交易次数</span>
                        <span class="summary-value">${summary.total_trades || 0} 笔</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">平均收益率</span>
                        <span class="summary-value" style="color: ${overall.avg_return >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                            ${overall.avg_return >= 0 ? '+' : ''}${overall.avg_return || 0}%
                        </span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">整体胜率</span>
                        <span class="summary-value">${overall.win_rate || 0}%</span>
                    </div>
                </div>
            </div>
            
            <div class="strategy-comparison">
                <h4>策略对比</h4>
                <div class="strategy-cards">
                    <div class="strategy-card momentum">
                        <div class="strategy-header">
                            <span class="strategy-name">动量策略</span>
                            <span class="strategy-count">${momentum.count || 0}笔</span>
                        </div>
                        <div class="strategy-stats">
                            <div class="stat">
                                <span class="stat-label">平均收益</span>
                                <span class="stat-value" style="color: ${momentum.avg_return >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                    ${momentum.avg_return >= 0 ? '+' : ''}${momentum.avg_return || 0}%
                                </span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">胜率</span>
                                <span class="stat-value">${momentum.win_rate || 0}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="strategy-card reversal">
                        <div class="strategy-header">
                            <span class="strategy-name">反转策略</span>
                            <span class="strategy-count">${reversal.count || 0}笔</span>
                        </div>
                        <div class="strategy-stats">
                            <div class="stat">
                                <span class="stat-label">平均收益</span>
                                <span class="stat-value" style="color: ${reversal.avg_return >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                    ${reversal.avg_return >= 0 ? '+' : ''}${reversal.avg_return || 0}%
                                </span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">胜率</span>
                                <span class="stat-value">${reversal.win_rate || 0}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 交易明细表格 - 包含每日收益
        if (trades.length > 0) {
            html += `
                <div class="trades-section">
                    <h4>交易明细 (包含5日收益详情)</h4>
                    <div class="trades-filter">
                        <select id="strategy-filter" class="glass-select" onchange="app.filterTrades()">
                            <option value="all">全部策略</option>
                            <option value="动量">动量策略</option>
                            <option value="反转">反转策略</option>
                        </select>
                        <select id="sort-by" class="glass-select" onchange="app.sortTrades()">
                            <option value="date">按日期</option>
                            <option value="return">按总收益率</option>
                            <option value="score">按评分</option>
                        </select>
                    </div>
                    <div class="trades-table-container">
                        <table class="trades-table" id="trades-table">
                            <thead>
                                <tr>
                                    <th>买入日期</th>
                                    <th>代码</th>
                                    <th>名称</th>
                                    <th>策略</th>
                                    <th>买入价</th>
                                    <th>第1天</th>
                                    <th>第2天</th>
                                    <th>第3天</th>
                                    <th>第4天</th>
                                    <th>第5天</th>
                                    <th>总收益</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${trades.map(t => {
                                    const daily = t.daily_returns || [];
                                    const getDayReturn = (dayNum) => {
                                        const d = daily.find(x => Number(x.day) === dayNum);
                                        if (!d) return '<span style="color:#999">-</span>';
                                        const sign = d.cumulative_return >= 0 ? '+' : '';
                                        const colorClass = d.cumulative_return >= 0 ? 'positive' : 'negative';
                                        return `<span class="${colorClass}">${sign}${d.cumulative_return.toFixed(1)}%</span>`;
                                    };
                                    return `
                                    <tr data-strategy="${t.strategy}">
                                        <td>${t.buy_date}</td>
                                        <td>${t.code}</td>
                                        <td>${t.name}</td>
                                        <td><span class="badge ${t.strategy === '动量' ? 'momentum' : 'reversal'}">${t.strategy}</span></td>
                                        <td>${t.buy_price.toFixed(2)}</td>
                                        <td class="return-cell">${getDayReturn(1)}</td>
                                        <td class="return-cell">${getDayReturn(2)}</td>
                                        <td class="return-cell">${getDayReturn(3)}</td>
                                        <td class="return-cell">${getDayReturn(4)}</td>
                                        <td class="return-cell">${getDayReturn(5)}</td>
                                        <td class="return-cell ${t.total_return >= 0 ? 'positive' : 'negative'}">
                                            <strong>${t.total_return >= 0 ? '+' : ''}${t.total_return.toFixed(2)}%</strong>
                                        </td>
                                    </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                    <div class="trades-legend">
                        <small style="color: var(--text-tertiary);">
                            注：第N天表示买入后第N个交易日的累计收益率
                        </small>
                    </div>
                </div>
            `;
        }
        
        // 保存交易数据供筛选使用
        this.currentTrades = trades;
        
        container.innerHTML = html;
    }
    
    // 筛选交易
    filterTrades() {
        const filter = document.getElementById('strategy-filter').value;
        const rows = document.querySelectorAll('#trades-table tbody tr');
        
        rows.forEach(row => {
            const strategy = row.getAttribute('data-strategy');
            if (filter === 'all' || strategy === filter) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    // 排序交易
    sortTrades() {
        const sortBy = document.getElementById('sort-by').value;
        if (!this.currentTrades) return;
        
        let sorted = [...this.currentTrades];
        if (sortBy === 'return') {
            sorted.sort((a, b) => b.total_return - a.total_return);
        } else if (sortBy === 'score') {
            sorted.sort((a, b) => b.score - a.score);
        } else {
            sorted.sort((a, b) => a.buy_date.localeCompare(b.buy_date));
        }
        
        // 重新渲染表格
        const tbody = document.querySelector('#trades-table tbody');
        tbody.innerHTML = sorted.map(t => `
            <tr data-strategy="${t.strategy}">
                <td>${t.buy_date}</td>
                <td>${t.code}</td>
                <td>${t.name}</td>
                <td><span class="badge ${t.strategy === '动量' ? 'momentum' : 'reversal'}">${t.strategy}</span></td>
                <td>${t.buy_price.toFixed(2)}</td>
                <td>${t.sell_price.toFixed(2)}</td>
                <td class="return-cell ${t.total_return >= 0 ? 'positive' : 'negative'}">
                    ${t.total_return >= 0 ? '+' : ''}${t.total_return.toFixed(2)}%
                </td>
            </tr>
        `).join('');
        
        // 重新应用筛选
        this.filterTrades();
    }
    
    // 显示成功提示
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-toast';
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(52, 199, 89, 0.9);
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            font-size: 14px;
            backdrop-filter: blur(10px);
            animation: slideIn 0.3s ease;
        `;
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => successDiv.remove(), 300);
        }, 3000);
    }

    // 重置回测UI
    resetBacktestUI() {
        document.getElementById('run-backtest-btn').disabled = false;
        document.getElementById('run-backtest-btn').innerHTML = `
            <span class="btn-icon">▶️</span>
            <span class="btn-text">开始回测</span>
        `;
        // 隐藏进度和状态
        document.getElementById('backtest-progress').style.display = 'none';
        document.getElementById('backtest-detail-status').style.display = 'none';
        // 重置进度条
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-text').textContent = '0%';
    }

    // 加载回测历史
    async loadBacktestHistory() {
        try {
            const response = await fetch(`${API_BASE}/backtest/results`);
            const data = await response.json();

            if (data.success) {
                const container = document.getElementById('backtest-history');
                
                if (data.data.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <span class="empty-icon">📂</span>
                            <p>暂无历史记录</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = `
                    <div class="stock-list">
                        ${data.data.map(item => `
                            <div class="stock-item backtest-item">
                                <div class="stock-info">
                                    <span class="stock-name">${item.start_date} 至 ${item.end_date}</span>
                                    <span class="stock-code">${item.created_at}</span>
                                </div>
                                <div class="backtest-actions">
                                    <button class="glass-button small" onclick="app.downloadBacktest('${item.id}')">
                                        下载
                                    </button>
                                    <button class="glass-button small danger" onclick="app.deleteBacktest('${item.id}')">
                                        删除
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }

    // 删除回测结果
    deleteBacktest = async (resultId) => {
        const self = window.app;
        
        if (!confirm('确定要删除这条回测记录吗？\n此操作不可恢复。')) {
            return;
        }
        
        const url = `${API_BASE}/backtest/delete/${encodeURIComponent(resultId)}`;
        console.log('=== 删除调试信息 ===');
        console.log('请求URL:', url);
        console.log('请求方法: DELETE');
        console.log('API_BASE:', API_BASE);
        console.log('当前页面端口:', window.location.port);
        console.log('当前页面主机:', window.location.host);
        
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            console.log('响应状态:', response.status);
            
            // 检查内容类型
            const contentType = response.headers.get('content-type');
            console.log('内容类型:', contentType);
            
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('非JSON响应:', text.substring(0, 200));
                alert('服务器返回错误，请查看控制台');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                self.showSuccess('删除成功');
                // 刷新历史记录列表
                self.loadBacktestHistory();
                // 如果当前显示的是被删除的结果，隐藏结果区域
                if (self.currentBacktestId === resultId) {
                    document.getElementById('backtest-results').style.display = 'none';
                    self.currentBacktestId = null;
                }
            } else {
                alert(data.message || '删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败: ' + error.message);
        }
    }

    // 下载回测结果 (使用箭头函数保持 this 绑定)
    downloadBacktest = async (resultId) => {
        const self = window.app; // 显式获取 app 实例
        console.log('downloadBacktest called with resultId:', resultId);
        console.log('currentBacktestId:', self.currentBacktestId);
        
        try {
            // 如果没有传入ID，使用当前显示的结果ID
            const id = resultId || self.currentBacktestId;
            console.log('Using id:', id);
            
            if (!id) {
                alert('没有可下载的回测结果');
                return;
            }
            
            // 显示下载中提示
            console.log('准备下载...');
            
            const response = await fetch(`${API_BASE}/backtest/download/${id}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/zip'
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                console.log('Received blob, size:', blob.size);
                
                // 检查blob是否有效
                if (blob.size === 0) {
                    alert('下载内容为空');
                    return;
                }
                
                const url = window.URL.createObjectURL(blob);
                console.log('Created object URL:', url);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `backtest_${id}.zip`;
                a.style.display = 'none';
                document.body.appendChild(a);
                
                console.log('Triggering download...');
                a.click();
                
                // 延迟清理
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    if (a.parentNode) {
                        document.body.removeChild(a);
                    }
                }, 1000);
                
                alert('下载已开始');
            } else if (response.status === 404) {
                alert('回测结果不存在或已过期');
            } else {
                const errorData = await response.json().catch(() => ({}));
                alert(errorData.message || `下载失败 (${response.status})`);
            }
        } catch (error) {
            console.error('下载失败:', error);
            alert('下载失败: ' + error.message);
        }
    }

    // 更新推送设置
    async updatePushSettings() {
        const enabled = document.getElementById('push-enabled').checked;
        
        try {
            const response = await fetch(`${API_BASE}/settings/push`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });

            const data = await response.json();

            if (data.success) {
                this.loadStatus(); // 刷新状态
            } else {
                alert(data.message || '更新设置失败');
            }
        } catch (error) {
            console.error('更新设置失败:', error);
            alert('网络错误');
        }
    }
}

// 初始化应用
const app = new FundFlowApp();

// 将应用暴露到window对象，以便事件属性访问
window.app = app;
console.log('FundFlowApp initialized, app object exposed to window');
