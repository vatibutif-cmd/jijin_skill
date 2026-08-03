---
name: "etfirst"
description: "通过命令行调用「首趋E指」小程序的指数、 ETF和场外产品数据查询接口。支持指数/ETF/场外基金列表、指数详情、ETF 详情、场外详情等聚合查询。当用户提到「首趋E指」「首屈E指」「手趋E指」等（含常见错字、大小写与拼写变体），或询问 市场行情、ETF 行情、指数行情、ETF 详情、指数详情、场外基金详情等数据需求时触发。"
---

# etfirst

## 目录

- [触发场景](#触发场景)
- [使用指南与示例](#使用指南与示例)
  - [🎯 什么时候使用本 Skill？](#-什么时候使用本-skill)
    - [典型触发场景](#典型触发场景)
    - [关键词触发规则](#关键词触发规则)
  - [✅ 支持的功能](#-支持的功能)
  - [❌ 不支持的功能](#-不支持的功能)
- [数据更新频率（重要）](#数据更新频率重要)
- [字段值约定（通用）](#字段值约定通用)
  - [🎯 典型使用场景](#-典型使用场景)
    - [场景 1：Agent 自动调研某指数](#场景-1agent-自动调研某指数)
    - [场景 2：批量导出某分类下所有 ETF](#场景-2批量导出某分类下所有-etf)
    - [场景 3：查询某指数相关的全部 ETF 和场外联接产品](#场景-3查询某指数相关的全部-etf-和场外联接产品)
    - [场景 4：对比多只 ETF 的关键指标](#场景-4对比多只-etf-的关键指标)
    - [场景 5：筛选某基金公司旗下的 ETF / 场外联接基金](#场景-5筛选某基金公司旗下的-etf--场外联接基金)
    - [❌ 错误用法示例](#-错误用法示例)
    - [✅ 正确做法](#-正确做法)
- [全局选项](#全局选项)
- [子命令总览](#子命令总览)
- [认证流程](#认证流程)
  - [常见错误码](#常见错误码)
- [`config` 命令](#config-命令)
- [`index-base` 命令选项](#index-base-命令选项)
- [返回数据说明](#返回数据说明)
  - [1. index-base clas — 指数分类字典](#1-index-base-clas--指数分类字典)
  - [2. index-base list-etf — 指数 / ETF / 场外列表](#2-index-base-list-etf--指数--etf--场外列表)
  - [3. index-detail all — 指数详情页聚合](#3-index-detail-all--指数详情页聚合)
    - [queryRiskReturnRatio — 风险收益比](#queryriskreturnratio--风险收益比)
    - [queryIndustryDistribution — 行业分布](#queryindustrydistribution--行业分布)
    - [queryChangeRateByIndexCode — 涨跌幅](#querychangeratebyindexcode--涨跌幅)
    - [queryIndexArchive — 指数档案（静态信息）](#queryindexarchive--指数档案静态信息)
    - [list — 历史估值序列](#list--历史估值序列)
    - [queryNetInflow — 净流入趋势](#querynetinflow--净流入趋势)
    - [queryIndexDetail — 指数综合详情](#queryindexdetail--指数综合详情)
  - [4. etf-detail all — ETF 详情页聚合](#4-etf-detail-all--etf-详情页聚合)
    - [getMarketIndicatorData — 市场指标](#getmarketindicatordata--市场指标)
    - [queryTrackIndex — 跟踪指数](#querytrackindex--跟踪指数)
    - [getEtfLinkInfo — ETF 联接信息](#getetflinkinfo--etf-联接信息)
    - [getNetInflow — 净流入](#getnetinflow--净流入)
    - [getProductWindRank — Wind 排名](#getproductwindrank--wind-排名)
    - [getManagerInfo — 基金经理](#getmanagerinfo--基金经理)
    - [getRiskReturnCharacter — 风险收益特征](#getriskreturncharacter--风险收益特征)
    - [getHoldStock — 持仓股票](#getholdstock--持仓股票)
    - [getIndustryDistribution — 行业分布](#getindustrydistribution--行业分布)
    - [getReturnTrendList — 收益走势](#getreturntrendlist--收益走势)
  - [5. otc-detail all — 场外详情页聚合](#5-otc-detail-all--场外详情页聚合)
    - [baseEtfLinkInfo — 场外基金基本信息](#baseetflinkinfo--场外基金基本信息)
    - [scaleChange — 规模变化](#scalechange--规模变化)
    - [linkFundHold — 联接基金持仓](#linkfundhold--联接基金持仓)
    - [otherSubShare — 同基金其它份额](#othersubshare--同基金其它份额)
    - [queryTrackIndex / getManagerInfo / getRiskReturnCharacter / getReturnTrendList](#querytrackindex--getmanagerinfo--getriskreturncharacter--getreturntrendlist)
- [使用要点](#使用要点)
- [示例](#示例)
  - [退出登录](#退出登录)

## 触发场景

满足以下任一条件即触发本 Skill：

- 用户输入包含「首趋E指」「首趋e指」「手趋E指」等关键词（含常见错字、大小写与拼写变体）。
- 用户询问 ETF 行情、指数行情、ETF 详情、指数详情、场外基金详情等数据查询需求。

## 使用指南与示例
### 🎯 什么时候使用本 Skill？

**当用户请求包含以下意图时，应触发本 Skill：**

#### 典型触发场景

| 用户需求 | 典型提问示例 | 对应命令 |
|---------|-------------|----------|
| 查询产品列表 | “帮我查一下沪深300相关的ETF有哪些”<br>“列出所有行业指数基金” | `index-base list-etf` |
| 查看指数详情 | “000300指数的PE/PB是多少”<br>“沪深300的成分股有哪些” | `index-detail all` |
| 查看 ETF 详情 | “510300的溢价率多少”<br>“华泰柏瑞沪深300ETF的持仓” | `etf-detail all` |
| 查看场外详情 | “000001基金的风险收益特征”<br>“南方沪深300联接的规模变化” | `otc-detail all` |
| 查询指数分类 | “指数有哪些分类”<br>“跨境指数包括哪些” | `index-base clas` |
| 数据导出/分析 | “导出所有科技类ETF的数据”<br>“按规模排序列出前20只ETF” | `index-base list-etf` + `--json` |
| CLI 认证管理 | “如何登录CLI”<br>“API Key怎么配置” | `auth login/logout` |

> **注意**：CLI 采用按需调用模式，每次请求都会调用后端接口。如需监控最新数据，请定期调用（建议间隔 ≥ 5 秒），详见 [不支持的功能](#-不支持的功能)。

#### 关键词触发规则

**高优先级关键词**（出现任一即应触发）：
- `etfirst`、`etfapp`、`指数`、`ETF`、`指数基金`、`联接产品`
- 指数代码（如 `000300`、`000905`）
- ETF 代码（如 `510300`、`159919`）
- 场外基金代码（如 `000001`、`000311`）
- 今日行情、最新行情、行业表现

**中优先级关键词**（结合上下文判断）：
- `ETF列表`、`指数详情`、`成分股`、`行业分布`
- `PE`、`PB`、`估值`、`溢价率`、`净流入`
- `基金经理`、`持仓`、`规模`、`风险特征`、`基金公司`

### ✅ 支持的功能

| 功能类别 | 具体能力 | 适用场景 |
|----------|----------|----------|
| **指数库查询** | 指数类型字典、指数/ETF/场外联接产品列表查询 | 产品筛选、分类浏览、排序 |
| **指数详情** | 指数的估值、行情、成分股、行业分布等数据查询 | 指数数据查询、深度分析和对比 |
| **ETF 详情** | ETF的行情、持仓、基金经理、风险特征等数据查询） | ETF 数据查询、深度分析和对比 |
| **场外联接基金详情** | 场外联接基金的规模变化、持仓、其他份额、跟踪指数等数据查询） | 场外联接基金数据查询、深度分析和对比 |

### ❌ 不支持的功能

| 功能类别 | 说明 | 替代方案 |
|----------|------|----------|
| **主动基金详情** | 不支持主动管理型基金（非指数型）的详情查询 | 请使用南方基金 APP 或其他数据源 |
| **交易操作** | 不支持申购、赎回、转换等交易指令 | 请使用南方基金 APP 或其他平台 |
| **账号管理** | 不支持用户注册、身份认证 | 请使用首趋E指小程序或者联系客服 |
| **历史数据批量导出** | 不支持一次性导出多年历史数据 | 需分页调用，注意频率限制 |
| **自定义指标计算** | 不提供 PE/PB 分位计算、技术指标等 | 后端已预计算，直接取用 |
| **组合管理** | 不支持自选列表、投资组合创建 | 请使用首趋E指小程序的自选功能 |
| **实时行情推送** | CLI 采用按需调用模式，不支持 WebSocket 实时推送 | 需定期调用接口获取最新数据（建议间隔 ≥ 5 秒） |

## 数据更新频率与日期标注（重要）

| 数据类别 | 时效行为 | API 日期字段 |
|---|---|---|
| **实时行情**（`index-base list-etf` 的 `yield` / `price` / `traval` / `premDisRto`；`index-detail all` 的 `queryIndexDetail` 中 `pointValue` / `pointValueUpdateTime`；`getRealTimeData` 全部字段） | 当日实时数据，每 5 秒刷新 | ⚠ 数据时间**必须**取 `getRealTimeData` 的 `tradingDay`+`time` 或 `queryIndexDetail` 的 `pointValueUpdateTime`，**禁止**取 `list-etf` 的 `dataDate`/`yieldDate` |
| **日频估值/资金流**（PE/PB/股息率/FED/ROE/净流入/规模/溢折率等） | 日频更新。**收盘前**展示前一交易日数据；**收盘后存在延迟**，不会即时切换为当日数据。每个字段有独立日期字段 | `peDate` / `roeDate` / `astDate` / 各子接口的 `tradingDay` / `endDate` |
| **季度/低频数据**（持仓、行业分布、基金经理、Wind 排名、规模变化等） | 按季度或披露周期更新 | 各子接口的 `endDate` / `tradingDay` |

 **Agent 返回数据时，必须参照 API 返回的日期字段，在回复末尾以独立段落逐项标注每个指标的数据日期**。不同指标日期可能不同（如行情=当日，ROE=上季度末），不可将所有数据笼统标注为同一日期。尤其在交易时段，实时行情数据日期与其他日频指标的日期一定不是同一天。当用户对当日数据时效性敏感时，需提示上述延迟特性。⚠ Agent 无需自行判断当天是否为交易日，仅需如实标注 API 返回的数据日期；**禁止**从数据日期反推交易日历。如用户询问是否为当日行情，统一说明「数据显示日期为 XX，非交易时段数据更新可能存在延迟」。
>
> **日期标注格式规范**：
>
> Agent 在返回行情数据后，必须在回复末尾添加「**日期标注：**」独立段落，按数据频率分组标注各指标的数据日期。格式要求如下：
>
> - 实时行情类指标（涨跌幅、最新价、成交额、溢折率、指数点位等）标注为：`YYYY-MM-DD HH:mm:ss 实时行情`。数据时间**必须**从实时行情接口获取，**禁止**从 `list-etf` 的 `dataDate`/`yieldDate` 取日期：
>   - `index-detail`/`etf-detail` 的 `getRealTimeData`：取 `tradingDay`（`yyyyMMdd`）+ `time`（`HHmmssSSS`）→ 标注为 `YYYY-MM-DD HH:mm:ss 实时行情`
>   - `index-detail` 的 `queryIndexDetail`：取 `pointValueUpdateTime`（`yyyy-MM-dd HH:mm:ss`）→ 标注为 `YYYY-MM-DD HH:mm:ss 实时行情`
> - 日频类指标（PE/PB/股息率/ROE/净流入/规模/今年以来涨幅等区间收益率）标注为：`数据日期 YYYY-MM-DD（日频）`。数据时间来源：`dataDate`/`yieldDate`/`peDate`/`roeDate`/`astDate` 等日期字段
> - 季度/低频类指标（持仓、行业分布、基金经理、Wind 排名等）标注为：`数据截止 YYYY-MM-DD`
>
> **日期标注示例**：
>
> ```
> 日期标注：
> - 涨跌：2026-06-15 15:00:03 实时行情
> - 今年以来/近1月/近1周：数据日期 2026-06-12（日频）
> - ROE：数据日期 2026-03-31（季度）
> ```
>
> **错误示例**（禁止）：
>
> - ❌ 涨跌幅 +2.10%、市盈率 14.47 倍、净资产收益率 2.27%、规模 175.08 亿元（数据日期: 20260612）← 笼统标注，不同日期的指标被归为同一日期
> - ❌ 涨跌幅 +2.10%、市盈率 14.47 倍、净资产收益率 2.27% ← 未标注任何数据日期

## 字段值约定（通用）

为避免歧义，本文档中各字段统一遵循以下约定：

| 类别 | 单位 / 格式 | 说明 |
|---|---|---|
| 涨跌幅、占比、分位、费率、波动率、回撤、收益率类 | `%` | 已乘以 100。例：`yield=0.85` 表示 +0.85%；`pePercent=45.30` 表示 PE 处于历史 45.30% 分位 |
| 净流入金额、基金规模（ast / scale 类字段） | `亿元` | 直接为数值，例 `12.5` 表示 12.5 亿元 |
| 金额（成交额、市值等） | `元`（人民币元） | 直接为数值，例 `1250000000` 表示 12.5 亿元 |
| 价格 | `元/份` 或 `元/股` | 单位价格 |
| 成交量 | `手`（1 手 = 100 份/股） | — |
| PE / PB / FED / ROE 比值类 | 倍数（无单位） | 例 `pe=12.50` 表示 12.50 倍 |
| 夏普比率、跟踪误差等无量纲指标 | 无单位 | — |
| 日期字段（`tradingDay` / `endDate` / `JYR` 等） | 字符串 `yyyyMMdd` | 例 `"20260512"` |
| 时间字段（`time`） | 字符串 `HHmmssSSS` | 时分秒毫秒 |
| 排名 / 分位 / 百分位类（`*Rank` / `*Percent`） | `%`（0–100） | 数值越小通常代表越优 / 越低 |
| 布尔标签（`isXxx` / `xxxFlag` / 标签类） | `Integer` | `1=是`，`0=否` |

**API 字段名 → 业务术语映射（Agent 向用户返回数据时必须使用业务术语，禁止使用 API 字段名）**：

| API 字段名 | 业务术语（用户可见） |
|---|---|
| `yield` | 涨跌幅 |
| `price` | 最新价 |
| `traval` | 成交额 |
| `premDisRto` | 溢折率 |
| `pe` / `pePercent` | 市盈率 / PE 分位 |
| `pb` / `pbPercent` | 市净率 / PB 分位 |
| `dp` | 股息率 |
| `roe` | 净资产收益率（ROE） |
| `ast` | 规模（保有规模 / AUM） |
| `netInflow` | 净流入 |
| `pointValue` | 指数点位 |
| `volatility` | 波动率 |
| `trackError` | 跟踪误差 |
| `mgrFee` / `trustFee` / `saleFee` | 管理费率 / 托管费率 / 销售服务费率 |
| `standardDeviation` | 波动率（风险特征版） |
| `sharpeRatio` | 夏普比率 |
| `maxDrawdown` | 最大回撤 |

> **禁止示例**："yield(yieldDate=20260612)"、"ast(astDate=20260612)"

**数据日期字段（Agent 必须用于标注各指标日期，标注时使用业务术语而非 API 字段名）**：

| 日期字段 | 所在接口 / 位置 | 说明 |
|---|---|---|
| `dataDate` | `index-base list-etf` 的 `dataList` 元素；`etf-detail all` 的 `getMarketIndicatorData` | 该条记录整体数据日期（与 `yield`/`price`/`traval` 等行情字段同步） |
| `yieldDate` | `index-base list-etf` 的 `dataList` 元素；`etf-detail all` 的 `getMarketIndicatorData` | 涨跌幅数据日期 |
| `peDate` | `index-base list-etf` 的 `dataList` 元素；`etf-detail all` 的 `getMarketIndicatorData` | PE 数据日期 |
| `roeDate` | `index-base list-etf` 的 `dataList` 元素；`etf-detail all` 的 `getMarketIndicatorData` | ROE 数据日期（通常为上季度末，如 `"20260331"`） |
| `astDate` | `index-base list-etf` 的 `dataList` 元素；`etf-detail all` 的 `getMarketIndicatorData` | 规模（AUM）数据日期 |
| `tradingDay` / `tradingday` | 各子接口（注意：部分接口返回小写 `tradingday`，部分返回大写 `tradingDay`） | 交易日。`queryRiskReturnRatio` / `queryChangeRateByIndexCode` / `queryCompanyWeight` 用小写 `tradingday`；`queryNetInflow` / `getRealTimeData` 等用大写 `tradingDay` |
| `endDate` | `index-detail` 的 `queryIndustryDistribution`；`etf-detail` 的 `getRiskReturnCharacter` / `getHoldStock` / `getIndustryDistribution`；`otc-detail` 的 `linkFundHold` | 数据截止日 |
| `pointValueUpdateTime` | `index-detail all` 的 `queryIndexDetail` | 实时点位最后刷新时间，格式 `yyyy-MM-dd HH:mm:ss`。**注意：该字段可能仅在交易时段返回，非交易时段可能缺失** |
| `scaleDate` | `etf-detail all` 的 `getEtfLinkInfo` | ETF 联接基金规模数据日期 |
| `tradeDate` | `etf-detail all` 的 `getReturnTrendList`；`otc-detail all` 的 `getReturnTrendList` | 收益走势序列中的交易日 |
| `date` | `otc-detail all` 的 `scaleChange` | 规模变化数据日期 |
| `END_DATE` | `etf-detail all` / `otc-detail all` 的 `getProductWindRank` | Wind 排名数据截止日（大写命名） |

> Agent 向用户返回数据时，必须从 API 响应中提取上述日期字段，在回复末尾以「日期标注：」独立段落逐项标注各指标的数据日期。不同指标日期可能不同（如行情=当日，ROE=上季度末），不可笼统标注。**禁止**将所有指标统一标注为同一个日期。同日期指标可合并一行，
### 🎯 典型使用场景

#### 场景 1：Agent 自动调研某指数

```bash
# 一键获取指数的估值、行情、成分股、行业分布等
etfirst --json index-detail all --index-code 000300
```

#### 场景 2：批量导出某分类下所有 ETF

```bash
# 一次性获取 industry 分类下的所有 ETF（最多 100 条）
etfirst --json index-base list-etf \
    --type 2 \
    --clas industry \
    --page-size 100
```

#### 场景 3：查询某指数相关的全部 ETF 和场外联接产品

```bash
# 查询沪深 300 相关的 ETF 产品
etfirst --json index-base list-etf \
    --type 2 \
    --index-code 000300 \
    --page-size 100

# 查询沪深 300 相关的场外联接基金
etfirst --json index-base list-etf \
    --type 3 \
    --index-code 000300 \
    --page-size 100

# 提取关键信息：产品代码、名称、规模、管理费
etfirst --json index-base list-etf \
    --type 2 \
    --index-code 000300 \
    --page-size 100 \
    | jq '.data.dataList[] | {prodCd, prodName, ast, mgrFee}'
```

#### 场景 4：对比多只 ETF 的关键指标

```bash
# 提取产品代码、名称、规模、PE
echo '510300 159919 510500' | tr ' ' '\n' | while read code; do
    etfirst --json etf-detail all --product-code "$code" \
        | jq '{
            productCode: .productCode,
            scale: .results.getMarketIndicatorData.ast,
            pe: .results.getMarketIndicatorData.pe
          }'
done
```

#### 场景 5：筛选某基金公司旗下的 ETF / 场外联接基金

> **注意**：CLI 的 `--key-word` 参数仅按产品代码或名称做模糊匹配，**无法**按 `managementCompany`（基金管理公司）字段精确筛选。要筛选某基金公司旗下产品，需拉取全量数据后在本地按 `managementCompany` 字段过滤。

```bash
# 示例：筛选南方基金旗下的全部 ETF
# ⚠ 关键：必须逐页拉取直到累计条数 ≥ totalRows，服务端每页实际返回远少于 page-size

# 方法 1：按 managementCompany 字段筛选任意基金公司（需分页拉全量后本地过滤）
# 第 1 页
etfirst --json index-base list-etf --type 2 --page-no 1 --page-size 100
# → 读取 totalRows（如 1532），记录 dataList 实际条数（如 5 条）
# → 累计已拉取 = 5，还需继续 → 拉第 2 页
etfirst --json index-base list-etf --type 2 --page-no 2 --page-size 100
# → 累计已拉取 = 5 + 5 = 10 < 1532 → 继续 ...
# → 直到累计条数 ≥ totalRows 才停止
# → 从全部记录中筛选 managementCompany == "华泰柏瑞基金"

# 方法 2：同上，筛选某公司下的场外联接基金（type=3）
# 同样逐页递进，直到累计条数 ≥ totalRows
etfirst --json index-base list-etf --type 3 --page-no 1 --page-size 100
# → 逐页拉取后本地筛选 managementCompany 含目标公司名的条目
```

**Agent 实现要点**：
1. 调用 `index-base list-etf` 拉取数据，**必须逐页递进直到累计条数 ≥ `totalRows`**——服务端每页实际返回远少于 `--page-size`，仅拉 1 页结果不全
2. 以每次响应中 `dataList` 的**实际长度**推进 `--page-no`，不可用 `page-no × page-size ≥ totalRows` 判断终止
3. 从每条记录的 `managementCompany` 字段做精确匹配或包含匹配
4. **禁止**用 `--key-word` 代替公司筛选——`--key-word` 只匹配产品代码/名称，不匹配 `managementCompany`

#### ❌ 错误用法示例

```bash
# 错误 1：尝试下单交易（CLI 不支持交易功能）
# etfirst trade buy --product-code 510300 --amount 1000  # 此命令不存在

# 错误 2：高频轮询（可能触发限流）
# while true; do etfirst index-base list-etf; done  # 请添加 sleep

# 错误 3：查询主动基金（仅支持指数型产品）
# etfirst --json otc-detail all --product-code 110011  # 主动基金不支持
```

#### ✅ 正确做法

```bash
# 正确 1：合理控制调用频率（建议间隔 ≥ 1 秒）
etfirst index-base list-etf --type 2 --page-size 50
sleep 1
etfirst index-base list-etf --type 3 --page-size 50

# 正确 2：使用聚合命令减少请求次数
etfirst --json index-detail all --index-code 000300  # 一次获取 9 类数据

# 正确 3：分页获取大量数据
echo '1 2 3' | tr ' ' '\n' | while read page; do
    etfirst --json index-base list-etf \
        --type 2 \
        --page-no "$page" \
        --page-size 100
done
```


## 全局选项

| 选项 | 说明 |
|---|---|
| `--json` | 以紧凑 JSON 形式输出，便于程序/Agent 解析。不带该选项时输出带缩进的人类可读 JSON |

## 子命令总览

```
etfirst auth login   --api-key <KEY>            # 登录
etfirst auth logout [--purge-key]               # 登出
etfirst config                                  # 查看当前配置
etfirst index-base clas      [过滤字段…]        # 指数分类字典
etfirst index-base list-etf  [过滤字段…]        # 指数/ETF/场外列表
etfirst index-detail all     --index-code X     # 指数详情页聚合
etfirst etf-detail   all     --product-code X   # ETF 详情页聚合
etfirst otc-detail   all     --product-code X   # 场外详情页聚合
etfirst                                         # 无子命令时进入交互式会话
etfirst repl                                    # 显式进入交互式会话
```

## 认证流程

所有业务接口都需要先登录。

```bash
# 登录（API Key 写入 ~/.cli_anything/etfapp/config.json，升级或清除 Session 均不丢失）
etfirst auth login --api-key <YOUR_KEY>

# 之后即可直接调用业务接口
etfirst --json index-base  clas --type 1
```

> **API Key 持久化**：Key 保存在 `~/.cli_anything/etfapp/config.json`，与会话文件（`session.json`）分离。
> CLI 升级（`pip install` 新版本）不会删除 config.json，Key 自动沿用。

### 常见错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|----------|
| `C0100` | API Key 缺失 | 检查 `--api-key` 参数 |
| `C0101` | API Key 无效 | 确认 Key 是否正确 |
| `C0102` | API Key 已禁用 | 联系管理员 |
| `C0104` | API Key 已过期 | 联系管理员重新颁发 |
| `A0302` / `A0303` | 登录态失效 | 重新执行 `auth login`（若已保存 Key，CLI 会自动续期） |

## `config` 命令

```bash
etfirst config
```

输出示例：

```json
{
  "profile": "dev",
  "logged_in": true,
  "api_key_saved": true,
  "config_file": "/home/user/.cli_anything/etfapp/config.json",
  "session_file": "/home/user/.cli_anything/etfapp/session.json"
}
```

| 字段 | 说明 |
|---|---|
| `api_key_saved` | 是否已在 config.json 中保存 API Key |
| `config_file` | API Key 持久化存储路径（升级 CLI 不影响此文件） |
| `session_file` | 会话文件路径（含 cookie、历史记录等） |

## `index-base` 命令选项

> 以下选项为 `index-base clas` 与 `index-base list-etf` 共用。`--type` 对 `clas` 必填；分页/排序选项主要对 `list-etf` 有意义。

| CLI 选项 | 说明 |
|---|---|
| `--type` | 产品类型枚举：`1`=指数；`2`=ETF；`3`=场外基金 |
| `--clas` | 指数分类代码（通过 `clas` 命令获取的 `code` 值） |
| `--key-word` | 按产品代码或名称做模糊匹配 |
| `--index-code` | 精确按指数代码筛选 |
| `--sort-key` | 排序字段名（取 `dataList` 元素中的数值字段名，如 `yield`、`netInflow`、`ast`） |
| `--sort-direction` | 排序方向：`asc`=升序；`desc`=降序 |
| `--page-no` | 页码（从 1 起），默认 `1` |
| `--page-size` | 每页条数，默认 `10` |

## 返回数据说明

所有接口返回统一封装：

```json
{
  "code": "00000",
  "message": "success",
  "data": { ... }
}
```

`code` 为 `"00000"`（或 `"0000"`/`"000000"`）表示成功，`data` 为业务数据；其它值表示失败，`message` 为错误描述。

---

### 1. index-base clas — 指数分类字典

按 `--type` 返回该类型下的分类树（最多 3 级嵌套）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | String | 分类代码。可作为 `list-etf --clas` 的入参 |
| `name` | String | 分类中文名称，例如「跨境指数」「行业指数」 |
| `count` | Integer | 该分类（含子分类）下的产品数量 |
| `childList` | List | 子分类列表，结构同本表；无子分类时为 `null` |

---

### 2. index-base list-etf — 指数 / ETF / 场外列表

**顶层返回**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `totalRows` | Integer | 满足筛选条件的总记录数；用于前端计算总页数 |
| `dataList` | List | 当前页的产品列表，长度 ≤ `--page-size` |

> **分页完整性约束**：服务端每页实际返回条数**可能远小于** `--page-size`，**不可**仅拉取第 1 页就认为数据完整。Agent 在做任何涉及全量筛选、统计汇总（如按 `managementCompany` 过滤、求总规模、计总数）的操作时，**必须逐页递进直到累计拉取条数 ≥ `totalRows` 才停止**，以每次响应中 `dataList` 的实际长度推进 `--page-no`，而非用 `page-no × page-size ≥ totalRows` 判断终止。

**`dataList` 元素字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `prodCd` | String | 产品代码（一般 6 位），例 `"510300"` |
| `prodName` | String | 产品简称，例 `"沪深300ETF"` |
| `prodFullName` | String | 产品全称 |
| `indexCd` | String | 跟踪/对应指数代码，例 `"000300"` |
| `indexName` | String | 指数简称 |
| `clasCd` / `clasName` | String | 一级分类代码 / 中文名，与 `clas` 命令的 `code`/`name` 一致 |
| `level2ClasCd` / `level2ClasName` | String | 二级分类代码 / 中文名 |
| `level3ClasCd` / `level3ClasName` | String | 三级分类代码 / 中文名 |
| `yield` | BigDecimal | 涨跌幅，单位 `%`。正数=上涨，负数=下跌。例 `0.85` = +0.85%。为当日实时数据（5 秒刷新）； |
| `netInflow` | BigDecimal | 最新交易日净流入，单位 `亿元`。正=净流入，负=净流出 |
| `l1wNetInflow` | BigDecimal | 最新交易日起向前推 1 周（自然周）累计净流入，单位 `亿元` |
| `l1mNetInflow` | BigDecimal | 最新交易日起向前推 1 个自然月累计净流入，单位 `亿元` |
| `l3mNetInflow` | BigDecimal | 最新交易日起向前推 3 个自然月累计净流入，单位 `亿元` |
| `l1yNetInflow` | BigDecimal | 最新交易日起向前推 12 个自然月累计净流入，单位 `亿元` |
| `ytdNetInflow` | BigDecimal | 本年 1 月 1 日至最新交易日累计净流入，单位 `亿元` |
| `ast` | BigDecimal | 追踪同一指数的 ETF 合计保有规模（AUM），日频更新，单位 `亿元` |
| `pe` | BigDecimal | 最新交易日市盈率（PE-TTM），单位：倍 |
| `pePercent` | BigDecimal | PE 历史分位（从 2016-01-04 起），单位 `%`（0~100，越低代表估值越低） |
| `pb` | BigDecimal | 最新交易日市净率，单位：倍 |
| `pbPercent` | BigDecimal | PB 历史分位（从 2016-01-04 起），单位 `%`（0~100） |
| `dp` | BigDecimal | 股息率，单位 `%`（年化） |
| `roe` | BigDecimal | 净资产收益率 ROE，单位 `%` |
| `volatility` | BigDecimal | 波动率，单位 `%`（年化） |
| `premDisRto` | BigDecimal | 溢折率，单位 `%`。正=溢价，负=折价（仅 ETF 字段，`--type 2` 时返回） |
| `traval` | BigDecimal | 成交额，单位 `元`（仅 ETF 字段，`--type 2` 时返回）。为当日累计实时成交额（5 秒刷新）。|
| `price` | String | 最新价，单位 `元/份`（仅 ETF 字段，`--type 2` 时返回）。为当前实时成交价（5 秒刷新）。 |
| `trackError` | BigDecimal | 近 12 个自然月跟踪误差，单位 `%`（越小代表跟踪越紧） |
| `mgrFee` | BigDecimal | 管理费率，单位 `%`（年化） |
| `trustFee` | BigDecimal | 托管费率，单位 `%`（年化） |
| `saleFee` | BigDecimal | 销售服务费率，单位 `%`（年化） |
| `managementCompany` | String | 基金管理公司全称 |
| `isSouthETF` | Integer | 是否南方基金产品：`1`=是，`0`=否 |
| `fundManager` | String | 基金经理姓名；多人时以「、」分隔 |
| `standardDeviation` | String | 波动率（风险特征版），单位 `%`（年化） |
| `sharpeRatio` | String | 夏普比率（无量纲） |
| `maxDrawdown` | String | 最大回撤，单位 `%`（一般为负数） |
| `riskReturnDate` | String | 风险特征数据日期 `yyyyMMdd` |
| `peDate` | String | 估值日期（PE/PB/股息率等指标对应的交易日），格式 `yyyyMMdd` |
| `valuation` | String | 估值标准（如"PE-TTM"） |
| `roeDate` | String | ROE 数据日期 `yyyyMMdd` |
| `astDate` | String | ETF 规模数据日期 `yyyyMMdd` |
| `astChgRto` | BigDecimal | 规模变化率，单位 `%` |
| `otcAstDate` | String | 场外规模数据日期 `yyyyMMdd` |
| `etfLinkAst` | BigDecimal | 场外联接基金规模，单位 `亿元` |
| `dataDate` | String | 数据日期/净流入日期 `yyyyMMdd` |
| `establishDate` | String | 产品成立日期 `yyyyMMdd` |
| `yieldDate` | String | 收益率日期 `yyyyMMdd` |
| `l1dYield` | BigDecimal | 上一日涨幅，单位 `%` |
| `l1wYield` | BigDecimal | 周度涨幅，单位 `%` |
| `l1mYield` | BigDecimal | 月度涨幅，单位 `%` |
| `l3mYield` | BigDecimal | 近 3 月涨幅，单位 `%` |
| `l6mYield` | BigDecimal | 近半年涨幅，单位 `%` |
| `l1yYield` | BigDecimal | 年度涨幅，单位 `%` |
| `ytdYield` | BigDecimal | 今年以来涨幅，单位 `%` |
| `inceptionYield` | BigDecimal | 成立以来涨幅，单位 `%` |
| `nav` | BigDecimal | 基金净值，单位 `元/份` |
| `cumulativeNav` | BigDecimal | 累计净值，单位 `元/份` |
| `closePrice` | String | 上一日收盘点位/价格 |
| `nowPrice` | String | 最新价（实时），单位 `元/份` |
| `percentageChange` | String | 涨跌幅，单位 `%` |
| `compositeFee` | BigDecimal | 综合费率（管理+托管+销售），单位 `%`（年化） |
| `trackEtfCd` | String | 跟踪 ETF 代码（场外联接基金对应的场内 ETF 代码） |
| `trackEtfName` | String | 跟踪 ETF 名称 |
| `turnOver` | BigDecimal | 换手率，单位 `%` |
| `mergeScale` | String | 合并规模（场内+场外合并后文本） |

> **`--type` 对行情字段的影响**：
> - `type=1`（指数）：返回 `yield`（涨跌幅），不返回 ETF 专属字段（`price` / `traval` / `premDisRto`）。
> - `type=2`（ETF）：返回 `yield`（涨跌幅）、`price`（最新价）、`traval`（成交额）、`premDisRto`（溢折率）。
> - `type=3`（场外）：不返回任何行情字段（`yield` / `price` / `traval` / `premDisRto` 均缺失）。

---

### 3. index-detail all — 指数详情页聚合

**参数**：

| CLI 选项 | 说明 | 默认值 |
|---|---|---|
| `--index-code` | 指数代码（必填），例 `000300` | — |
| `--index-type` | 指数大类：`1`=宽基指数；`2`=行业指数 | `2` |
| `--start-date` | 时间序列起始日 `yyyyMMdd` | 默认查询最近 30 天|
| `--end-date` | 时间序列结束日 `yyyyMMdd` | 当前日期 |
| `--net-inflow-type` | 净流入口径：`major`=指数主力净流入（单位亿元）；`etf`=追踪该指数的全部 ETF 合计净流入（单位元） | `major` |

**返回顶层结构**：`{ indexCode, params, results, _errors }`

| 字段 | 说明 |
|---|---|
| `indexCode` | 本次请求的指数代码 |
| `params` | 本次请求所用参数的快照（便于复现） |
| `results` | 所有子接口的结果字典（key 见下表） |
| `_errors` | 失败子接口的错误信息：`key`=子接口名，`value`=错误描述。子接口并行调用，单点失败不影响其它结果 |

**`results` 包含的子接口 key**：`queryRiskReturnRatio`、`queryIndustryDistribution`、`queryChangeRateByIndexCode`、`queryIndexArchive`、`list`、`queryCompanyWeight`、`queryNetInflow`、`queryIndexDetail`、`getRealTimeData`。各子接口返回结构详见下方字段说明。

#### queryRiskReturnRatio — 风险收益比
| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | Integer | 统计区间枚举：`12`=返1 年；`36`=返3 年；`60`=返5 年 |
| `tradingday` | String | 数据所属交易日 `yyyyMMdd` |
| `volatility` | String | 区间波动率，单位 `%`（年化） |
| `volatilityRank` | String | 同类排名百分位，单位 `%`（越低=越平稳） |
| `sharpeRatio` | String | 区间夏普比率（无量纲，越大=风险调整后收益越好） |
| `sharpeRatioRank` | String | 同类排名百分位，单位 `%`（越低=越优） |
| `maxDrawdown` | String | 区间最大回撤，单位 `%`（一般为负数） |
| `maxDrawdownRank` | String | 同类排名百分位，单位 `%`（越低=回撤越小） |

#### queryIndustryDistribution — 行业分布
| 字段 | 类型 | 说明 |
|---|---|---|
| `firstWeightList` | List | 一级行业权重列表，元素结构见 **CompanyTypeWeight** |
| `secondWeightList` | List | 二级行业权重列表 |
| `thirdWeightList` | List | 三级行业权重列表 |
| `companyWeightList` | List | 成分股权重列表，元素结构见 **CompanyWeight** |
| `tradingday` | String | 交易日 `yyyyMMdd` |
| `endDate` | String | 数据截止日 `yyyyMMdd` |

**CompanyTypeWeight**（行业权重）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `industryName` | String | 行业中文名 |
| `weight` | String | 占比，单位 `%` |

**CompanyWeight**（成分股权重）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `stockName` | String | 股票名称 |
| `industryName` | String | 所属行业 |
| `weight` | String | 占指数权重，单位 `%` |
| `changeVsPrevious` | String | 较上次指数调仓时的权重变化，单位 `%` |

#### queryChangeRateByIndexCode — 涨跌幅
| 字段 | 类型 | 说明 |
|---|---|---|
| `indexCode` | String | 指数代码 |
| `tradingday` | String | 数据日期 `yyyyMMdd` |
| `lastOneWeekChangeRate` | String | 最新交易日起向前推 1 周（自然周）涨跌幅，单位 `%` |
| `lastOneMonthChangeRate` | String | 最新交易日起向前推 1 个自然月涨跌幅，单位 `%` |
| `lastThreeMonthChangeRate` | String | 最新交易日起向前推 3 个自然月涨跌幅，单位 `%` |
| `thisYearChangeRate` | String | 本年 1 月 1 日至最新交易日涨跌幅，单位 `%` |

#### queryIndexArchive — 指数档案（静态信息）
| 字段 | 类型 | 说明 |
|---|---|---|
| `indexCode` | String | 指数代码 |
| `indexName` | String | 指数中文全称 |
| `abbrIndexName` | String | 指数简称 |
| `institutionName` | String | 编制/发布机构（如「中证指数」「国证指数」） |
| `baseValue` | String | 基点数值（指数发布时的起始点位） |
| `baseDate` | String | 基日 `yyyyMMdd` |
| `constituentNumber` | String | 样本（成分）数量 |
| `indexProfile` | String | 指数简介（文本段落） |
| `publishDate` | String | 指数发布日期 `yyyyMMdd` |
| `totalMarketCap` | String | 指数总市值，单位 `亿元` |
| `totalFreeFloatMarketCap` | String | 指数自由流通市值合计，单位 `亿元` |
| `maxFreeFloatMarketCap` | String | 单一样本最大自由流通市值，单位 `亿元` |
| `minFreeFloatMarketCap` | String | 单一样本最小自由流通市值，单位 `亿元` |
| `averageFreeFloatMarketCap` | String | 样本自由流通市值均值，单位 `亿元` |
| `medianFreeFloatMarketCap` | String | 样本自由流通市值中位数，单位 `亿元` |

#### list — 历史估值序列
返回每个交易日的 PE/PB 与分位，每条记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `JYR` | String | 交易日 `yyyyMMdd` |
| `ZSDM` | String | 指数代码 |
| `INDEXCODE` | String | 统一资讯指数代码 |
| `PE` | String | 市盈率，单位：倍 |
| `PEFW` | String | PE 历史分位（从 2016-01-04 起），单位 `%`（0~100） |
| `PB` | String | 市净率，单位：倍 |
| `PBFW` | String | PB 历史分位（从 2016-01-04 起），单位 `%`（0~100） |

#### queryNetInflow — 指数相关净流入数据
返回 `List<NetInflowVo.NetInflow>`，按 `tradingDay` 升序。调用口径由 `--net-inflow-type` 决定：`major`=指数主力净流入；`etf`=追踪该指数的全部 ETF 合计净流入。**单位均为亿元**。

| 字段 | 类型 | 说明 |
|---|---|---|
| `indexCode` | String | 指数代码（同入参 `indexCode`） |
| `tradingDay` | String | 交易日 `yyyyMMdd` |
| `netInflowValue` | String | 单日净流入金额，单位 `亿元`。正=净流入，负=净流出 |

#### queryIndexDetail — 指数综合详情
| 字段 | 类型 | 说明 |
|---|---|---|
| `indexCode` | String | 指数代码 |
| `indexName` | String | 指数名称 |
| `infoIndexCode` | String | 统一资讯指数代码 |
| `windIndexCode` | String | 万得（Wind）指数代码 |
| `type` | String | 指数类型枚举：`"01"`=宽基；`"05"`=行业；其余表示策略/主题等 |
| `sort` | Integer | 显示排序权重（小在前） |
| `opinionTitle` | String | 分析师观点标题 |
| `opinion` | String | 分析师观点正文 |
| `pe` | String | 最新交易日市盈率（PE-TTM），单位：倍 |
| `peAvg` | String | PE 历史均値（从 2016-01-04 起），单位：倍 |
| `pePercent` | String | PE 历史分位（从 2016-01-04 起），单位 `%` |
| `pb` / `pbAvg` / `pbPercent` | String | 同上，PB 维度；均値与分位同样从 2016-01-04 起计算 |
| `fed` | String | FED 溢价比値（股权风险溢价指标 = 1/PE − 无风险利率），数值越大代表股票相对债券越有性价比 |
| `fedAvg` | String | FED 历史均値（从 2016-01-04 起） |
| `fedPercent` | String | FED 历史分位（从 2016-01-04 起），单位 `%` |
| `lastYearPerChange` | String | 最新交易日起向前推 12 个自然月涨跌幅，单位 `%` |
| `pointValue` | String | 当前指数点位。**集成自实时行情**：仅交易时段每 5 秒更新，非交易时段保留上一次刷新的值（收盘后数据更新存在延迟） |
| `pointValueUpdateTime` | String | 点位最后一次刷新时间（与 `pointValue` 同步），格式 `yyyy-MM-dd HH:mm:ss` |
| `percentageChange` | String | 前一交易日涨跌幅，单位 `%` |
| `dividendYield` | String | 股息率，单位 `%` |
| `roe` | String | 净资产收益率 ROE，单位 `%` |
| `roePercent` | String | ROE 同类排名百分位，单位 `%` |
| `roeSpeed` | String | ROE 同比增速，单位 `%` |
| `etfScale` | String | 追踪本指数的 ETF 合计规模，单位 `亿元` |
| `otcScale` | String | 追踪本指数的场外基金合计规模，单位 `亿元` |
| `netInFlow` | String | 净流入金额，单位 `亿元` |
| `netInFlowPercent` | String | 净流入同类排名百分位，单位 `%` |
| `preClosePrice` | String | 前一交易日收点位 |
| `openPrice` | String | 今日开盘点位 |
| `traceEtfs` | List | 南方基金追踪本指数的 ETF 列表，元素含产品代码、简称等 |
| `videoUrl` | String | 关联视频 URL |
| `updateTime` | String | 数据更新时间 `yyyy-MM-dd HH:mm:ss` |

#### getRealTimeData — 实时行情（指数，type=1）
后端路径：`POST /etfapp/retail/product/getRealTimeData`，请求体 `{productCode=indexCode, type="1"}`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `tradingDay` | String | 交易日 `yyyyMMdd` |
| `time` | String | 实时时刻 `HHmmssSSS`（时分秒毫秒） |
| `percentageChange` | String | 当日指数涨跌幅，单位 `%` |
| `prePercentChange` | String | 前一交易日涨跌幅，单位 `%` |
| `closePrice` | String | 当前点位（交易时段）或收盘点位（非交易时段） |
| `preClosePrice` | String | 前一交易日收盘点位 |
| `nowPrice` | String | 当前点位，实时同步（语义同 `closePrice`） |
| `openPrice` | String | 当日开盘点位 |
| `highPrice` | String | 当日最高点位 |
| `lowPrice` | String | 当日最低点位 |
| `turnover` | String | 指数成分股合计成交金额（当日累计），单位 `元` |
| `volume` | String | 指数成分股合计成交量（当日累计），单位 `手` |
| `iopv` | String | 指数不提供，一般为空 |
| `premDisRto` | String | 指数不提供，一般为空 |

> **时效性**：**交易时段**返回当日实时行情（5 秒刷新）；**非交易时段**返回上一个刷新值，收盘后数据更新存在延迟。⚠ Agent 无需自行判断当天是否为交易日，仅需如实标注 API 返回的数据日期；**禁止**从数据日期反推交易日历。

---

### 4. etf-detail all — ETF 详情页聚合

**参数**：

| CLI 选项 | 说明 | 默认值 |
|---|---|---|
| `--product-code` | ETF 产品代码（必填），例 `510300` | — |
| `--index-code` | 跟踪指数代码；缺省时自动调跟踪指数接口获取 | — |
| `--start-date` / `--end-date` | 时间序列起止日 `yyyyMMdd` | 默认查询最近 30 天 |
| `--date-range` | 收益走势日期范围（与 `start/end` 二选一），例 `"1m"`、`"3m"`、`"1y"`、`"3y"`、`"sinceFound"` | — |
| `--net-inflow-type` | 净流入口径：`3`=本产品净流入；`2`=同指数下全部同类 ETF 合计净流入；`1`=子接口 `data` 返回 `null`（后端未实现） | `3` |

**返回顶层结构**：`{ productCode, indexCode, params, results, _errors }`（含义同 `index-detail`）

**`results` 包含的子接口 key**：`getMarketIndicatorData`、`queryTrackIndex`、`getEtfLinkInfo`、`getNetInflow`、`getProductWindRank`、`getManagerInfo`、`getRiskReturnCharacter`、`getHoldStock`、`getIndustryDistribution`、`getReturnTrendList`、`getRealTimeData`。各子接口返回结构详见下方字段说明。

#### getMarketIndicatorData — 市场指标
在 `index-base list-etf` 的 `dataList` 元素全部字段之上，额外提供下列「智选标签」字段（用于产品筛选高亮）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `smartSelect` | Integer | 是否雷达智选推荐：`1`=是，`0`=否 |
| `scaleBig` | Integer | 是否规模较大：`1`=是，`0`=否 |
| `trackErrorSmall` | Integer | 是否跟踪误差较小：`1`=是，`0`=否 |
| `premDisRtoLow` | Integer | 是否折价率较低：`1`=是，`0`=否 |
| `comRatioLow` | Integer | 是否综合费率较低：`1`=是，`0`=否 |

#### queryTrackIndex — 跟踪指数
返回 `HotIndexVo`（继承 `RealTimeModel`），含指数基本信息、估值、实时行情等字段。

| 字段 | 类型 | 说明 |
|---|---|---|
| `indexCode` / `indexName` / `indexAbbr` | String | 指数代码 / 全称 / 简称 |
| `infoIndexCode` | String | 统一资讯（聚源）指数代码 |
| `indexWindCode` | String | 万得（Wind）指数代码 |
| `trackIndexType` | String | 跟踪指数类型标签（业务自定义文本） |
| `indexType` | Integer | 类型枚举：`1`=指数；`2`=ETF；`3`=场外 |
| `ibm` | String | 分类代码 |
| `type` | String | 分类名称 |
| `typeLv1` / `typeNameLv1` | String | 一级分类代码 / 中文名 |
| `typeLv2` / `typeNameLv2` | String | 二级分类 |
| `typeLv3` / `typeNameLv3` | String | 三级分类 |
| `typeNameLv4` | String | 四级分类名称 |
| `trackCode` | String | 追踪指数代码 |
| `setUpDate` | String | 成立日期 `yyyyMMdd` |
| `netInflow` | BigDecimal | 净流入金额，单位 `亿元` |
| `pe` | BigDecimal | 最新交易日市盈率（PE-TTM），倍 |
| `peAvg` | String | PE 分位平均值 |
| `pePercent` | BigDecimal | PE 历史分位（从 2016-01-04 起），单位 `%` |
| `peLevel` | String | PE 等级标识（业务自定义档位） |
| `pb` / `pbAvg` / `pbPercent` | BigDecimal | 最新交易日市净率 / PB 历史均值 / PB 历史分位，分位单位 `%` |
| `fed` / `fedAvg` / `fedPercent` | String | FED 比値 / 历史均値（从 2016-01-04 起）/ 历史分位（从 2016-01-04 起），分位单位 `%` |
| `lastYearPerChange` | String | 最新交易日起向前推 12 个自然月涨跌幅，单位 `%` |
| `yelid` | BigDecimal | 日涨跌幅，单位 `%`（注意字段拼写） |
| `rankLabel` | Integer | 同类排名（业务自定义档位） |
| `isLinkRelation` | Boolean | 是否直接跳转到关联详情 |
| `isRecommend` | Integer | 是否精选推荐：`1`=是 |
| `isSouthFund` | Integer | 是否南方基金产品：`1`=是 |
| `relateFund` | Object | 关联的本公司同类产品（含代码/简称等） |

**继承自 RealTimeModel 的实时行情字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `tradingDay` | String | 交易日 `yyyyMMdd` |
| `time` | String | 时刻 `HHmmssSSS` |
| `percentageChange` | String | 涨跌幅，单位 `%` |
| `prePercentChange` | String | 前一交易日涨跌幅，单位 `%` |
| `closePrice` | String | 当前点位/价格 |
| `preClosePrice` | String | 前一交易日收盘点位 |
| `nowPrice` | String | 当前价 |
| `openPrice` | String | 开盘价 |
| `highPrice` | String | 最高价 |
| `lowPrice` | String | 最低价 |
| `turnover` | String | 成交金额，单位 `元` |
| `volume` | String | 成交量，单位 `手` |
| `iopv` | String | 净值估算（IOPV） |
| `premDisRto` | String | 溢折率，单位 `%` |

#### getEtfLinkInfo — ETF 联接信息
| 字段 | 类型 | 说明 |
|---|---|---|
| `etfFundCode` | String | 场内 ETF 基金代码 |
| `etfFundName` | String | 场内 ETF 名称 |
| `etfLinkFundCode` | String | 对应的 ETF 联接基金代码（场外申赎） |
| `etfLinkFundName` | String | ETF 联接基金名称 |
| `yieldSinceLaunch` | String | 联接基金成立以来收益率，单位 `%` |
| `productScale` | String | 产品规模，单位 `亿元` |
| `scaleDate` | String | 规模数据日期 `yyyyMMdd` |

#### getNetInflow — 净流入
返回 `List<NetInflowModel>`（`type=1` 时 `data` 为 `null`），按 `tradingDay` 升序。

| 字段 | 类型 | 说明 |
|---|---|---|
| `tradingDay` | String | 交易日 `yyyyMMdd` |
| `productCode` | String | 产品代码，仅 `type=3` 返回 |
| `indexCode` | String | 对应指数代码，仅 `type=2` 返回 |
| `netInflow` | BigDecimal | 单日净流入，单位 `亿元`。正=净流入，负=净流出 |

#### getProductWindRank — Wind 排名
返回 `List<Map<String, Object>>`，字段随产品类型动态变化，典型字段包括：基金代码、近 1M/3M/6M/1Y/3Y 收益率（单位 `%`）、同类排名（同类型基金中的名次）、分位（单位 `%`）等。

#### getManagerInfo — 基金经理
| 字段 | 类型 | 说明 |
|---|---|---|
| `managerId` | long | 经理 ID |
| `managerName` | String | 经理姓名 |
| `managerHeaderUrl` | String | 经理头像图片 URL |
| `workYears` | String | 从业年限（年），截至当前系统日期动态计算 |
| `managerLabel` | String | 经理标签（如「金牛」「明星」等业务标签） |

#### getRiskReturnCharacter — 风险收益特征
按统计区间分行返回：

| 字段 | 类型 | 说明 |
|---|---|---|
| `dateRange` | Integer | 统计区间枚举：`12`=近 1 年；`36`=近 3 年；`60`=近 5 年 |
| `endDate` | String | 数据截止日 `yyyyMMdd` |
| `standardDeviation` | BigDecimal | 区间波动率，单位 `%`（年化） |
| `rankStandardDeviation` | BigDecimal | 波动率同类排名百分位，单位 `%`（越低=越平稳） |
| `sharpeRatio` | BigDecimal | 夏普比率（无量纲，越大=风险调整后收益越优） |
| `rankSharpeRatio` | BigDecimal | 夏普比率同类排名百分位，单位 `%`（越低=越优） |
| `maximumBack` | BigDecimal | 最大回撤，单位 `%`（一般为负） |
| `rankMaximumBack` | BigDecimal | 最大回撤同类排名百分位，单位 `%`（越低=回撤越小） |

#### getHoldStock — 持仓股票
| 字段 | 类型 | 说明 |
|---|---|---|
| `holdName` | String | 持仓股票名称 |
| `holdWeight` | String | 占基金净值比，单位 `%` |
| `marketValue` | String | 持仓市值，单位 `元` |
| `holdAmount` | String | 持仓数量，单位 `股` |
| `endDate` | String | 持仓数据截止日 `yyyyMMdd`（季度披露） |
| `industryName` | String | 所属行业中文名 |
| `changeRatio` | String | 较上季度持仓权重变化，单位 `%` |

#### getIndustryDistribution — 行业分布
返回 `Map<分类层级名, List>`，每个 List 元素：

| 字段 | 类型 | 说明 |
|---|---|---|
| `industryName` | String | 行业中文名 |
| `industryRatio` | String | 该行业在基金中的占比，单位 `%` |
| `endDate` | String | 数据截止日 `yyyyMMdd` |

#### getReturnTrendList — 收益走势
返回 `Map<序列名, List>`，每条记录：

| 字段 | 类型 | 说明 |
|---|---|---|
| `tradeDate` | String | 交易日 `yyyyMMdd` |
| `closePrice` | String | 单位净值，单位 `元/份` |
| `dailyReturn` | String | 涨跌幅，单位 `%` |
| `yield` | String | 基准收益率，单位 `%` |
| `maxRetreat` | String | 区间最大回撤幅度，单位 `%`（一般为负） |
| `turnover` | String | 成交金额，单位 `元` |

#### getRealTimeData — 实时行情（场内 ETF，type=2）
后端路径：`POST /etfapp/retail/product/getRealTimeData`，请求体 `{productCode, type="2"}`。字段同上表，场内 ETF 额外返回以下与二级市场报价相关的字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `closePrice` | String | 当前二级市场成交价（交易时段）或收盘价，单位 `元/份` |
| `preClosePrice` | String | 前一交易日收盘价，单位 `元/份` |
| `nowPrice` | String | 当前价（语义同 `closePrice`） |
| `openPrice` / `highPrice` / `lowPrice` | String | 当日开盘/最高/最低价，单位 `元/份` |
| `turnover` | String | 本 ETF 交易金额（当日累计），单位 `元` |
| `volume` | String | 本 ETF 成交量（当日累计），单位 `手` |
| `iopv` | String | ETF 净值估算（IOPV），单位 `元/份` |
| `premDisRto` | String | 溢折率 = (closePrice - iopv) / iopv，单位 `%`，后端自动按上述公式计算 |

> **时效性**：**交易时段**返回当日实时行情（5 秒刷新）；⚠ Agent 无需自行判断当天是否为交易日，仅需如实标注 API 返回的数据日期；**禁止**从数据日期反推交易日历。

---

### 5. otc-detail all — 场外详情页聚合

**参数**：

| CLI 选项 | 说明 | 默认值 |
|---|---|---|
| `--product-code` | 场外基金代码（必填） | — |
| `--index-code` | 跟踪指数代码；缺省时自动获取 | — |
| `--start-date` / `--end-date` | 时间序列起止日 `yyyyMMdd` | 默认查询最近 30 天 |
| `--date-range` | 收益走势日期范围（可选），同 etf-detail | — |

**返回顶层结构**：`{ productCode, indexCode, params, results, _errors }`

**`results` 包含的子接口 key**：`baseEtfLinkInfo`、`queryTrackIndex`、`scaleChange`、`getProductWindRank`、`linkFundHold`、`getManagerInfo`、`otherSubShare`、`getRiskReturnCharacter`、`getReturnTrendList`。各子接口返回结构详见下方字段说明。

#### baseEtfLinkInfo — 场外基金基本信息
字段同 `index-base list-etf` 的 `dataList` 元素。

#### scaleChange — 规模变化
| 字段 | 类型 | 说明 |
|---|---|---|
| `fundCode` | String | 基金代码 |
| `asset` | BigDecimal | 资产规模，单位 `亿元` |
| `share` | BigDecimal | 基金份额，单位 `份` |
| `assetChangeRatio` | BigDecimal | 较上一季度末资产规模变化率，单位 `%` |
| `shareChangeRatio` | BigDecimal | 较上一季度末份额变化率，单位 `%` |
| `date` | String | 数据日期 `yyyyMMdd`（一般按季度披露） |

#### linkFundHold — 联接基金持仓
| 字段 | 类型 | 说明 |
|---|---|---|
| `fundCode` | String | 基金代码 |
| `endDate` | String | 数据截止日 `yyyyMMdd` |
| `stockRate` | String | 权益（股票）投资占比，单位 `%` |
| `bondRate` | String | 固定收益（债券）投资占比，单位 `%` |
| `fundRate` | String | 基金投资占比，单位 `%` |
| `derivativesRate` | String | 金融衍生品投资占比，单位 `%` |
| `pmRate` | String | 贵金属投资占比，单位 `%` |
| `bbfaRate` | String | 买入返售金融资产占比，单位 `%` |
| `mmiRate` | String | 货币市场工具占比，单位 `%` |
| `currencyRate` | String | 银行存款和结算备付金占比，单位 `%` |
| `fpRate` | String | 理财产品投资占比，单位 `%` |
| `otherRate` | String | 其它资产占比，单位 `%` |
| `top10Fund` | List | 前 10 大重仓基金，元素含名称/代码/占比 `%` |
| `top10Stock` | List | 前 10 大重仓股票，元素含名称/代码/占比 `%` |
| `top5Bond` | List | 前 5 大重仓债券，元素含名称/代码/占比 `%` |

#### otherSubShare — 同基金其它份额
| 字段 | 类型 | 说明 |
|---|---|---|
| `fundName` | String | 基金全称 |
| `shortName` | String | 基金简称 |
| `fundCode` | String | 当前份额基金代码 |
| `shareType` | String | 份额类型，如 `"A"`、`"C"`、`"D"`、`"E"` |
| `fundMainCode` | String | 基金主代码（同一基金不同份额共享） |
| `foundDate` | String | 成立日期 `yyyyMMdd` |
| `confirmDays` | Integer | 交易确认时间（单位：天） |
| `fundStatus` | String | 基金运作状态枚举：`"0"`=运作中；`"10"`=已清盘；`"12"`=成立中（建仓期） |
| `holdPeriodFund` | String | 是否持有期基金：`"1"`=是；`"0"`=否 |
| `holdPeriod` | String | 持有期基金的持有期限（业务文本，如「30 天」「6 个月」） |

#### queryTrackIndex / getManagerInfo / getRiskReturnCharacter / getReturnTrendList
字段含义同 `etf-detail` 中的同名接口。

---

## 使用要点

- **聚合命令容错**：`index-detail` / `etf-detail` / `otc-detail` 的 `all` 子命令并行调用各子接口，任一失败只记入 `_errors`，不阻断其它结果。
- **JSON 输出**：使用 `--json` 输出紧凑 JSON，适合 Agent 解析；不带该选项输出人类可读的缩进 JSON。
- **退出码**：非零退出码表示失败，请同时检查错误输出。
- **数据时效性**：行情数据每 5 秒更新；其他全部数据为日频，且收盘后存在延迟，不会即时切换为当日数据。
- ⚠ **【硬性约束】实时行情数据时间来源**：Agent 返回实时行情类指标（涨跌幅、最新价、成交额、溢折率、指数点位等）时，数据时间**必须**从以下两个接口之一获取，**禁止**从 `list-etf` 的 `dataDate`/`yieldDate` 取日期：
  - `etf-detail all` / `index-detail all` 的 `getRealTimeData` 子接口 → 取 `tradingDay`（`yyyyMMdd`）+ `time`（`HHmmssSSS`），拼合为 `YYYY-MM-DD HH:mm:ss`
  - `index-detail all` 的 `queryIndexDetail` 子接口 → 取 `pointValueUpdateTime`（已是 `yyyy-MM-dd HH:mm:ss` 格式）
  - 若仅调用了 `list-etf`，则**必须补充调用** `etf-detail all`（ETF）或 `index-detail all`（指数）以获取上述时间戳，否则无法标注实时行情时间
  - 日频/季度指标的数据日期不受此约束，仍取 `dataDate`/`yieldDate`/`peDate`/`roeDate`/`astDate` 等
- **数据日期标注**：Agent 向用户返回数据时，**必须在回复末尾以「日期标注：」独立段落逐项标注各指标的数据日期**，标注时使用业务术语而非 API 字段名。不同指标的日期可能不同（例如：实时行情类=当日，PE=当日或前日，ROE=上季度末），**按数据频率分组标注**：
  - 实时行情类标 `YYYY-MM-DD HH:mm:ss 实时行情`（时间来源见上方硬性约束）
  - 日频类标 `数据日期 YYYY-MM-DD（日频）`（数据时间取 `dataDate`/`yieldDate`/`peDate`/`roeDate`/`astDate` 等）
  - 季度类标 `数据截止 YYYY-MM-DD`。

  **日期标注示例**：
  ```
  日期标注：
  - 涨跌/点位：2026-06-15 15:00:03 实时行情
  - 今年以来/近1月/近1周：数据日期 2026-06-12（日频）
  - 净值、PE、股息率：同上
  - ROE：数据日期 2026-03-31（季度）
  - "—" 表示成立不足该时段，无对应数据
  ```

  **错误示例**：涨跌幅 +2.10%、市盈率 14.47 倍、净资产收益率 2.27%、规模 175.08 亿元（数据日期: 20260612）← 笼统标注，且不同日期的指标被归为同一日期
- **业务化表述**：Agent 向用户返回数据时，必须使用「业务术语映射」表中对应的业务术语（如"涨跌幅"而非"yield"、"规模"而非"ast"、"成交额"而非"traval"），禁止直接输出 API 字段名。
- **分页完整性**：`index-base list-etf` 的服务端每页实际返回条数远小于 `--page-size`（实测 type=2 约 5 条、type=3 约 15 条）。**凡涉及全量筛选、统计汇总（按 `managementCompany` 过滤、求总规模、计总数等），Agent 必须逐页递进直到累计拉取条数 ≥ `totalRows` 才停止**，禁止仅拉取第 1 页就执行筛选或汇总。以每次响应中 `dataList` 的实际长度推进 `--page-no`，而非用 `page-no × page-size ≥ totalRows` 判断终止。
- **单位与符号约定**：所有 `%` 字段已乘以 100；金额字段统一为 `元`（无亿/万换算）；正/负号一律保留语义（涨跌、流入流出、溢折等）。

## 示例

```bash
# 1. 登录
etfirst auth login --api-key <YOUR_KEY>

# 2. 查指数分类字典
etfirst --json index-base clas --type 1

# 3. 拉取 ETF 列表
etfirst --json index-base list-etf \
    --type 2 --clas <字典里的 key> \
    --page-no 1 --page-size 20 \
    --sort-key yield --sort-direction desc

# 4. 聚合指数详情页
etfirst --json index-detail all --index-code 000300

# 5. 聚合 ETF 详情页
etfirst --json etf-detail all --product-code 510300

# 6. 聚合场外详情页
etfirst --json otc-detail all --product-code 000001
```

### 退出登录

```bash
etfirst auth logout              # 仅清除登录态（保留 Key，下次可直登）
etfirst auth logout --purge-key  # 同时清除 config.json 中保存的 API Key
```
