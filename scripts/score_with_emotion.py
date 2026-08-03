#!/usr/bin/env python3
"""FAMAS 情绪校准评分工具 — 恐贪指数 + RSI

用法:
  python3 score_with_emotion.py <基金代码1> [基金代码2 ...]
  python3 score_with_emotion.py 024418 015795 007467

功能:
  1. 从 etfirst 拉取净值序列
  2. 计算每只基金 RSI(14)
  3. 根据市场恐贪指数 + RSI 校准基础分
  4. 输出适配度等级（合规版，不输出交易指令）
"""
import sys, os, json, subprocess, shutil

# 找到 etfirst
def find_etfirst():
    candidates = [
        os.path.expanduser("~/.local/bin/etfirst"),
        "/usr/local/bin/etfirst",
        shutil.which("etfirst"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

ETFIRST = find_etfirst()
if not ETFIRST:
    print("错误: 找不到 etfirst，请先安装", file=sys.stderr)
    sys.exit(1)

# 基础分（由五维评分引擎算出，可通过 BASE_SCORES 环境变量传入，格式: 代码:分数,代码:分数）
BASE_SCORES = {}
for _pair in os.environ.get('BASE_SCORES', '').split(','):
    if ':' in _pair:
        _c, _s = _pair.split(':')
        BASE_SCORES[_c.strip()] = float(_s.strip())

# 恐贪区间校准
FG_RULES = [
    (0, 20, 5, "极度恐惧"), (20, 40, 3, "恐惧"),
    (40, 60, 0, "中性"), (60, 80, -3, "贪婪"), (80, 100, -5, "极度贪婪"),
]

# RSI 区间校准
RSI_RULES = [
    (0, 20, 5, "极度超卖"), (20, 30, 3, "超卖"),
    (30, 70, 0, "中性"), (70, 80, -3, "超买"), (80, 100, -5, "极度超买"),
]

def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0)); losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def fetch_nav(code):
    """从 etfirst 拉取净值序列（绕过代理）"""
    env = dict(os.environ)
    for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        env.pop(k, None)
    r = subprocess.run(
        [ETFIRST, '--json', 'otc-detail', 'all', '--product-code', str(code), '--date-range', '250'],
        capture_output=True, text=True, env=env
    )
    if r.returncode != 0: return None, r.stderr[:100]
    try:
        d = json.loads(r.stdout)
    except: return None, "JSON解析失败"
    results = d.get('results', {})
    tr = results.get('getReturnTrendList', {})
    series = None
    if isinstance(tr, dict):
        for k, v in tr.items():
            if isinstance(v, list) and v:
                series = v; break
    if not series:
        hist = results.get('list', [])
        if isinstance(hist, list) and len(hist) > 30:
            pes = [float(h.get('PE')) for h in hist if h.get('PE')]
            if len(pes) > 30: series = [{"closePrice": p} for p in pes]
    if not series: return None, "无净值序列"
    closes = [float(x.get('closePrice')) for x in series if x.get('closePrice')]
    if len(closes) < 30: return None, "数据不足30天"
    return closes, None

def fg_adjustment(fg_value):
    for lo, hi, adj, label in FG_RULES:
        if lo <= fg_value <= hi: return adj, label
    return 0, "未知"

def rsi_adjustment(rsi):
    for lo, hi, adj, label in RSI_RULES:
        if lo <= rsi <= hi: return adj, label
    return 0, "未知"

def adaptation_level(total):
    """将总分映射为适配度等级（合规版，不输出交易指令）"""
    if total >= 85: return "★★★★★ 高适配"
    if total >= 70: return "★★★★☆ 较高适配"
    if total >= 55: return "★★★☆☆ 中等适配"
    if total >= 40: return "★★☆☆☆ 较低适配"
    if total >= 25: return "★☆☆☆☆ 低适配"
    return "☆☆☆☆☆ 极低适配"

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    codes = sys.argv[1:]
    fg_value = float(os.environ.get('FG_INDEX', '25'))
    fg_adj, fg_label = fg_adjustment(fg_value)

    print(f"{'基金':<12}{'RSI':<7}{'RSI状态':<14}{'基础分':<7}{'RSI调':<6}{'恐贪调':<6}{'校准后':<7}{'适配度'}")
    print("-"*72)
    for code in codes:
        closes, err = fetch_nav(code)
        if err:
            print(f"{code:<12}数据错误: {err}")
            continue
        rsi = calc_rsi(closes)
        rsi_adj, rsi_label = rsi_adjustment(rsi)
        base = BASE_SCORES.get(code, 50)
        total = base + rsi_adj + fg_adj
        sr = f"{rsi_adj:+d}"
        sf = f"{fg_adj:+d}"
        print(f"{code:<12}{rsi:<7}{rsi_label:<14}{base:<7.1f}{sr:<6}{sf:<6}{total:<7.1f}{adaptation_level(total)}")

    print(f"\n恐贪指数: {fg_value:.0f} ({fg_label}) → 校准 {fg_adj:+d}")
    print("提示: 基础分默认50，可通过 BASE_SCORES='代码:分数,代码:分数' 环境变量传入真实评分")

if __name__ == '__main__':
    main()
