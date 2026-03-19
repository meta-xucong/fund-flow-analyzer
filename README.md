# 盘前资金流向分析系统

基于 AKShare 的 A 股市场盘前资金流向分析系统，每日自动生成市场分析报告，识别热点板块和个股。

## 功能特性

- **市场概览**: 全市场涨跌统计、情绪评分、量能分析
- **板块分析**: 板块强度排名、资金流向、热点识别
- **智能选股**: 三种策略 (动量/反转/资金流)
- **报告生成**: 文本报告、JSON数据、可视化图表
- **数据存储**: SQLite持久化、历史数据查询
- **自动调度**: 支持定时任务执行

## 项目结构

```
vibe_coding5/
├── config/                 # 配置文件
│   ├── settings.py        # 全局配置
│   └── sectors.json       # 重点板块配置
├── core/                   # 核心模块
│   ├── fetcher.py         # 数据采集(AKShare)
│   ├── storage.py         # 数据存储(SQLite)
│   ├── analyzer.py        # 分析算法
│   ├── selector.py        # 选股策略
│   └── report_generator.py # 报告生成
├── data/                   # 数据目录
│   ├── raw/               # 原始数据
│   ├── processed/         # 处理后数据
│   └── market_data.db     # SQLite数据库
├── reports/                # 报告输出
│   ├── daily/             # 每日报告
│   └── archive/           # 历史存档
├── tests/                  # 测试用例
├── tools/                  # 工具脚本
├── main.py                 # 主入口
└── requirements.txt        # 依赖清单
```

## 安装

### 1. 克隆项目

```bash
cd vibe_coding5
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行每日分析

```bash
# 执行今日分析
python main.py

# 执行指定日期分析
python main.py --date 2024-03-19

# 不保存数据到数据库
python main.py --no-save
```

### 回测模式

```bash
# 回测指定日期范围
python main.py --backtest 2024-01-01 2024-03-19
```

### 查询历史报告

```bash
# 查看指定日期报告
python main.py --query 2024-03-19

# 查看最新报告
python main.py --latest
```

## 选股策略

### 1. 动量策略 (momentum)
- **逻辑**: 追涨强势股
- **条件**: 涨幅 2%~7%，量比>1.5，成交额>3亿
- **适用**: 市场强势，热点明确时

### 2. 反转策略 (reversal)
- **逻辑**: 低吸反弹股
- **条件**: 跌幅 -7%~-3%，量比>2，5日资金为正
- **适用**: 市场调整，寻找反弹机会

### 3. 资金流向策略 (fund_flow)
- **逻辑**: 跟踪主力布局
- **条件**: 5日资金为正，当日涨幅<7%，成交额>5亿
- **适用**: 中线布局，跟踪主力资金

## 报告输出

执行分析后，报告将保存在 `reports/daily/` 目录:

- `report_YYYY-MM-DD.txt` - 文本格式报告
- `report_YYYY-MM-DD.json` - JSON格式数据
- `report_YYYY-MM-DD.png` - 可视化图表

## 数据库结构

SQLite数据库包含以下表:

- `market_overview` - 市场概况
- `sector_data` - 板块数据
- `stock_data` - 个股数据
- `stock_picks` - 选股结果
- `northbound_flow` - 北向资金

## 配置说明

编辑 `config/settings.py` 可调整:

- 选股策略参数 (涨幅范围、量比阈值等)
- 板块强度计算权重
- 报告生成时间
- 重点监控板块列表

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_selector.py -v
```

## 定时任务

使用 APScheduler 或系统定时任务:

```bash
# Linux (crontab)
0 9 * * 1-5 cd /path/to/vibe_coding5 && python main.py

# Windows (任务计划程序)
# 每天 9:00 执行 main.py
```

## 依赖版本

- Python >= 3.9
- akshare >= 1.11.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- sqlalchemy >= 2.0.0

## 注意事项

1. AKShare数据源为东方财富，数据有15分钟延迟
2. 交易日9:00执行可获得盘前数据
3. 首次运行需要下载历史数据，耗时较长
4. 建议定期清理 `logs/` 目录避免日志文件过大

## 许可证

MIT License
