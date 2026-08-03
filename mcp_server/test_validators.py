#!/usr/bin/env python3
"""FAMAS MCP Server 单元测试 — validators + server 工具逻辑。

用法:
  python3 -m pytest mcp_server/test_validators.py -v
  或
  python3 mcp_server/test_validators.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils"))

from validators import (
    check_fund_code, check_keyword, check_top_n, check_days,
    check_index, check_date, check_ann_kw, check_max_results,
    check_flow_type, check_channel, check_webhook_url, error_resp,
)


def test_fund_code():
    assert check_fund_code("005911") == (True, "")
    assert check_fund_code("12345")[0] is False   # 5 位
    assert check_fund_code("1234567")[0] is False  # 7 位
    assert check_fund_code("abc123")[0] is False   # 非数字
    assert check_fund_code("")[0] is False          # 空
    assert check_fund_code(None)[0] is False        # None


def test_keyword():
    assert check_keyword("科技") == (True, "")
    assert check_keyword("")[0] is False
    assert check_keyword("a" * 21)[0] is False      # 超长
    assert check_keyword(None)[0] is False


def test_top_n():
    assert check_top_n(10) == (True, "")
    assert check_top_n(0)[0] is False
    assert check_top_n(21)[0] is False
    assert check_top_n("5")[0] is False             # 非 int


def test_days():
    assert check_days(252) == (True, "")
    assert check_days(0)[0] is False
    assert check_days(1096)[0] is False             # 超上限
    assert check_days(100, hi=365) == (True, "")    # 自定义上限内
    assert check_days(366, hi=365)[0] is False      # 超自定义上限


def test_index():
    assert check_index("000300") == (True, "")
    assert check_index("HSTECH") == (True, "")
    assert check_index("999999")[0] is False


def test_date():
    assert check_date("2026-07-01", "start_date") == (True, "")
    assert check_date(None, "start_date") == (True, "")   # 可选
    assert check_date("2026/07/01", "start_date")[0] is False
    assert check_date("2026-7-1", "start_date")[0] is False


def test_ann_kw():
    assert check_ann_kw("经理变更") == (True, "")
    assert check_ann_kw(None) == (True, "")          # 可选
    assert check_ann_kw("清盘") == (True, "")
    assert check_ann_kw("随便词")[0] is False


def test_max_results():
    assert check_max_results(15) == (True, "")
    assert check_max_results(0)[0] is False
    assert check_max_results(31)[0] is False


def test_flow_type():
    assert check_flow_type("sector") == (True, "")
    assert check_flow_type("all") == (True, "")
    assert check_flow_type("bad")[0] is False


def test_channel():
    assert check_channel("dingtalk") == (True, "")
    assert check_channel("WECOM") == (True, "")      # 大小写
    assert check_channel(None) == (True, "")          # 可选
    assert check_channel("bad")[0] is False


def test_webhook_url():
    assert check_webhook_url("https://oapi.dingtalk.com/robot/send?access_token=x") == (True, "")
    assert check_webhook_url("")[0] is False
    assert check_webhook_url(None)[0] is False
    assert check_webhook_url("ftp://example.com")[0] is False


def test_error_resp():
    r = error_resp("INVALID_INPUT", "bad code", "005911")
    assert r["error"] is True
    assert r["error_code"] == "INVALID_INPUT"
    assert r["fund_code"] == "005911"
    # 无 fund_code
    r2 = error_resp("NOT_FOUND", "no data")
    assert "fund_code" not in r2


if __name__ == "__main__":
    # 简易 runner（无 pytest 时也能跑）
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print("  PASS " + t.__name__)
            passed += 1
        except AssertionError as e:
            print("  FAIL " + t.__name__ + ": " + str(e))
    print("\n" + str(passed) + "/" + str(len(tests)) + " 通过")
    sys.exit(0 if passed == len(tests) else 1)
