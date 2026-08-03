# FAMAS-Skill 变更日志

## v2.2.0 (2026-08-04) — A股数据层集成

### 新增

- **A股数据层集成（a-stock-data V3.6.0 · Apache-2.0）**：从 [simonlin1212/a-stock-data](https://github.com/simonlin1212/a-stock-data) 深度封装进 MCP Server
  - `mcp_server/a_stock_data/` 新模块，提取与基金分析最相关的纯 HTTP 零鉴权函数
  - **MCP 新增 4 个工具**（总计 14 工具）：
    - `a_stock_quote_tool` — 批量A股/指数/ETF实时行情（腾讯财经，不封IP）
    - `a_stock_board_fund_flow` — 板块资金流向（行业/概念/地域 × 今日/5日/10日）
    - `a_stock_industry_rank` — 全行业涨跌幅排名（含领涨股/涨跌家数）
    - `a_stock_stock_news` — 个股新闻（辅助持仓穿透追踪重仓股）
  - **完整技能保留**：`.claude/skills/a-stock-data/SKILL.md`（47 端点全量），文档存于 `docs/a-stock-data/`
- **单元测试**：`mcp_server/test_a_stock_data.py`（6/6 通过，含离线校验 + 网络冒烟）
- **pyproject 可选依赖**：`[project.optional-dependencies] a-stock`（mootdx + stockstats，用于完整 A股能力）

### 变更

- `mcp_server/server.py` 版本升至 2.2.0，`famas_health` 工具列表更新为 14 工具
- `mcp_server/pyproject.toml` 版本升至 2.2.0

### 集成价值（对基金分析）

| A股工具 | 对应基金分析场景 |
|---------|-----------------|
| a_stock_quote_tool | 持仓重仓股实时估值、指数行情锚定 |
| a_stock_board_fund_flow | 行业资金流向 → sector_screener 行业筛选 |
| a_stock_industry_rank | 行业轮动 → macro_strategist 风格判断 |
| a_stock_stock_news | 重仓股异动追踪 → watchtower 预警补充 |

---

## v2.1.0-conv (2026-08-04)

### 合规收敛（最高优先级）

- **系统 B 全面收敛到合规框架**: `famas-score-fund` SKILL、`docs/fund-scoring-engine.md`、`agents/personal_investment_advisor.md`、`scripts/score_with_emotion.py` 中的交易指令（满仓/加仓/减仓/清仓/抄底/逃顶等）全部改为**适配度等级 + 配置方向**输出，与 `knowledge/CLAUDE.md` 和 Router 合规红线保持一致
- 明确"分数→适配度等级"映射（★★★★★ 高适配 ~ ☆☆☆☆☆ 极低适配），不再输出"分数→操作指令"

### 修复

- **Agent frontmatter**: 全部 11 个 `agents/*.md` 补齐 frontmatter（name/description/tools），使其可被 Agent 工具真正加载为子 Agent
- **MCP 代码缺陷**:
  - `fund_manager_info` 从业时间单位修复（`累计从业时间` 单位为年，现拆分为 `experience_years` + `tenure_days=年×365`）
  - `fund_holdings` 硬编码年份 `"2026"` 改为动态 `datetime.now().year`
  - `fund_holdings` 行业汇总移除列表推导副作用；HHI 去掉 `*10` 缩放，与文档量纲一致
  - `fund_manager_info` 的 `manager_name` 模式从 `NOT_IMPLEMENTED` 实现为真实姓名检索（`fetch_manager_by_name`）
- **pyproject 依赖补全**: 声明 `fastmcp`、`requests`，版本升至 2.1.0，描述更新为 10 工具
- **文档口径统一**: `docs/mcp-data-layer-design.md` 从"6 工具"改为"10 工具"，移除已废弃的 `tools/` 目录结构；`README.md` 项目结构同步（11 Agent、新增 skills/scripts 目录）
- **配置同步**: `mcp_server/claude_desktop_config.json` 从 `python3 server.py` 改为 `uv run famas-data-server`（与设计文档一致）

### 其他

- 保留 `famas-score-fund` 的五维评分、环境自适应权重、恐贪/RSI 情绪校准等量化方法论，仅修改输出语义

---

## v2.0 (2026-07-26)

### 新增

- **MCP 数据工具层**: 基于 AKShare 实现 `famas-data` MCP Server，提供 6 个数据工具覆盖全部 10 个 Agent 的数据需求
- **Router 主控 Prompt**: 6 种意图识别（SINGLE_FUND/SECTOR_SCREEN/PORTFOLIO/COMPARE/MONITOR/CHAT）+ 合规红线 + 多意图处理规则
- **Workflow A 完整编排规范**: 顺序执行、依赖关系、中间结果传递、冲突检测 6 规则、超时/失败降级 4 级、星级加权公式
- **数据校验规则集**: 4 层校验（幻觉检测/数值边界/交叉验证/失败处理）共 39 个检测点
- **Knowledge 文件组织方案**: 三层架构（常驻层 13,000 字/按需层按 Workflow 触发/不放入层以链接替代）
- **10 个 Agent Prompt 输出格式约束**: 每个 Agent 末尾追加 `<output_format>` 标签，含完整 JSON Schema + missing_data 机制
- **3 个关键 Agent Few-shot 示例**: performance_analyst, cost_analyzer, wealth_advisor 各含完整数据流示例
- **MCP 数据层设计文档**: 6 个工具的完整 API 定义 + Agent→工具映射表 + MCP Server 注册配置

### 变更

- **Agent Prompt 优化**: 全部 10 个 Agent 统一追加 `quality_flags` 字段和 `missing_data` 数组
- **SKILL.md 刷新**: 4 个 Skill 的 frontmatter description 更新为 v2.0，明确数据源和 Agent 调用链
- **MCP Server 架构精简**: 移除独立的 `tools/` 目录，6 个工具逻辑全部 inline 进 `server.py`（消除 null-byte 文件损坏问题）
- **三平台 Skill 文件同步**: `.claude/` 和 `.agents/` 下的 SKILL.md 统一以 `.claude/` 为权威源

### 文档

- `docs/FAMAS-Router-Prompt.md` — 完整版 Router（7,335 字）
- `docs/data-validation-rules.md` — 完整版校验规则（17,425 字）
- `docs/mcp-data-layer-design.md` — MCP 设计文档（19,356 字）
- `docs/knowledge-file-organization.md` — Knowledge 组织方案
- `docs/CHANGELOG.md` — 本文件

---

## v1.0 (2026-06-21)

- 初始版本：10 个 Agent 定义 + 4 条 Workflow 定义 + 4 份输出模板
- 三平台 Skill 适配：Claude Code (`.claude/`)、OpenAI Codex (`.agents/`)、TRAE (`.trae/`)
- 纯 Prompt 工程，无数据层实现
