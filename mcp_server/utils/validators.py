"""Input validators — shared by all 6 tools."""

import re
from typing import Optional, Tuple

FUND_CODE_RE = re.compile(r"^\d{6}$")
INDEX_ENUM = {"000300", "000905", "399006", "HSTECH"}
ANN_KW_ENUM = {"经理变更", "清盘", "大额赎回", "费率", "分红", "限购", "终止"}


def check_fund_code(fc: Optional[str]) -> Tuple[bool, str]:
    if not fc: return False, "fund_code is required"
    if not FUND_CODE_RE.match(str(fc)):
        return False, f"fund_code must be 6 digits, got '{fc}'"
    return True, ""


def check_keyword(kw: Optional[str]) -> Tuple[bool, str]:
    if not kw: return False, "keyword is required"
    s = str(kw).strip()
    if len(s) < 1 or len(s) > 20:
        return False, f"keyword must be 1-20 chars, got {len(s)}"
    return True, ""


def check_index(ic: str) -> Tuple[bool, str]:
    if ic not in INDEX_ENUM:
        return False, f"index_code must be one of {sorted(INDEX_ENUM)}, got '{ic}'"
    return True, ""


def check_date(fmt: Optional[str], label: str) -> Tuple[bool, str]:
    if fmt is None: return True, ""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(fmt)):
        return False, f"{label} must be YYYY-MM-DD, got '{fmt}'"
    return True, ""


def check_days(d: int, hi: int = 1095) -> Tuple[bool, str]:
    if not isinstance(d, int) or d < 1 or d > hi:
        return False, f"days must be 1-{hi}, got {d}"
    return True, ""


def check_top_n(n: int) -> Tuple[bool, str]:
    if not isinstance(n, int) or n < 1 or n > 20:
        return False, f"top_n must be 1-20, got {n}"
    return True, ""


def check_ann_kw(kw: Optional[str]) -> Tuple[bool, str]:
    if kw is not None and str(kw).strip() not in ANN_KW_ENUM:
        return False, f"keyword must be one of {sorted(ANN_KW_ENUM)}, got '{kw}'"
    return True, ""


def check_max_results(mr: int) -> Tuple[bool, str]:
    if not isinstance(mr, int) or mr < 1 or mr > 30:
        return False, f"max_results must be 1-30, got {mr}"
    return True, ""


FLOW_TYPE_ENUM = {"sector", "northbound", "all"}
CHANNEL_ENUM = {"dingtalk", "wecom", "feishu", "generic"}


def check_flow_type(ft: str) -> Tuple[bool, str]:
    if str(ft).strip() not in FLOW_TYPE_ENUM:
        return False, f"flow_type must be one of {sorted(FLOW_TYPE_ENUM)}, got '{ft}'"
    return True, ""


def check_channel(ch: Optional[str]) -> Tuple[bool, str]:
    if ch is not None and str(ch).strip().lower() not in CHANNEL_ENUM:
        return False, f"channel must be one of {sorted(CHANNEL_ENUM)}, got '{ch}'"
    return True, ""


def check_webhook_url(url: Optional[str]) -> Tuple[bool, str]:
    if not url:
        return False, "webhook_url is required"
    if not (str(url).startswith("http://") or str(url).startswith("https://")):
        return False, f"webhook_url must start with http:// or https://, got '{url}'"
    return True, ""


def error_resp(code: str, msg: str, fund_code: str | None = None) -> dict:
    r = {"error": True, "error_code": code, "message": msg}
    if fund_code: r["fund_code"] = fund_code
    return r
