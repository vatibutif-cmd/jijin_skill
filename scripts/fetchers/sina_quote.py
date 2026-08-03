#!/usr/bin/env python3
"""新浪行情获取器（稳定免费源）

用法:
  python3 sina_quote.py 600519         # 单只
  python3 sina_quote.py 600519,000858  # 批量
  python3 sina_quote.py --market       # 关键指数
"""
import os, sys, requests, re
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(k, None)
UA = {"User-Agent":"Mozilla/5.0","Referer":"https://finance.sina.com.cn"}

def norm(code):
    code=str(code).strip()
    if code.startswith(('sh','sz','bj')): return code
    if code.startswith(('6','9','5')): return f"sh{code}"
    return f"sz{code}"

def fetch(codes):
    """批量获取行情"""
    if isinstance(codes, str): codes = [codes]
    codes = [norm(c) for c in codes]
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    try:
        r = requests.get(url, headers=UA, timeout=8)
        if r.status_code != 200: return {}
        text = r.content.decode('gbk')
        result = {}
        for line in text.strip().split('\n'):
            m = re.match(r'var hq_str_(\w+)="([^"]+)"', line)
            if m:
                code, data = m.group(1), m.group(2).split(',')
                if len(data) > 3:
                    result[code] = {
                        "name": data[0], "open": data[1], "prev_close": data[2],
                        "price": data[3], "high": data[4], "low": data[5],
                        "volume": data[8],
                    }
        return result
    except Exception as e:
        return {"error": str(e)[:60]}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    if sys.argv[1] == "--market":
        codes = ["sh000001","sz399001","sz399006","sh000300"]
    else:
        codes = sys.argv[1].split(',')
    result = fetch(codes)
    for code, d in result.items():
        if "error" in d: print(f"{code}: ❌ {d['error']}")
        else:
            chg = (float(d['price'])-float(d['prev_close']))/float(d['prev_close'])*100
            print(f"{d['name']}({code}): 现价{d['price']} 涨跌{chg:+.2f}%")
