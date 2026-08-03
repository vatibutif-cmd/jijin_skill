# FAMAS-Skill 变更日志

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
- **Workflow A 完整编