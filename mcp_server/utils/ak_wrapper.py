"""AKShare interface wrapper with TTL caching and graceful error handling.

Real AKShare API signatures (verified against akshare==1.18.78):
  fund_individual_basic_info_xq(symbol=)  → (N,2) item/value pairs
  fund_open_fund_info_em(symbol=, indicator="单位净值走势") → (N,3) 净值日期/单位净值/日增长率
  fund_portfolio_hold_em(symbol=, date="2026") → (N,7)
  fund_manager_em() → (35329,8) — no args, filter by 现任基金代码 column
  fund_announcement_report_em(symbol=) → (N,5)
  fund_name_em() → (27336,5) — no args, filter by 基金简称 column
  index_zh_a_hist(symbol=, period="daily", start_date=, end_date=) → (N,6)
"""

import time
import logging
from functools import wraps
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger("famas-mcp")

_cache: dict[str, tuple[float, Any]] = {}
_cache_hits = 0
_cache_misses = 0


def _cache_key(func_name: str, *args, **kwargs) -> str:
    return f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"


def cached(ttl_seconds: int):
    """Decorator: cache function result for ttl_seconds."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global _cache_hits, _cache_misses
            key = _cache_key(func.__name__, *args, **kwargs)
            now = time.time()
            if key in _cache:
                expiry, value = _cache[key]
                if now < expiry:
                    _cache_hits += 1
                    return value
            _cache_misses += 1
            result = func(*args, **kwargs)
            _cache[key] = (now + ttl_seconds, result)
            return result
        return wrapper
    return decorator


def safe_date(dt) -> Optional[str]:
    """Convert to YYYY-MM-DD string."""
    if dt is None: return None
    if isinstance(dt, str): return dt[:10] if len(dt) >= 10 else dt
    if isinstance(dt, datetime): return dt.strftime("%Y-%m-%d")
    try: return str(dt)[:10]
    except: return str(dt)


def safe_float(value, default: float = 0.0) -> float:
    """Convert to float, returning default on failure."""
    if value is None: return default
    try: return float(value)
    except (ValueError, TypeError): return default


# ═══════════════════════════════════════════════════════════════════
# Tool 1: fund_basic_info
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=3600)
def fetch_fund_basic_info(fund_code: str) -> dict:
    """Returns (14,2) key-value DataFrame as a flat dict {item: value}."""
    import akshare as ak
    try:
        df = ak.fund_individual_basic_info_xq(symbol=fund_code)
        if df is None or df.empty:
            return {"error": True, "error_code": "NOT_FOUND", "message": f"Fund {fund_code} not found"}
        # Convert item/value pairs to flat dict
        result = {}
        for _, row in df.iterrows():
            key = str(row["item"]).strip()
            val = row["value"]
            result[key] = val
        return result
    except Exception as e:
        logger.warning(f"fund_individual_basic_info_xq {fund_code}: {e}")
        return {"error": True, "error_code": "AKSHARE_ERROR", "message": str(e)[:200]}


@cached(ttl_seconds=3600)
def search_funds_by_keyword(keyword: str) -> list:
    """Search fund_name_em (27336 rows) by 基金简称. Returns list of rows."""
    import akshare as ak
    try:
        df = ak.fund_name_em()
        mask = df["基金简称"].str.contains(keyword, na=False)
        matched = df[mask]
        return matched.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"fund_name_em keyword '{keyword}': {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 2: fund_nav_history
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=1800)
def fetch_nav_history(fund_code: str, days: int) -> list:
    """Returns list of {净值日期, 单位净值, 日增长率} dicts."""
    import akshare as ak
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df is None or df.empty:
            return []
        return df.tail(days).to_dict(orient="records")
    except Exception as e:
        logger.warning(f"fund_open_fund_info_em {fund_code}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 3: fund_holdings
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=86400)
def fetch_holdings(fund_code: str, date: str = "2026") -> list:
    """Returns list of {序号, 股票代码, 股票名称, 占净值比例, 持股数, 持仓市值, 季度}."""
    import akshare as ak
    try:
        df = ak.fund_portfolio_hold_em(symbol=fund_code, date=date)
        if df is None or df.empty:
            return []
        return df.head(10).to_dict(orient="records")
    except Exception as e:
        logger.warning(f"fund_portfolio_hold_em {fund_code}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 4: fund_manager_info
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=3600)
def _get_all_managers() -> list:
    """Load the full manager table once and cache."""
    import akshare as ak
    try:
        df = ak.fund_manager_em()
        return df.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"fund_manager_em: {e}")
        return []


def fetch_manager_by_fund(fund_code: str) -> list:
    """Filter full manager table by 现任基金代码 containing fund_code."""
    all_managers = _get_all_managers()
    results = []
    for r in all_managers:
        codes_raw = str(r.get("现任基金代码", "") if "现任基金代码" in r else r.get("现任基金", ""))
        if fund_code in codes_raw:
            results.append(r)
    return results


def fetch_manager_by_name(manager_name: str) -> list:
    """Filter full manager table by 姓名 containing manager_name."""
    all_managers = _get_all_managers()
    results = []
    for r in all_managers:
        name_raw = str(r.get("姓名", ""))
        if manager_name in name_raw:
            results.append(r)
    return results


# ═══════════════════════════════════════════════════════════════════
# Tool 5: index_data
# ═══════════════════════════════════════════════════════════════════

INDEX_SYMBOL_MAP = {
    "000300": "000300",
    "000905": "000905",
    "399006": "399006",
}

HSTECH_MAP = {"HSTECH": "恒生科技"}  # handled separately

@cached(ttl_seconds=1800)
def fetch_a_share_index(index_code: str, start_date: str, end_date: str) -> list:
    """Fetch A-share index via index_zh_a_hist. start_date/end_date in 20260701 format."""
    import akshare as ak
    try:
        s = start_date.replace("-", "") if "-" in start_date else start_date
        e = end_date.replace("-", "") if "-" in end_date else end_date
        df = ak.index_zh_a_hist(symbol=index_code, period="daily", start_date=s, end_date=e)
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"index_zh_a_hist {index_code}: {e}")
        return []


@cached(ttl_seconds=1800)
def fetch_hstech_index(start_date: str, end_date: str) -> list:
    """Fetch Hang Seng TECH via stock_hk_index_daily_em."""
    import akshare as ak
    try:
        df = ak.stock_hk_index_daily_em(symbol="恒生科技")
        if df is None or df.empty:
            return []
        # Filter by date
        if "date" in df.columns:
            df["date"] = df["date"].astype(str)
            mask = (df["date"] >= start_date) & (df["date"] <= end_date)
            df = df[mask]
        return df.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"stock_hk_index_daily_em: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 6: fund_announcements
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=1800)
def fetch_announcements(fund_code: str) -> list:
    """fetch fund_announcement_report_em. Returns list of dicts."""
    import akshare as ak
    try:
        df = ak.fund_announcement_report_em(symbol=fund_code)
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"fund_announcement_report_em {fund_code}: {e}")
        return []


def get_cache_stats() -> dict:
    """Return cache hit/miss statistics."""
    total = _cache_hits + _cache_misses
    hit_rate = round(_cache_hits / total * 100, 1) if total > 0 else 0
    return {
        "cache_entries": len(_cache),
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "hit_rate_pct": hit_rate,
    }


# ═══════════════════════════════════════════════════════════════════
# Tool 7: realtime_index_spot (实时指数行情)
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=30)
def fetch_realtime_index_spot(index_codes: Optional[str] = None, top_n: int = 15) -> list:
    """Fetch realtime index spot data from EastMoney push2 service."""
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    proxies = {'http': None, 'https': None}
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': 1, 'pz': max(top_n, 30), 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2, 'invt': 2, 'fid': 'f3',
        'fs': 'm:1 t:1,m:0 t:5',
        'fields': 'f12,f14,f2,f3,f4,f6',
    }
    try:
        r = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=5)
        raw = r.json().get('data', {}).get('diff', [])
        results = []
        filter_codes = [c.strip() for c in index_codes.split(',')] if index_codes else None

        for item in raw:
            code = str(item.get('f12', ''))
            name = str(item.get('f14', ''))
            if filter_codes and not any(fc in code or fc in name for fc in filter_codes):
                continue
            close = safe_float(item.get('f2'))
            chg_pct = safe_float(item.get('f3'))
            chg_amt = safe_float(item.get('f4'))
            vol_amt = safe_float(item.get('f6'))
            vol_yi = round(vol_amt / 1e8, 2) if vol_amt else 0.0

            results.append({
                "index_code": code,
                "index_name": name,
                "latest_price": close,
                "change_pct": chg_pct,
                "change_amount": chg_amt,
                "turnover_yi": vol_yi,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if len(results) >= top_n:
                break
        return results
    except Exception as e:
        logger.warning(f"fetch_realtime_index_spot: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 8: realtime_etf_spot (实时 ETF 行情与折溢价)
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=30)
def fetch_realtime_etf_spot(etf_code_or_kw: Optional[str] = None, category: Optional[str] = None, top_n: int = 15) -> list:
    """Fetch realtime ETF spot data including IOPV / premium estimation."""
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    proxies = {'http': None, 'https': None}
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': 1, 'pz': 50, 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2, 'invt': 2, 'fid': 'f6', # 按成交额排序
        'fs': 'b:MK0021+b:MK0022+b:MK0023',
        'fields': 'f12,f14,f2,f3,f4,f5,f6,f8,f15,f16,f17,f18,f23',
    }
    try:
        r = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=5)
        raw = r.json().get('data', {}).get('diff', [])
        results = []

        kw = str(etf_code_or_kw).strip() if etf_code_or_kw else None
        cat_kw = str(category).strip() if category else None

        for item in raw:
            code = str(item.get('f12', ''))
            name = str(item.get('f14', ''))
            if kw and (kw not in code and kw not in name):
                continue
            if cat_kw and cat_kw not in name:
                continue

            price = safe_float(item.get('f2'))
            chg_pct = safe_float(item.get('f3'))
            turnover_rate = safe_float(item.get('f8'))
            amount = safe_float(item.get('f6'))
            amount_yi = round(amount / 1e8, 2) if amount else 0.0
            iopv = safe_float(item.get('f23'))

            # Estimate premium/discount pct if IOPV available and valid
            premium_pct = 0.0
            premium_status = "正常"
            if iopv and iopv > 0 and price:
                premium_pct = round(((price - iopv) / iopv) * 100, 2)
                if premium_pct > 1.5:
                    premium_status = "高溢价风险"
                elif premium_pct < -1.5:
                    premium_status = "折价吸引"

            results.append({
                "etf_code": code,
                "etf_name": name,
                "latest_price": price,
                "change_pct": chg_pct,
                "turnover_rate_pct": turnover_rate,
                "amount_yi": amount_yi,
                "iopv": iopv,
                "premium_pct": premium_pct,
                "premium_status": premium_status,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if len(results) >= top_n:
                break
        return results
    except Exception as e:
        logger.warning(f"fetch_realtime_etf_spot: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# Tool 9: capital_flow_data (板块/资金流向)
# ═══════════════════════════════════════════════════════════════════

@cached(ttl_seconds=60)
def fetch_capital_flow(flow_type: str = "all", top_n: int = 10) -> dict:
    """Fetch realtime sector capital flows and Northbound/Southbound flow."""
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    proxies = {'http': None, 'https': None}

    result = {
        "flow_type": flow_type,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sector_flows": [],
        "northbound_flow": {},
    }

    # 1. Sector Capital Flows
    if flow_type in ("sector", "all"):
        url_sec = 'http://push2.eastmoney.com/api/qt/clist/get'
        params_sec = {
            'pn': 1, 'pz': max(top_n * 2, 30), 'po': 1, 'np': 1,
            'ut': 'b2884c39002816ce865ee8f47db4f2b9',
            'fltt': 2, 'invt': 2, 'fid': 'f62', # 按主力净流入额排序
            'fs': 'm:90 t:2',
            'fields': 'f12,f14,f2,f3,f62,f184',
        }
        try:
            r = requests.get(url_sec, params=params_sec, headers=headers, proxies=proxies, timeout=5)
            raw = r.json().get('data', {}).get('diff', [])
            sector_list = []
            for item in raw[:top_n]:
                flow_raw = safe_float(item.get('f62'))
                flow_yi = round(flow_raw / 1e8, 2) if flow_raw else 0.0
                sector_list.append({
                    "sector_code": str(item.get('f12', '')),
                    "sector_name": str(item.get('f14', '')),
                    "sector_change_pct": safe_float(item.get('f3')),
                    "main_net_inflow_yi": flow_yi,
                    "main_net_ratio_pct": safe_float(item.get('f184')),
                })
            result["sector_flows"] = sector_list
        except Exception as e:
            logger.warning(f"fetch_capital_flow sector: {e}")

    # 2. Northbound / Southbound Flow
    if flow_type in ("northbound", "all"):
        url_kamt = 'http://push2.eastmoney.com/api/qt/kamt/get'
        params_kamt = {'fields1': 'f1,f2,f3,f4', 'fields2': 'f51,f52,f53,f54,f55,f56'}
        try:
            r = requests.get(url_kamt, params=params_kamt, headers=headers, proxies=proxies, timeout=5)
            data_kamt = r.json().get('data', {})
            hk2sh = data_kamt.get('hk2sh', {})
            hk2sz = data_kamt.get('hk2sz', {})
            sh_amt = safe_float(hk2sh.get('dayNetAmtIn'))
            sz_amt = safe_float(hk2sz.get('dayNetAmtIn'))
            total_north_yi = round((sh_amt + sz_amt) / 10000.0, 2) if (sh_amt is not None and sz_amt is not None) else 0.0

            result["northbound_flow"] = {
                "沪股通净流入_万元": sh_amt,
                "深股通净流入_万元": sz_amt,
                "北向资金合计净流入_亿元": total_north_yi,
                "status": "净流入" if total_north_yi >= 0 else "净流出"
            }
        except Exception as e:
            logger.warning(f"fetch_capital_flow northbound: {e}")

    return result


# ═══════════════════════════════════════════════════════════════════
# Tool 10: push_notification (消息推送通道)
# ═══════════════════════════════════════════════════════════════════

def send_webhook_push(
    webhook_url: str,
    channel: Optional[str] = None,
    title: str = "FAMAS 基金系统预警通知",
    content: str = "",
    msg_type: str = "alert",
    secret: Optional[str] = None
) -> dict:
    """Send alert or report push notification via Webhook (DingTalk, WeCom, Feishu, Generic)."""
    import requests, time, hmac, hashlib, base64, urllib.parse

    target_channel = channel.lower() if channel else "generic"
    # Auto-detect channel from URL if channel is generic or missing
    if "dingtalk.com" in webhook_url:
        target_channel = "dingtalk"
    elif "weixin.qq.com" in webhook_url:
        target_channel = "wecom"
    elif "feishu.cn" in webhook_url or "larksuite.com" in webhook_url:
        target_channel = "feishu"

    headers = {'Content-Type': 'application/json'}
    proxies = {'http': None, 'https': None}
    final_url = webhook_url

    # DingTalk signature handling
    if target_channel == "dingtalk" and secret:
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        sep = "&" if "?" in final_url else "?"
        final_url = f"{final_url}{sep}timestamp={timestamp}&sign={sign}"

    # Build payload by channel type
    if target_channel == "dingtalk":
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{content}\n\n> *推送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | FAMAS系统*"
            }
        }
    elif target_channel == "wecom":
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"### {title}\n\n{content}\n\n> 推送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }
    elif target_channel == "feishu":
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "red" if msg_type == "alert" else "blue"
                },
                "elements": [
                    {"tag": "markdown", "content": content},
                    {"tag": "note", "elements": [{"tag": "plain_text", "content": f"FAMAS 基金智选分析系统 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}]}
                ]
            }
        }
    else:
        # Generic JSON payload
        payload = {
            "title": title,
            "content": content,
            "msg_type": msg_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "FAMAS-Skill"
        }

    try:
        r = requests.post(final_url, json=payload, headers=headers, proxies=proxies, timeout=8)
        is_ok = r.status_code in (200, 201)
        res_text = r.text[:200]
        logger.info(f"Webhook push to {target_channel}: status={r.status_code}")
        return {
            "status": "success" if is_ok else "failed",
            "channel": target_channel,
            "http_status": r.status_code,
            "response": res_text,
            "delivered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.warning(f"Webhook push failed: {e}")
        return {
            "status": "failed",
            "channel": target_channel,
            "error": str(e)[:200],
            "delivered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
                       