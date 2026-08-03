# FAMAS MCP 数据工具层设计文档

> **版本**: v2.1 | **日期**: 2026-08-01 | **数据源**: AKShare + 东方财富实时推送

---

## 一、设计原则

1. **核心 10 个工具**（原 6 工具 + 实时行情/资金流/推送 4 工具），命名空间 `famas-data`，覆盖 10 个 Agent 全链路数据与消息推送需求
2. **每个工具只做一件事**，输入输出边界清晰，不交叉
3. **AKShare 原生接口 + 实时推送一对一映射**，高效稳定
4. **所有工具返回纯 JSON**，不做渲染、不夹带观点——事实输出原则贯彻到数据层
5. 支持 Webhook 通道自动推送 Markdown 预警卡片与诊断报告至钉钉、企业微信、飞书等客户端

---

## 二、10个工具详细定义

### 工具 1: `fund_basic_info`

**功能描述**: 查询单只公募基金的基本信息，包括名称、类型、规模、基金经理、成立日期、费率结构、业绩基准、持有人结构。可同时接受 `keyword` 参数做全市场基金搜索（返回匹配列表），实现"单基金详情 + 全市场检索"双模式。

**兼容 AKShare 接口**: `ak.fund_individual_basic_info_xq()` + `ak.fund_name_em()`

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `fund_code` | string | 否 | `^\d{6}$` | 6位基金代码，与 `keyword` 二选一。传入时返回该基金的完整详情 |
| `keyword` | string | 否 | 1-20字符，中文 | 基金名称或类型关键词（如"沪深300""科技"），与 `fund_code` 二选一。传入时返回匹配基金列表（最多20条） |
| `top_n` | int | 否 | 1-20，默认10 | 仅 `keyword` 模式生效，控制返回条数 |

**输出JSON结构**:

```json
// ===== fund_code 模式返回 =====
{
  "mode": "detail",
  "fund_code": "020712",
  "fund_name": "XX灵活配置混合A",
  "fund_type": "混合型-灵活",
  "inception_date": "2020-03-15",
  "current_scale": 48.32,
  "scale_unit": "亿元",
  "scale_date": "2026-06-30",
  "manager_name": "张三",
  "manager_tenure_days": 1580,
  "co_manager_names": [],
  "benchmark": "沪深300指数收益率×60%+中证全债指数收益率×40%",
  "management_fee": 1.50,
  "custody_fee": 0.25,
  "service_fee": 0.00,
  "subscription_fee_range": "0.00%-1.50%",
  "redemption_fee_range": "0.00%-1.50%",
  "institutional_ratio": 35.2,
  "individual_ratio": 64.8,
  "stock_position_lower": 0,
  "stock_position_upper": 95,
  "special_clauses": ["可投港股通", "无衍生品权限"],
  "risk_level": "R3",
  "source": "天天基金/证监会披露"
}

// ===== keyword 模式返回 =====
{
  "mode": "search",
  "keyword": "沪深300",
  "total_matches": 87,
  "returned": 10,
  "funds": [
    {
      "fund_code": "510300",
      "fund_name": "华泰柏瑞沪深300ETF",
      "fund_type": "股票型-指数",
      "current_scale": 1250.00,
      "scale_unit": "亿元",
      "manager_name": "李四",
      "inception_date": "2012-05-04",
      "management_fee": 0.50,
      "tracking_index": "沪深300"
    }
    // ... 最多 top_n 条
  ]
}
```

---

### 工具 2: `fund_nav_history`

**功能描述**: 获取单只基金的每日净值序列，包含单位净值、累计净值、日增长率，用于业绩归因计算（年化收益、最大回撤、夏普比率、卡玛比率、波动率等）。最多返回1095个交易日（约3年），超过请分段拉取。

**兼容 AKShare 接口**: `ak.fund_open_fund_info_em(indicator="单位净值走势")`

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `fund_code` | string | 是 | `^\d{6}$` | 6位基金代码 |
| `days` | int | 否 | 1-1095，默认252 | 拉取近N个交易日的净值，252约等于1年。1095为硬上限 |

**输出JSON结构**:

```json
{
  "fund_code": "020712",
  "fund_name": "XX灵活配置混合A",
  "data_start": "2025-07-01",
  "data_end": "2026-07-25",
  "trading_days": 252,
  "latest_nav": 1.8523,
  "latest_acc_nav": 2.1523,
  "nav_series": [
    {
      "date": "2026-07-25",
      "unit_nav": 1.8523,
      "accumulated_nav": 2.1523,
      "daily_return_pct": 1.23
    }
    // ... 共 days 条
  ],
  "summary": {
    "period_return_pct": 12.35,
    "max_drawdown_pct": -18.42,
    "max_drawdown_start": "2025-10-08",
    "max_drawdown_end": "2026-01-15",
    "annual_volatility_pct": 22.10,
    "positive_day_ratio": 0.54
  },
  "source": "东方财富基金净值"
}
```

> **说明**: `summary` 中的指标是AKShare接口可直出的基础统计；Sharpe Ratio、Calmar Ratio、Alpha等复杂指标由 Agent（performance_analyst）自行计算，不在工具层预计算——保持工具层轻薄。

---

### 工具 3: `fund_holdings`

**功能描述**: 获取基金最新季报/半年报/年报披露的前十大重仓股明细，包含股票代码、名称、行业分类、占净值比例，同时返回行业分布汇总。数据滞后约20-30天（季报披露截止日）。这是 `sector_screener` 做行业穿透筛选和 `portfolio_doctor` 做持仓重合度分析的核心数据源。

**兼容 AKShare 接口**: `ak.fund_portfolio_hold_em()`

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `fund_code` | string | 是 | `^\d{6}$` | 6位基金代码 |
| `year` | int | 否 | 2020-2026 | 指定年份，不传则自动取最新一期季报 |
| `quarter` | int | 否 | 1-4，与year配合 | 指定季度 |

**输出JSON结构**:

```json
{
  "fund_code": "020712",
  "fund_name": "XX灵活配置混合A",
  "report_date": "2026-06-30",
  "report_type": "二季报",
  "total_holdings_count": 48,
  "top10_ratio": 45.80,
  "top10_holdings": [
    {
      "rank": 1,
      "stock_code": "600519",
      "stock_name": "贵州茅台",
      "sector": "食品饮料",
      "weight_pct": 7.82,
      "change_direction": "增持",
      "change_pct": 1.20
    }
    // ... 共 10 条
  ],
  "sector_distribution": [
    { "sector": "食品饮料", "weight_pct": 18.50 },
    { "sector": "医药生物", "weight_pct": 12.30 },
    { "sector": "电子", "weight_pct": 10.80 }
    // ...
  ],
  "market_distribution": {
    "a_share_pct": 82.0,
    "hk_stock_pct": 6.5,
    "bond_pct": 8.0,
    "cash_other_pct": 3.5
  },
  "concentration_hhi": 0.12,
  "source": "基金季度报告"
}
```

---

### 工具 4: `fund_manager_info`

**功能描述**: 查询基金经理的从业履历，包括当前管理基金列表、历史管理产品、任职时长、跳槽记录、管理总规模、共管情况。这是 `manager_profiler` 画像分析和 `watchtower` 经理变更监控的核心数据源。

**兼容 AKShare 接口**: `ak.fund_manager()` / `ak.fund_individual_basic_info_xq()`（经理字段）

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `fund_code` | string | 与 `manager_name` 二选一 | `^\d{6}$` | 传入基金代码则自动返回该基金当前所有在任经理的信息 |
| `manager_name` | string | 与 `fund_code` 二选一 | 2-10个汉字 | 传入姓名则返回该经理的全量履历 |

**输出JSON结构**:

```json
{
  "query_by": "fund_code",
  "fund_code": "020712",
  "managers": [
    {
      "manager_name": "张三",
      "is_primary": true,
      "tenure_start": "2022-01-10",
      "tenure_days": 1658,
      "current_managed_funds": [
        {
          "fund_code": "020712",
          "fund_name": "XX灵活配置混合A",
          "tenure_days": 1658,
          "return_since_tenure_pct": 38.50,
          "scale_billion": 48.32
        },
        {
          "fund_code": "020713",
          "fund_name": "XX灵活配置混合C",
          "tenure_days": 1658,
          "return_since_tenure_pct": 35.20,
          "scale_billion": 12.10
        }
      ],
      "historical_funds": [
        {
          "fund_code": "010234",
          "fund_name": "YY成长混合",
          "tenure_start": "2018-05-01",
          "tenure_end": "2022-01-05",
          "tenure_days": 1345,
          "return_during_tenure_pct": 62.30
        }
      ],
      "total_scale_billion": 62.50,
      "job_hop_count": 1,
      "job_hop_detail": ["2020年从YY基金转至XX基金"],
      "education": "硕士",
      "experience_years": 8.5,
      "co_management_count": 0
    }
  ],
  "source": "天天基金/证监会从业人员公示"
}
```

---

### 工具 5: `index_data`

**功能描述**: 获取指定指数的历史行情数据（收盘价、涨跌幅、成交量），覆盖沪深300（大盘价值锚）、中证500（中小盘锚）、创业板指（成长股锚）、恒生科技（港股科技锚）。用于 `performance_analyst` 做基准对比归因，以及 `macro_strategist` 判断当前市场风格。

**兼容 AKShare 接口**: `ak.stock_zh_index_daily_em()`

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `index_code` | string | 是 | 枚举值见下方 | 选择要查询的指数 |
| `start_date` | string | 否 | `YYYY-MM-DD`，默认365天前 | 起始日期 |
| `end_date` | string | 否 | `YYYY-MM-DD`，默认今日 | 截止日期 |

**index_code 枚举**:

| 值 | 指数 | 代表含义 |
|----|------|----------|
| `000300` | 沪深300 | 大盘/价值风格锚，最常见的主动基金基准 |
| `000905` | 中证500 | 中盘风格锚 |
| `399006` | 创业板指 | 成长/小盘风格锚 |
| `HSTECH` | 恒生科技指数 | 港股科技锚，用于QDII归因 |

**输出JSON结构**:

```json
{
  "index_code": "000300",
  "index_name": "沪深300",
  "start_date": "2025-07-01",
  "end_date": "2026-07-25",
  "trading_days": 248,
  "latest_close": 4120.35,
  "period_return_pct": 8.52,
  "period_max_drawdown_pct": -15.30,
  "daily_series": [
    {
      "date": "2026-07-25",
      "close": 4120.35,
      "change_pct": 0.85,
      "volume_billion": 285.30
    }
    // ...
  ],
  "source": "东方财富指数行情"
}
```

---

### 工具 6: `fund_announcements`

**功能描述**: 搜索某只基金在指定时间范围内的公告列表，支持按关键词过滤（经理变更、清盘风险、大额赎回、费率调整等）。这是 `watchtower` 监控预警和 `prospectus_analyzer` 文档解析的数据入口。

**兼容 AKShare 接口**: `ak.fund_announcement_em()` / `ak.fund_notice_em()`

**输入参数**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `fund_code` | string | 是 | `^\d{6}$` | 6位基金代码 |
| `keyword` | string | 否 | 1-20字符 | 过滤关键词，支持：经理变更、清盘、大额赎回、费率、分红、限购、终止。不传返回全部 |
| `days` | int | 否 | 1-365，默认90 | 搜索近N天内的公告 |
| `max_results` | int | 否 | 1-30，默认15 | 最多返回条数 |

**输出JSON结构**:

```json
{
  "fund_code": "020712",
  "fund_name": "XX灵活配置混合A",
  "search_period_days": 90,
  "keyword_filter": "经理变更",
  "total_found": 3,
  "announcements": [
    {
      "date": "2026-07-15",
      "title": "XX灵活配置混合A基金经理变更公告",
      "type": "基金经理变更",
      "summary": "新增共管基金经理王五",
      "alert_trigger": true,
      "alert_type": "经理变更",
      "alert_priority": "高",
      "source_url": "http://fund.eastmoney.com/..."
    },
    {
      "date": "2026-06-20",
      "title": "XX灵活配置混合A招募说明书更新",
      "type": "招募说明书",
      "summary": "更新投资范围说明",
      "alert_trigger": false,
      "alert_type": null,
      "alert_priority": null,
      "source_url": "http://fund.eastmoney.com/..."
    }
  ],
  "source": "东方财富基金公告/巨潮资讯"
}
```

> **说明**: `alert_trigger` 和 `alert_priority` 由工具层基于关键词规则预标记（"清盘"→高、"经理变更"→高、"大额赎回"→高、"费率"→中），但最终判定仍由 `watchtower` Agent 根据上下文做综合判断。

---

## 三、Agent → 工具映射表

```
                     ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
                     │  fund_       │  fund_nav_   │  fund_       │  fund_       │  index_      │  fund_       │
                     │  basic_info  │  history     │  holdings    │  manager_info│  data        │  announcements│
┌────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ prospectus_analyzer│      ●       │              │              │              │              │      ●       │
│ performance_analyst│              │      ●       │      ●       │              │      ●       │              │
│ cost_analyzer      │      ●       │      ○       │              │              │              │              │
│ manager_profiler   │              │              │              │      ●       │              │              │
│ macro_strategist   │              │              │              │              │      ●       │              │
│ wealth_advisor     │      —       │      —       │      —       │      —       │      —       │      —       │
│ sector_screener    │      ●       │              │      ●       │              │              │              │
│ fund_comparator    │      ●       │      ●       │      ●       │      ●       │              │              │
│ portfolio_doctor   │      ●       │              │      ●       │              │              │              │
│ watchtower         │      ○       │              │              │      ●       │              │      ●       │
└────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

● = 主要数据源    ○ = 辅助/补充数据源    — = 不直接调工具（消费前序Agent输出）
```

**补充说明**:

- `wealth_advisor` 是纯编排 Agent，消费前序 5 个 Layer 2 Agent 的 JSON 输出，不直接访问数据
- `fund_comparator` 理论上需要调用 4 个工具对 2-5 只基金分别拉数据，实际由上游 Agent 的结果缓存复用
- `macro_strategist` 除了 `index_data` 外，利率/汇率/政策等宏观数据通过 Claude 的 `WebSearch` 获取（非结构化公开数据）
- `watchtower` + `fund_basic_info` 的 ○ 关系用于定期对比规模变化

---

## 四、MCP Server 注册配置

### 4.1 配置文件

文件路径: `%APPDATA%/Claude/claude_desktop_config.json`（Windows）

```json
{
  "mcpServers": {
    "famas-data": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/staff3/Documents/trae_projects/jijin-skill/FAMAS-Skill/mcp_server",
        "run",
        "famas-data-server"
      ],
      "description": "FAMAS 基金投研数据服务 —— 基于 AKShare 提供 6 个工具：基本信息、净值、持仓、经理、指数、公告",
      "disabled": false
    }
  }
}
```

### 4.2 MCP Server 目录结构

```
FAMAS-Skill/
├── mcp_server/
│   ├── pyproject.toml          # 项目配置 + 依赖声明
│   ├── __init__.py
│   ├── server.py               # FastMCP 主入口，10 个 tool 全部 inline 注册
│   ├── test_all_realtime.py    # 实时行情冒烟测试脚本
│   └── utils/
│       ├── __init__.py
│       ├── ak_wrapper.py        # AKShare/东方财富接口封装 + TTL 缓存 + Webhook 推送
│       └── validators.py        # 输入参数校验（fund_code 格式等）
```

### 4.3 `pyproject.toml` 关键内容

```toml
[project]
name = "famas-mcp-data-server"
version = "2.1.0"
description = "MCP data server for FAMAS - Fund Analysis Multi-Agent System. 10 tools covering all 10 agents' data needs."
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "fastmcp>=2.0.0",
    "akshare>=1.16.0",
    "pandas>=2.0.0",
    "requests>=2.31.0",
]

[project.scripts]
famas-data-server = "server:main"
```

### 4.4 工具调用示例（Claude 侧）

在 Skill 执行过程中，Claude 会这样调用 MCP 工具：

```
// 1. 用户输入基金代码 020712
// 2. Skill 编排器依次调用：

mcp__famas-data__fund_basic_info({ fund_code: "020712" })
    → 返回基金名称、类型、规模、费率、持仓上下限...

mcp__famas-data__fund_nav_history({ fund_code: "020712", days: 756 })
    → 返回近3年净值序列，Agent 自行计算 Sharpe / Calmar / Alpha

mcp__famas-data__fund_holdings({ fund_code: "020712" })
    → 返回最新季报前十大重仓 + 行业分布

mcp__famas-data__fund_manager_info({ fund_code: "020712" })
    → 返回所有在任经理的履历与历史业绩

mcp__famas-data__index_data({ index_code: "000300", start_date: "2023-07-01" })
    → 返回沪深300历史行情，用于基准归因 + 风格判断

mcp__famas-data__fund_announcements({ fund_code: "020712", keyword: "经理变更", days: 180 })
    → 返回近半年经理变更相关公告
```

---

## 五、补充说明

### 1) 为什么没有"全市场基金池查询"独立工具

`sector_screener` 需要的筛选能力通过 `fund_basic_info` 的 `keyword` 模式满足。当 Agent 需要按行业/主题/风格筛选时，先通过 `keyword` 获取候选池（Top 20），再对候选池逐个调 `fund_holdings` 验证风格纯度。两步走避免了一个超大查询堵塞 MCP 通道。

### 2) 宏观数据的边界

利率、汇率、货币政策等宏观数据 AKShare 虽然支持（`ak.macro_china_*`），但这类数据的结构语义与基金数据完全不同，强行放入同一个 MCP Server 会违反单一职责。在实际运行时，`macro_strategist` Agent 通过 Claude 内置的 `WebSearch` 获取最新宏观数据，既保持工具层纯粹，也保证了数据的时效性。

### 3) 缓存策略

AKShare 的免费接口有频率限制（约 1-2 QPS）。建议 `ak_wrapper.py` 内置一个简单的 TTL 缓存：基本信息缓存 1 小时、净值缓存到当日收盘后、持仓缓存到下一季报披露日、公告缓存 30 分钟。这样即使多个 Agent 并行调用也不会触发限频。

### 4) 错误处理约定

所有 6 个工具在 AKShare 调用失败时统一返回：

```json
{
  "error": true,
  "error_code": "AKSHARE_TIMEOUT",
  "message": "数据源暂不可用，请稍后重试",
  "fund_code": "020712",
  "retry_suggested": true
}
```

这样 Agent 可以优雅降级 —— 比如用已有缓存数据继续分析，缺少的数据明确标注"暂不可用"。
                                   