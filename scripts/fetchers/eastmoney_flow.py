#!/usr/bin/env python3
"""东财 push2delay 实时资金流获取器（京东金融同源）

数据源: https://push2delay.eastmoney.com (延迟行情, 稳定可用)
提供: 行业/概念板块当日主力净流入 + 个股资金流

用法:
  python3 eastmoney_flow.py --industry   # 行业板块资金流TOP
  python3 eastmoney_flow.py --concept    # 概念板块资金流TOP
  python3 eastmoney_flow.py --sector 白酒 # 查特定板块
  python3 eastmoney_flow.py --stock 600519 # 个股资金流
"""
import os, sys, requests, json
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(k, None)
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Referer":"https://show.jd.com/"}
BASE = "https://push2delay.eastmoney.com/api/qt/clist/get"

def sector_flow(sector_type="行业", top=20):
    """板块资金流排名。sector_type: 行业/概念"""
    fs = "m:90+t:2+f:!50" if sector_type=="行业" else "m:90+t:3+f:!50"
    try:
        r = requests.get(BASE,
            params={"fid":"f62","po":"1","pz":str(top),"pn":"1","np":"1","fltt":"2","invt":"2",
                    "fs":fs,"fields":"f12,f14,f2,f3,f62,f184"},
            headers=UA, timeout=10)
        d = r.json()
        diffs = d.get("data",{}).get("diff",[])
        if isinstance(diffs, dict): diffs = list(diffs.values())
        result = []
        for x in diffs:
            result.append({
                "code": x.get("f12"), "name": x.get("f14"),
                "change_pct": x.get("f3"), "main_flow_yi": round(x.get("f62",0)/1e8,2),
                "flow_ratio": x.get("f184"),
            })
        return result, None
    except Exception as e:
        return None, str(e)[:80]

def stock_flow(secid):
    """个股资金流历史"""
    try:
        r = requests.get("https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get",
            params={"secid":secid,"fields1":"f1,f2,f3","fields2":"f51,f52,f53,f54,f55",
                    "klt":"101","lmt":"5"},
            headers=UA, timeout=10)
        d = r.json()
        klines = d.get("data",{}).get("klines",[])
        result = []
        for k in klines:
            parts = k.split(",")
            # 日期,主力,小单,中单,大单
            result.append({"date":parts[0], "main_flow":round(float(parts[1])/1e8,2),
                          "small":round(float(parts[2])/1e8,2),"medium":round(float(parts[3])/1e8,2),
                          "large":round(float(parts[4])/1e8,2)})
        return result, None
    except Exception as e:
        return None, str(e)[:80]

def search_sector(keyword):
    """搜索板块并返回资金流"""
    for st in ["行业","概念"]:
        result, err = sector_flow(st, top=100)
        if result:
            for x in result:
                if keyword in x["name"]:
                    return x, st
    return None, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "--industry":
        result, err = sector_flow("行业")
        print(f"{'板块':<16}{'涨跌%':<8}{'主力净流入(亿)':<12}")
        for x in result:
            print(f"{x['name']:<16}{x['change_pct']:<8}{x['main_flow_yi']:+.2f}")
    elif cmd == "--concept":
        result, err = sector_flow("概念")
        print(f"{'板块':<16}{'涨跌%':<8}{'主力净流入(亿)':<12}")
        for x in result:
            print(f"{x['name']:<16}{x['change_pct']:<8}{x['main_flow_yi']:+.2f}")
    elif cmd == "--sector":
        kw = sys.argv[2]
        x, st = search_sector(kw)
        if x: print(f"{x['name']}({st}): 涨跌{x['change_pct']}% 主力{x['main_flow_yi']:+.2f}亿")
        else: print(f"未找到板块: {kw}")
    elif cmd == "--stock":
        code = sys.argv[2]
        secid = f"1.{code}" if code.startswith(('6','9','5')) else f"0.{code}"
        result, err = stock_flow(secid)
        if result:
            for x in result:
                print(f"{x['date']}: 主力{x['main_flow']:+.2f}亿 大单{x['large']:+.2f}亿")
