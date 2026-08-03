---
name: "famas-data-service"
description: "统一数据服务入口：调用 scripts/data_scheduler.py 获取股票/指数实时行情（腾讯）、基金净值（etfirst）、板块数据（etfirst）、板块资金连续性。所有返回带 freshness 标记（fresh/stale/pending），旧数据不冒充新数据。当需要查行情、基金净值、板块资金、估值分位时使用。"
---

# FAMAS 数据服务

你是一个统一数据服务调用器。通过 `scripts/data_scheduler.py` 获取金融数据。

## 数据源

- **etfirst**（主干）: 基金净值、板块净流入、指数估值分位
- **腾讯行情**（实时）: 股票/指数盘中实时涨跌
- **AKShare**（兜底）: 基金净值、大盘资金
- **hithink-finance**（补充）: A股行情、财报、ETF

## 核心铁律

**旧数据不能冒充新数据。** 所有返回都带 `freshness` 字段：
- `fresh`: 数据新鲜，可用
- `stale`: 数据过期，需提示用户
- `pending`: 数据源未给，显示"待更新"

## 命令

```bash
# 股票/指数实时行情（腾讯）
python3 scripts/data_scheduler.py quote 600519
python3 scripts/data_scheduler.py index sh000300

# 基金净值/详情（etfirst）
python3 scripts/data_scheduler.py nav 024418
python3 scripts/data_scheduler.py fund 005911

# 板块数据（etfirst）：PE分位、近1月/3月涨幅、净流入历史
python3 scripts/data_scheduler.py sector 930601

# 全部板块资金连续性评分
python3 scripts/data_scheduler.py sectors
```

## 使用流程

1. 识别用户数据需求（行情/净值/板块/资金）
2. 选择对应命令执行
3. 检查返回的 `freshness`:
   - `fresh` → 直接使用数据
   - `stale` → 提示"数据截至XX，可能不是最新"
   - `pending` → 明确告诉用户"数据待更新"，不编造数据
4. 分析数据并给出结论

## 常用指数代码

| 指数 | 代码 |
|------|------|
| 中证软件 | 930601 |
| 科创半导体材料设备 | 950125 |
| 红利低波 | H30269 |
| 恒生科技 | HSTECH |
| 港股创新药 | 931787 |
| 创业板指 | 399006 |
| 证券公司 | 399975 |
| 人工智能 | 930713 |
| 中证医疗 | 399989 |
| 中证白酒 | 399997 |

## 数据输出示例

```json
{
  "data": {
    "fund_name": "华夏上证科创板半导体材料设备ETF联接C",
    "nav": 2.1988,
    "pe_percent": 93.44,
    "valuation": "过高"
  },
  "data_date": "2026-08-03",
  "freshness": "fresh",
  "data_source": "etfirst"
}
```
