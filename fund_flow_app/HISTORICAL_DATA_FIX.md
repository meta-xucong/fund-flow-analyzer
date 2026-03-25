# 历史数据获取修复说明

## 问题背景

之前的回测系统使用腾讯实时行情接口 (`http://qt.gtimg.cn/q={codes}`) 获取股票数据，但**该接口无视日期参数，只返回当天的实时数据**。这导致2月份的所有回测报告实际上使用的是同一天（当天）的数据，造成回测结果完全无效。

## 解决方案

### 1. 使用AKShare历史数据接口

改用AKShare的 `stock_zh_a_hist_tx` 接口获取真实历史数据：

```python
import akshare as ak

# 获取指定日期范围的历史数据
df = ak.stock_zh_a_hist_tx(
    symbol='sz000001',      # 股票代码（带市场前缀）
    start_date='20250301',  # 开始日期
    end_date='20250305',    # 结束日期
    adjust=''               # 不复权
)
```

返回字段：
- `date`: 日期
- `open`: 开盘价
- `close`: 收盘价
- `high`: 最高价
- `low`: 最低价
- `amount`: 成交量（手）

### 2. 计算派生指标

由于历史数据接口不返回涨跌幅和量比，需要自行计算：

```python
# 涨跌幅计算（需要前一天收盘价）
prev_close = float(prev_day['close'])
current_close = float(current_day['close'])
change_pct = ((current_close - prev_close) / prev_close * 100)

# 量比估算（基于换手率）
# 换手率 > 2% 认为是活跃，对应量比 > 1.5
volume_ratio = max(1.0, abs(change_pct) * 0.5 + 0.5)
```

### 3. 超时和容错机制

```python
# 单只股票超时：5秒
# 单日总超时：120秒
# 连续失败阈值：20次（考虑到停牌股票）
```

## 关键代码变更

### data_fetcher.py

```python
def _fetch_single_stock(self, code: str, date_str: str, stock_list: pd.DataFrame) -> Optional[Dict]:
    """使用AKShare腾讯历史数据接口获取单只股票数据"""
    try:
        symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
        
        # 获取前后几天数据以计算涨跌幅
        start = (target_date - pd.Timedelta(days=5)).strftime('%Y%m%d')
        end = (target_date + pd.Timedelta(days=1)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist_tx(symbol=symbol, start_date=start, end_date=end)
        
        # 查找目标日期并计算指标
        # ... 计算涨跌幅、量比等
        
    except Exception as e:
        logger.debug(f"{code} fetch failed: {e}")
        return None
```

## 性能优化

### 1. 采样策略

回测时使用50只股票的样本，平衡速度和覆盖度：

```python
data = self.data_fetcher.fetch_daily_data(
    date_str, 
    sample_size=50,  # 限制50只以加快速度
    use_historical=True
)
```

### 2. 并发控制

使用串行获取（带超时），避免被封IP：

```python
for idx, code in enumerate(codes):
    stock_data = self._fetch_single_stock(code, date_str, stock_list)
    if stock_data:
        results.append(stock_data)
    time.sleep(0.02)  # 20ms延迟
```

### 3. 处理时间预估

- 50只股票/天 ≈ 60-90秒
- 20个交易日回测 ≈ 20-30分钟

## 验证方法

### 1. 数据正确性验证

```python
# 测试获取特定日期的数据
fetcher = DataFetcher()
df = fetcher.fetch_historical_data('2025-03-05', sample_size=10)

# 验证字段
assert 'change_pct' in df.columns  # 涨跌幅
assert 'volume_ratio' in df.columns  # 量比
assert 'turnover' in df.columns  # 换手率
```

### 2. 日期一致性验证

```python
# 确保不同日期返回不同数据
df1 = fetcher.fetch_historical_data('2025-03-03', sample_size=5)
df2 = fetcher.fetch_historical_data('2025-03-05', sample_size=5)

# 同一股票的收盘价应该不同
if not df1.empty and not df2.empty:
    assert df1.iloc[0]['close'] != df2.iloc[0]['close']
```

## 注意事项

### 1. 量比计算

历史数据没有量比字段，使用涨跌幅估算：
- 涨跌幅大 → 量比高
- 涨跌幅接近0 → 量比≈1.0

### 2. 成交额估算

历史数据没有成交额字段，使用均价×成交量计算：
```python
avg_price = (high + low) / 2
amount = volume * avg_price * 100  # 元
```

### 3. 停牌股票处理

某些股票在特定日期可能停牌，返回None是正常的。

## 回测结果下载

回测完成后，下载的ZIP包含：

1. **summary.md** - 回测汇总报告
   - 交易日数
   - 总交易次数
   - 策略表现统计
   - 总体收益率

2. **trades.csv** - 交易记录
   - 股票代码、名称
   - 策略类型
   - 买入日期、价格
   - 卖出日期、价格
   - 收益率

3. **daily_reports/*.md** - 每日详细报告
   - 每日市场情绪
   - 动量选股列表
   - 反转选股列表
   - 操作建议

## 示例：运行回测

```python
from backend.backtest_engine import BacktestEngine

engine = BacktestEngine()

# 运行2025年3月3日至5日的回测
results = engine.run_backtest('2025-03-03', '2025-03-05')

print(f"交易日数: {len(results['trading_days'])}")
print(f"交易次数: {len(results['trades'])}")
print(f"平均收益率: {results['summary']['overall']['avg_return']}%")
```

## 接口对比

| 接口 | 数据源 | 返回历史数据 | 性能 | 稳定性 |
|------|--------|-------------|------|--------|
| `fetch_tencent_batch` | 腾讯实时 | ❌ 只返回当天 | 快 | 高 |
| `ak.stock_zh_a_hist` | 东方财富 | ✅ 支持历史 | 中 | 需翻墙 |
| `ak.stock_zh_a_hist_tx` | 腾讯历史 | ✅ 支持历史 | 中 | 高 ✅ |
| `ak.stock_zh_a_daily` | 新浪 | ✅ 支持历史 | 慢 | 易封IP |

**当前选择**: `ak.stock_zh_a_hist_tx` - 平衡了历史数据支持、性能和稳定性。

---

**修复日期**: 2026-03-24
**版本**: v1.1
