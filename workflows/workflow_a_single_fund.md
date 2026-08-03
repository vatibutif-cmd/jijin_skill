# Workflow A: 单基金深度分析 — 执行编排规范

> **适用范围**: Claude 单对话环境（顺序执行，不能真并行）
> **版本**: v2.0 | **更新**: 2026-07-26

---

## 一、执行顺序与数据依赖关系

5 个基础 Agent 按依赖拓扑排序，分 3 个阶段顺序执行。每个阶段内部虽有逻辑并行（同一轮对话中连续调用），但严格按数据就绪状态串行。

```
阶段0: 数据就绪检查
  └─ 确认 famas-data MCP Server 可用，不可用则降级为 WebSearch 模式

阶段1: 基础信息提取（无上游依赖）
  └─ Agent 1: prospectus_analyzer
       └─ 输出: 基金名称、类型、经理姓名、费率、基准、规模、特殊条款

阶段2: 并行分析层（依赖阶段1的经理姓名，内部无互依）
  ├─ Agent 2: performance_analyst    （不依赖他人，独立净值归因）
  ├─ Agent 3: cost_analyzer          （不依赖他人，独立费率穿透）
  └─ Agent 4: manager_profiler       （依赖 prospectus_analyzer 输出的经理姓名）
       └─ 从阶段1输出的 JSON 中提取 manager_name，再调 MCP 工具

阶段3: 宏观适配层（依赖阶段1的策略特征 + 阶段2的业绩/持仓/成本）
  └─ Agent 5: macro_strategist
       └─ 输入: prospectus_analyzer.投资范围/基准 + performance_analyst.风格定位

阶段4: 综合评级（消费全部上游输出）
  └─ Agent 6: wealth_advisor
       └─ 输入: 阶段1-3全部5个Agent的JSON，不允许自行补充数据
```

### 依赖关系图

```
prospectus_analyzer ─────────────────────────────────────────────┐
       │                                                          │
       ├── manager_name ──→  manager_profiler ──────────────────┐ │
       │                                                         │ │
       ├── fund_type ──→ macro_strategist ←── style_tilt ───────┼─┤
       │       ↑              ↑              (from performance) │ │
       │       │              │                                  │ │
       └───────┼──────────────┼──────────────────────────────────┼─┘
               │              │                                  │
               ▼              │                                  │
         performance_analyst ─┘                                  │
         cost_analyzer                                           │
               │              │                                  │
               └──────────────┼──────────────────────────────────┘
                              │
                              ▼
                       wealth_advisor
```

### 精确执行脚本

```
[Step 0] 确认 MCP 状态 → famas_health()
            ↓ 不可用 → 全链路降级为 WebSearch + 标注"精度有限"

[Step 1] prospectus_analyzer
  ├─ 调 MCP: fund_basic_info(fund_code)
  ├─ 调 MCP: fund_announcements(fund_code, days=365, max_results=5)
  ├─ 整理输出 JSON₁ → 缓存到上下文
  └─ 提取: fund_name, fund_type, manager_name, benchmark_raw,
            stock_position_range, fee_raw, scale_raw, special_clauses

[Step 2a] performance_analyst
  ├─ 调 MCP: fund_nav_history(fund_code, days=756)    ← 近3年
  ├─ 调 MCP: fund_holdings(fund_code, year=2026)
  ├─ 调 MCP: index_data(index_code="000300" or 从benchmark推导, ...)
  ├─ 自行计算: Sharpe, Calmar, HHI, 风格漂移
  └─ 输出 JSON₂ → 缓存到上下文

[Step 2b] cost_analyzer
  ├─ 调 MCP: fund_basic_info(fund_code)    ← 可复用 Step 1 缓存
  ├─ 调 MCP: fund_nav_history(fund_code, days=252)  ← 估算换手率趋势
  ├─ 自行计算: TCR, 隐性成本, 规模惩罚评估
  └─ 输出 JSON₃ → 缓存到上下文

[Step 2c] manager_profiler
  ├─ 从 JSON₁ 提取: manager_name
  ├─ 调 MCP: fund_manager_info(fund_code)
  ├─ 整理: 能力圈、稳定性、逆风表现
  └─ 输出 JSON₄ → 缓存到上下文

[Step 3] macro_strategist
  ├─ 从 JSON₁ 提取: fund_type, benchmark, investment_scope
  ├─ 从 JSON₂ 提取: style_tilt, top3_sectors
  ├─ 调 MCP: index_data(index_code="000300", ...)  ← 可复用 Step 2a
  ├─ 调 WebSearch: 最新利率/汇率/政策     ← MCP 不覆盖的宏观数据
  └─ 输出 JSON₅ → 缓存到上下文

[Step 4] wealth_advisor
  ├─ 收集: JSON₁ + JSON₂ + JSON₃ + JSON₄ + JSON₅
  ├─ 禁止额外工具调用 ← 铁律
  ├─ 按加权公式计算星级
  ├─ 生成时机矩阵
  ├─ 输出 JSON₆
  └─ 组装: Markdown 报告 ← 消费 JSON₆
```

---

## 二、中间结果的传递方式

### 传递格式约定

所有 Agent 输出均为合法 JSON 对象，后续 Agent 通过以下方式引用前序结果：

**方式一：显式字段提取（推荐）**

下游 Agent 在生成 prompt 时，从上游 JSON 中按路径提取所需字段，不拷贝整个对象避免 token 膨胀。

```
manager_profiler 从 JSON₁ 中提取:
  JSON₁.manager_name       → "刘格菘"
  JSON₁.fund_code          → "005911"

macro_strategist 从 JSON₁ + JSON₂ 中提取:
  JSON₁.fund_type          → "混合型-偏股"
  JSON₁.benchmark.primary  → "75%×沪深300+25%×中证全债"
  JSON₂.style_analysis.value_growth_tilt → "偏成长"
  JSON₂.sector_attribution.top3_sectors  → ["电力设备","电子","医药生物"]
```

**方式二：全量引用（仅 wealth_advisor）**

wealth_advisor 消费全部 5 个 JSON 的完整对象，但每个 JSON 在传入前已被压缩为关键字段摘要（由编排器完成，不是 wealth_advisor 自己能做的）。

### 上下文缓存策略

在同一轮 Claude 对话中，前序 Agent 的输出 JSON 保留在上下文 window 中，无需重复传递。操作序列为：

1. Agent N 输出 JSON 后，编排器将其存入对话上下文（Claude 自动记住）
2. Agent N+1 被执行时，编排器在给它的 System Prompt 中注入"前序输出摘要"段落
3. 该摘要仅包含 Agent N+1 确实需要的字段，避免上下文膨胀

示例——编排器给 manager_profiler 的 System Prompt 注入：

```markdown
## 前序Agent输出摘要

prospectus_analyzer (步骤1) 已确认:
- 基金代码: 005911
- 基金名称: 广发双擎升级混合
- 基金经理: 刘格菘
- 基金类型: 混合型-偏股（主动管理型 → 触发 manager_profiler）

请以上述经理姓名作为输入，执行基金经理画像分析。
```

---

## 三、冲突检测规则

### 3.1 可检测的冲突类型

| 冲突类型 | 检测条件 | 冲突信号 | 处理方式 |
|----------|----------|----------|----------|
| **业绩-规模冲突** | Alpha 高 + 规模 > 80 亿 | 好业绩吸引资金涌入 → 策略容量压力 | wealth_advisor 的 risk_control_score 扣 0.5 分；在时机矩阵中提示"规模增长可能侵蚀超额收益" |
| **业绩-风格冲突** | Alpha 高 + 风格漂移 > 0.5 | 超额收益可能来自风格漂移而非选股能力 | wealth_advisor 的 performance_score 扣 0.3 分；标注"超额收益部分来源于风格暴露，非纯 Alpha" |
| **成本-业绩冲突** | TCR 高 + 长期 Alpha 低 | 高成本在侵蚀本已薄的超额收益 | cost_score 降至 2.0 以下；wealth_advisor 综合星级上限不超过 3 星 |
| **经理-业绩冲突** | 经理任职 < 1 年 + Alpha 高 | 超额收益样本不足，不可持续风险高 | manager_score 上限 3.0；标注"经理任职期过短，历史业绩参考价值有限" |
| **宏观-持仓冲突** | 宏观逆风 + 持仓极度集中 | 逆风环境下集中持仓放大下行风险 | risk_control_score 扣 0.5 分；在 key_risks 中补充"当前宏观环境对该基金核心持仓构成逆风" |
| **规模-经理冲突** | 经理总规模 > 200 亿 + 投资风格为集中型 | 规模膨胀与集中投资风格不兼容 | manager_score 扣 0.3 分；标注"经理当前管理总规模可能超出其集中型投资策略的舒适区间" |

### 3.2 冲突升级机制

如果同一只基金触发了 2 个及以上冲突信号：

1. wealth_advisor 必须在其 `rating_rationale` 中显式列出所有冲突信号
2. 综合星级下调 0.5-1 星（从按公式计算的结果下调）
3. `key_risks` 数组中加入一个 `severity: "高"` 的条目，汇总所有冲突

### 3.3 冲突检测不作为阻碍

注意：检测到冲突 **不意味着** 工作流中断。wealth_advisor 仍需完成评级和报告生成。冲突信号仅影响分数和风险提示。

---

## 四、超时与失败降级

### 4.1 MCP 工具调用失败的处理

| 失败场景 | 降级策略 | 对下游的影响 |
|----------|----------|-------------|
| `fund_basic_info` 失败 | ① 用 WebSearch 搜索天天基金页面提取字段 ② 标注"数据来源：公开网页搜索，精度有限" ③ fund_name 无法获取则用 fund_code 代替 | 所有下游 Agent 缺失 fund_type、manager_name——触发 manager_profiler 跳过、wealth_advisor 权重调整 |
| `fund_nav_history` 失败 | ① 尝试用更小的 days 参数重试（252→90→30）② 仍失败则跳过 performance_analyst 的量化指标，仅保留持仓分析 ③ 标注"净值数据不可用，业绩指标缺失" | wealth_advisor 的 performance_score 和 risk_control_score 设为 null，综合星级基于剩余维度计算 |
| `fund_holdings` 失败 | ① 尝试不同 year 参数重试 ② 仍失败则跳过行业归因和持仓分析 ③ 标注"持仓数据不可用" | sector_screener 和 fund_comparator 如在后续工作流中调用，同样受影响 |
| `fund_manager_info` 失败 | ① 从 fund_basic_info 中提取 manager_name 做 stub 输出 ② 标注"仅含基本信息，详细履历不可用" | wealth_advisor 的 manager_score 上限降至 3.0 |
| `index_data` 失败（A股指数） | ① 切换为 `index_zh_a_hist` 重试 ② 仍失败则用 WebSearch 获取近 1 年指数近似数据 ③ 标注"基准数据精度有限" | performance_analyst 缺失 Alpha 和超额收益计算 |
| `fund_announcements` 失败 | ① 降级为 WebSearch 搜索"基金代码+公告"② 仅标记触发词匹配的标题 ③ 标注"公告数据来自搜索引擎" | watchtower 和 prospectus_analyzer 的特殊条款区受影响 |

### 4.2 降级模式下的 wealth_advisor 处理

wealth_advisor 在被传入缺失维度的数据时：

1. 对缺失维度在 `dimension_scores` 中填 **null**
2. 在 `missing_data` 数组中声明"由于数据不可用，XX维度未参与评级"
3. 综合星级基于可用维度加权平均计算
4. `rating_rationale` 前加一行 **"[降级模式] 部分数据源不可用，本评级基于有限信息生成，置信度降低"**

### 4.3 降级模式下的 Token 控制

当检测到 3 个及以上 MCP 工具调用失败时，编排器自动：
1. 跳过 manager_profiler（非核心路径）
2. 跳过 macro_strategist（宏观数据由手动 WebSearch 替代）
3. 保留 prospectus_analyzer + performance_analyst 最简路径
4. 输出精简报告（压缩至原来 40% 的篇幅）

---

## 五、wealth_advisor 整合规则与星级加权公式

### 5.1 输入校验

wealth_advisor 收到 5 个 JSON 后，必须先执行输入完整性检查：

```
IF JSON₁.fund_code ≠ JSON₂.fund_code THEN 报错"基金代码不一致"
IF JSON₁ 缺失 manager_name 且 JSON₄ 非空 THEN 报错"经理信息冲突"
IF 任一 JSON 的 missing_data 数组长度 > 3 THEN 标记为"部分数据缺失"
```

### 5.2 五维评分映射

wealth_advisor 从上游 5 个 JSON 中按如下规则为每个维度打分（1.0-5.0 分，步长 0.5）：

| 维度 | 数据来源 | 打分逻辑 |
|------|----------|----------|
| **performance_score** | JSON₂ | Alpha 映射: `>10%→5.0`, `5-10%→4.0`, `0-5%→3.0`, `<0%→2.0`；波动率惩罚: `>30%→扣1.0`；Sharpe 修正: `<0.3→扣0.5`, `>1.0→加0.5`。最终 clamp 到 [1.0, 5.0] |
| **cost_score** | JSON₃ | TCR 中位数对比: `低于中位数→4.0-5.0`, `处于中位数→3.0`, `高于中位数→2.0`；规模惩罚: `>80亿且Alpha<3%→扣1.0`；QDII附加: `有QDII额外费→扣0.5`。最终 clamp 到 [1.0, 5.0] |
| **manager_score** | JSON₄ | 任职年限: `>5年→4.0`, `2-5年→3.0`, `<2年→2.0`；逆风表现修正: `排名前25%→加1.0`, `后50%→扣1.0`；跳槽惩罚: `近3年有跳槽→扣0.5`；共管惩罚: `共管比例>50%→扣0.5`。最终 clamp 到 [1.0, 5.0] |
| **macro_fit_score** | JSON₅ | fit_score 直接映射: `80-100→4.5`, `60-80→3.5`, `40-60→2.5`, `0-40→1.5`；顺风因子 ≥2 则加 0.5；逆风因子 ≥3 则扣 0.5。最终 clamp 到 [1.0, 5.0] |
| **risk_control_score** | JSON₂ | 最大回撤映射: `< -15%→4.0`, `-15%~-25%→3.0`, `-25%~-35%→2.0`, `>-35%→1.0`；修复天数修正: `< 90 天→加 0.5`, `> 270 天→扣 0.5`；风格漂移惩罚: `> 0.5→扣 0.5`。最终 clamp 到 [1.0, 5.0] |

### 5.3 综合星级加权公式

```
star_raw = Σ( score_i × weight_i ) / Σ(weight_i)

其中:
  performance_score   × 0.25
  cost_score          × 0.15
  manager_score       × 0.20
  macro_fit_score     × 0.15
  risk_control_score  × 0.25

star_rounded = round(star_raw)  → 映射到 1-5 星
```

**权重设计理由**：
- performance(0.25) + risk_control(0.25) 占 50%——对投资者最关键的"赚钱能力 + 亏钱底线"
- manager(0.20) 次之——主动基金的核心驱动力是经理质量
- cost(0.15) + macro(0.15) 各占 15%——辅助判断，非决定性因子

**边界情况**：
- 如果某个维度为 null（降级模式），该维度不参与加权，其余维度按原比例缩放
- 权重缩放公式: `weight_new_i = weight_i / Σ(有效维度权重)`
- 例如 performance_score 缺失: `cost 0.15/0.75=0.20, manager 0.20/0.75=0.267, macro 0.15/0.75=0.20, risk 0.25/0.75=0.333`
- 如果 3 个及以上维度缺失 → star_raw 不可计算 → star_rating 填 null，不输出星级

**冲突调权**：
- 每触发一个冲突信号（见第三章），star_raw 扣 0.25
- star_rounded 最低为 1（不会出现 0 星）

### 5.4 评级措辞映射

| 星级 | 含义 | 评级措辞 |
|------|------|----------|
| ★★★★★ | 在各维度综合表现优异 | "该基金在当前市场环境下，对XX类型投资者具备较高适配度" |
| ★★★★☆ | 大部分维度表现良好，个别维度有瑕疵 | "该基金在多维度表现稳健，对XX类型投资者具备适配度，但需关注以下方面" |
| ★★★☆☆ | 各方面均衡，无明显短板也无突出亮点 | "该基金表现中规中矩，对特定类型投资者存在适配可能，但并非突出选择" |
| ★★☆☆☆ | 存在明显短板或风险 | "该基金在部分维度存在显著不足，适配范围较窄" |
| ★☆☆☆☆ | 多维度存在严重问题 | "该基金在核心维度表现较弱，适配度有限" |

---

## 六、最终输出的组装

### 6.1 输出优先级

wealth_advisor 完成 JSON₆ 生成后，编排器按以下优先级组装最终输出：

```
1. [必选] 意图标签: [INTENT: SINGLE_FUND | PARAMS: {fund_code}]
2. [必选] Markdown 可读报告（从 JSON₆ 渲染）
3. [必选] 标准化免责声明
4. [可选] 结构化 JSON₆（仅当用户明确要求"输出JSON"或调试模式时追加）
```

### 6.2 Markdown 报告渲染

从 JSON₆ 到 Markdown 的映射表（与 `templates/comprehensive_rating_card.md` 对齐）：

```markdown
[INTENT: SINGLE_FUND | PARAMS: {fund_code}]

## 基金综合分析报告 — {fund_code}

### 一、基础信息
- 基金类型: {JSON₁.fund_type}
- 业绩基准: {JSON₁.benchmark.primary}
- 成立日期: {JSON₁.inception_date}
- 最新规模: {JSON₁.current_scale_billion}亿元
- 基金经理: {JSON₁.manager_name}（任职{JSON₄.current_fund_tenure_days}天）

### 二、综合评级: {star_rendered}（{star_rating}/5）

| 维度 | 得分 | 说明 |
|------|------|------|
| 业绩表现 | {JSON₆.dimension_scores.performance_score} | {JSON₆.dimension_explanations.performance_explanation} |
| 成本控制 | {JSON₆.dimension_scores.cost_score} | {JSON₆.dimension_explanations.cost_explanation} |
| 经理质量 | {JSON₆.dimension_scores.manager_score} | {JSON₆.dimension_explanations.manager_explanation} |
| 宏观适配 | {JSON₆.dimension_scores.macro_fit_score} | {JSON₆.dimension_explanations.macro_fit_explanation} |
| 风控水平 | {JSON₆.dimension_scores.risk_control_score} | {JSON₆.dimension_explanations.risk_control_explanation} |

**评级依据**: {JSON₆.comprehensive_rating.rating_rationale}

### 三、时机矩阵

> {JSON₆.timing_matrix.valuation_percentile}
>
> **长期配置投资者**: {JSON₆.timing_matrix.long_term_investor_guidance}
>
> **趋势交易投资者**: {JSON₆.timing_matrix.trend_trader_guidance}
>
> **综合判断**: {JSON₆.timing_matrix.entry_timing_assessment}

### 四、风险画像

- **风险等级**: {JSON₆.risk_profile.risk_level}
- **近3年最大回撤**: {JSON₆.risk_profile.max_drawdown_3y_pct}%
- **夏普比率**: {JSON₆.risk_profile.sharpe_ratio}
- **风格漂移**: {JSON₆.risk_profile.style_drift_assessment}

### 五、适配投资者

- **适合**: {逗号分隔的 suitable_for}
- **不适合**: {逗号分隔的 unsuitable_for}
- **建议投资期限**: {JSON₆.investor_fit.recommended_horizon}

### 六、核心风险提示

{遍历 JSON₆.key_risks，按 severity 降序排列}
{每条渲染为: **{severity}风险 - {risk_description}**: {monitoring_points}}

{如果触发冲突信号，在此追加 "⚠️ 冲突预警" 段落}

{如果处于降级模式，在此追加 "⚠️ 数据降级说明" 段落}

---
*免责声明：本报告仅作信息整理与适配度分析，不构成投资建议。基金过往业绩不预示未来表现。市场有风险，投资需谨慎。*

*数据来源: 天天基金/东方财富/AKShare，截至{analysis_date}*
```

### 6.3 星级渲染

星级不使用 emoji，用文本表示：

```
★★★★★ (5/5)  →  综合表现优异
★★★★☆ (4/5)  →  大部分维度表现良好
★★★☆☆ (3/5)  →  各方面均衡
★★☆☆☆ (2/5)  →  存在明显短板
★☆☆☆☆ (1/5)  →  多维度存在严重问题
```

### 6.4 元数据注释

在报告末尾（免责声明之前）、JSON₆ 渲染完成后，若以下任一条件为真则追加：

**冲突信号注释**：
```markdown
---
⚠️ **冲突预警**: 本次分析检测到以下数据冲突：
- {冲突类型}: {冲突描述}
上述冲突已在综合评级中体现（星级下调X星）。建议重点关注。
```

**数据降级注释**：
```markdown
---
⚠️ **数据降级说明**: 以下数据源在本轮分析中不可用：
- {数据源名称}: {失败原因}。已使用{替代方案}，相关结论置信度降低。
```

---

## 附录A: 快速参考——6个阶段调用的工具清单

| 阶段 | Agent | 调用的 MCP 工具 | 无 MCP 时的降级数据源 |
|------|-------|----------------|---------------------|
| 1 | prospectus_analyzer | `fund_basic_info` + `fund_announcements` | WebSearch 天天基金页面 |
| 2a | performance_analyst | `fund_nav_history` + `fund_holdings` + `index_data` | WebSearch 净值/持仓数据 |
| 2b | cost_analyzer | `fund_basic_info`(缓存) + `fund_nav_history` | WebSearch 费率信息 |
| 2c | manager_profiler | `fund_manager_info` | 从 `fund_basic_info` 提取经理名做 stub |
| 3 | macro_strategist | `index_data`(缓存) + WebSearch | 央行官网/东方财富宏观数据 |
| 4 | wealth_advisor | **禁止调用任何工具** | 仅消费上游 JSON |

## 附录B: 完整执行示例的 Token 估算

以广发双擎升级混合(005911)为例：

| 步骤 | 操作 | 估算 Token |
|------|------|-----------|
| Step 1 | prospectus_analyzer (2次MCP调用+解析) | ~4,000 |
| Step 2a | performance_analyst (3次MCP调用+6个指标计算) | ~5,500 |
| Step 2b | cost_analyzer (1次MCP调用+TCR计算) | ~3,500 |
| Step 2c | manager_profiler (1次MCP调用+画像整理) | ~3,000 |
| Step 3 | macro_strategist (1次MCP+1次WebSearch+评分) | ~2,500 |
| Step 4 | wealth_advisor (0次MCP, 纯整合+评级+报告渲染) | ~5,000 |
| **合计** | | **~23,500 tokens** |

> 这个数字在 Claude 上下文中完全可行（假设上下文窗口 200K），单轮对话即可完成。
