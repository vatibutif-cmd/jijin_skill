# FAMAS 数据架构规范（分层数据治理）

> **版本**: v1.0 | **更新**: 2026-08-03
> **核心铁律**: **旧数据不能冒充新数据**。预期有数据但数据源未给 → 显示"待更新"

---

## 一、数据源分层策略

| 数据源 | 角色 | 用途 | 稳定性 |
|--------|------|------|--------|
| **etfirst** | 主干数据 | 基金净值、板块净流入、指数估值分位 | ✅ 稳定 |
| **腾讯行情** | 盘中实时 | 个股/指数实时涨跌 | ✅ 稳定 |
| **AKShare/东财** | 兜底 | 基金净值、大盘资金 | ⚠️ 部分接口限流 |
| **hithink-finance** | 同花顺补充 | A股行情、财报、ETF | ✅ 已集成 |

## 二、分层架构

```
┌─────────────────────────────────────────────┐
│  数据源层: Tushare / AKShare / 腾讯 / etfirst │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  ODS 原始数据层                               │
│  保存数据源原始返回（不修改、不加工）            │
│  ods/tushare_20260803/ stock_daily.csv       │
│  ods/tencent_20260803/ quote_600519.json     │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  DWD 明细数据层                               │
│  清洗、字段映射、标准化、去重                   │
│  统一字段: ts_code, trade_date, open/high/... │
│  数据新鲜度标记: data_date, freshness          │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  ADS 应用数据层                               │
│  指标计算: 均线/MACD/RSI/资金连续性/估值分位    │
│  聚合: 板块资金、持仓评分、组合诊断              │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  API 服务层                                   │
│  统一接口: /api/quote /api/fund /api/sector   │
│  返回含 freshness 字段，Agent 据此判断        │
│  旧数据不能冒充新数据 → 数据源未给返回 pending  │
└─────────────────────────────────────────────┘
```

## 三、数据新鲜度铁律

### 3.1 核心规则

> **旧数据不能冒充新数据。** 如果预期交易日应该有数据，但数据源还没给，页面就显示"待更新"。

### 3.2 新鲜度判定

| 数据类型 | 预期更新频率 | 过期阈值 | 显示规则 |
|---------|------------|---------|---------|
| 股票/指数实时行情 | 盘中实时 | >15分钟 | 过期→"待更新" |
| 日线行情 | 每个交易日收盘后 | 数据日期 < 最近交易日 | →"待更新" |
| 基金净值 | 每个交易日收盘后 | 净值日期 < 最近交易日 | →"待更新" |
| 财务数据 | 季报/年报 | 报告期过期 | →标注报告期 |
| 板块资金 | 每日收盘后 | < 最近交易日 | →"待更新" |

### 3.3 实现方式

每条记录带 `data_date` + `freshness` 字段：
```json
{
  "data_date": "2026-08-01",
  "freshness": "fresh",        // fresh / stale / pending
  "expected_update": "2026-08-01 15:00",
  "data_source": "tushare"
}
```

### 3.4 判定逻辑

```
1. 计算最近预期交易日: 从交易日历获取（排除周末/节假日）
2. 比较数据日期 vs 最近交易日:
   - data_date == 最近交易日 → fresh
   - data_date < 最近交易日 → stale（旧数据）
   - 无数据但应有 → pending（待更新）
3. 前端根据 freshness:
   - fresh → 显示数值
   - stale/pending → 显示"待更新"
```

## 四、各层实现规范

### ODS 原始数据层
- 按 `数据源_日期/表名` 存储原始返回
- 不做任何清洗修改
- 文件格式: 原始 CSV/JSON

### DWD 明细数据层
- 统一字段命名（snake_case）
- 数据清洗（去空、类型转换、去重）
- 添加 `data_date`、`data_source` 标记
- 输出标准化 CSV/Parquet

### ADS 应用数据层
- 指标计算（复用 scripts/ 下已有工具）
- 板块聚合（资金连续性等）
- 持仓/组合分析结果

### API 服务层
- 统一返回 JSON: `{data, data_date, freshness, data_source}`
- 调用各层数据，计算 freshness

### 前端展示层
- 接收 API 的 freshness 字段
- `fresh` → 显示数值
- `stale/pending` → 显示"待更新"（醒目提示）

## 五、目录结构

```
FAMAS-Skill/
├── ods/          原始数据层
├── dwd/          明细数据层
├── ads/          应用数据层
├── api/          服务端API
├── web/          前端页面
├── scripts/      工具脚本
│   ├── fetchers/    数据获取（tushare/akshare/tencent/etfirst）
│   ├── processors/  清洗加工
│   └── indicators/  指标计算
└── data/         运行数据
```

## 六、数据源接入优先级

```
etfirst(主干) > 腾讯(实时) > AKShare(兜底) > hithink(补充)
```

获取数据时按优先级依次尝试，全部失败返回 `pending` 状态。

## 七、当前实现状态（2026-08-03）

### 已实现

| 层 | 组件 | 状态 |
|----|------|------|
| 数据源 | etfirst（主干）、腾讯行情、AKShare、hithink | ✅ |
| 获取器 | `scripts/fetchers/tencent_quote.py`（腾讯实时） | ✅ 稳定 |
| 调度器 | `scripts/data_scheduler.py`（etfirst主干+腾讯实时+新鲜度） | ✅ |
| 新鲜度 | `scripts/processors/freshness.py`（fresh/stale/pending） | ✅ |
| 指标 | `scripts/indicators/`（RSI等） | ✅ |

### 数据服务命令

```bash
python3 scripts/data_scheduler.py quote 600519    # 股票实时行情（腾讯）
python3 scripts/data_scheduler.py nav 024418      # 基金净值（etfirst）
python3 scripts/data_scheduler.py sector 930601   # 板块数据（etfirst）
python3 scripts/data_scheduler.py sectors         # 全部板块资金连续性
```

### 验证结果

```
/api/quote/600519  → 贵州茅台 1350.6 (-0.82%) fresh
/api/nav/024418    → 净值 2.1988 fresh
/api/sector/930601 → PE分位 75.48% fresh
```

### 核心铁律落地

"旧数据不能冒充新数据"已实现：
- 数据带 `data_date` + `freshness`
- 过期 → `stale`，前端显示"待更新"
- 数据源未给 → `pending`，前端显示"待更新"
- 全部数据源失败 → 明确返回 pending，不返回旧数据冒充
