"""FAMAS MCP Server — All 10 data tools + health check loaded from this single module.

Each tool is an async function registered via FastMCP. Data layer delegates
to utils/ak_wrapper.py which wraps AKShare with TTL caching.

Usage (development):
    python server.py              # start MCP server on stdio
Usage (production):
    uv run famas-data-server      # declared in pyproject.toml [project.scripts]
"""

import sys, os, logging

# ── Ensure sibling modules are importable ──────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

# Direct imports (everything lives at mcp_server/ level)
from utils.validators import (
    check_fund_code, check_keyword, check_top_n, check_days,
    check_index, check_date, check_ann_kw, check_max_results,
    check_flow_type, check_channel, check_webhook_url,
    error_resp,
)
from utils.ak_wrapper import (
    fetch_fund_basic_info, search_funds_by_keyword,
    fetch_nav_history, fetch_holdings,
    fetch_manager_by_fund, fetch_manager_by_name, fetch_announcements,
    fetch_a_share_index, fetch_hstech_index,
    fetch_realtime_index_spot, fetch_realtime_etf_spot,
    fetch_capital_flow, send_webhook_push,
    safe_float, get_cache_stats,
)
# A股数据层（集成自 a-stock-data，见 mcp_server/a_stock_data/）
try:
    from a_stock_data import (
        stock_quote as a_stock_quote,
        board_fund_flow as a_board_fund_flow,
        industry_comparison as a_industry_comparison,
        eastmoney_stock_news as a_stock_news,
    )
    _A_STOCK_AVAILABLE = True
except ImportError:
    _A_STOCK_AVAILABLE = False

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("famas-mcp")

# ── FastMCP instance ─────────────────────────────────────────────────
server = FastMCP("famas-data")

# ═══════════════════════════════════════════════════════════════════════
# Utility helpers (used across tools)
# ═══════════════════════════════════════════════════════════════════════

import math
from datetime import datetime, timedelta
from typing import Optional

INDEX_NAMES = {"000300": "沪深300", "000905": "中证500",
               "399006": "创业板指", "HSTECH": "恒生科技指数"}

_ALERT_TRIGGERS = {
    "经理变更": ("基金经理变更", "高"), "清盘": ("清盘风险", "高"),
    "大额赎回": ("大额赎回", "高"), "费率": ("费率调整", "中"),
    "分红": ("分红公告", "低"), "限购": ("限购调整", "低"), "终止": ("基金终止", "高"),
}

_SECTOR_KW = {
    "食品饮料": ["酒", "食品", "饮料", "乳", "肉", "粮", "调味"],
    "医药生物": ["药", "医", "生物", "疫苗", "医疗"],
    "电子": ["电子", "半导体", "芯片", "光", "电路"],
    "电力设备": ["电池", "能源", "电", "光伏", "锂", "风"],
    "银行": ["银行"],
    "非银金融": ["保险", "证券", "信托"],
    "计算机": ["软件", "数据", "信息", "云", "智能"],
    "汽车": ["汽车", "车", "轮胎"],
    "房地产": ["地产", "房", "置地", "园区"],
    "有色金属": ["铜", "铝", "金", "矿", "钴", "稀土"],
    "国防军工": ["航空", "航天", "军工", "船舶"],
    "通信": ["通信", "电信", "移动", "联通"],
}

def _sector_for(name: str) -> str:
    for s, kws in _SECTOR_KW.items():
        if any(kw in str(name) for kw in kws):
            return s
    return "其他"

def _alert_scan(title: str, kw: Optional[str]):
    t = str(title)
    if kw and kw in _ALERT_TRIGGERS:
        at, pr = _ALERT_TRIGGERS[kw]
        return (kw in t, at, pr)
    for k, (at, pr) in sorted(_ALERT_TRIGGERS.items(), key=lambda x: len(x[0]), reverse=True):
        if k in t: return (True, at, pr)
    return (False, None, None)


# ═══════════════════════════════════════════════════════════════════════
# Tool 1: fund_basic_info
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def fund_basic_info(fund_code: str | None = None, keyword: str | None = None, top_n: int = 10) -> dict:
    """查询公募基金基本信息。fund_code 模式返回详情（名称/类型/规模/经理/费率/基准）；keyword 模式全市场搜索（最多 top_n 条）。二选一"""
    if fund_code:
        ok, err = check_fund_code(fund_code)
        if not ok: return error_resp("INVALID_INPUT", err, fund_code)
    elif keyword:
        ok, err = check_keyword(keyword)
        if not ok: return error_resp("INVALID_INPUT", err)
        ok, err = check_top_n(top_n)
        if not ok: return error_resp("INVALID_INPUT", err)
    else:
        return error_resp("INVALID_INPUT", "Provide either fund_code or keyword")

    if fund_code:
        raw = fetch_fund_basic_info(fund_code)
        if isinstance(raw, dict) and raw.get("error"):
            return error_resp(raw["error_code"], raw["message"], fund_code)
        scale_str = raw.get("最新规模", "0")
        scale_num = safe_float(str(scale_str).replace("亿", "").replace(",", "").strip())
        mgmt_str = raw.get("管理费率", "0")
        mgmt_num = safe_float(str(mgmt_str).replace("%", "").strip())
        return {
            "mode": "detail",
            "fund_code": raw.get("基金代码", fund_code),
            "fund_name": str(raw.get("基金名称", "")),
            "fund_full_name": str(raw.get("基金全称", "")),
            "fund_type": str(raw.get("基金类型", "")),
            "inception_date": str(raw.get("成立时间", "")),
            "current_scale_billion": round(scale_num, 2),
            "company": str(raw.get("基金公司", "")),
            "manager_name": str(raw.get("基金经理", "")),
            "custodian": str(raw.get("托管银行", "")),
            "benchmark": str(raw.get("业绩比较基准", "")),
            "management_fee_pct": round(mgmt_num, 2),
            "strategy": str(raw.get("投资策略", "")),
            "objective": str(raw.get("投资目标", "")),
            "rating": str(raw.get("基金评级", "")),
            "source": "天天基金/证监会披露",
        }

    funds = search_funds_by_keyword(keyword)
    results = [{"fund_code": str(r.get("基金代码", "")),
                 "fund_name": str(r.get("基金简称", "")),
                 "fund_type": str(r.get("基金类型", ""))}
                for r in funds[:top_n]]
    return {"mode": "search", "keyword": keyword,
            "total_matches": len(funds), "returned": len(results), "funds": results}


# ═══════════════════════════════════════════════════════════════════════
# Tool 2: fund_nav_history
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def fund_nav_history(fund_code: str, days: int = 252) -> dict:
    """拉取基金历史净值序列。每日单位净值+日增长率+基础统计（区间收益/最大回撤/波动率/上涨比）。max 1095天"""
    ok, err = check_fund_code(fund_code)
    if not ok: return error_resp("INVALID_INPUT", err, fund_code)
    ok, err = check_days(days)
    if not ok: return error_resp("INVALID_INPUT", err, fund_code)

    raw = fetch_nav_history(fund_code, days)
    series = [{"date": str(r.get("净值日期", ""))[:10],
               "unit_nav": safe_float(r.get("单位净值", 0)),
               "daily_return_pct": round(safe_float(r.get("日增长率", 0)), 4)}
              for r in raw]
    if not series:
        return error_resp("NOT_FOUND", f"No NAV for {fund_code}", fund_code)

    navs = [s["unit_nav"] for s in series if s["unit_nav"] > 0]
    rets  = [s["daily_return_pct"] for s in series if s.get("daily_return_pct") is not None]
    p_ret = ((navs[-1]/navs[0])-1)*100 if len(navs)>=2 else 0
    peak=navs[0] if navs else 0; dd=0.0; ds=de=0; pi=0
    for i,v in enumerate(navs):
        if v>peak: peak=v; pi=i
        d=(v-peak)/peak*100
        if d<dd: dd=d; ds=pi; de=i
    if rets and len(rets)>=2:
        m=sum(rets)/len(rets)
        var=sum((r-m)**2 for r in rets)/(len(rets)-1)
        vol=math.sqrt(var)*math.sqrt(252)
        pos=sum(1 for r in rets if r>0)/len(rets)
    else: vol=0; pos=0

    return {"fund_code":fund_code,
            "data_start":series[0]["date"],"data_end":series[-1]["date"],
            "trading_days":len(series),"latest_nav":navs[-1] if navs else 0,
            "nav_series":series,
            "summary":{"period_return_pct":round(p_ret,2),
                        "max_drawdown_pct":round(dd,2),
                        "max_drawdown_start":series[ds]["date"] if ds<len(series) else "",
                        "max_drawdown_end":series[de]["date"] if de<len(series) else "",
                        "annual_volatility_pct":round(vol,2),
                        "positive_day_ratio":round(pos,4)},
            "source":"东方财富基金净值"}


# ═══════════════════════════════════════════════════════════════════════
# Tool 3: fund_holdings
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def fund_holdings(fund_code: str, year: int | None = None, quarter: int | None = None) -> dict:
    """获取最新季报前十大重仓股，含行业分类、权重、集中度HHI。数据滞后约20-30天"""
    ok, err = check_fund_code(fund_code)
    if not ok: return error_resp("INVALID_INPUT", err, fund_code)
    yr = str(year) if year else str(datetime.now().year)
    raw = fetch_holdings(fund_code, yr)
    hh = [{"rank":int(r.get("序号",0)),
           "stock_code":str(r.get("股票代码","")).strip(),
           "stock_name":str(r.get("股票名称","")).strip(),
           "sector":_sector_for(str(r.get("股票名称",""))),
           "weight_pct":safe_float(r.get("占净值比例",0)),
           "shares_held":safe_float(r.get("持股数",0)),
           "market_value":safe_float(r.get("持仓市值",0))}
          for r in raw]
    sw={}
    for h in hh:
        sw[h["sector"]] = sw.get(h["sector"], 0) + h["weight_pct"]
    sd=sorted([{"sector":s,"weight_pct":round(w,2)} for s,w in sw.items()],key=lambda x:x["weight_pct"],reverse=True)
    ts=sum(h["weight_pct"] for h in hh)
    hhi=sum((h["weight_pct"]/ts)**2 for h in hh) if ts>0 else 0
    return {"fund_code":fund_code,
            "report_period":raw[0].get("季度","") if raw else "",
            "top10_ratio_pct":round(ts,2),
            "top10_holdings":hh,
            "sector_distribution":sd,
            "concentration_hhi":round(hhi,4),
            "source":"基金季度报告"}


# ═══════════════════════════════════════════════════════════════════════
# Tool 4: fund_manager_info
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def fund_manager_info(fund_code: str | None = None, manager_name: str | None = None) -> dict:
    """查询基金经理履历：公司、从业年限、管理规模、最佳回报。fund_code 查该基金在任经理"""
    if fund_code:
        ok, err = check_fund_code(fund_code)
        if not ok: return error_resp("INVALID_INPUT", err, fund_code)
    elif not manager_name:
        return error_resp("INVALID_INPUT", "Provide either fund_code or manager_name")
    if manager_name and not fund_code:
        # 按姓名检索：从全量经理表过滤（ak_wrapper.fetch_manager_by_name）
        rows = fetch_manager_by_name(manager_name)
        if not rows:
            return error_resp("NOT_FOUND", f"No manager data for name '{manager_name}'")
        mgrs = [{"manager_name":str(r.get("姓名","")),
                 "company":str(r.get("所属公司","")),
                 "current_fund_codes":str(r.get("现任基金代码","")),
                 "current_fund_names":str(r.get("现任基金","")),
                 "experience_years":round(safe_float(r.get("累计从业时间",0)),1),
                 "tenure_days":int(safe_float(r.get("累计从业时间",0))*365),
                 "total_scale_billion":safe_float(r.get("现任基金资产总规模",0)),
                 "best_return_pct":safe_float(r.get("现任基金最佳回报",0))}
                for r in rows]
        return {"query_by":"manager_name","manager_name":manager_name,"managers":mgrs,
                "source":"天天基金/证监会从业人员公示"}
    rows = fetch_manager_by_fund(fund_code)
    if not rows:
        raw = fetch_fund_basic_info(fund_code)
        if isinstance(raw,dict) and not raw.get("error") and raw.get("基金经理"):
            return {"query_by":"fund_code","fund_code":fund_code,
                    "managers":[{"manager_name":str(raw.get("基金经理","")),
                                 "company":str(raw.get("基金公司","")),
                                 "note":"Basic info only; detailed career unavailable"}],
                    "source":"基金基本信息系统"}
        return error_resp("NOT_FOUND",f"No manager data for {fund_code}",fund_code)
    mgrs = [{"manager_name":str(r.get("姓名","")),
             "company":str(r.get("所属公司","")),
             "current_fund_codes":str(r.get("现任基金代码","")),
             "current_fund_names":str(r.get("现任基金","")),
             "experience_years":round(safe_float(r.get("累计从业时间",0)),1),
             "tenure_days":int(safe_float(r.get("累计从业时间",0))*365),
             "total_scale_billion":safe_float(r.get("现任基金资产总规模",0)),
             "best_return_pct":safe_float(r.get("现任基金最佳回报",0))}
            for r in rows]
    return {"query_by":"fund_code","fund_code":fund_code,"managers":mgrs,
            "source":"天天基金/证监会从业人员公示"}


# ═══════════════════════════════════════════════════════════════════════
# Tool 5: index_data
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def index_data(index_code: str, start_date: str | None = None, end_date: str | None = None) -> dict:
    """获取指数行情。index_code: 000300(沪深300) 000905(中证500) 399006(创业板指) HSTECH(恒生科技)"""
    ok, err = check_index(index_code)
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_date(start_date,"start_date")
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_date(end_date,"end_date")
    if not ok: return error_resp("INVALID_INPUT", err)
    today=datetime.now().strftime("%Y-%m-%d")
    sd=start_date or (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d")
    ed=end_date or today

    if index_code=="HSTECH":
        raw=fetch_hstech_index(sd,ed)
    else:
        raw=fetch_a_share_index(index_code,sd,ed)

    series=[]
    for r in raw:
        if index_code=="HSTECH":
            series.append({"date":str(r.get("date",r.get("日期","")))[:10],
                           "close":safe_float(r.get("close",r.get("收盘",0))),
                           "change_pct":safe_float(r.get("pct_chg",r.get("涨跌幅",0)))})
        else:
            series.append({"date":str(r.get("日期",""))[:10],
                           "close":safe_float(r.get("收盘",0)),
                           "change_pct":safe_float(r.get("涨跌幅",0)),
                           "volume_billion":safe_float(r.get("成交量",0))/1e8})
    if not series:
        return error_resp("NOT_FOUND",f"No data for {index_code} in {sd}~{ed}")

    closes=[s["close"] for s in series if s["close"]>0]
    ret=((closes[-1]/closes[0])-1)*100 if len(closes)>=2 else 0
    peak=closes[0] if closes else 0; max_dd=0.0
    for c in closes:
        if c>peak: peak=c
        dd=(c-peak)/peak*100
        if dd<max_dd: max_dd=dd

    return {"index_code":index_code,"index_name":INDEX_NAMES.get(index_code,index_code),
            "start_date":sd,"end_date":ed,"trading_days":len(series),
            "latest_close":round(closes[-1],2) if closes else 0,
            "period_return_pct":round(ret,2),
            "period_max_drawdown_pct":round(max_dd,2),
            "daily_series":series,"source":"东方财富指数行情"}


# ═══════════════════════════════════════════════════════════════════════
# Tool 6: fund_announcements
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def fund_announcements(fund_code: str, keyword: str | None = None,
                              days: int = 90, max_results: int = 15) -> dict:
    """搜索基金公告并自动标记预警。keyword: 经理变更/清盘/大额赎回/费率/分红/限购/终止"""
    ok, err = check_fund_code(fund_code)
    if not ok: return error_resp("INVALID_INPUT", err, fund_code)
    ok, err = check_ann_kw(keyword)
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_days(days,365)
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_max_results(max_results)
    if not ok: return error_resp("INVALID_INPUT", err)

    raw=fetch_announcements(fund_code)
    cutoff=(datetime.now()-timedelta(days=days)).strftime("%Y-%m-%d")
    parsed=[]
    for r in raw:
        title=str(r.get("公告标题","")); date_str=str(r.get("公告日期",""))[:10]
        if date_str<cutoff: continue
        if keyword and keyword not in title: continue
        trig,atype,pri=_alert_scan(title,keyword)
        parsed.append({"date":date_str,"title":title,"alert_trigger":trig,
                        "alert_type":atype,"alert_priority":pri,
                        "source_url":f"fund.eastmoney.com/{fund_code}/gg.html"})
    parsed.sort(key=lambda x:x["date"],reverse=True);parsed=parsed[:max_results]
    trigs=[p for p in parsed if p["alert_trigger"]]
    return {"fund_code":fund_code,"search_period_days":days,"keyword_filter":keyword,
            "total_found":len(parsed),
            "alert_summary":{"total_alerts":len(trigs),
                              "high_priority":sum(1 for p in trigs if p["alert_priority"]=="高"),
                              "medium_priority":sum(1 for p in trigs if p["alert_priority"]=="中"),
                              "low_priority":sum(1 for p in trigs if p["alert_priority"]=="低")},
            "announcements":parsed,"source":"东方财富基金公告/巨潮资讯"}


# ═══════════════════════════════════════════════════════════════════════
# Tool 7: realtime_index_spot
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def realtime_index_spot(index_codes: str | None = None, top_n: int = 15) -> dict:
    """获取大盘指数/行业指数实时行情与涨跌幅。index_codes: '000300,399006,HSTECH' (可选)"""
    ok, err = check_top_n(top_n)
    if not ok: return error_resp("INVALID_INPUT", err)
    data = fetch_realtime_index_spot(index_codes=index_codes, top_n=top_n)
    return {
        "index_filter": index_codes,
        "total_results": len(data),
        "data": data,
        "source": "东方财富实时指数行情"
    }


# ═══════════════════════════════════════════════════════════════════════
# Tool 8: realtime_etf_spot
# ═══════════════════════════════════════════════════════════════════
@server.tool()
async def realtime_etf_spot(etf_code_or_kw: str | None = None, category: str | None = None, top_n: int = 15) -> dict:
    """获取 ETF 基金实时行情、换手率、成交额及折溢价率(IOPV)。etf_code_or_kw: '510300' 或 '半导体' (可选)"""
    ok, err = check_top_n(top_n)
    if not ok: return error_resp("INVALID_INPUT", err)
    data = fetch_realtime_etf_spot(etf_code_or_kw=etf_code_or_kw, category=category, top_n=top_n)
    return {
        "filter": etf_code_or_kw,
        "category": category,
        "total_results": len(data),
        "data": data,
        "source": "东方财富 ETF 实时数据"
    }


# ═══════════════════════════════════════════════════════════════════════
# Tool 9: capital_flow_data
# ═══════════════════════════════════════════════════════════════════
@server.tool()
async def capital_flow_data(flow_type: str = "all", top_n: int = 10) -> dict:
    """获取板块/行业主力资金流向榜单及北向/南向资金实时流向。flow_type: 'sector'|'northbound'|'all'"""
    ok, err = check_flow_type(flow_type)
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_top_n(top_n)
    if not ok: return error_resp("INVALID_INPUT", err)
    res = fetch_capital_flow(flow_type=flow_type, top_n=top_n)
    res["source"] = "东方财富主力资金与北向流向"
    return res


# ═══════════════════════════════════════════════════════════════════════
# Tool 10: push_notification
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def push_notification(
    webhook_url: str,
    channel: str | None = None,
    title: str = "FAMAS 基金系统预警通知",
    content: str = "",
    msg_type: str = "alert",
    secret: str | None = None
) -> dict:
    """通过 Webhook 推送预警通知或分析报告至钉钉、企业微信、飞书或自定义 Server。"""
    ok, err = check_webhook_url(webhook_url)
    if not ok: return error_resp("INVALID_INPUT", err)
    ok, err = check_channel(channel)
    if not ok: return error_resp("INVALID_INPUT", err)

    res = send_webhook_push(
        webhook_url=webhook_url,
        channel=channel,
        title=title,
        content=content,
        msg_type=msg_type,
        secret=secret
    )
    return res


# ═══════════════════════════════════════════════════════════════════════
# A股数据工具（集成自 a-stock-data · V3.6.0 · Apache-2.0）
# ═══════════════════════════════════════════════════════════════════════

@server.tool()
async def a_stock_quote_tool(codes: str) -> dict:
    """批量获取A股/指数/ETF实时行情（腾讯财经，不封IP）。codes: 逗号分隔的6位代码，如 '600519,000300,510300'。返回现价/涨跌幅/PE/PB/市值/换手率等"""
    if not _A_STOCK_AVAILABLE:
        return error_resp("MODULE_UNAVAILABLE", "a_stock_data module not installed; pip install requests")
    code_list = [c.strip() for c in str(codes).split(",") if c.strip()]
    if not code_list:
        return error_resp("INVALID_INPUT", "codes is required", None)
    if len(code_list) > 20:
        return error_resp("INVALID_INPUT", "max 20 codes per call", None)
    try:
        return {"source": "腾讯财经", "quotes": a_stock_quote(code_list)}
    except Exception as e:
        return error_resp("QUOTE_ERROR", str(e)[:200])


@server.tool()
async def a_stock_board_fund_flow(board_type: str = "industry", period: str = "today", top_n: int = 20) -> dict:
    """板块资金流向排名（东方财富）。board_type: industry(行业)/concept(概念)/region(地域)；period: today(今日)/5d(5日)/10d(10日)。返回主力净流入/净占比/领涨股，供行业筛选与宏观风格判断"""
    if not _A_STOCK_AVAILABLE:
        return error_resp("MODULE_UNAVAILABLE", "a_stock_data module not installed")
    if board_type not in ("industry", "concept", "region"):
        return error_resp("INVALID_INPUT", "board_type must be industry/concept/region")
    if period not in ("today", "5d", "10d"):
        return error_resp("INVALID_INPUT", "period must be today/5d/10d")
    if not isinstance(top_n, int) or top_n < 1 or top_n > 200:
        return error_resp("INVALID_INPUT", "top_n must be 1-200")
    try:
        data = a_board_fund_flow(board_type, period, top_n)
        data["source"] = "东方财富 push2"
        return data
    except Exception as e:
        return error_resp("FLOW_ERROR", str(e)[:200])


@server.tool()
async def a_stock_industry_rank(top_n: int = 20) -> dict:
    """全行业涨跌幅排名（东方财富，~100个行业）。返回涨幅榜TOP与跌幅榜BOTTOM，含上涨/下跌家数与领涨股，供行业轮动判断"""
    if not _A_STOCK_AVAILABLE:
        return error_resp("MODULE_UNAVAILABLE", "a_stock_data module not installed")
    if not isinstance(top_n, int) or top_n < 1 or top_n > 50:
        return error_resp("INVALID_INPUT", "top_n must be 1-50")
    try:
        data = a_industry_comparison(top_n)
        data["source"] = "东方财富 push2"
        return data
    except Exception as e:
        return error_resp("RANK_ERROR", str(e)[:200])


@server.tool()
async def a_stock_stock_news(code: str, page_size: int = 20) -> dict:
    """获取个股新闻（东方财富）。code: 6位股票代码。返回日期/标题/来源/链接，供持仓穿透时追踪重仓股动态"""
    if not _A_STOCK_AVAILABLE:
        return error_resp("MODULE_UNAVAILABLE", "a_stock_data module not installed")
    ok, err = check_fund_code(code)
    if not ok:
        return error_resp("INVALID_INPUT", err, code)
    if not isinstance(page_size, int) or page_size < 1 or page_size > 50:
        return error_resp("INVALID_INPUT", "page_size must be 1-50")
    try:
        news = a_stock_news(code, page_size)
        return {"code": code, "total": len(news), "news": news, "source": "东方财富"}
    except Exception as e:
        return error_resp("NEWS_ERROR", str(e)[:200])


# ═══════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════
@server.tool()
async def famas_health() -> dict:
    """FAMAS MCP Server 健康检查 + 缓存统计"""
    return {"status":"ok","version":"2.2.0",
            "tools":["fund_basic_info","fund_nav_history","fund_holdings",
                      "fund_manager_info","index_data","fund_announcements",
                      "realtime_index_spot","realtime_etf_spot","capital_flow_data","push_notification",
                      "a_stock_quote_tool","a_stock_board_fund_flow","a_stock_industry_rank","a_stock_stock_news"],
            "a_stock_module": _A_STOCK_AVAILABLE,
            "cache":get_cache_stats()}


# ── Entry ─────────────────────────────────────────────────────────────
def main():
    logger.info("FAMAS MCP Data Server v2.2.0 — 14 tools / 10 agents / Realtime & Push + A股数据层")
    server.run()

if __name__=="__main__":
    main()

