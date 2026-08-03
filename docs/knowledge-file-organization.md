# FAMAS Knowledge 文件组织方案

> **目标**: Claude Project Knowledge 三层架构 → 常驻层 ≤ 15,000 字 / 按需层精确匹配 Workflow / 不放入层以链接替代
> **版本**: v1.0 | **更新**: 2026-07-26

---

## 总览

```
FAMAS-Skill/                          → 项目仓库（全量，不全部进 Knowledge）
│
├── knowledge/                         → Claude Project Knowledge 根目录
│   ├── _layer1_always/               → 每次对话自动加载（≤15,000 字）
│   │   ├── ROUTER.md                 → 路由+合规（核心，精简到 ~3,000 字）
│   │   ├── COMPLIANCE.md            → 合规红线+免责声明（~500 字）
│   │   ├── AGENT-CATALOG.md         → 10 Agent 速查表（~1,500 字）
│   │   ├── WORKFLOW-MAP.md          → 4 Workflow 执行顺序+Agent 映射（~1,500 字）
│   │   ├── DATA-TOOLS.md            → 6 MCP 工具速查（~2,000 字）
│   │   ├── VALIDATION-CHECKLIST.md  → 校验规则精简版（~4,000 字）
│   │   └── OUTPUT-FORMAT.md         → 全局输出规范（~500 字）
│   │
│   ├── _layer2_on_demand/           → 按 Workflow 触发时加载
│   │   ├── workflow_a/              → 单基金分析
│   │   ├── workflow_b/              → 行业筛选
│   │   ├── workflow_c/              → 组合诊断
│   │   └── workflow_d/              → 监控预警
│   │
│   └── _layer3_reference/           → 不放入 Knowledge，仅链接
│       └── README.md                → 项目文档链接清单
│
└── docs/                             → 设计文档（不在 Knowledge 路径内）
    ├── FAMAS-Router-Prompt.md        → 完整版 Router（7,335 字）
    ├── data-validation-rules.md      → 完整版校验规则（11,037 字）
    └── mcp-data-layer-design.md      → MCP 设计文档（13,678 字）
```

---

## Layer 1: 常驻层（~13,000 字，≤15,000 字硬上限）

### 1. ROUTER.md（~3,000 字）

**放入理由**: 每条消息都需意图识别 → 必须常驻。  
**精简策略**: 从完整版 7,335 字砍到 ~3,000 字。

| 砍掉的内容 | 原因 | 替代方案 |
|-----------|------|----------|
| 6 种意图的"触发条件"详细自然语言描述 | Router 已经有能力从简短规则推断意图 | 每种意图保留 1-2 句关键词触发 |
| 每种意图的"调用 Agent"列表 | 移到 WORKFLOW-MAP.md（已在常驻层） | 交叉引用 `[→ WORKFLOW-MAP.md]` |
| "输出参考模板"链接 | 模板不在 Knowledge 中 | 保留模板名但去除详细模板内容 |
| Agent 分工速查表 | 移到 AGENT-CATALOG.md | 交叉引用 |
| MCP 工具映射表 | 移到 DATA-TOOLS.md | 交叉引用 |
| 回复结构规范的详细示例 | 已足够简洁 | 无替代 |

**保留内容**（必须）:
```
- 你是谁（1 段）
- 合规红线 <COMPLIANCE_RULES> 完整 XML（但精简措辞）
- 6 种意图的简短定义 + 触发关键词（每种 3-5 行）
- 多意图处理规则（保留，这是核心逻辑）
- 模糊意图处理规则（保留，防止猜测）
- 意图标签格式 [INTENT: XXX | PARAMS: YYY]（保留）
- 标准免责声明模板（保留）
```

---

### 2. COMPLIANCE.md（~500 字）

**放入理由**: 合规红线最高优先级 → 每次对话必须生效。  
**精简策略**: 从 Router 中提取 `<COMPLIANCE_RULES>` 块独立成文件，去除所有解释性文字。

**内容**（极简）:
```
<COMPLIANCE_RULES priority="HIGHEST">
1. 禁止交易信号: 不输出 买入/卖出/加仓/减仓/清仓/抄底/追涨/止盈/止损
2. 禁止点位预测: 不预测具体点位和涨跌幅，可用分位/区间描述
3. 强制免责: 每次分析/评级/筛选/诊断结尾追加标准免责声明
4. 数据溯源: 所有事实数据标来源，无法溯源标"暂无公开数据"
5. 事实与观点分离: L2 Agent 仅事实，L4 Agent 可综合观点
</COMPLIANCE_RULES>

<DISCLAIMER>
免责声明：本报告仅作信息整理与适配度分析，不构成投资建议。
基金过往业绩不预示未来表现。市场有风险，投资需谨慎。
</DISCLAIMER>
```

---

### 3. AGENT-CATALOG.md（~1,500 字）

**放入理由**: 编排器需要知道"有哪些 Agent、各自能做什么"，否则无法路由。  
**精简策略**: 10 个 Agent × 每个 ~100 字 = 1,000 字 + 速查映射表 500 字。

**内容**（极简）:
```
## 10 Agent 速查

| # | Agent | 层级 | 职责（一行） | 所属 Workflow |
|---|-------|------|-------------|-------------|
| 1 | prospectus_analyzer | L2 | 文档解析：投资范围/费率/基准/持有人 | A |
| 2 | performance_analyst | L2 | 业绩归因：收益/回撤/风格/行业 | A |
| 3 | cost_analyzer       | L2 | 费率穿透：显性+隐性+TCR+规模惩罚 | A, C |
| 4 | manager_profiler    | L2 | 经理画像：能力圈/稳定性/逆风表现 | A |
| 5 | macro_strategist    | L1 | 宏观适配：利率/汇率/风格/政策 | A |
| 6 | wealth_advisor      | L4 | 综合评级：星级+时机矩阵+适配画像 | A |
| 7 | sector_screener     | L3 | 全市场筛选：按行业/主题/风格筛选 | B |
| 8 | fund_comparator     | L3 | 横向PK：多基金对比+淘汰建议 | B, C |
| 9 | portfolio_doctor    | L4 | 组合诊断：集中度/相关性/再平衡 | C |
|10 | watchtower          | L0 | 持续监控：6维预警 | D |

## 每个 Agent 的核心输出（仅字段名，无嵌套详细）
[表格式一行列出 top-level JSON 字段]
```

---

### 4. WORKFLOW-MAP.md（~1,500 字）

**放入理由**: 意图识别后需要"这条 Workflow 跑哪些 Agent、什么顺序"。  
**精简策略**: 4 条 Workflow × 每条 ~350 字 = 1,400 字。

**内容**:
```
## Workflow A: 单基金分析
Intent: SINGLE_FUND
执行顺序: prospectus → (performance || cost || manager) → macro → wealth
依赖关系: manager_profiler 依赖 prospectus 输出的经理姓名
Token 预算: ~23,500
调用的 Agent Prompt: 从 _layer2_on_demand/workflow_a/ 加载
→ 详细编排: workflows/workflow_a_single_fund.md

## Workflow B: 行业筛选
Intent: SECTOR_SCREEN
执行顺序: sector_screener → fund_comparator
→ 详细编排: workflows/workflow_b_sector_screen.md

## Workflow C: 组合诊断
Intent: PORTFOLIO
执行顺序: portfolio_doctor → (cost_analyzer || fund_comparator)
→ 详细编排: workflows/workflow_c_portfolio.md

## Workflow D: 监控预警
Intent: MONITOR
执行顺序: watchtower（首轮巡检）→ 建议配置 scheduled task
→ 详细编排: workflows/workflow_d_monitoring.md
```

---

### 5. DATA-TOOLS.md（~2,000 字）

**放入理由**: 编排器需要知道"有哪些数据工具、怎么调用"，否则会乱调或漏调。  
**精简策略**: 6 个工具 × 每个 ~300 字 = 1,800 字。

**内容**（极简）:
```
## 6 MCP 工具速查（famas-data MCP Server）

### fund_basic_info(fund_code?, keyword?, top_n?)
- fund_code模式: 返回 基金名称/类型/规模/经理/费率/基准/成立日期
- keyword模式: 全市场搜索匹配基金列表
- 调用者: prospectus_analyzer, cost_analyzer, sector_screener, portfolio_doctor

### fund_nav_history(fund_code, days=252)
- 返回 每日单位净值/日增长率 + 基础统计(max 1095天)
- 调用者: performance_analyst, cost_analyzer(辅助)

### fund_holdings(fund_code, year?, quarter?)
- 返回 前10大重仓股(代码/名称/行业/权重) + 行业分布 + HHI
- 调用者: performance_analyst, sector_screener, fund_comparator, portfolio_doctor

### fund_manager_info(fund_code?, manager_name?)
- 返回 经理姓名/公司/任职天数/总规模/最佳回报
- 调用者: manager_profiler, watchtower

### index_data(index_code, start_date?, end_date?)
- index_code: 000300(沪深300) | 000905(中证500) | 399006(创业板指) | HSTECH(恒生科技)
- 返回 日期/收盘价/涨跌幅 + 区间收益/最大回撤
- 调用者: performance_analyst, macro_strategist

### fund_announcements(fund_code, keyword?, days=90, max_results=15)
- keyword: 经理变更|清盘|大额赎回|费率|分红|限购|终止
- 返回 公告标题/日期/预警标记
- 调用者: prospectus_analyzer, watchtower
```

---

### 6. VALIDATION-CHECKLIST.md（~4,000 字）

**放入理由**: 输出质量依赖校验 → 每次生成 JSON 后都需要检查。  
**精简策略**: 从完整版 11,037 字压缩为"执行检查清单"格式，去除详细解释和示例。

| 砍掉的内容 | 原因 | 替代方案 |
|-----------|------|----------|
| H1-H3 的详细检测代码 | 编排器有校验逻辑，不需要伪代码 | 保留规则描述 |
| B1 完整映射表 | 保留关键指标但不列完整 path | 保留 4 个最关键的 |
| B2 全部 8 条约束 | 保留最常触发的 4 条 | 其余移到完整版 docs |
| C3 全部 6 个检测对 | 保留最致命的 3 个 | 其余按需查阅 |
| 全部示例 | 示例太长但不可压缩 | 移入完整版 |
| 附录 A/B | 编排器内建的校验逻辑 | 不需要在 Knowledge 中 |

**保留内容**（必须）:
```
- 4 层规则架构总览
- H1 数字溯源规则（精简版）
- H2 关键字段→必需工具映射表
- H3 时间轴逻辑（4 项检查）
- B1 4 个最关键指标的硬边界（Sharpe/回撤/费率/持仓和）
- B2 4 条逻辑约束
- C1 同源费率一致性（最重要的一条交叉验证）
- C2 衍生指标验算阈值
- Layer 4: quality_flags 格式 + overall_confidence 取值
- wealth_advisor 校验汇总规则
```

---

### 7. OUTPUT-FORMAT.md（~500 字）

**放入理由**: 所有 Agent 共享的输出约束 → 一次定义全局生效。  
**精简策略**: 从 10 个 Agent 各自的 `<output_format>` 中提取共性规则。

**内容**（极简）:
```
## 全局输出约束

<output_format>
所有 FAMAS Agent 的输出必须满足:

1. 最终回复必须是且仅是一个合法 JSON 对象
2. 绝对不要在 JSON 前后添加任何解释性文字或 markdown 包裹
3. 数据缺失时字段填 null，同时在 missing_data 数组中说明原因
4. 每个 JSON 必须包含 quality_flags 数组（可为空数组 []）

例外: wealth_advisor 的输出由编排器在生成 Markdown 报告前消费，
其 JSON 不作为最终用户可见输出。但 JSON 本身仍遵守上述格式约束。
</output_format>
```

---

## Layer 2: 按需层（按 Workflow 子目录组织）

### 触发机制

编排器识别到意图后，从对应子目录加载所有文件。不加载其他 Workflow 的文件。

```
[INTENT: SINGLE_FUND]
  → 加载 _layer2_on_demand/workflow_a/* 全部文件
  → 不加载 workflow_b/c/d

[INTENT: SECTOR_SCREEN]
  → 加载 _layer2_on_demand/workflow_b/*
  → 不加载其他

[INTENT: PORTFOLIO]
  → 加载 _layer2_on_demand/workflow_c/*

[INTENT: MONITOR]
  → 加载 _layer2_on_demand/workflow_d/*

[INTENT: CHAT]
  → 不加载任何 Layer 2 文件
```

### 每个 Workflow 子目录的文件清单

```
_layer2_on_demand/
│
├── workflow_a/                         → SINGLE_FUND
│   ├── prospectus_analyzer.md         → Agent prompt（含 few-shot + output_format）
│   ├── performance_analyst.md         → Agent prompt（含 few-shot + output_format）
│   ├── cost_analyzer.md               → Agent prompt（含 few-shot + output_format）
│   ├── manager_profiler.md            → Agent prompt
│   ├── macro_strategist.md            → Agent prompt
│   ├── wealth_advisor.md              → Agent prompt（含 few-shot）
│   ├── workflow_spec.md               → Workflow A 完整编排规范（来自 workflow_a_single_fund.md）
│   └── template.md                    → comprehensive_rating_card.md 报告模板
│   【总计 ~42,000 字，6 个 Agent + 编排规范 + 模板】
│
├── workflow_b/                         → SECTOR_SCREEN
│   ├── sector_screener.md             → Agent prompt
│   ├── fund_comparator.md             → Agent prompt
│   ├── workflow_spec.md               → Workflow B 编排规范
│   └── template.md                    → sector_screening_report.md
│   【总计 ~12,000 字，2 个 Agent + 编排规范 + 模板】
│
├── workflow_c/                         → PORTFOLIO
│   ├── portfolio_doctor.md            → Agent prompt
│   ├── cost_analyzer.md               → Agent prompt（与 workflow_a 共享，但独立文件）
│   ├── fund_comparator.md             → Agent prompt（与 workflow_b 共享）
│   ├── workflow_spec.md               → Workflow C 编排规范
│   └── template.md                    → portfolio_diagnosis_report.md
│   【总计 ~14,000 字，3 个 Agent + 编排规范 + 模板】
│
└── workflow_d/                         → MONITOR
    ├── watchtower.md                  → Agent prompt
    ├── workflow_spec.md               → Workflow D 编排规范
    └── template.md                    → monitoring_alert_report.md
    【总计 ~8,000 字，1 个 Agent + 编排规范 + 模板】
```

### 文件来源映射

Layer 2 文件不新建，而是从现有项目仓库中**按需复制**到 Claude Project Knowledge。维护时只维护项目仓库中的源文件，Knowledge 中的副本通过 Claude Project 的"Add files"功能手工同步。

| Knowledge 路径 | 源文件路径 | 备注 |
|---------------|-----------|------|
| `workflow_a/prospectus_analyzer.md` | `agents/prospectus_analyzer.md` | 直接复制 |
| `workflow_a/wealth_advisor.md` | `agents/wealth_advisor.md` | 直接复制 |
| `workflow_a/workflow_spec.md` | `workflows/workflow_a_single_fund.md` | 直接复制 |
| `workflow_a/template.md` | `templates/comprehensive_rating_card.md` | 直接复制 |
| ... | ... | ... |

### 共享 Agent 的处理

`cost_analyzer` 同时出现在 workflow_a 和 workflow_c 中。  
**策略**: 两个子目录各存一份独立副本。Claude Project Knowledge 不支持文件去重，且每份文件仅 ~5K 字，冗余成本可接受。维护时确保两份副本内容一致。

### 为什么 Agent Prompt 不全部放在常驻层

常驻层总容量 15,000 字，10 个 Agent Prompt 共 37,364 字 → 超出上限 2.5 倍。而且 80% 的对话只涉及 1-2 条 Workflow，加载全部 Agent 会稀释 Router 注意力并增加 token 开销。

---

## Layer 3: 不放入层

以下文件不放入 Claude Project Knowledge，原因和替代方案如下：

### 不放入清单

| 文件 | 字数 | 原因 | 替代方案 |
|------|------|------|----------|
| `README.md` | 15,433 | 项目总览，非运行时所需 | 常驻层 ROUTER.md 已包含"你是谁"段落 |
| `docs/FAMAS-Router-Prompt.md` | 7,335 | 完整版 Router | 常驻层 ROUTER.md 是精简版（~3,000 字），完整版仅在开发调试时参考 |
| `docs/data-validation-rules.md` | 11,037 | 完整版校验规则 | 常驻层 VALIDATION-CHECKLIST.md 是精简版（~4,000 字） |
| `docs/mcp-data-layer-design.md` | 13,678 | MCP 设计文档（实现层） | DATA-TOOLS.md 已有工具速查；实现细节在代码仓库中查阅 |
| `AGENTS.md` | 850 | Codex 项目级指令，Claude 中不需要 | 内容已在 COMPLIANCE.md 和 AGENT-CATALOG.md 中覆盖 |
| `.claude/`, `.agents/`, `.trae/`下的 SKILL.md | ~15,000 | 这些是 Skill 定义，不通过 Knowledge 加载 | Claude Skill 机制独立于 Knowledge，已在系统中注册 |
| `mcp_server/` 目录 | 代码文件 | Python 源代码 | 运行时通过 `famas-data` MCP Server 暴露，不需要作为文本加载 |
| 任一 Agent 的完整版 Prompt | ~3,000-7,000/个 | 仅在对应 Workflow 触发时需要 | 在 Layer 2 按需加载 |

### 替代方案设计

对于 Layer 3 中被排除的文档，编排器在需要时通过以下方式获取：

1. **Agent Prompt（非当前 Workflow）**: 不加载。编排器只加载当前触发的 Workflow 子目录中的 Agent。比如用户在单基金分析流程中突然问"这个基金的经理和 005827 的经理比谁好"，编排器判断这是新意图 COMPARE → 提示用户"需要切换到对比模式吗？"并加载 workflow_a 的精简版（去 macro 去 wealth）+ fund_comparator。

2. **完整版 Router**: 如果编排器在边缘 case 上路由不确定，按照 <AMBIGUITY_RULES> 追问用户，不需要参考完整版。

3. **完整版校验规则**: 校验失败 ≤ 2 个 ERROR 时，精简版足够。如果同一轮对话中 3+ 个 ERROR 触发降级模式，编排器在报告中注明"部分校验规则被简化"——不需要在运行时加载完整版。

---

## 字符数预算核对

### Layer 1（常驻层）

| 文件 | 预估字数 |
|------|----------|
| ROUTER.md | 3,000 |
| COMPLIANCE.md | 500 |
| AGENT-CATALOG.md | 1,500 |
| WORKFLOW-MAP.md | 1,500 |
| DATA-TOOLS.md | 2,000 |
| VALIDATION-CHECKLIST.md | 4,000 |
| OUTPUT-FORMAT.md | 500 |
| **合计** | **13,000** |

距 15,000 上限尚有 2,000 字缓冲空间，用于未来追加。

### Layer 2（按 Workflow，单次加载量）

| Workflow | Agent 文件 | +编排规范 | +模板 | ≈ 单次加载 |
|----------|-----------|----------|------|-----------|
| A (SINGLE_FUND) | 6 个 Agent × ~5K | ~13K | ~1K | ~44K |
| B (SECTOR_SCREEN) | 2 个 Agent × ~3K | ~2K | ~1K | ~9K |
| C (PORTFOLIO) | 3 个 Agent × ~4K | ~2K | ~1K | ~15K |
| D (MONITOR) | 1 个 Agent × ~3K | ~2K | ~1K | ~6K |

单次对话最大加载量（Workflow A）：Layer 1(13K) + Workflow A(44K) = **57K 字**，在 Claude 200K 上下文窗口中占比约 28%，留下 72% 给工具调用和用户交互。合理。

---

## 附录: 精简版文件编写参考

以下给出每个常驻层文件的"必须保留/可以砍掉"清单，指导实际编写：

### ROUTER.md 精简清单
- ✅ 保留: 你是谁(1段)、合规红线、6种意图+触发关键词、多意图规则、模糊意图规则、意图标签格式、免责声明模板
- ❌ 砍掉: 每种意图的调用Agent列表→交叉引用、输出参考模板链接→交叉引用、Agent分工速查表→交叉引用、MCP映射表→交叉引用、回复结构规范详细示例
- 📏 目标: 3,000 字（从 7,335 → 砍 59%）

### DATA-TOOLS.md 精简清单
- ✅ 保留: 每个工具的名称/参数/返回简述/调用者
- ❌ 砍掉: 详细的 JSON schema 示例、降级策略、缓存策略
- 📏 目标: 2,000 字

### VALIDATION-CHECKLIST.md 精简清单
- ✅ 保留: H1-H3规则描述(无示例)、B1-4个关键边界、B2-4条约束、C1费率一致性、C2验算阈值、Layer4处理规则
- ❌ 砍掉: 所有伪代码块、所有示例段落、B1完整映射表、B2/B3余下规则、C3余下检测对
- 📏 目标: 4,000 字（从 11,037 → 砍 64%）
