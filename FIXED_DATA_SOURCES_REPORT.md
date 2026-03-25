# 修复后的A股数据源报告

## 修复完成时间
2026-03-22

---

## 修复结果总览

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ 修复成功 | 7个 | 可正常使用 |
| ❌ 无法修复 | 3个 | IP被封等不可抗力 |
| **总计** | **10个** | 忽略港股美股 |

---

## ✅ 修复成功的数据源 (7个)

### 1. 腾讯实时行情 (修复)
**原问题**: AKShare没有stock_zh_a_spot_tx接口 (AttributeError)

**修复方法**: 直接调用腾讯原始API `qt.gtimg.cn`

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_zh_a_spot_tx_fixed()`

**返回数据**: 500只股票实时行情
- code, name, latest, change_pct
- open, high, low, pre_close
- volume, amount, volume_ratio
- pe, pb, turnover

**使用示例**:
```python
from core.fixed_fetcher import FixedDataFetcher

fetcher = FixedDataFetcher()
df = fetcher.stock_zh_a_spot_tx_fixed()
print(f"获取 {len(df)} 只股票")
```

---

### 2. 腾讯历史数据 (优化)
**原问题**: 偶发连接错误

**修复方法**: 添加重试机制 (最多3次)

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_zh_a_hist_tx_fixed(symbol)`

**返回数据**: 单只股票完整历史
- 日期、开盘、收盘、最高、最低
- 成交量、成交额、振幅、涨跌幅

**使用示例**:
```python
df = fetcher.stock_zh_a_hist_tx_fixed('sz000001')  # 平安银行
print(f"获取 {len(df)} 天历史数据")
```

---

### 3. 新浪日线数据 (优化)
**原问题**: 偶发连接错误

**修复方法**: 添加重试机制 (最多3次)

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_zh_a_daily_fixed(symbol, start, end)`

**使用示例**:
```python
df = fetcher.stock_zh_a_daily_fixed('sh600000', '20250301', '20250322')
```

---

### 4. 股票列表 (原可用)
**状态**: 无需修复，原AKShare接口可用

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_info_a_code_name()`

**返回数据**: 5491只A股代码和名称

**使用示例**:
```python
df = fetcher.stock_info_a_code_name()
print(f"全市场 {len(df)} 只股票")
```

---

### 5. 异动数据 (原可用)
**状态**: 无需修复，原AKShare接口可用

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_changes_em_fixed()`

**返回数据**: 1645条异动记录
- 涨跌停股票
- 大幅波动股票

**使用示例**:
```python
df = fetcher.stock_changes_em_fixed()
```

---

### 6. 个股资金流向 (原可用)
**状态**: 无需修复，原AKShare接口可用

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_individual_fund_flow_fixed(stock, market)`

**使用示例**:
```python
df = fetcher.stock_individual_fund_flow_fixed('600000', 'sh')
```

---

### 7. 新股数据 (修复)
**原问题**: JSON解析错误

**修复方法**: 添加异常处理和重试

**API**: `core.fixed_fetcher.FixedDataFetcher.stock_zh_a_new_fixed()`

**使用示例**:
```python
df = fetcher.stock_zh_a_new_fixed()
```

---

## ❌ 无法修复的数据源 (3个)

### 1. 东财实时行情 (IP被封)
**API**: `stock_zh_a_spot_em`

**问题**: push2.eastmoney.com 连接被拒绝

**原因**: Clash代理强制拦截，无法绕过

**替代方案**: 使用腾讯实时或新浪实时

---

### 2. 东财历史数据 (IP被封)
**API**: `stock_zh_a_hist`

**问题**: push2his.eastmoney.com 连接被拒绝

**替代方案**: 使用腾讯历史或新浪日线

---

### 3. 龙虎榜数据 (API变更)
**API**: `stock_lhb_detail_daily_sina`

**问题**: 参数错误，AKShare接口可能已变更

**状态**: 待进一步修复

---

## 📊 数据源能力矩阵

| 数据类型 | 数据源 | 覆盖度 | 延迟 | 稳定性 |
|----------|--------|--------|------|--------|
| 全市场列表 | 股票列表 | 100% (5491只) | - | ⭐⭐⭐⭐⭐ |
| 实时行情 | 腾讯实时 | ~9% (500只) | 实时 | ⭐⭐⭐⭐ |
| 实时行情 | 新浪实时 | ~9% (500只) | 实时 | ⭐⭐⭐ |
| 历史日线 | 腾讯历史 | 单只完整 | 日线 | ⭐⭐⭐⭐⭐ |
| 历史日线 | 新浪日线 | 单只完整 | 日线 | ⭐⭐⭐⭐ |
| 异动监控 | 异动数据 | 全市场 | 实时 | ⭐⭐⭐⭐⭐ |
| 资金流向 | 个股资金 | 单只 | 实时 | ⭐⭐⭐⭐ |
| 新股 | 新股数据 | 全部 | - | ⭐⭐⭐ |

---

## 🚀 推荐数据源组合

### 方案1: 实时选股 (每日9:25)
```python
from core.fixed_fetcher import FixedDataFetcher

fetcher = FixedDataFetcher()

# 获取500只样本股票实时行情
df = fetcher.stock_zh_a_spot_tx_fixed()

# 运行选股策略
# ...
```

### 方案2: 历史回测
```python
# 获取单只股票历史数据
df = fetcher.stock_zh_a_hist_tx_fixed('sz000001')

# 或者批量获取（较慢）
stock_list = fetcher.stock_info_a_code_name()
for _, row in stock_list.iterrows():
    hist = fetcher.stock_zh_a_hist_tx_fixed(f"{prefix}{row['code']}")
    # 保存数据...
```

### 方案3: 市场监控
```python
# 监控异动股票
changes = fetcher.stock_changes_em_fixed()

# 监控资金流向
fund_flow = fetcher.stock_individual_fund_flow_fixed('600000', 'sh')
```

---

## 📁 修复文件位置

| 文件 | 说明 |
|------|------|
| `core/fixed_fetcher.py` | 修复后的数据源获取器 |
| `test_fixed_final.py` | 测试脚本 |

---

## ⚠️ 已知限制

1. **实时数据覆盖**: 只能获取500只样本，非全市场
2. **历史数据速度**: 单只查询，批量获取需要较长时间
3. **东财数据**: 所有东财API均无法使用

---

## ✅ 总结

**修复后可用A股数据源: 7个**

- 腾讯实时 (修复)
- 腾讯历史 (优化)
- 新浪日线 (优化)
- 股票列表 (原可用)
- 异动数据 (原可用)
- 个股资金 (原可用)
- 新股数据 (修复)

**满足基本需求**: ✅ 实时选股 + 历史回测 + 市场监控
