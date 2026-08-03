#!/usr/bin/env python3
"""腾讯行情实时获取器（盘中实时涨跌）

用法:
  python3 tencent_quote.py 600519   # 查询贵州茅台
  python3 tencent_quote.py sh600519 sz000001 sh000300
  python3 tencent_quote.py --market  # 查询关键指数
"""
import os, sys, requests, json
from datetime import datetime

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 代码前缀映射
def normalize_code(code):
    code = str(code).strip()
    if code.startswith(('sh','sz','bj')):
        return code
    if code.startswith(('6','9','5')):  # 上海: 6开头股票, 5开头ETF
        return f"sh{code}"
    if code.startswith(('0','3','2')):  # 深圳
        return f"sz{code}"
    if code == "000300": return "sh000300"  # 沪深300
    if code == "000905": return "sh000905"  # 中证500
    if code == "399006": return "sz399006"  # 创业板指
    if code == "399001": return "sz399001"  # 深证成指
    return f"sh{code}"

def fetch_quote(code):
    """获取单只股票/指数实时行情"""
    q = normalize_code(code)
    url = f"https://qt.gtimg.cn/q={q}"
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        text = r.text
        if '~' not in text or 'v_pv_none_match' in text:
            return None, "无匹配数据"
        parts = text.split('~')
        if len(parts) < 35:
            return None, "数据格式异常"
        return {
            "code": parts[2],
            "name": parts[1],
            "price": float(parts[3]),
            "prev_close": float(parts[4]),
            "open": float(parts[5]),
            "volume": parts[6],
            "high": float(parts[33]),
            "low": float(parts[34]),
            "change": float(parts[31]),
            "change_pct": float(parts[32]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }, None
    except Exception as e:
        return None, str(e)[:80]

def fetch_batch(codes):
    """批量获取"""
    results = {}
    for code in codes:
        data, err = fetch_quote(code)
        if data:
            results[code] = data
        else:
            results[code] = {"error": err}
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    if sys.argv[1] == "--market":
        codes = ["sh000300","sh000905","sz399006","sz399001"]
    else:
        codes = sys.argv[1:]
    results = fetch_batch(codes)
    for code, data in results.items():
        if "error" in data:
            print(f"{code}: ❌ {data['error']}")
        else:
            print(f"{data['name']}({data['code']}): 现价{data['price']} 涨跌{data['change_pct']}%")
