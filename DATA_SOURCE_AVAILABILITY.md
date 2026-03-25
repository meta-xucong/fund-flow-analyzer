# AKShare数据源可用性报告

## 测试时间
2026-03-22

## 网络环境
- Clash代理开启
- NO_PROXY已设置

---

## ✅ 可用数据源 (6个)

| 数据源 | API名称 | 返回数据量 | 用途 |
|--------|---------|-----------|------|
| **腾讯历史** | `stock_zh_a_hist_tx` | 8369条 | ⭐主要数据源，单只股票历史数据完整 |
| **新浪日线** | `stock_zh_a_daily` | 2条 | 单只股票日线数据 |
| **股票列表** | `stock_info_a_code_name` | 5491只 | 全市场股票代码和名称 |
| **异动数据** | `stock_changes_em` | 1645条 | 涨跌停、大幅波动等异动股票 |
| **个股资金** | `stock_individual_fund_flow` | 120条 | 单只股票资金流向 |
| **新浪实时** | `core.sina_fetcher` | 500只 | ⭐自定义获取器，实时行情 |

---

## ❌ 不可用数据源 (9个)

| 数据源 | API名称 | 失败原因 |
|--------|---------|----------|
| 东财实时 | `stock_zh_a_spot_em` | 连接被拒绝 (IP被封) |
| 同花顺实时 | `stock_zh_a_spot` | JSON解析错误 (返回HTML) |
| 腾讯实时 | `stock_zh_a_spot_tx` | API不存在 (AttributeError) |
| 东财历史 | `stock_zh_a_hist` | 连接被拒绝 (IP被封) |
| 新股 | `stock_zh_a_new` | JSON解析错误 |
| 港股 | `stock_hk_spot_em` | 连接被拒绝 (IP被封) |
| 美股 | `stock_us_spot_em` | 连接被拒绝 (IP被封) |
| 板块资金 | `stock_sector_fund_flow_rank` | 连接被拒绝 (IP被封) |
| 龙虎榜 | `stock_lhb_detail_daily_sina` | 参数错误 |

---

## 🎯 推荐数据源组合

### 方案1: 实时数据获取 (用于每日9:25选股)
```python
from core.sina_fetcher import SinaDataFetcher

fetcher = SinaDataFetcher()
df = fetcher.fetch_market_spot(500)  # 获取500只样本
```
**可用字段:**
- code, name, latest, change_pct
- volume, amount, volume_ratio
- pe, pb, turnover
- buy/sell 1-5 price/vol

### 方案2: 单只股票历史数据 (用于回测)
```python
import akshare as ak

# 腾讯历史 - 数据完整
df = ak.stock_zh_a_hist_tx(symbol='sz000001')

# 新浪日线
df = ak.stock_zh_a_daily(symbol='sh600000', start_date='20250320', end_date='20250321')
```

### 方案3: 全市场股票列表
```python
import akshare as ak

# 获取所有股票代码
df = ak.stock_info_a_code_name()  # 5491只
```

### 方案4: 市场异动监控
```python
import akshare as ak

# 获取异动股票（涨跌停、大幅波动等）
df = ak.stock_changes_em()  # 1645条
```

---

## 📊 数据覆盖度

| 数据类型 | 覆盖率 | 数据源 |
|----------|--------|--------|
| 全市场股票列表 | 100% | stock_info_a_code_name |
| 实时行情 | ~9% (500/5491) | sina_fetcher |
| 单只股票历史 | 100% | stock_zh_a_hist_tx |
| 资金流向 | 个股可用 | stock_individual_fund_flow |
| 板块资金 | ❌ 不可用 | - |
| 龙虎榜 | ❌ 不可用 | - |

---

## ⚠️ 限制说明

### 实时数据限制
- 新浪获取器每次最多获取500只股票（API限制）
- 无法获取全市场实时数据
- 适合作为样本分析，不适合全市场扫描

### 历史数据限制
- 腾讯历史只能单只查询
- 批量获取需要逐个调用（较慢）
- 没有全市场历史数据接口

### 无法获取的数据
- ❌ 北向资金流向 (东财API被封)
- ❌ 板块资金流向 (东财API被封)
- ❌ 龙虎榜数据 (接口错误)
- ❌ 港股、美股实时数据

---

## 💡 解决方案建议

### 短期 (1-2周)
使用新浪获取器每天收集500只样本数据，累积历史数据

### 中期 (1-3月)
接入Tushare Pro付费API获取完整历史数据

### 长期
搭建本地数据中心，积累自己的历史数据库
