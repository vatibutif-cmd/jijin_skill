#!/usr/bin/env python3
"""FAMAS 数据服务核心 — 基于 etfirst 主干 + 腾讯实时补充

数据源: etfirst（主干，南方基金） + 腾讯行情（盘中实时）
核心铁律: 旧数据不能冒充新数据。数据源未给时返回 pending（待更新）。

用法:
  python3 data_scheduler.py quote 600519      # 股票实时行情（腾讯）
  python3 data_scheduler.py index sh000300    # 指数行情（腾讯）
  python3 data_scheduler.py nav 024418        # 基金净值（etfirst）
  python3 data_scheduler.py fund 024418       # 基金详情（etfirst）
  python3 data_scheduler.py sector 930601     # 板块数据（etfirst）
  python3 data_scheduler.py sectors           # 全部板块资金连续性
"""
import os, sys, json, subprocess
from datetime import datetime

# 绕过代理
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetchers"))

from processors.freshness import build_response


def _find_etfirst():
    for p in [os.path.expanduser("~/.local/bin/etfirst"), "/usr/local/bin/etfirst"]:
        if os.path.exists(p):
            return p
    return None


def _run_etfirst(args):
    etf_cmd = _find_etfirst()
    if not etf_cmd:
        return None, "etfirst 未找到"
    etf_env = dict(os.environ)
    for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
        etf_env.pop(k, None)
    result = subprocess.run(
        [etf_cmd] + args,
        capture_output=True, text=True, env=etf_env
    )
    if result.returncode != 0:
        return None, f"etfirst 调用失败: {result.stderr[:80]}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "etfirst JSON解析失败"


def fetch_quote_tencent(code):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetchers"))
    from tencent_quote import fetch_quote
    data, err = fetch_quote(code)
    return data, err


def fetch_nav_etfirst(code):
    d, err = _run_etfirst(['--json', 'otc-detail', 'all', '--product-code', str(code), '--date-range', '30'])
    if err:
        return None, err
    results = d.get("results", {})
    base = results.get("baseEtfLinkInfo", {})
    if base:
        return {
            "fund_code": code,
            "fund_name": base.get("prodName"),
            "fund_type": base.get("clasName"),
            "nav": base.get("nav"),
            "nav_date": base.get("navDate"),
            "yield": base.get("yield"),
            "ytd_yield": base.get("ytdYield"),
            "m1_yield": base.get("l1mYield"),
            "scale": base.get("ast"),
            "pe_percent": base.get("pePercent"),
            "pb_percent": base.get("pbPercent"),
            "valuation": base.get("valuation"),
            "track_index": base.get("indexName"),
        }, None
    return None, "etfirst 无基金数据"


def fetch_sector_etfirst(code):
    d, err = _run_etfirst(['--json', 'index-detail', 'all', '--index-code', str(code), '--index-type', '1'])
    if err:
        return None, err
    results = d.get("results", {})
    qd = results.get("queryIndexDetail", {})
    cr = results.get("queryChangeRateByIndexCode", {})
    ni = results.get("queryNetInflow", [])
    if qd:
        return {
            "index_code": code,
            "index_name": qd.get("indexName"),
            "pe": qd.get("pe"),
            "pe_percent": qd.get("pePercent"),
            "pb_percent": qd.get("pbPercent"),
            "roe": qd.get("roe"),
            "m1": cr.get("lastOneMonthChangeRate"),
            "m3": cr.get("lastThreeMonthChangeRate"),
            "ytd": cr.get("thisYearChangeRate"),
            "net_inflow_history": [
                {"date": x.get("tradingDay"), "flow": x.get("netInflowValue")}
                for x in ni if isinstance(ni, list)
            ],
        }, None
    return None, "etfirst 无板块数据"


def get_quote(code):
    data, err = fetch_quote_tencent(code)
    if data:
        return build_response(data, "intraday", datetime.now().strftime("%Y-%m-%d"), "tencent")
    return build_response(None, "intraday", None, f"tencent:{err}")


def get_nav(code):
    data, err = fetch_nav_etfirst(code)
    if data:
        nav_date = data.get("nav_date") or datetime.now().strftime("%Y-%m-%d")
        return build_response(data, "fund_nav", nav_date, "etfirst")
    return build_response(None, "fund_nav", None, f"etfirst:{err}")


def get_sector(code):
    data, err = fetch_sector_etfirst(code)
    if data:
        return build_response(data, "fund_flow", datetime.now().strftime("%Y-%m-%d"), "etfirst")
    return build_response(None, "fund_flow", None, f"etfirst:{err}")


def get_all_sectors():
    import glob
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_fund_flow.py")],
        capture_output=True, text=True
    )
    files = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fund_flow", "auto", "sectors_*.json")))
    if not files:
        return build_response(None, "fund_flow", None, "auto_fund_flow:无数据")
    with open(files[-1], encoding="utf-8") as f:
        data = json.load(f)
    sorted_data = dict(sorted(data.items(), key=lambda x: -x[1].get("continuity_score", 0)))
    return build_response(sorted_data, "fund_flow", datetime.now().strftime("%Y-%m-%d"), "etfirst")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "sectors":
        result = get_all_sectors()
    elif len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    else:
        code = sys.argv[2]
        if cmd in ("quote", "index"):
            result = get_quote(code)
        elif cmd in ("nav", "fund"):
            result = get_nav(code)
        elif cmd == "sector":
            result = get_sector(code)
        else:
            print(__doc__); sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
