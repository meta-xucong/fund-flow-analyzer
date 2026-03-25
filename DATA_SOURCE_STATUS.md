# 数据源可用性状态报告

## 测试环境
- **时间**: 2026-03-22
- **网络**: Clash代理 (127.0.0.1:7890)

---

## 数据源可用性列表

| 序号 | 数据源 | API名称 | 状态 | 返回记录 | 失败原因 |
|------|--------|---------|------|----------|----------|
| 1 | 同花顺/新浪实时 | `stock_zh_a_spot` | ❌ 不可用 | 0 | JSONError - 返回HTML而非JSON |
| 2 | 东财实时 | `stock_zh_a_spot_em` | ❌ 不可用 | 0 | ProxyBlocked - 代理屏蔽 |
| 3 | 东财历史 | `stock_zh_a_hist` | ❌ 不可用 | 0 | ProxyBlocked - 代理屏蔽 |
| 4 | **腾讯历史** | `stock_zh_a_hist_tx` | ✅ **可用** | 2651 | OK |
| 5 | 新股 | `stock_zh_a_new` | ❌ 不可用 | 0 | JSONDecodeError |
| 6 | 港股 | `stock_hk_spot_em` | ❌ 不可用 | 0 | ProxyBlocked |
| 7 | **新浪日线** | `stock_zh_a_daily` | ✅ **可用** | 2 | OK |

---

## 当前可用数据源 (2个)

### 1. 腾讯历史数据 (`stock_zh_a_hist_tx`)
```python
import akshare as ak
df = ak.stock_zh_a_hist_tx(symbol='sz002730')  # 使用sz/sh前缀
```
- **特点**: 单只股票历史数据，2651条记录
- **限制**: 不能获取全市场，只能一只一只取
- **速度**: 慢 (约19秒/只)

### 2. 新浪日线数据 (`stock_zh_a_daily`)
```python
import akshare as ak
df = ak.stock_zh_a_daily(symbol='sh600000', start_date='20250320', end_date='20250321')
```
- **特点**: 单只股票日线数据
- **限制**: 需要已知股票代码，无法获取全市场列表
- **速度**: 快

---

## 多源获取器轮询排序

当前 `core/multi_source_fetcher.py` 的轮询优先级：

```
Priority 1: tonghuashun_sina (同花顺/新浪实时) - ❌ 实际不可用
Priority 2: tencent_spot (腾讯实时) - ❌ API不存在
Priority 3: eastmoney_spot (东财实时) - ❌ 被禁用
Priority 4: tencent_hist (腾讯历史) - ✅ 可用但慢
Priority 5: new_stocks (新股) - ❌ 不可用
Priority 6: hk_spot (港股) - ❌ 不可用
```

**实际可用链**: 
- Primary: 腾讯历史 (`stock_zh_a_hist_tx`) - 单只股票历史
- Secondary: 新浪日线 (`stock_zh_a_daily`) - 单只股票日线

**问题**: 没有能获取全市场股票列表的API！

---

## 当前解决方案

由于无法获取全市场实时数据，系统提供三种运行模式：

### 模式1: 模拟数据模式 (推荐用于开发测试)
```python
from core.fetcher_v2 import get_fetcher_v2, DataFetcherV2
fetcher = get_fetcher_v2(mode=DataFetcherV2.MODE_MOCK)
df = fetcher.fetch_market_spot()  # 返回500只模拟股票
```

### 模式2: 缓存模式 (如果有历史缓存)
```python
fetcher = get_fetcher_v2(mode=DataFetcherV2.MODE_CACHE)
df = fetcher.fetch_market_spot()  # 从本地缓存读取
```

### 模式3: 网络模式 (不可用)
```python
fetcher = get_fetcher_v2(mode=DataFetcherV2.MODE_NETWORK)
df = fetcher.fetch_market_spot()  # 会失败并自动降级到模拟数据
```

---

## 结论

**当前网络环境下，实时全市场数据获取不可行。**

可选方案：
1. **开发测试**: 使用模拟数据模式 (已验证核心功能正常)
2. **实盘运行**: 需要切换网络环境或接入其他数据源
3. **替代方案**: 使用Tushare Pro、Wind等付费API
