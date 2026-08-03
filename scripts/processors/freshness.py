#!/usr/bin/env python3
"""数据新鲜度判定模块

核心铁律: 旧数据不能冒充新数据。
预期交易日应该有数据，但数据源还没给 -> 返回 pending（待更新）。
"""
import os, sys, json
from datetime import datetime, timedelta

def is_weekend(d):
    return d.weekday() >= 5

def get_latest_trading_day(today=None):
    today = today or datetime.now().date()
    d = today
    while is_weekend(d):
        d -= timedelta(days=1)
    return d

def get_expected_update_time(data_type):
    times = {
        "intraday": "盘中实时",
        "daily": "15:00",
        "fund_nav": "20:00",
        "fund_flow": "15:30",
        "financial": "季报期",
    }
    return times.get(data_type, "未知")

def judge_freshness(data_date, data_type, today=None):
    today = today or datetime.now().date()
    if isinstance(data_date, str):
        data_date = datetime.strptime(data_date[:10], "%Y-%m-%d").date()
    latest_td = get_latest_trading_day(today)
    if data_type == "intraday":
        if data_date == today:
            return "fresh"
        return "stale"
    if data_type in ("daily", "fund_nav", "fund_flow"):
        if data_date == latest_td:
            return "fresh"
        if data_date < latest_td:
            return "stale"
        return "pending"
    if data_type == "financial":
        return "fresh"
    return "pending"

def build_response(data, data_type, data_date=None, data_source="unknown"):
    if data is None:
        return {
            "data": None,
            "data_date": data_date,
            "freshness": "pending",
            "display": "待更新",
            "data_source": data_source,
            "expected_update": get_expected_update_time(data_type),
        }
    freshness = judge_freshness(data_date, data_type)
    return {
        "data": data,
        "data_date": data_date,
        "freshness": freshness,
        "display": "待更新" if freshness != "fresh" else None,
        "data_source": data_source,
        "expected_update": get_expected_update_time(data_type),
    }

if __name__ == "__main__":
    today = datetime.now().date()
    print(f"今天: {today}")
    print(f"最近交易日: {get_latest_trading_day(today)}")
    for date, dtype, desc in [
        ("2026-08-03", "intraday", "今日盘中"),
        ("2026-07-31", "daily", "上周五日线"),
        ("2026-07-31", "fund_nav", "上周五净值"),
        ("2026-08-03", "fund_flow", "今日资金"),
    ]:
        print(f"{desc}: {judge_freshness(date, dtype)}")
