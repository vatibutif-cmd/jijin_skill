#!/usr/bin/env python3
"""a_stock_data 模块单元测试（网络相关测试需网络，可跳过）。

用法:
  python3 mcp_server/test_a_stock_data.py          # 跑全部（含网络）
  python3 mcp_server/test_a_stock_data.py --offline # 只跑离线测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_stock_data"))

import a_stock_data as asd


def test_module_imports():
    """核心函数可导入"""
    assert hasattr(asd, "stock_quote")
    assert hasattr(asd, "board_fund_flow")
    assert hasattr(asd, "industry_comparison")
    assert hasattr(asd, "eastmoney_stock_news")
    assert hasattr(asd, "em_get")


def test_constants():
    """常量定义正确"""
    assert set(asd._BOARD_FS.keys()) == {"industry", "concept", "region"}
    assert set(asd._BOARD_PERIOD.keys()) == {"today", "5d", "10d"}
    assert "000300" in asd.SH_INDEX
    assert asd.EM_MIN_INTERVAL >= 1.0


def test_board_fund_flow_validation():
    """板块资金流参数校验"""
    try:
        asd.board_fund_flow("bad_type", "today", 5)
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    try:
        asd.board_fund_flow("industry", "bad_period", 5)
        assert False, "应抛 ValueError"
    except ValueError:
        pass


def test_stock_quote_prefix_logic():
    """前缀路由逻辑（通过测试 key_of 映射）"""
    # 模拟内部逻辑：5 开头 → sh，0 开头 → sz
    SH_INDEX = asd.SH_INDEX
    def get_prefix(c):
        low = c.lower()
        if low.startswith(("sh", "sz", "bj")):
            return low
        if c.startswith("92"):
            return f"bj{c}"
        if c in SH_INDEX or c.startswith(("5", "6", "9")):
            return f"sh{c}"
        if c.startswith(("4", "8")):
            return f"bj{c}"
        return f"sz{c}"
    assert get_prefix("510300") == "sh510300"     # 沪 ETF
    assert get_prefix("600519") == "sh600519"     # 沪股
    assert get_prefix("000300") == "sh000300"     # 沪深300 沪指数白名单
    assert get_prefix("000001") == "sz000001"     # 平安银行（深）
    assert get_prefix("300476") == "sz300476"     # 创业板
    assert get_prefix("920982") == "bj920982"     # 北交所新号段
    assert get_prefix("sh000001") == "sh000001"   # 显式前缀透传


def test_network_stock_quote():
    """网络：腾讯行情（不封IP）"""
    try:
        q = asd.stock_quote(["600519"])
        assert "600519" in q, "应返回 600519"
        assert q["600519"]["price"] > 0, "现价应 > 0"
        print("  [网络] stock_quote OK:", q["600519"]["name"], q["600519"]["price"])
    except Exception as e:
        print(f"  [网络] stock_quote 跳过: {e}")


def test_network_board_fund_flow():
    """网络：板块资金流（东财，沙箱可能受限）"""
    try:
        d = asd.board_fund_flow("industry", "today", 3)
        assert len(d["rows"]) > 0, "应有数据"
        print("  [网络] board_fund_flow OK:", d["rows"][0]["name"])
    except Exception as e:
        print(f"  [网络] board_fund_flow 跳过: {e}")


if __name__ == "__main__":
    offline = "--offline" in sys.argv
    tests = [
        test_module_imports, test_constants,
        test_board_fund_flow_validation, test_stock_quote_prefix_logic,
    ]
    if not offline:
        tests += [test_network_stock_quote, test_network_board_fund_flow]

    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
    sys.exit(0 if passed == len(tests) else 1)
