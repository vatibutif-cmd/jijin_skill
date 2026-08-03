#!/usr/bin/env python3
"""计算 RSI(14) 技术指标工具

用法:
  python3 calc_rsi.py <净值CSV或JSON文件路径> [周期]
  python3 calc_rsi.py --etfirst <基金代码>   # 从 etfirst 拉取

数据格式: 支持 CSV(列: date,close) 或 从 etfirst 输出的 JSON
"""
import sys, os, json, csv, glob, subprocess

def calc_rsi(closes, period=14):
    """Wilder 平滑 RSI 计算"""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def from_csv(path, period=14):
    closes = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ('close', 'closePrice', 'nav', '单位净值'):
                if k in row and row[k]:
                    try:
                        closes.append(float(row[k]))
                        break
                    except: pass
    return calc_rsi(closes, period)

def from_etfirst(code, period=14):
    """从 etfirst otc-detail 拉取净值序列计算"""
    # 尝试用已登录的 etfirst
    r = subprocess.run(
        ['etfirst', '--json', 'otc-detail', 'all', '--product-code', str(code), '--date-range', '250'],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return None, "etfirst 调用失败"
    try:
        d = json.loads(r.stdout)
    except:
        return None, "JSON 解析失败"
    results = d.get('results', {})
    tr = results.get('getReturnTrendList', {})
    series = None
    if isinstance(tr, dict):
        for k, v in tr.items():
            if isinstance(v, list) and v:
                series = v
                break
    if not series:
        return None, "无净值序列"
    closes = []
    for x in series:
        try:
            closes.append(float(x.get('closePrice')))
        except:
            continue
    return calc_rsi(closes, period), None

def rsi_signal(rsi):
    """RSI 信号解读"""
    if rsi is None: return "无数据"
    if rsi < 20: return "极度超卖(0-20) → 超跌反弹机会，+5分"
    if rsi < 30: return "超卖(20-30) → 接近买点，+3分"
    if rsi < 70: return "中性(30-70) → 不修正"
    if rsi < 80: return "超买(70-80) → 接近卖点，-3分"
    return "极度超买(80-100) → 回调风险，-5分"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == '--etfirst':
        code = sys.argv[2]
        rsi, err = from_etfirst(code)
        if err: print(f"错误: {err}"); sys.exit(1)
        print(f"基金 {code}: RSI(14) = {rsi}")
        print(f"信号: {rsi_signal(rsi)}")
    else:
        path = sys.argv[1]
        period = int(sys.argv[2]) if len(sys.argv) > 2 else 14
        rsi = from_csv(path, period)
        if rsi is None: print("无法计算（数据不足）"); sys.exit(1)
        print(f"RSI({period}) = {rsi}")
        print(f"信号: {rsi_signal(rsi)}")
