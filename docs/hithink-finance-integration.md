# hithink-finance 集成说明

> **状态**: 已安装 CLI + 10 个 Skill | **版本**: 0.1.4 | **日期**: 2026-08-03

## 一、功能概述

hithink-finance 是"同花顺金融数据服务"的 Agent 统一入口，支持：
- **A股行情**: 快照、日线历史、复权、交易日历
- **财报**: 利润表、资产负债表、现金流、财务指标
- **指数/板块**: 目录、成分股、行情
- **公募基金**: 资料、净值、收益、持仓、持有人、ETF/LOF 行情
- **特色数据**: 涨停、异动、热榜、龙虎榜
- **数据管理**: 本地 DuckDB 同步、SQL、导出

## 二、安装清单

| 组件 | 状态 | 位置 |
|------|------|------|
| skillhub CLI | ✅ | `~/.local/bin/skillhub` |
| hithink-finance CLI | ✅ v0.1.4 | `~/.npm-global/bin/hithink-finance` |
| 主路由 SKILL.md | ✅ | `.claude/skills/hithink-finance/` |
| 9个配套 Skill | ✅ | `~/.claude/skills/hithink-finance-*` |

配套 Skill 列表：
- hithink-finance-symbol（标地消歧）
- hithink-finance-market（行情）
- hithink-finance-financials（财报）
- hithink-finance-index（指数/板块）
- hithink-finance-special-data（特色数据）
- hithink-finance-fund（公募基金）
- hithink-finance-data（数据管理）
- hithink-finance-research（研究编排）
- hithink-finance-shared（认证/生命周期）
- hithink-finance-valuation（估值）

## 三、API Key 配置（待完成）

API Key 在 https://fuyao.aicubes.cn/admin 获取。配置方式：

```bash
# 方式1: 环境变量
export HITHINK_FINANCE_API_KEY="你的Key"

# 方式2: CLI 安全登录（推荐，Key 不落日志）
hithink-finance auth login --api-key-stdin

# 方式3: 用户凭据文件
echo 'HITHINK_FINANCE_API_KEY=你的Key' > ~/.config/hithink-finance/credentials.env
chmod 600 ~/.config/hithink-finance/credentials.env
```

## 四、常用命令

```bash
# A股行情快照
hithink-finance market snapshot --symbol 000001.SZ

# A股日线历史
hithink-finance market history --symbol 000001.SZ

# 基金净值
hithink-finance fund nav --symbol 005911.OF

# 基金持仓
hithink-finance fund holdings --symbol 005911.OF

# 指数行情
hithink-finance index list
```

## 五、网络注意事项

沙箱环境代理失效时，需绕过代理运行：
```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  hithink-finance <命令>
```

## 六、与 FAMAS 的集成

hithink-finance 可作为 **etfirst 的补充数据源**：
- etfirst: 南方基金指数库（估值分位、指数详情）
- hithink-finance: 同花顺全市场数据（行情、财报、基金、特色数据）

两者互补，共同支撑评分引擎的资金/估值/技术维度。
