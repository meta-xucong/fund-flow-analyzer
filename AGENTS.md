# AGENTS.md - 盘前资金流向分析系统

> 本文档为 AI Agent 提供代码编写规范指导，确保项目一致性和可维护性。

---

## 1. 项目概述

### 1.1 项目目标
构建自动化盘前资金流向分析系统，每日开盘前生成市场资金流向报告，识别热点板块和个股，为交易决策提供数据支持。

### 1.2 核心技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 数据源 | AKShare | 免费A股数据接口，包含行情+资金+板块 |
| 存储 | SQLite | 本地轻量级数据库，支持历史查询 |
| 计算 | Pandas + NumPy | 标准数据处理和计算 |
| 可视化 | Matplotlib + Plotly | 静态图表 + 交互式图表 |
| 调度 | APScheduler | Python定时任务调度 |

---

## 2. 项目结构规范

### 2.1 目录结构
```
vibe_coding5/
├── AGENTS.md                 # 本文件 - Agent编码规范
├── CODING_RULES.md           # 通用编码规则
├── requirements.txt          # 依赖清单
├── config/
│   ├── __init__.py
│   ├── settings.py           # 全局配置
│   └── sectors.json          # 重点板块配置
├── core/
│   ├── __init__.py
│   ├── fetcher.py            # 数据采集模块
│   ├── storage.py            # 数据存储模块
│   ├── analyzer.py           # 分析算法模块
│   ├── selector.py           # 选股策略模块
│   └── report_generator.py   # 报告生成模块
├── data/
│   ├── raw/                  # 原始数据
│   ├── processed/            # 处理后数据
│   └── market_data.db        # SQLite数据库
├── reports/
│   ├── daily/                # 每日报告
│   └── archive/              # 历史报告存档
├── tests/
│   ├── test_fetcher.py
│   ├── test_analyzer.py
│   └── test_selector.py
├── tools/
│   └── verify_source_integrity.py  # 代码完整性检查
└── main.py                   # 主入口
```

### 2.2 模块职责

| 模块 | 文件 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| 数据采集 | `fetcher.py` | 获取AKShare数据 | API参数 | 原始DataFrame |
| 数据存储 | `storage.py` | 清洗存储到SQLite | 原始数据 | 结构化数据 |
| 分析引擎 | `analyzer.py` | 板块强度计算 | 市场数据 | 板块评分 |
| 选股策略 | `selector.py` | 多策略选股 | 全市场数据 | 精选股票列表 |
| 报告生成 | `report_generator.py` | 生成分析报告 | 分析结果 | 可视化报告 |
| 定时调度 | `scheduler.py` | 每日自动执行 | 时间触发 | 执行日志 |

---

## 3. AKShare 使用规范

### 3.1 官方文档合规
- **必须** 严格遵循 [AKShare官方文档](https://www.akshare.xyz/)
- **禁止** 猜测或编造API参数
- **必须** 在代码注释中标注使用的AKShare版本
- **必须** 处理API变更导致的兼容性问题

### 3.2 核心API清单

```python
# 市场概况数据
stock_zh_a_spot_em()          # 全市场实时行情

# 板块数据  
stock_board_concept_cons_em() # 概念板块成分股
stock_sector_fund_flow_rank() # 板块资金流向排名

# 个股资金
stock_individual_fund_flow()  # 个股资金流向

# 北向资金
stock_hsgt_hist_em()          # 沪深港通历史数据

# 龙虎榜
stock_lhb_detail_daily_sina() # 龙虎榜详情
```

### 3.3 API调用规范
```python
# ✅ 正确示例
import akshare as ak
import pandas as pd
from typing import Optional

def fetch_market_spot() -> Optional[pd.DataFrame]:
    """
    获取A股实时行情数据
    
    API: ak.stock_zh_a_spot_em()
    AKShare版本: 1.11.0+
    更新频率: 实时
    """
    try:
        df = ak.stock_zh_a_spot_em()
        df['fetch_time'] = pd.Timestamp.now()
        return df
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        return None

# ❌ 错误示例 - 不要这样做
def get_data():  # 函数名不清晰
    return ak.some_random_api()  # 未验证的API
```

---

## 4. 数据模型规范

### 4.1 数据库表结构

```sql
-- 市场概况表
CREATE TABLE market_overview (
    date DATE PRIMARY KEY,
    total_stocks INTEGER,
    up_count INTEGER,
    down_count INTEGER,
    limit_up_count INTEGER,
    limit_down_count INTEGER,
    total_amount DECIMAL(20,2),
    sentiment_score DECIMAL(5,2),
    northbound_net DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 板块数据表
CREATE TABLE sector_data (
    date DATE,
    sector_code VARCHAR(20),
    sector_name VARCHAR(50),
    change_pct DECIMAL(8,4),
    amount DECIMAL(20,2),
    main_inflow DECIMAL(20,2),
    up_count INTEGER,
    down_count INTEGER,
    leader_stock VARCHAR(20),
    strength_score DECIMAL(5,2),
    PRIMARY KEY (date, sector_code)
);

-- 个股数据表
CREATE TABLE stock_data (
    date DATE,
    code VARCHAR(20),
    name VARCHAR(50),
    sector_codes TEXT,  -- JSON格式存储多个板块
    close_price DECIMAL(10,4),
    change_pct DECIMAL(8,4),
    volume_ratio DECIMAL(8,4),
    main_inflow_1d DECIMAL(20,2),
    main_inflow_5d DECIMAL(20,2),
    main_inflow_10d DECIMAL(20,2),
    PRIMARY KEY (date, code)
);

-- 选股结果表
CREATE TABLE stock_picks (
    date DATE,
    strategy VARCHAR(20),
    code VARCHAR(20),
    name VARCHAR(50),
    score DECIMAL(5,2),
    reason TEXT,
    PRIMARY KEY (date, strategy, code)
);
```

### 4.2 DataFrame规范

```python
# 统一列名规范 (snake_case)
COLUMNS = {
    'code': '股票代码',
    'name': '股票名称', 
    'close': '收盘价',
    'change_pct': '涨跌幅',
    'volume': '成交量',
    'volume_ratio': '量比',
    'main_inflow': '主力净流入',
    'sector_name': '板块名称',
    'sector_change_pct': '板块涨跌幅'
}

# 数据类型规范
DTYPES = {
    'code': 'str',
    'close': 'float64',
    'change_pct': 'float64',
    'volume': 'int64',
    'main_inflow': 'float64'
}
```

---

## 5. 算法实现规范

### 5.1 板块强度计算算法

```python
class SectorStrengthCalculator:
    """
    板块强度评分计算器
    
    评分维度 (总分100分):
    - 涨跌幅: 25%
    - 资金流入占比: 25%
    - 板块贡献度: 25%
    - 龙头表现: 25%
    """
    
    WEIGHTS = {
        'change_pct': 0.25,
        'fund_flow_ratio': 0.25,
        'contribution': 0.25,
        'leader_performance': 0.25
    }
    
    def calculate(self, sector_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算板块强度评分
        
        Args:
            sector_data: 板块原始数据
            
        Returns:
            包含strength_score的DataFrame
        """
        # 实现评分逻辑
        pass
```

### 5.2 选股策略规范

```python
from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd

class StockSelectionStrategy(ABC):
    """选股策略抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @abstractmethod
    def select(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        执行选股
        
        Args:
            market_data: 全市场数据
            
        Returns:
            精选股票DataFrame (包含score和reason列)
        """
        pass
    
    @abstractmethod
    def validate(self, stock_data: pd.DataFrame) -> bool:
        """验证股票是否符合策略条件"""
        pass

# 具体策略实现示例
class MomentumStrategy(StockSelectionStrategy):
    """动量策略 - 追涨"""
    
    name = "momentum"
    
    # 选股条件
    MIN_CHANGE_PCT = 2.0   # 最小涨幅
    MAX_CHANGE_PCT = 7.0   # 最大涨幅 (避免涨停)
    MIN_VOLUME_RATIO = 1.5 # 最小量比
    MIN_AMOUNT = 3e8       # 最小成交额(元)
    
    def select(self, market_data: pd.DataFrame) -> pd.DataFrame:
        filtered = market_data[
            (market_data['change_pct'] >= self.MIN_CHANGE_PCT) &
            (market_data['change_pct'] <= self.MAX_CHANGE_PCT) &
            (market_data['volume_ratio'] >= self.MIN_VOLUME_RATIO) &
            (market_data['amount'] >= self.MIN_AMOUNT)
        ].copy()
        
        # 计算得分
        filtered['score'] = (
            filtered['change_pct'] * 0.4 +
            (filtered['volume_ratio'] - 1) * 10 * 0.2 +
            filtered['main_inflow'] / 1e8 * 0.4
        )
        
        filtered['reason'] = '动量突破: 涨幅' + filtered['change_pct'].astype(str) + '%'
        
        return filtered.sort_values('score', ascending=False).head(10)
```

---

## 6. 代码风格规范

### 6.1 Python代码规范
- 遵循 PEP 8 编码规范
- 使用类型注解 (Type Hints)
- 函数长度不超过 50 行
- 类长度不超过 200 行
- 圈复杂度不超过 10

### 6.2 命名规范
```python
# 变量名 - snake_case
total_amount = 1000000.0
is_market_open = True

# 函数名 - snake_case
def calculate_sector_strength(data):
    pass

# 类名 - PascalCase
class ReportGenerator:
    pass

# 常量 - UPPER_SNAKE_CASE
MAX_STOCK_PICKS = 10
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# 私有成员 - 下划线前缀
def _internal_helper():
    pass
```

### 6.3 文档字符串规范
```python
def fetch_fund_flow(
    start_date: str,
    end_date: str,
    sector_code: Optional[str] = None
) -> pd.DataFrame:
    """
    获取资金流向数据
    
    Args:
        start_date: 开始日期, 格式 YYYY-MM-DD
        end_date: 结束日期, 格式 YYYY-MM-DD
        sector_code: 板块代码, 默认为None表示全市场
        
    Returns:
        资金流向DataFrame, 包含以下列:
        - date: 日期
        - code: 股票代码
        - name: 股票名称
        - main_inflow: 主力净流入(元)
        - retail_inflow: 散户净流入(元)
        
    Raises:
        ValueError: 日期格式错误
        APIError: AKShare接口调用失败
        
    Examples:
        >>> df = fetch_fund_flow('2024-01-01', '2024-01-31', 'BK0428')
        >>> print(df.head())
    """
    pass
```

---

## 7. 错误处理规范

### 7.1 异常层次
```python
class FundFlowSystemError(Exception):
    """系统基础异常"""
    pass

class DataFetchError(FundFlowSystemError):
    """数据获取异常"""
    pass

class DataValidationError(FundFlowSystemError):
    """数据验证异常"""
    pass

class AnalysisError(FundFlowSystemError):
    """分析计算异常"""
    pass
```

### 7.2 错误处理模式
```python
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, exceptions=(Exception,)):
    """失败重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"{func.__name__} 第{attempt+1}次尝试失败: {e}")
                    if attempt == max_retries - 1:
                        raise
        return wrapper
    return decorator

# 使用示例
@retry_on_failure(max_retries=3, exceptions=(DataFetchError,))
def fetch_market_data():
    """获取市场数据(带重试)"""
    pass
```

---

## 8. 日志规范

### 8.1 日志配置
```python
import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / f"{datetime.now():%Y%m%d}.log", encoding='utf-8')
        ]
    )
```

### 8.2 日志级别使用
```python
# DEBUG - 调试信息
logger.debug(f"原始数据行数: {len(df)}")

# INFO - 正常流程
logger.info("开始获取市场数据...")
logger.info(f"成功获取 {len(df)} 条股票数据")

# WARNING - 警告信息
logger.warning(f"API调用延迟: {delay}s")

# ERROR - 错误信息
logger.error(f"获取数据失败: {e}")

# CRITICAL - 严重错误
logger.critical("数据库连接失败，系统即将退出")
```

---

## 9. 测试规范

### 9.1 测试结构
```python
# tests/test_analyzer.py
import unittest
import pandas as pd
from core.analyzer import SectorStrengthCalculator

class TestSectorStrengthCalculator(unittest.TestCase):
    """板块强度计算器测试"""
    
    def setUp(self):
        """测试前置"""
        self.calculator = SectorStrengthCalculator()
        self.sample_data = pd.DataFrame({
            'sector_code': ['BK001', 'BK002'],
            'sector_name': ['AI算力', '机器人'],
            'change_pct': [3.2, 2.8],
            'main_inflow': [5e8, 3e8]
        })
    
    def test_calculate_returns_dataframe(self):
        """测试返回值类型"""
        result = self.calculator.calculate(self.sample_data)
        self.assertIsInstance(result, pd.DataFrame)
    
    def test_score_range(self):
        """测试分数范围"""
        result = self.calculator.calculate(self.sample_data)
        self.assertTrue((result['strength_score'] >= 0).all())
        self.assertTrue((result['strength_score'] <= 100).all())
```

### 9.2 测试覆盖率要求
- 核心算法: ≥ 90%
- 数据获取: ≥ 70%
- 报告生成: ≥ 60%

---

## 10. 报告格式规范

### 10.1 JSON报告结构
```json
{
  "meta": {
    "report_id": "RPT20260319090000",
    "date": "2026-03-19",
    "data_source": "AKShare",
    "version": "1.0",
    "generated_at": "2026-03-19T09:00:00+08:00"
  },
  "summary": {
    "market_sentiment": "短期偏乐观",
    "sentiment_score": 68.5,
    "top_sector": "AI算力",
    "focus_action": "关注AI算力板块回调买入机会",
    "risk_level": "中"
  },
  "market_overview": {
    "total_stocks": 5380,
    "up_count": 3200,
    "down_count": 2100,
    "limit_up_count": 45,
    "limit_down_count": 8,
    "total_amount": 125000000000,
    "northbound_net": 1250000000
  },
  "sector_ranking": [
    {
      "rank": 1,
      "sector_code": "BK0428",
      "sector_name": "AI算力",
      "change_pct": 3.2,
      "main_inflow": 850000000,
      "strength_score": 82.5,
      "leader_stock": "中科曙光"
    }
  ],
  "stock_picks": {
    "momentum": [
      {
        "code": "603019",
        "name": "中科曙光",
        "change_pct": 5.2,
        "volume_ratio": 1.8,
        "score": 85.3,
        "reason": "动量突破: 涨幅5.2%, 量比1.8"
      }
    ],
    "reversal": [],
    "fund_flow": []
  },
  "risk_assessment": {
    "market_risk": "中等",
    "sector_risk": "AI板块过热",
    "suggestions": ["控制仓位50%", "避免追高"]
  },
  "action_plan": {
    "watchlist": ["603019", "002527"],
    "position_suggestion": "50%",
    "key_events": ["关注美联储利率决议", "关注北向资金流向"]
  }
}
```

### 10.2 可视化报告规范
```python
# 图表配色方案
COLOR_SCHEME = {
    'up': '#E74C3C',      # 红色 - 上涨
    'down': '#27AE60',    # 绿色 - 下跌  
    'neutral': '#95A5A6', # 灰色 - 中性
    'highlight': '#F39C12', # 橙色 - 重点
    'primary': '#3498DB',   # 蓝色 - 主色
}

# 图表尺寸规范
FIGURE_SIZES = {
    'sector_ranking': (12, 8),
    'market_overview': (10, 6),
    'stock_picks': (14, 10)
}
```

---

## 11. 性能规范

### 11.1 响应时间要求
| 操作 | 目标时间 | 最大时间 |
|------|----------|----------|
| 数据采集 | < 30s | 60s |
| 数据分析 | < 10s | 30s |
| 报告生成 | < 20s | 60s |
| 总耗时 | < 2min | 5min |

### 11.2 资源使用限制
- 内存: < 2GB
- CPU: < 50%
- 磁盘: 日志保留30天，数据库保留1年

---

## 12. 安全规范

### 12.1 敏感信息处理
```python
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ 正确 - 使用环境变量
DB_PASSWORD = os.getenv('DB_PASSWORD')
API_KEY = os.getenv('API_KEY')

# ❌ 错误 - 硬编码密码
DB_PASSWORD = "123456"
```

### 12.2 数据脱敏
```python
def mask_sensitive_data(data: dict) -> dict:
    """脱敏敏感数据"""
    masked = data.copy()
    sensitive_keys = ['password', 'api_key', 'secret', 'token']
    for key in sensitive_keys:
        if key in masked:
            masked[key] = '***'
    return masked
```

---

## 13. 回复后缀规范

每个助手回复必须以以下后缀结尾：

```
喵~
```

---

## 14. 编码安全规范

### 14.1 文件操作
- 所有源文件使用 UTF-8 编码
- 避免全文件重写，优先使用补丁编辑
- 编辑后运行完整性检查：
  ```bash
  python tools/verify_source_integrity.py --root .
  ```

### 14.2 版本控制
```bash
# 提交前检查
python -m pytest tests/ -q
python -m flake8 core/ --max-line-length=100
python tools/verify_source_integrity.py --root .
```

---

## 15. 实施检查清单

### 15.1 代码提交前检查
- [ ] 代码通过所有单元测试
- [ ] 代码通过 flake8 检查
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 日志敏感信息已脱敏
- [ ] 编码完整性检查通过

### 15.2 功能实现检查
- [ ] AKShare API调用符合官方文档
- [ ] 错误处理覆盖所有异常路径
- [ ] 数据验证逻辑完整
- [ ] 性能满足响应时间要求
- [ ] 内存使用在限制范围内

---

*最后更新: 2026-03-19*  
*文档版本: v1.0*
