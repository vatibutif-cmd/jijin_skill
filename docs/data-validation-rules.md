# FAMAS 数据校验规则集 (Data Validation Ruleset)

> **适用范围**: 全局约束，所有 10 个 Agent 的输出均受此规则集约束
> **版本**: v1.0 | **更新**: 2026-07-26
> **定位**: Project Knowledge / Custom Instructions 追加

---

## 规则集架构

```
┌─────────────────────────────────────────────────────────────┐
│                    规则集分为四层                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: 幻觉检测 (Hallucination Detection)     ← 事实溯源  │
│ Layer 2: 数值边界校验 (Numeric Bounds)          ← 合理性    │
│ Layer 3: 交叉验证 (Cross-Validation)            ← 一致性    │
│ Layer 4: 校验失败处理 (Validation Failure)      ← 处置      │
└─────────────────────────────────────────────────────────────┘
```

校验触发时机：每个 Agent 生成 JSON 输出后、传递给下游 Agent 之前，由编排器（Router）自动执行。wealth_advisor 在组装最终报告前额外执行一次全量校验。

---

## Layer 1: 幻觉检测 (Hallucination Detection)

### 1.1 数字来源可追溯规则

**规则 H1**: 如果 Agent 输出的 JSON 中出现了某个具体数值（非字符串描述性文字），则本轮对话的工具调用记录中必须存在该数值的数据源。

**检测方式**:
```
对于输出的每个 number 类型字段:
  ① 提取该字段路径（如 JSON₂.return_metrics.annual_return_1y_pct）
  ② 回溯本轮对话中所有 MCP 工具调用的返回结果
  ③ 搜索该数值的近似值（允许 ±5% 的舍入误差）是否存在于任一工具返回中
  ④ 若不存在 → 标记为 H1-疑似幻觉
```

**豁免项**（以下字段不受 H1 约束）:
- 计算公式得出的衍生指标（Sharpe, Calmar, HHI, Alpha, TCR 等）——其输入值必须在工具返回中可溯源
- wealth_advisor 的综合评分和星级——这些是主观判断，不要求数值溯源
- 字符串描述性字段（如 `rating_rationale`, `timing_suggestion`）

**示例**:
```
✅ 通过: JSON₂.risk_metrics.max_drawdown_pct = -28.40
         → 工具返回 fund_nav_history.summary.max_drawdown_pct = -28.40 ✓

❌ 触发: JSON₂.return_metrics.annual_return_1y_pct = 15.20
         → 工具返回 fund_nav_history 中无对应区间收益，且无 WebSearch 来源
         → H1-疑似幻觉: annual_return_1y_pct = 15.20 无法溯源
```

### 1.2 非结构化信息溯源规则

**规则 H2**: 如果 Agent 输出的字符串字段中包含人名、日期、具体事件描述，则该信息的获取方式必须在 field-level 可追溯。

**检测方式**:
```
对于关键字符串字段 (manager_name, inception_date, benchmark 等):
  ① 映射到对应的 MCP 工具（如 manager_name → fund_basic_info 或 fund_manager_info）
  ② 检查该工具在本轮对话中是否被成功调用
  ③ 若未调用 → 标记为 H2-不可追溯信息
```

**映射表**:

| 字段 | 必需工具调用 | 降级源 |
|------|-------------|--------|
| `manager_name` (在 manager_profiler 中) | `fund_manager_info` | `fund_basic_info`（仅姓名） |
| `inception_date` | `fund_basic_info` | WebSearch |
| `benchmark` | `fund_basic_info` | WebSearch |
| `management_fee_pct` | `fund_basic_info` | WebSearch |
| `top10_holdings[].stock_name` | `fund_holdings` | 无降级源 |
| `announcements[].title` | `fund_announcements` | WebSearch |

**示例**:
```
❌ 触发: JSON₄.manager_name = "刘格菘"
         → fund_manager_info 未被调用，fund_basic_info 也未被调用
         → H2-不可追溯: manager_name 的来源不明（可能是训练数据记忆，非实时数据）

✅ 通过: JSON₄.manager_name = "刘格菘"
         → fund_manager_info(fund_code="005911") 已调用，返回包含"刘格菘" ✓
```

### 1.3 时间轴逻辑一致性规则

**规则 H3**: 输出的时间相关陈述必须与基金客观时间线一致。

**检测项**:

| 检测条件 | 逻辑校验 | 失败标记 |
|----------|----------|----------|
| 输出中包含"近3年收益" | `当前日期 - inception_date ≥ 1095 天` | H3-时间轴错误: 基金成立不足3年 |
| 输出中包含"近5年收益" | `当前日期 - inception_date ≥ 1825 天` | H3-时间轴错误: 基金成立不足5年 |
| 输出中包含经理"任职期间收益" | `tenure_days > 0`（来自 manager_info） | H3-时间轴错误: 经理任职数据缺失 |
| 输出引用"2026Q1季报" | `fund_holdings.report_period` 包含"2026年1季度" | H3-时间轴错误: 季报时间不匹配 |

**示例**:
```
❌ 触发: JSON₂.return_metrics.annual_return_5y_pct = 12.80
         → JSON₁.inception_date = "2024-02-07"，成立约2.4年
         → H3-时间轴错误: 基金 005911 成立仅2.4年，无法计算"近5年收益"
         → 该字段应填 null，不应给出虚假数值
```

---

## Layer 2: 数值边界校验 (Numeric Bounds)

### 2.1 指标硬边界

**规则 B1**: 以下金融指标必须落在硬边界内，超出边界视为数据异常。

| 指标 | 字段路径 | 硬边界 | 边界来源 | 失败标记 |
|------|----------|--------|----------|----------|
| 夏普比率 | `risk_metrics.sharpe_ratio` | -3.0 ~ 5.0 | 中国公募基金实证区间（99%分位） | B1-Sharpe 越界 |
| 卡玛比率 | `risk_metrics.calmar_ratio` | -5.0 ~ 5.0 | 业界常规范围 | B1-Calmar 越界 |
| 年化收益率 | `return_metrics.*_pct` | -100.0 ~ 200.0 | 单年度公募基金收益极值 | B1-收益越界 |
| 最大回撤 | `risk_metrics.max_drawdown_pct` | -100.0 ~ 0.0 | 数学定义 | B1-回撤越界 |
| 年化波动率 | `risk_metrics.annual_volatility_pct` | 0.0 ~ 100.0 | 常规上限 | B1-波动率越界 |
| 超额收益 Alpha | `return_metrics.alpha_*_pct` | -50.0 ~ 50.0 | 年化 Alpha 合理区间 | B1-Alpha 越界 |
| 管理费率 | `management_fee_pct` | 0.10 ~ 3.50 | 公募基金监管上限+下限 | B1-费率越界 |
| 托管费率 | `custody_fee_pct` | 0.05 ~ 0.50 | 公募基金常规范围 | B1-托管费率越界 |

**处理**: 越界字段不改值，但标注 `B1-XX越界: {value} 超出 [{min}, {max}] 合理范围`。下游 Agent 应优先采用工具返回的原始值，而非越界的 Agent 计算值。

### 2.2 逻辑一致性边界

**规则 B2**: 以下字段组合必须满足数学/业务逻辑约束。

| 约束条件 | 校验公式 | 失败标记 |
|----------|----------|----------|
| 前十大持仓占比之和 ≤ 100% | `SUM(top10_holdings[].weight_pct) ≤ 100` | B2-持仓和越界 |
| 行业分布权重之和 ≤ 100% | `SUM(sector_distribution[].weight_pct) ≤ 100` | B2-行业和越界 |
| 持有人结构比例之和 = 100%（近似） | `|institutional_ratio_pct + individual_ratio_pct - 100| ≤ 2` | B2-持有人和不闭合 |
| 基金规模 > 0 | `current_scale_billion > 0` | B2-规模为零或负 |
| 最大回撤幅度 ≥ 单日最大跌幅（近似） | `|max_drawdown_pct| ≥ |MIN(daily_return_pct)|` | B2-回撤小于日波动（异常） |
| 夏普 ≥ 0 时区间收益 ≥ 0（近似） | `sharpe_ratio > 0.5 → period_return_pct > -5` | B2-Sharpe正但收益负（矛盾） |
| 成立日期 ≤ 当前日期 | `inception_date ≤ today` | B2-成立日在未来 |
| 费率侵蚀比 ≤ 100% | `return_erosion_ratio_pct ≤ 100` | B2-侵蚀比越界 |

**处理**: 触发 B2 校验不通过时，该字段组合所对应的上层分析结论应标注为"数据一致性异常，结论置信度降低"。

### 2.3 异常值漂移检测

**规则 B3**: 如果 Agent 输出的某数值较同类基金均值偏离超过 3 个标准差，需在输出中显式标注。

| 指标 | 同类均值参考 | 偏离阈值 | 标记 |
|------|-------------|----------|------|
| 年化收益 | 同类中位数 ± 15% | |3σ| > 45% | B3-收益极端偏离 |
| 最大回撤 | 同类中位数 -22% | |回撤| > 40% | B3-回撤极端偏离 |
| 管理费率 | 同类中位数 1.50% | 费率 > 2.5% 或 < 0.3% | B3-费率极端偏离 |
| 换手率 | 同类中位数 120% | 换手率 > 500% | B3-换手率极端 |
| 机构持有比例 | 同类中位数 30% | 机构 > 90% 或 < 1% | B3-持有人极端 |

**处理**: 标注后不阻断开流，但下游 Agent 应在适配投资者画像中注明"该指标处于极端分位"。

---

## Layer 3: 交叉验证 (Cross-Validation)

### 3.1 同源数据一致性

**规则 C1**: 两个不同 Agent 引用了同一底层数据源的结果，其数值必须一致。

**检测项**:

| 交叉验证对 | 字段A | 字段B | 允许偏差 | 失败标记 |
|-----------|-------|-------|----------|----------|
| prospectus vs cost | `JSON₁.fee_structure.management_fee_pct` | `JSON₃.explicit_fees.management_fee_pct` | 0.00% | C1-费率不一致 |
| prospectus vs cost | `JSON₁.fee_structure.custody_fee_pct` | `JSON₃.explicit_fees.custody_fee_pct` | 0.00% | C1-托管费率不一致 |
| prospectus vs portfolio_doctor | `JSON₁.current_scale_billion` | `JSON₉.portfolio.scale` | 5% | C1-规模数据不一致 |
| performance vs wealth | `JSON₂.risk_metrics.max_drawdown_pct` | `JSON₆.risk_profile.max_drawdown_3y_pct` | 0.01% | C1-回撤数据不一致 |
| performance vs wealth | `JSON₂.risk_metrics.sharpe_ratio` | `JSON₆.risk_profile.sharpe_ratio` | 0.01% | C1-Sharpe 数据不一致 |

**示例**:
```
❌ 触发: JSON₁.fee_structure.management_fee_pct = 1.50
         JSON₃.explicit_fees.management_fee_pct = 1.20
         → C1-费率不一致: prospectus_analyzer 和 cost_analyzer 报告的管理费率相差 0.30%
         → 可能原因: cost_analyzer 使用了错误的数据源或调用了不同份额的费用率
```

### 3.2 衍生指标可复现性

**规则 C2**: performance_analyst 计算的衍生指标，若其计算输入可获取，则结果应可复现。

**检测方式**:
```
对于 performance_analyst 的每个衍生指标:
  ① 如果 fund_nav_history 原始数据可用（未降级），则用相同公式重新计算
  ② 比较 Agent 输出值 vs 编排器验算值
  ③ 偏差超过阈值 → 标记冲突
```

| 衍生指标 | 验算公式 | 允许偏差 | 失败标记 |
|----------|----------|----------|----------|
| 区间收益率 | `(end_nav - start_nav) / start_nav × 100` | 0.50% | C2-收益率偏差 |
| 年化波动率 | `STDDEV(daily_returns) × SQRT(252)` | 2.00% | C2-波动率偏差 |
| 最大回撤 | `MIN((nav - peak) / peak) × 100` | 1.00% | C2-回撤计算偏差 |
| 上行/下行捕获率 | 对比基准同期数据 | 有工具返回 → 同公式；无工具返回 → 不可验证 | C2-捕获率偏差 |

**示例**:
```
⚠ 触发: Agent 输出 annual_return_1y_pct = 8.35
         → fund_nav_history 返回近252日净值序列
         → 编排器验算: (1.8523 - 1.8310) / 1.8310 × 100 = 1.16%
         → C2-收益率偏差: Agent报告8.35%，验算值1.16%，偏差7.19% > 允许0.50%
         → 优先级最高: 该指标标记为"不可信"
```

### 3.3 跨维度逻辑一致性

**规则 C3**: 不同维度之间的定性描述应逻辑自洽。

**检测项**:

| 条件A | 条件B | 逻辑约束 | 失败标记 |
|-------|-------|----------|----------|
| fund_type 包含"债券"或"货币" | manager_profiler 被调用且输出非 null | 债券/货币基金通常无需经理画像，但若有主动管理成分可保留 | C3-低信号画像（警告，不阻断） |
| 行业 HHI < 0.05 | style_analysis 标记为"集中" | 低 HHI 意味着分散，不应描述为"集中" | C3-风格描述矛盾 |
| Alpha > 10%（年化） | 风格漂移 quarterly > 1.0 | 高 Alpha + 高漂移 → 大概率是风格暴露而非选股能力 | C3-Alpha来源可疑 |
| 最大回撤 < -35% | risk_level = "R3" | 回撤超过-35% 不能标记为 R3（中风险），至少应为 R4 | C3-风险等级低估 |
| 机构持有比例 > 80% | 规模 < 5 亿 | 高机构 + 小规模 → 单一机构大额赎回风险 | C3-机构集中度风险未标注 |
| Sharpe > 2.0 | 年化收益 < 5% | Sharpe > 2 需要极低波动率，年化通常应>5% | C3-Sharpe与收益不协调 |

---

## Layer 4: 校验失败处理 (Validation Failure)

### 4.1 失败分级

| 级别 | 条件 | 处置 |
|------|------|------|
| **INFO** (信息) | B3 异常值标注、C3 低信号警告 | 不影响评级，仅在 `quality_flags` 中记录 |
| **WARN** (警告) | H1/H2 单项触发但可降级修复、C1 小偏差(<1%)、C3 描述矛盾 | 输出中附加警告标注，不阻断工作流 |
| **ERROR** (错误) | H1 多项触发、H3 时间轴错误、B1 越界、B2 逻辑不闭合、C2 计算偏差超标 | 对应字段降权或置 null；wealth_advisor 相关维度评分上限降至 3.0 |
| **CRITICAL** (致命) | 3项及以上 ERROR、基准数据全部不可用、fund_code 不一致 | 终止当前 Agent 输出，降级为"数据质量不足"模式 |

### 4.2 quality_flags 字段定义

所有 Agent 的输出 JSON 必须包含 `quality_flags` 数组。格式如下：

```json
{
  "quality_flags": [
    {
      "level": "WARN",
      "code": "H1",
      "field": "return_metrics.annual_return_1y_pct",
      "detail": "数值 8.35 无法在工具返回的净值序列中溯源（验算值为 1.16%），偏差 7.19%",
      "action": "该字段已标记为低置信度，下游Agent应谨慎引用"
    }
  ],
  "validation_summary": {
    "total_checks": 18,
    "passed": 15,
    "info": 1,
    "warn": 1,
    "error": 1,
    "critical": 0,
    "overall_confidence": "medium"
  }
}
```

**overall_confidence 取值**:
- `"high"` — 0 个 ERROR，≤ 2 个 WARN
- `"medium"` — 1-2 个 ERROR 或 3-5 个 WARN
- `"low"` — 3+ 个 ERROR 或任一 CRITICAL
- `"unreliable"` — 5+ 个 ERROR，数据质量不足以支撑分析结论

### 4.3 wealth_advisor 的校验汇总逻辑

wealth_advisor 在消费前序 5 个 Agent 的 JSON 时，先读取每个 JSON 的 `validation_summary.overall_confidence`：

```
IF 任一上游Agent的 overall_confidence = "unreliable"
  → wealth_advisor 的综合评级 star_rating = null
  → rating_rationale 首行: "[数据质量不足] 上游分析数据存在严重问题，无法给出有效评级"
  → 报告中所有评级相关字段置 null

ELSE IF 2个及以上上游Agent的 overall_confidence = "low"
  → star_rating 正常计算，但在评级后标注: "[置信度受限] 部分上游数据质量偏低，本评级仅供参考"
  → key_risks 中追加一条: "数据质量风险: XX、YY Agent 的数据校验存在异常，结论置信度降低"

ELSE
  → 正常评级流程，quality_flags 汇总所有上游标记
```

### 4.4 校验报告的呈现

在最终 Markdown 报告中，如果 quality_flags 非空，在免责声明之前追加：

```markdown
---
### 数据质量校验报告

| 级别 | 条数 | 说明 |
|------|------|------|
| INFO | {count} | 轻度异常，不影响结论 |
| ⚠ WARN | {count} | 需关注，但不影响核心评级 |
| ❌ ERROR | {count} | 对部分结论的可信度有影响 |
| 🚫 CRITICAL | {count} | 严重影响分析可靠性 |

{逐条列出 ERROR 和 CRITICAL 级别的详情}

**综合评估**: {overall_confidence 的中文映射}
```

---

## 附录A: 校验执行清单（编排器使用）

编排器在每轮对话中需维护一个 `validation_log`，记录校验结果：

```
[ ] Layer 1 - H1: 数字溯源检查 (针对每个 Agent 输出的每个 number 字段)
[ ] Layer 1 - H2: 非结构化信息溯源 (manager_name, inception_date, benchmark)
[ ] Layer 1 - H3: 时间轴逻辑一致性 (inception_date vs 收益年份)
[ ] Layer 2 - B1: 指标硬边界 (所有 Agent 输出)
[ ] Layer 2 - B2: 逻辑一致性边界 (持仓和、持有人和、回撤vs波动)
[ ] Layer 2 - B3: 异常值漂移 (可选——需要同类基金对比基准)
[ ] Layer 3 - C1: 同源数据一致性 (prospectus vs cost vs wealth)
[ ] Layer 3 - C2: 衍生指标可复现性 (仅 performance_analyst)
[ ] Layer 3 - C3: 跨维度逻辑一致性 (定性 vs 定量)

完成后:
[ ] 为每个 Agent 的 JSON 追加 quality_flags
[ ] 更新 wealth_advisor 的 validation_summary
[ ] 在最终报告中追加数据质量校验报告段落
```

## 附录B: 校验规则覆盖矩阵

| 规则层 | 规则数 | 适用 Agent | 自动/手动 |
|--------|--------|-----------|-----------|
| H1 数字溯源 | 1（检测逻辑） | 全部 | 自动（比对工具返回） |
| H2 信息溯源 | 1 + 映射表 | 全部 | 自动（检查工具调用记录） |
| H3 时间轴 | 4 项检测 | performance, wealth | 自动（比对 inception_date） |
| B1 硬边界 | 8 个指标 | performance, cost | 自动（布尔判断） |
| B2 逻辑约束 | 8 条约束 | 全部 | 自动（数学验证） |
| B3 漂移检测 | 5 个指标 | 全部 | 半自动（需同类基准） |
| C1 同源一致性 | 5 个交叉对 | prospectus/cost/wealth/portfolio | 自动（字段比对） |
| C2 衍生可复现 | 4 项验算 | performance_analyst | 自动（重新计算） |
| C3 跨维度逻辑 | 6 个检测对 | 全部 | 半自动（需定性理解） |
