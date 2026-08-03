"""A股数据层 — 从 a-stock-data skill 提取的与基金分析最相关的函数。

数据源: 腾讯财经（不封IP，行情）+ 东方财富 push2（板块/资金流，内置限流防封）。
来源: https://github.com/simonlin1212/a-stock-data (Apache-2.0, V3.6.0)

本模块只提取与 FAMAS 基金分析最相关的「纯 HTTP 零鉴权」函数，
不依赖 mootdx（TCP 通达信）与 iwencai（需 API Key），保证开箱即用。

包含:
  - stock_quote          批量实时行情（腾讯）
  - board_fund_flow      板块资金流向（东财）
  - industry_comparison  全行业涨跌幅排名（东财）
  - eastmoney_stock_news 个股新闻（东财，辅助持仓穿透）
"""

import time
import random
import urllib.request
import requests

# ═══════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# 东财防封：全局节流 + 会话复用
_em_last_call = [0.0]
EM_MIN_INTERVAL = 1.0  # 秒，最小请求间隔
EM_SESSION = requests.Session()
EM_SESSION.headers.update({"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"})

# 板块类型 → 东财 fs 参数
_BOARD_FS = {"industry": "m:90+t:2", "concept": "m:90+t:3", "region": "m:90+t:1"}
# 周期 → (排序fid, 主力净额, 主力净占比, 涨跌幅, 领涨股name)
_BOARD_PERIOD = {
    "today": ("f62",  "f62",  "f184", "f3",   "f204"),
    "5d":    ("f164", "f164", "f165", "f109", "f257"),
    "10d":   ("f174", "f174", "f175", "f160", None),
}

# 沪市指数白名单（与深市 000xxx 个股同段，需白名单区分）
SH_INDEX = {"000300", "000905", "000016", "000688", "000852", "000010"}


# ═══════════════════════════════════════════════════════════════════
# 东财统一请求入口（限流防封）
# ═══════════════════════════════════════════════════════════════════

def em_get(url: str, params: dict | None = None, headers: dict | None = None,
           timeout: int = 15, **kwargs):
    """东财统一请求入口：自动节流 + 复用 session + 默认 UA。"""
    wait = EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
    if wait > 0:
        time.sleep(wait + random.uniform(0.1, 0.5))
    try:
        return EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    finally:
        _em_last_call[0] = time.time()


# ═══════════════════════════════════════════════════════════════════
# 腾讯实时行情（不封IP）
# ═══════════════════════════════════════════════════════════════════

def stock_quote(codes: list) -> dict:
    """批量拉取腾讯财经实时行情。

    codes: 6 位代码列表，如 ["688017", "300476"]，支持指数 ["000300"]、ETF ["510300"]。
    返回: {code: {name, price, pe_ttm, pb, mcap_yi, change_pct, ...}}
    """
    prefixed = []
    key_of = {}
    for c in codes:
        low = str(c).lower()
        if low.startswith(("sh", "sz", "bj")):
            p = low
        elif c.startswith("92"):
            p = f"bj{c}"
        elif c in SH_INDEX or c.startswith(("5", "6", "9")):
            p = f"sh{c}"
        elif c.startswith(("4", "8")):
            p = f"bj{c}"
        else:
            p = f"sz{c}"
        prefixed.append(p)
        key_of[p] = c

    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode("gbk")

    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        code = key_of.get(key, key[2:])
        result[code] = {
            "name": vals[1],
            "price": float(vals[3]) if vals[3] else 0,
            "last_close": float(vals[4]) if vals[4] else 0,
            "open": float(vals[5]) if vals[5] else 0,
            "change_amt": float(vals[31]) if vals[31] else 0,
            "change_pct": float(vals[32]) if vals[32] else 0,
            "high": float(vals[33]) if vals[33] else 0,
            "low": float(vals[34]) if vals[34] else 0,
            "amount_wan": float(vals[37]) if vals[37] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "pe_ttm": float(vals[39]) if vals[39] else 0,
            "amplitude_pct": float(vals[43]) if vals[43] else 0,
            "float_mcap_yi": float(vals[44]) if vals[44] else 0,
            "mcap_yi": float(vals[45]) if vals[45] else 0,
            "pb": float(vals[46]) if vals[46] else 0,
            "limit_up": float(vals[47]) if vals[47] else 0,
            "limit_down": float(vals[48]) if vals[48] else 0,
            "vol_ratio": float(vals[49]) if vals[49] else 0,
            "pe_static": float(vals[52]) if vals[52] else 0,
        }
        # 僵尸报价检测（停牌/废码）
        q = result[code]
        q["is_stale"] = (q["amount_wan"] == 0 and q["price"] == q["last_close"] and q["price"] > 0)
        if q["is_stale"] and key[2:4] in ("43", "83", "87"):
            q["stale_reason"] = "北交所老号段，多数已迁至 920xxx，请按名称反查现行代码"
        elif q["is_stale"]:
            q["stale_reason"] = "成交量为 0（停牌/未开盘/废码），报价非当日真实成交"
    return result


# ═══════════════════════════════════════════════════════════════════
# 板块资金流向（东财，内置限流）
# ═══════════════════════════════════════════════════════════════════

def board_fund_flow(board_type: str = "industry", period: str = "today",
                    top_n: int = 20) -> dict:
    """板块资金流向排名（按主力净流入降序）。

    board_type: industry(行业) / concept(概念) / region(地域)
    period:     today(今日) / 5d(5日) / 10d(10日)
    返回: {board_type, period, total, rows:[{rank, name, code, change_pct,
           main_net, main_pct, leader, (today: super_large_net/large_net/medium_net/small_net)}]}
    """
    if board_type not in _BOARD_FS:
        raise ValueError(f"board_type 须为 {list(_BOARD_FS)}")
    if period not in _BOARD_PERIOD:
        raise ValueError(f"period 须为 {list(_BOARD_PERIOD)}")
    fid, f_main, f_pct, f_chg, f_leader = _BOARD_PERIOD[period]

    fields = ["f12", "f14", f_chg, f_main, f_pct]
    if f_leader:
        fields.append(f_leader)
    if period == "today":
        fields += ["f66", "f72", "f78", "f84"]

    url = "https://push2.eastmoney.com/api/qt/clist/get"
    base = {
        "pz": "200", "po": "1", "np": "1",
        "fltt": "2", "invt": "2", "fid": fid,
        "fs": _BOARD_FS[board_type],
        "fields": ",".join(dict.fromkeys(fields)),
    }

    def _page(pn: int):
        r = em_get(url, params={**base, "pn": str(pn)},
                   headers={"User-Agent": UA}, timeout=15)
        d = r.json().get("data") or {}
        return (d.get("diff") or []), int(d.get("total") or 0)

    _PAGE = 200
    items, total = _page(1)
    pn = 2
    while len(items) < top_n:
        if total and len(items) >= total:
            break
        more, _ = _page(pn)
        if not more:
            break
        items += more
        pn += 1
        if len(more) < _PAGE:
            break
    total = max(total, len(items))

    rows = []
    for i, it in enumerate(items):
        row = {
            "rank": i + 1,
            "name": it.get("f14", ""),
            "code": it.get("f12", ""),
            "change_pct": it.get(f_chg, 0),
            "main_net": it.get(f_main, 0),
            "main_pct": it.get(f_pct, 0),
            "leader": it.get(f_leader, "") if f_leader else "",
        }
        if period == "today":
            row.update({
                "super_large_net": it.get("f66", 0),
                "large_net": it.get("f72", 0),
                "medium_net": it.get("f78", 0),
                "small_net": it.get("f84", 0),
            })
        rows.append(row)

    return {"board_type": board_type, "period": period,
            "total": total, "rows": rows[:top_n]}


# ═══════════════════════════════════════════════════════════════════
# 全行业涨跌幅排名（东财）
# ═══════════════════════════════════════════════════════════════════

def industry_comparison(top_n: int = 20) -> dict:
    """全行业涨跌幅排名（东财行业板块，~100 个行业）。

    返回: {top: [{rank, name, change_pct, code, up_count, down_count, leader}],
           bottom: [...], total: int}
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1", "pz": "100", "po": "1", "np": "1",
        "fltt": "2", "invt": "2", "fid": "f3",
        "fs": "m:90+t:2",
        "fields": "f2,f3,f4,f12,f13,f14,f104,f105,f128,f136,f140,f141,f207",
    }
    r = em_get(url, params=params, headers={"User-Agent": UA}, timeout=15)
    d = r.json()
    items = d.get("data", {}).get("diff", [])
    if not items:
        return {"top": [], "bottom": [], "total": 0}

    rows = []
    for i, item in enumerate(items):
        rows.append({
            "rank": i + 1,
            "name": item.get("f14", ""),
            "change_pct": item.get("f3", 0),
            "code": item.get("f12", ""),
            "up_count": item.get("f104", 0),
            "down_count": item.get("f105", 0),
            "leader": item.get("f140", ""),
            "leader_change": item.get("f136", 0),
        })

    return {
        "top": rows[:top_n],
        "bottom": rows[-top_n:],
        "total": len(rows),
    }


# ═══════════════════════════════════════════════════════════════════
# 个股新闻（东财，辅助持仓穿透）
# ═══════════════════════════════════════════════════════════════════

def eastmoney_stock_news(code: str, page_size: int = 20) -> list:
    """东财个股新闻。

    code: 6 位股票代码。
    返回: [{date, title, source, url}]
    """
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    params = {
        "cb": "jQuery351005072532226693537_" + str(int(time.time() * 1000)),
        "param": '{"uid":"","keyword":"' + code + '","type":["cmsArticleWebOld"],'
                 '"client":"web","clientType":"web","clientVersion":"curr","param":{"cmsArticleWebOld":{"searchScope":"default",'
                 '"sort":"default","pageIndex":1,"pageSize":' + str(page_size) + ','
                 '"preTag":"<em>","postTag":"</em>"}}}',
        "_": str(int(time.time() * 1000)),
    }
    r = em_get(url, params=params, headers={"User-Agent": UA}, timeout=15)
    text = r.text
    # 去掉 JSONP 包裹
    start, end = text.find("("), text.rfind(")")
    if start == -1 or end == -1:
        return []
    import json as _json
    try:
        data = _json.loads(text[start + 1:end])
    except Exception:
        return []
    articles = (data.get("result", {}) or {}).get("cmsArticleWebOld", []) or []
    result = []
    for a in articles:
        result.append({
            "date": (a.get("date") or "")[:10],
            "title": a.get("title", "").replace("<em>", "").replace("</em>", ""),
            "source": a.get("mediaName", ""),
            "url": a.get("url", ""),
        })
    return result


if __name__ == "__main__":
    # 冒烟测试（需网络）
    print("=== 测试 stock_quote ===")
    try:
        q = stock_quote(["600519", "000300"])
        for code, v in q.items():
            print(f"  {v['name']}({code}): {v['price']} PE={v['pe_ttm']}")
    except Exception as e:
        print(f"  失败: {e}")
    print("=== 测试 board_fund_flow ===")
    try:
        d = board_fund_flow("industry", "today", 5)
        for r in d["rows"]:
            print(f"  {r['rank']}. {r['name']}: 主力{r['main_net']/1e8:.2f}亿 涨{r['change_pct']}%")
    except Exception as e:
        print(f"  失败: {e}")
