# FAMAS-Skill 项目彻底分析报告

> 分析日期: 2026-08-04 | 分析对象: `FAMAS-Skill` 全仓库
> 范围: README/AGENTS/Knowledge、11 个 Agent、6 个技能、MCP 服务端、8 个 Python 脚本、6 份设计文档、git 历史

---

## 一、项目定位（官方口径）

FAMAS（Fund Analysis Multi-Agent System）是面向个人投资者的基金投研决策支持系统，由 10 个专业 Agent 协作，覆盖"单基金深度分析 → 多基金对比筛选 → 组合持仓诊断 → 持续监控预警"全链路。

核心设计原则：
- 分工解耦：每 Agent 单一领域
- 数据驱动：所有结论可溯源
- 合规前置：禁止输出买卖信号
- 渐进可用：支持极简到完整多 Agent 部署

---

## 二、最严重发现：项目已分裂为两个合规立场相反的系统

深入分析后发现，仓库内实际存在**两套并行体系**，而非一套：

| | 系统 A（v2.0 研究诊断引擎） | 系统 B（v3.x 交易决策引擎） |
|---|---|---|
| 载体 | 10 Agent + 4 Workflow + AKShare MCP | `famas-score-fund` + `personal_investment_advisor` + etfirst/腾讯/hithink |
| 输出 | 星级、适配度、时机矩阵、风险提示 | **操作指令**：满仓/加仓/减半/清仓/止盈/止损/抄底/逃顶 |
| 合规立场 | 严格遵守"严禁买卖信号"红线 | 直接输出交易动作，或重新解释规则开豁免 |
| 数据层 | `famas-data` MCP (AKShare) | etfirst CLI + 腾讯行情 + hithink + 板块资金表 |

### 2.1 明确违规项

- **`famas-score-fund` SKILL.md**：Step 4 分数→操作映射表直接输出 `🟢 满仓持有 + 逢跌加仓`、`⛔ 清仓离场`；Step 5 预警线"主力出货，优先减仓"；Step 8 RSI"黄金抄底信号""逃顶信号"。与 `knowledge/CLAUDE.md` 红线"严禁输出 买入/卖出/加仓/减仓/清仓/抄底/追涨/止盈/止损/做多/做空"**直接冲突**。
- **`docs/fund-scoring-engine.md`**：全文以"操作指令"为核心，含 2026-07-31 真实持仓的操作清单（清仓科创半导体、减仓恒生科技等）。
- **`agents/personal_investment_advisor.md`**：自设豁免逻辑——"可以说'在 XX 条件下提交赎回'（操作建议），不能说'这只基金该卖了'（交易信号）"，并输出"到日期/价位的操作建议"。这种区分在合规上是打擦边球。

### 2.2 影响

用户在同一系统里会得到两套互相矛盾的输出：系统 A 拒绝给交易信号，系统 B 直接给"清仓/加仓"指令。**这是需要用户决策的最大问题**：要么承认 B 是个人实盘助手（独立于合规体系），要么让 B 收敛到 A 的合规框架。

---

## 三、工具数口径混乱（文档 vs 实现）

| 位置 | 声称 |
|---|---|
| `mcp_server/server.py` 实际注册 | **11 个**（10 工具 + `famas_health`） |
| `server.py` 顶部 docstring | "All 6 tools loaded" |
| `server.py` main() 日志 | "10 tools / 10 agents" |
| `docs/mcp-data-layer-design.md` | 标题"6 个工具"，正文又说"核心 10 个工具" |
| `README.md` | "10 tools / 10 agents" |
| `mcp_server/pyproject.toml` | description "6 tools"，version 1.0.0 |

结论：v2.0 设计是 6 工具，后来加了实时行情（realtime_index/etf）、资金流、推送变成 10 工具，但**文档、pyproject、README 未同步**。

---

## 四、Agent 定义问题（用户所说的"不完整"）

- **`agents/*.md` 全部无 frontmatter**：首行是 `# name — 职责`，没有 `---` frontmatter（缺 name/description/tools 字段），在 Claude Code 中无法通过 Agent 工具真正加载为可调用子 Agent。它们只是 System Prompt 文档。
- 部分 Agent 无 `<output_format>` JSON Schema：`manager_profiler`、`fund_comparator`、`portfolio_doctor`、`sector_screener`、`watchtower`、`prospectus_analyzer`、`cost_analyzer` 等缺少统一的输出 JSON Schema 约束；仅 `performance_analyst`、`wealth_advisor` 有完整 few-shot + output_format。
- `personal_investment_advisor` 是第 11 个 Agent，README 和 Router 都未收录，游离在主体系外。

---

## 五、代码级缺陷

1. **`fund_manager_info` 从业时间单位错误**（`server.py` L259）：
   `tenure_days: int(safe_float(r.get("累计从业时间",0)))`
   "累计从业时间"来自 `ak.fund_manager_em()`，单位是**年**（如 8.5），此处直接当 `tenure_days` 返回，数值失真（8.5 年变成了 8 天）。
2. **`fund_holdings` 硬编码年份**（`server.py` L208）：`yr = str(year) if year else "2026"`，2027 年必坏。
3. **`fund_manager_info` 的 manager_name 模式**返回 `NOT_IMPLEMENTED`（L243），与设计文档"manager_name 二选一"矛盾。
4. **`fund_holdings` 的 `sw` 构建**用列表推导副作用 `[sw.update(...) for h in hh]`，可读性差且脆弱。
5. **HHI 计算 `*10` 缩放**（`server.py` L221）：`sum((w/ts)**2)*10`，与文档示例 `concentration_hhi: 0.12` 量纲不一致，需确认是有意缩放还是笔误。
6. **`fund_basic_info` 规模解析**：`scale_str.replace("亿","")` 后 `safe_float`，若规模字符串含其他单位（如"万元"）会解析错误。
7. **SSRF 隐患**：`push_notification` 接受任意 `webhook_url`，若 MCP 暴露给不可信输入可被利用。
8. **pyproject 依赖缺失**：代码 `import requests`（4 处）、`from fastmcp import FastMCP`，但 pyproject 只声明 mcp/akshare/pandas；README 安装命令 `pip install akshare pandas mcp` 同样缺 requests 和 fastmcp。

---

## 六、数据层未落地

- `api/`、`ods/`、`dwd/`、`ads/`、`scripts/indicators/` 均为**空目录**。
- `docs/data-architecture.md` 描述的 ODS→DWD→ADS→API 四层架构**尚未实现**，只有 `data/fund_flow/` 有真实文件。
- 数据管线分裂：
  - `auto_fund_flow.py`（自动，etfirst，板块代码映射 24 个）
  - `fund_flow_tracker.py`（手动 CSV 导入，周度）
  - `_latest_scores.json` 的板块名（软件服务/证券/创新药/人形机器人/上证指数/半导体/存储芯片）与 `auto_fund_flow.py` 的 `SECTOR_INDICES`（软件服务/科创半导体/红利低波/恒生科技…）**名称不一致**，两条管线数据无法互通。
- `data_scheduler.py` 声称"腾讯实时 + etfirst 主干"，但 `get_all_sectors()` 里的 freshness 用的是 `datetime.now()` 而非真实数据日期。

---

## 七、Git 卫生与版本同步

- `.agents/skills/` 与 `.claude/skills/` 的 4 个主 SKILL 逐字节一致 ✅
- `.claude` 多出的 5 个技能全部 **git 未跟踪**：`famas-data-service`、`famas-score-fund`、`etfirst`、`hithink-finance`、`@org-6602ci5n/`（含重复的 hithink-finance）
- `.trae/skills/famas-fund-analysis` 还是 v1.0（单技能大杂烩），与主体系脱节
- 工作区 29 个文件有未提交修改（v2.0 → 当前演进中），且有 `.git/index.lock` 残留，曾有并发 git 操作
- 大量 docstring/description 仍写"6 工具"，版本号在 1.0.0/2.0/2.1.0 间不一致

---

## 八、测试与质量

- 仅 `mcp_server/test_all_realtime.py` 一个手动冒烟脚本
- `docs/testing-guide.md` 描述 L1-L6 测试体系，但 `validators.py`、`server.py`、`scripts/` 均无单元测试
- 无 CI 配置

---

## 九、改进建议（按优先级）

### P0（合规冲突，必须决策）
1. 明确系统 A / 系统 B 关系：将 `famas-score-fund` 与 `personal_investment_advisor` 要么纳入合规框架（去除"清仓/加仓"等指令，改为"适配度+配置方向"），要么在 SKILL 中显式标注为"个人实盘助手，独立于 FAMAS 合规体系，仅供已了解风险的用户使用"。

### P1（一致性与可用性）
2. 统一工具口径：以 server.py 实际 10 工具为准，同步 README、mcp-data-layer-design、pyproject（version 2.1.0、依赖补 requests/fastmcp）。
3. 修复 `fund_manager_info` 从业时间单位、`fund_holdings` 硬编码年份。
4. 为全部 11 个 Agent 补齐 frontmatter（name/description/tools），使其成为可被 Agent 工具加载的真实子 Agent；补全 `<output_format>` JSON Schema。

### P2（数据与架构）
5. 统一板块命名，打通 `auto_fund_flow` 与 `fund_flow_tracker` 两条管线。
6. 落地或移除空目录 api/ods/dwd/ads/scripts/indicators，避免误导。
7. 清理 git：提交未跟踪技能、移除 index.lock、同步 .trae 版本。
8. 为 validators.py 和 server.py 补单元测试；为 `push_notification` 增加 URL 白名单校验。

---

*免责声明：本报告仅作项目结构、代码与文档的一致性分析，不构成投资建议，也不涉及对任何基金的评价。*
