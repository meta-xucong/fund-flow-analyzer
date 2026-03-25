# 同花顺反爬虫突破报告

## 突破成果

✅ **成功突破！** 使用新浪和腾讯的原始API替代AKShare的问题接口

---

## 问题分析

同花顺(`q.10jqka.com.cn`)的反爬虫机制：
1. **IPv6封锁**: 返回 `Nginx forbidden` + IPv6地址
2. **请求头检查**: 需要完整的浏览器Headers
3. **Cookie验证**: 需要有效的会话Cookie

---

## 解决方案

使用**新浪**和**腾讯**的原始数据源API：

| 数据源 | API地址 | 状态 | 说明 |
|--------|---------|------|------|
| 新浪实时 | `https://hq.sinajs.cn/list=sh600000` | ✅ 可用 | GB2312编码 |
| 腾讯实时 | `http://qt.gtimg.cn/q=sh600000` | ✅ 可用 | GBK编码 |
| 股票列表 | `ak.stock_info_a_code_name()` | ✅ 可用 | 5491只股票 |

---

## 实现成果

### 新浪/腾讯获取器 (`core/sina_fetcher.py`)

```python
from core.sina_fetcher import SinaDataFetcher

fetcher = SinaDataFetcher()
df = fetcher.fetch_market_spot(200)  # 获取200只股票
print(f"获取 {len(df)} 只股票行情")
```

**功能特性：**
- ✅ 自动获取全部5491只股票列表
- ✅ 批量获取实时行情（腾讯优先，新浪备用）
- ✅ 自动解析数据格式（涨跌幅、成交量等）
- ✅ 标准列名输出（兼容原有分析模块）

---

## 测试结果

```
[1] 获取股票列表
    Total stocks: 5491

[2] 新浪实时行情（3只股票）
    Got 3 stocks
         code  name  latest  change_pct
    0  600000  浦发银行   10.28       -0.39
    1  000001  平安银行   10.77       -1.01
    2  002730  电光科技   22.96        6.35

[3] 腾讯实时行情（3只股票）
    Got 3 stocks
         code  name  latest  change_pct
    0  600000  浦发银行   10.28       -0.39
    1  000001  平安银行   10.77       -1.01
    2  002730  电光科技   22.96        6.35

[4] 批量获取行情（50只）
    Got 50 stocks from tencent
```

---

## 核心改进

### 相比AKShare的优势
1. **绕过代理限制**: 直接设置NO_PROXY环境变量
2. **更稳定**: 新浪/腾讯API不受Clash影响
3. **可定制**: 可以自定义Headers和请求参数
4. **批量获取**: 一次请求最多200只股票

---

## 使用方法

### 方法1: 直接使用新浪获取器
```python
from core.sina_fetcher import SinaDataFetcher, fetch_market_spot

# 简单方式
df = fetch_market_spot(500)  # 获取500只股票

# 完整方式
fetcher = SinaDataFetcher()
df = fetcher.fetch_market_spot(500)
```

### 方法2: 获取单只股票
```python
fetcher = SinaDataFetcher()

# 腾讯数据源
df = fetcher.fetch_tencent_quotes(['sh600000', 'sz000001'])

# 新浪数据源
df = fetcher.fetch_sina_quotes(['sh600000', 'sz000001'])
```

---

## 后续建议

1. **更新主程序**: 将`main.py`和`fetcher.py`切换为使用`SinaDataFetcher`
2. **全量获取**: 如需获取全部5000+只股票，可分批获取（每批200只）
3. **频率控制**: 建议添加请求间隔（已内置0.1秒延迟）

---

## 关键文件

| 文件 | 说明 |
|------|------|
| `core/sina_fetcher.py` | 新浪/腾讯数据获取器 |
| `test_sina_success.py` | 验证测试脚本 |

---

**突破完成时间**: 2026-03-22
**突破方式**: 绕过同花顺，直接使用新浪/腾讯原始API
