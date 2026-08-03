#!/usr/bin/env python3
"""板块资金流自动获取器 — 基于 etfirst（稳定）替代 AKShare（不稳定）

功能:
  1. 自动从 etfirst 拉取各板块指数的净流入历史
  2. 计算资金连续性评分（近20日净流入轨迹）
  3. 自动汇总涨跌幅、估值分位
  4. 存储到 data/fund_flow/auto/

用法:
  python3 auto_fund_flow.py              # 获取全部配置板块
  python3 auto_fund_flow.py --score      # 计算资金连续性评分
  python3 auto_fund_flow.py --list       # 列出可用指数
"""
import os, sys, json, subprocess, shutil, glob
from datetime import datetime

# 绕过代理
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR = os.path.abspath(os.path.join(BASE, "data", "fund_flow", "auto"))
os.makedirs(DATA_DIR, exist_ok=True)

# 找到 etfirst
def find_etfirst():
    for c in [os.path.expanduser("~/.local/bin/etfirst"), "/usr/local/bin/etfirst", shutil.which("etfirst")]:
        if c and os.path.exists(c):
            return c
    return None

ETFIRST = find_etfirst()

# 板块 → 指数代码映射
SECTOR_INDICES = {
    "软件服务": "930601", "科创半导体": "950125", "红利低波": "H30269",
    "恒生科技": "HSTECH", "港股创新药": "931787", "创业板指": "399006",
    "证券公司": "399975", "人工智能": "930713", "中证医疗": "399989",
    "消费": "000932", "中证白酒": "399997", "中证有色": "399395",
    "中证军工": "399967", "中证银行": "399986", "中证传媒": "399971",
    "中证煤炭": "399998", "中证电子": "930652", "电力": "H30199",
    "云计算": "930851", "机器人": "950096", "创新药": "931152",
    "细分食品": "000815", "CS计算机": "930651", "800证保": "399966",
}

def fetch_index(code, name):
    """从 etfirst 拉取指数详情"""
    env = dict(os.environ)
    for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
        env.pop(k, None)
    r = subprocess.run(
        [ETFIRST, '--json', 'index-detail', 'all', '--index-code', code, '--index-type', '1'],
        capture_output=True, text=True, env=env
    )
    if r.returncode != 0:
        return None, r.stderr[:80]
    try:
        d = json.loads(r.stdout)
    except:
        return None, "JSON解析失败"
    results = d.get('results', {})
    qd = results.get('queryIndexDetail', {})
    cr = results.get('queryChangeRateByIndexCode', {})
    ni = results.get('queryNetInflow', [])
    
    return {
        "name": name, "index_code": code,
        "gain_today": qd.get('percentageChange'),
        "pe_percent": qd.get('pePercent'),
        "pe": qd.get('pe'),
        "m1": cr.get('lastOneMonthChangeRate'),
        "m3": cr.get('lastThreeMonthChangeRate'),
        "net_inflow_history": [
            {"date": x.get('tradingDay'), "flow": float(x.get('netInflowValue', 0))}
            for x in ni if isinstance(ni, list)
        ],
    }, None

def continuity_score(history, window=5):
    """计算资金连续性评分（0-10）
    规则:
      - 最近 window 条净流入，正数多=强
      - 连续为正加分，连续为负减分
    """
    if not history:
        return 0, 0
    recent = history[-window:]
    positive = sum(1 for h in recent if h["flow"] > 0)
    flows = [h["flow"] for h in recent]
    avg_flow = sum(flows) / len(flows)
    
    # 连续正/负检测
    consecutive_pos = 0
    consecutive_neg = 0
    for h in reversed(recent):
        if h["flow"] > 0:
            consecutive_pos += 1
            consecutive_neg = 0
        else:
            consecutive_neg += 1
            consecutive_pos = 0
    
    score = 0
    if avg_flow > 50: score += 4
    elif avg_flow > 10: score += 3
    elif avg_flow > 0: score += 2
    elif avg_flow > -10: score += 1
    else: score += 0
    
    score += min(3, positive)  # 正天数加分
    score += min(3, consecutive_pos)  # 连续正加分
    score -= min(2, consecutive_neg)  # 连续负减分
    
    return max(0, min(10, score)), round(avg_flow, 1)

def fetch_all():
    """获取所有板块数据"""
    results = {}
    for name, code in SECTOR_INDICES.items():
        print(f"  拉取 {name}({code})...", end="")
        data, err = fetch_index(code, name)
        if err:
            print(f" ❌ {err}")
            continue
        score, avg_flow = continuity_score(data.get("net_inflow_history", []))
        data["continuity_score"] = score
        data["avg_flow"] = avg_flow
        results[name] = data
        print(f" ✅ 连续性={score}")
    return results

def main():
    if not ETFIRST:
        print("错误: 找不到 etfirst"); sys.exit(1)
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    
    if cmd == "--list":
        for name, code in SECTOR_INDICES.items():
            print(f"  {name}: {code}")
        return
    
    if cmd == "--score":
        # 读取最近数据
        files = sorted(glob.glob(os.path.join(DATA_DIR, "sectors_*.json")))
        if not files:
            print("暂无数据，请先运行获取"); return
        with open(files[-1], encoding="utf-8") as f:
            data = json.load(f)
        print(f"\n=== 资金连续性评分 ({files[-1].split('/')[-1]}) ===")
        for name, d in sorted(data.items(), key=lambda x: -x[1]["continuity_score"]):
            print(f"  {name}: {d['continuity_score']}分 | 平均资金{d['avg_flow']}亿 | 近1月{d['m1']}%")
        return
    
    # 默认: 获取全部
    print("=== 从 etfirst 获取板块资金数据 ===")
    results = fetch_all()
    path = os.path.join(DATA_DIR, f"sectors_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存到 {path}")
    
    # 展示评分
    print("\n=== 资金连续性评分 ===")
    for name, d in sorted(results.items(), key=lambda x: -x[1]["continuity_score"]):
        print(f"  {name}: {d['continuity_score']}分 | 平均资金{d['avg_flow']}亿 | 近1月{d['m1']}%")

if __name__ == "__main__":
    main()
